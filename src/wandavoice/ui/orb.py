# VOX Orb + MCC UI — tkinter-based, runs via XWayland on COSMIC/Wayland
import threading
import time
import math


# State → color mapping
_ORB_COLORS = {
    "idle":      "#2E2E3A",  # deep slate
    "loading":   "#F2A900",  # vibrant gold
    "listening": "#007BFF",  # neon blue
    "thinking":  "#A020F0",  # purple/magenta
    "speaking":  "#00FF66",  # bright green
    "error":     "#FF3333",  # red
}

_ORB_TERM = {
    "idle":      "\033[90m",
    "loading":   "\033[93m",
    "listening": "\033[94m",
    "thinking":  "\033[95m",
    "speaking":  "\033[92m",
    "error":     "\033[91m",
}


def create_round_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class VoxOrb:
    """
    Sleek, Modern Graphical Orb + MCC using tkinter.
    """

    def __init__(self, config):
        self.config = config
        self.enabled = config.get("voice.ui.orb_enabled", True)
        self.height = int(config.get("voice.ui.orb.size", 72))
        self.width = int(self.height * 3.5) # Oval shape
        self.alpha = float(config.get("voice.ui.orb.alpha", 0.90))
        self.position = config.get("voice.ui.orb.position", "top-right")
        self.padding = int(config.get("voice.ui.orb.padding", 24))

        self._root = None
        self._orb_canvas = None
        self._orb_bg = None
        self._orb_label = None
        self._bars = []
        
        self.num_bars = 16
        self.bar_history = [0.0] * self.num_bars

        self._mcc_win = None
        self._mcc_canvas = None
        self._mcc_state_text = None
        self._mcc_user_text = None
        self._mcc_vox_text = None
        
        self._state = "loading"
        self._running = False
        self._ready = threading.Event()
        self._tk_ok = False

        if self.enabled:
            print(f"UI initialized (width={self.width}, height={self.height})")

    def _broadcast_event(self, type_str: str, payload: dict):
        try:
            from wandavoice.mcc_server import broadcast
            broadcast(type_str, payload)
        except Exception:
            pass

    def set_state(self, state: str):
        self._state = state
        color = _ORB_TERM.get(state, "")
        print(f"{color}[ORB] {state.upper()}\033[0m")
        
        # Map orb states to MCC states
        if state == "listening":
            self._broadcast_event("session_start", {})
        elif state == "thinking":
            self._broadcast_event("llm_done", {"tokens": "?", "backend": "gemini", "profile": "auto"})
        elif state == "speaking":
            self._broadcast_event("tts_start", {})
        elif state == "idle":
            self._broadcast_event("session_end", {})
            
        if self._tk_ok and self._root:
            fill = _ORB_COLORS.get(state, "#2E2E3A")
            self._root.after(0, self._tk_set_state, state, fill)

    def set_audio_level(self, level: float):
        if self._state == "listening":
            self._broadcast_event("audio_level", {"rms": level})
        if self._tk_ok and self._root and self._state == "listening":
            self._root.after(0, self._tk_update_bars, level)

    def set_transcript(self, text: str):
        self._broadcast_event("stt_partial", {"text": text})
        if self._tk_ok and self._root:
            self._root.after(0, self._tk_set_transcript, text)

    def set_response(self, text: str):
        self._broadcast_event("llm_stream_chunk", {"text": text + "\n"})
        if self._tk_ok and self._root:
            self._root.after(0, self._tk_set_response, text)

    def _tk_set_state(self, state: str, fill: str):
        try:
            if hasattr(self, "_pill_canvas") and self._pill_bg:
                self._pill_canvas.itemconfig(self._pill_bg, fill=fill)
            if hasattr(self, "_pill_label") and self._pill_label:
                self._pill_canvas.itemconfig(self._pill_label, text=state.upper())
            if hasattr(self, "_console_canvas") and self._console_state_text:
                self._console_canvas.itemconfig(self._console_state_text, text=state.upper(), fill=fill)
                
            if state != "listening":
                self.bar_history = [0.0] * self.num_bars
                self._tk_draw_bars()
                
        except Exception:
            pass

    def _tk_set_transcript(self, text: str):
        try:
            if hasattr(self, "_console_canvas") and self._console_user_text:
                self._console_canvas.itemconfig(self._console_user_text, text=f"{text[:140]}")
        except: pass

    def _tk_set_response(self, text: str):
        try:
            if hasattr(self, "_console_canvas") and self._console_vox_text:
                self._console_canvas.itemconfig(self._console_vox_text, text=f"{text[:200]}")
        except: pass

    def _tk_update_bars(self, level: float):
        try:
            self.bar_history.pop(0)
            scaled = min(level * 12.0, 1.0)
            self.bar_history.append(scaled)
            self._tk_draw_bars()
        except Exception:
            pass

    def _tk_draw_bars(self):
        if not hasattr(self, "_pill_canvas") or not self._bars:
            return
        max_h = self.height * 0.45
        mid_y = self.height / 2
        for i, val in enumerate(self.bar_history):
            h = max(3, val * max_h)
            x0, y0, x1, y1 = self._pill_canvas.coords(self._bars[i])
            self._pill_canvas.coords(self._bars[i], x0, mid_y - h/2, x1, mid_y + h/2)

    def _build_pill_window(self, root):
        """Builds the VOX Pill (Small Speech Window)."""
        import tkinter as tk

        pill = tk.Toplevel(root)
        pill.title("VOX Pill")
        pill.overrideredirect(True)
        pill.attributes("-topmost", True)
        pill.attributes("-alpha", self.alpha)
        pill.configure(bg="#000000")

        sw = root.winfo_screenwidth()
        if self.position == "top-right":
            x = sw - self.width - self.padding
            y = self.padding
        else:
            x = self.padding
            y = self.padding

        pill.geometry(f"{self.width}x{self.height}+{x}+{y}")

        canvas = tk.Canvas(
            pill, width=self.width, height=self.height,
            bg="#000000", highlightthickness=0
        )
        canvas.pack()

        pad = 6
        radius = (self.height - 2*pad) / 2
        self._pill_bg = create_round_rect(canvas, pad, pad, self.width - pad, self.height - pad, radius, fill=_ORB_COLORS["loading"], outline="")

        self._pill_label = canvas.create_text(
            self.width * 0.25, self.height // 2,
            text="LOAD", fill="#FFFFFF",
            font=("Helvetica", 10, "bold")
        )

        bar_width = 4
        bar_spacing = 5
        total_bars_width = self.num_bars * (bar_width + bar_spacing)
        start_x = self.width - pad - radius - total_bars_width + 10

        for i in range(self.num_bars):
            bx = start_x + i * (bar_width + bar_spacing)
            by = self.height / 2
            bar = canvas.create_line(bx, by-1, bx, by+1, width=bar_width, fill="#FFFFFF", capstyle="round")
            self._bars.append(bar)

        self._pill_canvas = canvas

    def _build_console_window(self, root):
        """Builds the VOX Console (Chat Window)."""
        import tkinter as tk

        console = tk.Toplevel(root)
        console.title("VOX Console")
        console.attributes("-topmost", True)
        console.attributes("-alpha", self.alpha)
        console.configure(bg="#000000")
        console.resizable(True, True)

        W, H = 400, 250
        sw = root.winfo_screenwidth()
        x = sw - W - self.padding
        y = self.height + self.padding * 2
        console.geometry(f"{W}x{H}+{x}+{y}")
        
        canvas = tk.Canvas(console, width=W, height=H, bg="#000000", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        self._console_canvas = canvas
        self._console_win = console
        self._draw_console_contents(W, H)
        console.bind("<Configure>", self._on_console_resize)

    def _draw_console_contents(self, W, H):
        canvas = self._console_canvas
        canvas.delete("all")
        pad = 8
        create_round_rect(canvas, pad, pad, W-pad, H-pad, 16, fill="#12121A", outline="#2E2E3A", width=2)
        
        canvas.create_text(pad + 20, pad + 20, text="VOX CONSOLE", fill="#A0A0B0", font=("Helvetica", 9, "bold"), anchor="w")
        self._console_state_text = canvas.create_text(W - pad - 20, pad + 20, text=self._state.upper(), fill=_ORB_COLORS.get(self._state, "#F2A900"), font=("Helvetica", 9, "bold"), anchor="e")
        canvas.create_line(pad+20, pad+35, W-pad-20, pad+35, fill="#2E2E3A", width=1)

        canvas.create_text(pad + 20, pad + 55, text="YOU", fill="#666677", font=("Helvetica", 8, "bold"), anchor="w")
        self._console_user_text = canvas.create_text(pad + 20, pad + 75, text="—", fill="#E0E0E0", font=("Helvetica", 11), anchor="nw", width=W-2*pad-40)

        canvas.create_text(pad + 20, H - 90, text="VOX", fill="#666677", font=("Helvetica", 8, "bold"), anchor="w")
        self._console_vox_text = canvas.create_text(pad + 20, H - 70, text="—", fill="#00FF66", font=("Helvetica", 11), anchor="nw", width=W-2*pad-40)

    def _on_console_resize(self, event):
        if hasattr(self, "_last_console_size") and self._last_console_size == (event.width, event.height): return
        if event.width < 100 or event.height < 100: return
        self._last_console_size = (event.width, event.height)
        self._draw_console_contents(event.width, event.height)

    def run(self, show_pill=True):
        if not self.enabled: return
        self._running = True
        try:
            import tkinter as tk
            self._root = tk.Tk()
            self._root.withdraw() 
            if show_pill: self._build_pill_window(self._root)
            self._build_console_window(self._root)
            self._tk_ok = True
            self._ready.set()
            self._root.mainloop()
        except Exception as e:
            print(f"[ORB] Window error: {e}")
            self._ready.set()
        finally:
            self._tk_ok = False
            self._running = False

    def run_standalone(self, ws_url: str, show_pill=True):
        """Runs the UI as a standalone process connected via WebSocket."""
        import asyncio
        import websockets
        import json
        import threading
        import time

        def ws_worker():
            async def _listen():
                while self._running:
                    try:
                        async with websockets.connect(ws_url) as ws:
                            print(f"[UI] Connected to Engine at {ws_url}")
                            async for msg in ws:
                                ev = json.loads(msg)
                                typ = ev.get("type")
                                payload = ev.get("payload", {})
                                
                                if typ == "session_start": self.set_state("listening")
                                elif typ == "session_end": self.set_state("idle")
                                elif typ == "tts_start": self.set_state("speaking")
                                elif typ == "llm_done": self.set_state("thinking")
                                elif typ == "stt_partial": self.set_transcript(payload.get("text", ""))
                                elif typ == "llm_stream_chunk": self.set_response(payload.get("text", "").strip())
                                elif typ == "audio_level": self.set_audio_level(float(payload.get("rms", 0.0)))
                    except Exception as e:
                        # Log error and wait for retry
                        self.set_transcript("Waiting for VOX Engine...")
                        time.sleep(3)
            
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_listen())

        threading.Thread(target=ws_worker, daemon=True).start()
        self.run(show_pill=show_pill)
        if not self.enabled:
            return
        self._running = True
        try:
            import tkinter as tk

            self._root = tk.Tk()
            self._root.withdraw() 

            if show_orb:
                self._build_orb_window(self._root)
            
            self._build_mcc_window(self._root)

            self._tk_ok = True
            self._ready.set()
            self._root.mainloop()
        except Exception as e:
            print(f"[ORB] Window error: {e} — using terminal fallback")
            self._ready.set()
        finally:
            self._tk_ok = False
            self._running = False

    def stop(self):
        self._running = False
        if hasattr(self, '_gtk_process') and self._gtk_process:
            try:
                self._gtk_process.terminate()
                self._gtk_process.wait(timeout=1.0)
            except Exception:
                try:
                    self._gtk_process.kill()
                except:
                    pass
        
        if self._tk_ok and self._root:
            try:
                # To prevent "Tcl_AsyncDelete: async handler deleted by the wrong thread" 
                # we don't aggressively destroy on stop if not in main thread,
                # we let the thread die naturally or safely schedule a quit.
                self._root.after_idle(self._root.quit)
            except Exception:
                pass
