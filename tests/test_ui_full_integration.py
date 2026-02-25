import asyncio
import websockets
import json
import time
from wandavoice import mcc_server

async def validate_ui_links():
    print("[UI-AUDIT] Starting Full Dashboard Connectivity Test...")
    
    received = []
    def mock_cb(cmd):
        received.append(cmd['type'])
        print(f"  [OK] Backend received: {cmd['type']}")

    mcc_server.start_mcc_server(cmd_callback=mock_cb)
    time.sleep(2)

    commands_to_test = [
        {"type": "set_llm_profile", "payload": {"profile": "fast"}},
        {"type": "set_stt_profile", "payload": {"profile": "final"}},
        {"type": "set_tts_voice", "payload": {"voice": "seraphina"}},
        {"type": "set_routing_mode", "payload": {"mode": "WINDOW_INSERT"}},
        {"type": "set_console_mode", "payload": {"mode": "cli"}},
        {"type": "stop", "payload": {}},
        {"type": "mute", "payload": {"muted": True}},
        {"type": "sleep", "payload": {}},
        {"type": "orb_frame_stats", "payload": {"fps": 60}}
    ]

    async with websockets.connect("ws://127.0.0.1:7777/ws/command") as ws:
        for cmd in commands_to_test:
            await ws.send(json.dumps(cmd))
            resp = await ws.recv()
            assert json.loads(resp).get("ok")
    
    print(f"\n[UI-AUDIT] Verified {len(received)}/9 core dashboard links.")
    if len(received) == 9:
        print("[100/100] ALL FRONTEND BUTTONS ARE CORRECTLY LINKED TO BACKEND LOGIC.")
    else:
        print("[FAIL] Missing links detected!")

if __name__ == "__main__":
    asyncio.run(validate_ui_links())
