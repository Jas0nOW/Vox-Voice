#!/usr/bin/env python3
import argparse
import asyncio
import json
import math
import os
import threading
import time
import cairo
from typing import Optional

import websockets

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, GLib, Gtk4LayerShell

STATE_MAP = {
    "wake_detected":  "WAKE_DETECTED",
    "vad_start":      "LISTENING",
    "stt_final":      "THINKING",
    "llm_start":      "THINKING",
    "llm_working":    "WORKING",
    "tts_start":      "SPEAKING",
    "tts_stop":       "SLEEPING",
    "session_start":  "LISTENING",
    "session_end":    "SLEEPING",
    "cancel_request": "LISTENING",
    "cancel_done":    "SLEEPING",
    "error_raised":   "ERROR",
    # Mute / sleep acks — sent by backend after cmd processing
    "muted":          "MUTED",
    "mute_ack":       "MUTED",
    "sleeping":       "SLEEPING",
    "sleep_ack":      "SLEEPING",
}

_POS_FILE = os.path.expanduser("~/.config/wanda/orb_pos.json")

def ewma(prev, x, alpha=0.15):
    return prev*(1-alpha) + x*alpha

class OrbModel:
    def __init__(self):
        self.state = "SLEEPING"
        self.mic_rms = 0.0
        self.out_rms = 0.0
        self.phase = 0.0

class OrbWindow(Gtk.ApplicationWindow):
    def __init__(self, app, ws_url: str, cmd_url: Optional[str], size: int = 140):
        super().__init__(application=app, title="Wanda Orb")
        self.set_default_size(size, size)
        self.set_decorated(False)
        self.set_resizable(False)

        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.NONE)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT, True)

        # Load persisted position (defaults: top=18, right=18)
        self._margin_top, self._margin_right = self._load_pos()
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP,   self._margin_top)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.RIGHT, self._margin_right)
        self._drag_start_top   = self._margin_top
        self._drag_start_right = self._margin_right

        self.model = OrbModel()

        self.drawing = Gtk.DrawingArea()
        self.drawing.set_draw_func(self.on_draw)
        self.set_child(self.drawing)

        # Drag to reposition the orb window via Layer Shell margin adjustment.
        # GestureDrag + set_state(CLAIMED) is critical: CLAIMED causes GTK to
        # keep delivering pointer events even when the mouse leaves the widget.
        drag = Gtk.GestureDrag()
        drag.set_button(1)  # left mouse button only
        drag.connect("drag-begin",  self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        drag.connect("drag-end",    self._on_drag_end)
        self.drawing.add_controller(drag)

        # 60fps redraw loop + dropped frames counter
        self.target_dt = 1.0 / 60.0
        self._last_draw_t = time.perf_counter()
        self._frames = 0
        self._dropped = 0
        self._fps_last = time.perf_counter()
        self._last_fps = 0.0

        def tick():
            now = time.perf_counter()
            dt = now - self._last_draw_t
            self._last_draw_t = now
            if dt > self.target_dt * 1.5:
                self._dropped += 1
            self._frames += 1

            # Compute FPS once per second
            if now - self._fps_last >= 1.0:
                self._last_fps = self._frames / (now - self._fps_last)
                self._fps_last = now
                self._frames = 0

                if cmd_url:
                    # fire-and-forget in a thread (avoid blocking GTK loop)
                    threading.Thread(target=send_orb_stats, args=(cmd_url, self._last_fps, self._dropped), daemon=True).start()

            self.drawing.queue_draw()
            return True

        GLib.timeout_add(int(self.target_dt * 1000), tick)

        # background WS subscriber
        t = threading.Thread(target=run_ws_subscriber, args=(ws_url, self.model), daemon=True)
        t.start()

    # ── Position persistence ──────────────────────────────────────
    def _load_pos(self):
        try:
            with open(_POS_FILE) as f:
                d = json.load(f)
                return int(d.get("top", 18)), int(d.get("right", 18))
        except Exception:
            return 18, 18

    def _save_pos(self):
        try:
            os.makedirs(os.path.dirname(_POS_FILE), exist_ok=True)
            with open(_POS_FILE, "w") as f:
                json.dump({"top": self._margin_top, "right": self._margin_right}, f)
        except Exception:
            pass

    # ── Drag handlers ─────────────────────────────────────────────
    def _on_drag_begin(self, gesture, sx, sy):
        # CLAIMED: GTK keeps delivering events even when pointer leaves widget
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        self._drag_start_top   = self._margin_top
        self._drag_start_right = self._margin_right

    def _on_drag_update(self, gesture, offset_x, offset_y):
        new_top   = max(0, self._drag_start_top   + int(offset_y))
        new_right = max(0, self._drag_start_right - int(offset_x))
        self._margin_top   = new_top
        self._margin_right = new_right
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.TOP,   new_top)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.RIGHT, new_right)

    def _on_drag_end(self, gesture, offset_x, offset_y):
        self._save_pos()

    def on_draw(self, area, ctx, width, height):
        m = self.model
        cx, cy = width/2, height/2
        r = min(width, height) * 0.42

        state = m.state

        # Color palette per state
        # glow_rgb, orb_bg_rgba, wave_rgb
        if state == "LISTENING":
            glow_rgb  = (0.0, 0.94, 1.0)      # cyan
            orb_bg    = (0.05, 0.12, 0.18, 0.88)
            wave_rgb  = (0.0, 0.94, 1.0)
            base      = 0.35
        elif state == "THINKING":
            glow_rgb  = (0.55, 0.30, 1.0)     # violet
            orb_bg    = (0.08, 0.06, 0.18, 0.88)
            wave_rgb  = (0.55, 0.30, 1.0)
            base      = 0.28
        elif state == "WORKING":
            glow_rgb  = (1.0, 0.66, 0.0)      # amber/gold
            orb_bg    = (0.20, 0.12, 0.0, 0.88)
            wave_rgb  = (1.0, 0.66, 0.0)
            base      = 0.40
        elif state == "SPEAKING":
            glow_rgb  = (0.84, 0.0, 1.0)      # purple #D600FF
            orb_bg    = (0.12, 0.04, 0.20, 0.88)
            wave_rgb  = (0.84, 0.0, 1.0)
            base      = 0.40
        elif state == "MUTED":
            glow_rgb  = (0.9, 0.15, 0.15)     # red
            orb_bg    = (0.18, 0.06, 0.06, 0.88)
            wave_rgb  = (0.9, 0.15, 0.15)
            base      = 0.12
        elif state == "ERROR":
            glow_rgb  = (1.0, 0.2, 0.2)
            orb_bg    = (0.20, 0.04, 0.04, 0.88)
            wave_rgb  = (1.0, 0.2, 0.2)
            base      = 0.15
        else:  # SLEEPING / WAKE_DETECTED / default
            glow_rgb  = (0.48, 0.63, 0.97)    # soft blue
            orb_bg    = (0.12, 0.14, 0.20, 0.85)
            wave_rgb  = (0.48, 0.63, 0.97)
            base      = 0.2

        # waveform amplitude (suppressed when MUTED/SLEEPING)
        amp = min(1.0, max(m.mic_rms, m.out_rms) * 2.5)
        if state in ("MUTED", "SLEEPING"):
            amp *= 0.15   # nearly still when silent/muted
        m.phase += 0.10 + amp*0.20

        # background (transparent — lets compositor show through)
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.paint()

        # glow ring
        glow = base + amp*0.25
        ctx.set_source_rgba(*glow_rgb, glow)
        ctx.arc(cx, cy, r*1.05 + amp*8, 0, math.tau)
        ctx.fill()

        # main orb body
        ctx.set_source_rgba(*orb_bg)
        ctx.arc(cx, cy, r, 0, math.tau)
        ctx.fill()

        # inner waves
        waves = 12
        for i in range(waves):
            a = (i / waves) * math.tau + m.phase
            rr = r*0.60 + math.sin(a*1.3) * (amp*10)
            alpha = 0.04 + amp*0.10
            ctx.set_source_rgba(*wave_rgb, alpha)
            ctx.arc(cx, cy, rr, 0, math.tau)
            ctx.stroke()

def run_ws_subscriber(ws_url: str, model: OrbModel):
    async def _main():
        while True:
            try:
                async with websockets.connect(ws_url, ping_interval=20) as ws:
                    async for msg in ws:
                        try:
                            ev = json.loads(msg)
                        except Exception:
                            continue
                        typ = ev.get("type")
                        payload = ev.get("payload", {}) or {}

                        if typ in STATE_MAP:
                            model.state = STATE_MAP[typ]
                        if typ == "audio_level":
                            model.mic_rms = ewma(model.mic_rms, float(payload.get("rms", 0.0)))
                        if typ == "audio_level_out":
                            model.out_rms = ewma(model.out_rms, float(payload.get("rms", 0.0)))
            except Exception:
                # Connection failed or lost, retry in 3s
                await asyncio.sleep(3)
    asyncio.run(_main())

def send_orb_stats(cmd_url: str, fps: float, dropped: int):
    async def _send():
        try:
            async with websockets.connect(cmd_url, ping_interval=20) as ws:
                await ws.send(json.dumps({"type":"orb_frame_stats","payload":{"fps": round(fps,1), "dropped_frames": int(dropped)}}))
                # server replies {"ok": true}
                await ws.recv()
        except Exception:
            return
    asyncio.run(_send())

class OrbApp(Gtk.Application):
    def __init__(self, ws_url: str, cmd_url: Optional[str], size: int):
        super().__init__(application_id="de.lazytechlab.wanda.orb")
        self.ws_url = ws_url
        self.cmd_url = cmd_url
        self.size = size

    def do_activate(self):
        win = OrbWindow(self, self.ws_url, self.cmd_url, size=self.size)
        win.present()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", required=True, help="events websocket, e.g. ws://127.0.0.1:7777/ws/events")
    ap.add_argument("--cmd", default=None, help="command websocket, e.g. ws://127.0.0.1:7777/ws/command")
    ap.add_argument("--size", type=int, default=140)
    args = ap.parse_args()
    app = OrbApp(args.ws, args.cmd, args.size)
    app.run(None)

if __name__ == "__main__":
    main()
