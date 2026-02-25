from __future__ import annotations

import json
from fastapi import FastAPI, WebSocket
import uvicorn

from voice_engine.engine import VoiceEngine
from voice_engine.events import Command

async def run_gateway(engine: VoiceEngine, host: str, port: int, autostart: bool = False) -> None:
    app = FastAPI()

    @app.websocket("/ws/events")
    async def ws_events(ws: WebSocket):
        await ws.accept()
        q = engine.bus.subscribe()
        if autostart:
            await engine.handle_command(Command(type="start_sim"))
        try:
            while True:
                ev = await q.get()
                await ws.send_text(ev.model_dump_json())
        except Exception:
            return

    @app.websocket("/ws/command")
    async def ws_command(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                msg = await ws.receive_text()
                cmd = Command.model_validate_json(msg)
                await engine.handle_command(cmd)
                await ws.send_text(json.dumps({"ok": True}))
        except Exception:
            return

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
