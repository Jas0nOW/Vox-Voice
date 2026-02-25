#!/usr/bin/env python3
"""
WANDA State Relay — ws://127.0.0.1:7777
/ws/events  → pub/sub broadcast (orb + MCC listen here)
/ws/command → MCC sends commands here; relay maps them to events
"""

import asyncio
import json
import logging

import websockets
from websockets.server import serve

logging.basicConfig(level=logging.INFO, format="[relay] %(message)s")
log = logging.getLogger(__name__)

# ── Subscriber sets ──────────────────────────────────────────────────────────
_event_clients: set = set()

# ── Command → Event mapping ──────────────────────────────────────────────────
# Each command maps to a list of event dicts to broadcast
CMD_EVENTS: dict[str, list[dict]] = {
    "start_sim":  [{"type": "session_start"}, {"type": "vad_start"}],
    "stop":       [{"type": "tts_stop"}, {"type": "session_end"}],
    "mute":       [{"type": "muted"}],
    "sleep":      [{"type": "sleep_ack"}, {"type": "session_end"}],
    "ptt_start":  [{"type": "vad_start"}],
    "ptt_stop":   [{"type": "stt_final", "payload": {"text": "", "confidence": 1.0}}],
}

# Commands that get echoed back as-is (with their payload)
CMD_ECHO = {
    "set_routing_mode",
    "set_console_mode",
    "set_llm_backend",
    "set_llm_profile",
    "set_wake_words",
    "set_skill_allowlist",
    "watchdog_restart",
    "mark_golden",
    "cancel_request",
}


async def broadcast(event: dict) -> None:
    if not _event_clients:
        return
    msg = json.dumps(event)
    dead = set()
    for ws in list(_event_clients):
        try:
            await ws.send(msg)
        except Exception:
            dead.add(ws)
    _event_clients.difference_update(dead)


# ── Handlers ─────────────────────────────────────────────────────────────────
async def handle_events(ws) -> None:
    """Subscriber: holds connection open, receives broadcast events."""
    _event_clients.add(ws)
    log.info("events client connected  (total=%d)", len(_event_clients))
    try:
        await ws.wait_closed()
    finally:
        _event_clients.discard(ws)
        log.info("events client gone       (total=%d)", len(_event_clients))


async def handle_command(ws) -> None:
    """Command sink: reads MCC commands, emits matching events."""
    log.info("command client connected")
    try:
        async for raw in ws:
            try:
                cmd = json.loads(raw)
            except Exception:
                continue

            ctype   = cmd.get("type", "")
            payload = cmd.get("payload", {}) or {}

            log.info("cmd: %s %s", ctype, payload)

            # Map → events
            for ev in CMD_EVENTS.get(ctype, []):
                await broadcast({**ev, "payload": {**ev.get("payload", {}), **payload}})

            # Echo passthrough commands
            if ctype in CMD_ECHO:
                await broadcast({"type": ctype, "payload": payload})

            # Ack to sender
            try:
                await ws.send(json.dumps({"ok": True, "type": ctype}))
            except Exception:
                pass

    except websockets.exceptions.ConnectionClosed:
        pass
    log.info("command client gone")


# ── Router ────────────────────────────────────────────────────────────────────
async def router(ws) -> None:
    path = ws.request.path
    if path == "/ws/events":
        await handle_events(ws)
    elif path == "/ws/command":
        await handle_command(ws)
    else:
        await ws.close(1008, f"Unknown path: {path}")


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    log.info("WANDA relay starting on ws://127.0.0.1:7777")
    log.info("  /ws/events  — subscribe (orb, MCC)")
    log.info("  /ws/command — publish   (MCC buttons)")
    async with serve(router, "127.0.0.1", 7777):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
