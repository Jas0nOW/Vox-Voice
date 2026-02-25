import asyncio
import websockets
import json
import threading
import time
import subprocess
import os
import uuid

_connected_clients = set()
_loop = None
_command_callback = None

async def handler(websocket):
    _connected_clients.add(websocket)
    path = websocket.request.path
    try:
        if path == "/ws/events":
            # Send initial session start to sync state
            await websocket.send(json.dumps({
                "session_id": str(uuid.uuid4()),
                "component": "mcc",
                "type": "session_start",
                "payload": {},
                "timestamp": time.time()
            }))
            
            # Keep connection open
            async for msg in websocket:
                pass
                
        elif path == "/ws/command":
            async for msg in websocket:
                try:
                    data = json.loads(msg)
                    if _command_callback:
                        _command_callback(data)
                    await websocket.send(json.dumps({"ok": True}))
                except Exception as e:
                    print(f"MCC Server error processing command: {e}")
                    pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        _connected_clients.remove(websocket)

async def _serve():
    try:
        async with websockets.serve(handler, "127.0.0.1", 7777):
            await asyncio.Future()  # run forever
    except OSError as e:
        print(f"\n[MCC Error] Could not bind to port 7777: {e}")
        print("[MCC Error] Another VOX instance or ghost process is likely running.")
        print("[MCC Error] Run 'vox kill' to clean up your environment.")
        # We exit the thread cleanly instead of crashing


def _start_asyncio_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    try:
        _loop.run_until_complete(_serve())
    except asyncio.CancelledError:
        pass

def broadcast(event_type: str, payload: dict):
    if not _loop or not _connected_clients:
        return
        
    msg = json.dumps({
        "session_id": "vox-local-session",
        "component": "vox",
        "type": event_type,
        "payload": payload,
        "timestamp": time.time()
    })
    
    async def _send():
        tasks = []
        for client in list(_connected_clients):
            try:
                tasks.append(asyncio.create_task(client.send(msg)))
            except Exception:
                pass
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    asyncio.run_coroutine_threadsafe(_send(), _loop)

def start_mcc_server(cmd_callback=None):
    global _command_callback
    _command_callback = cmd_callback
    
    print("[MCC] Starting Native WebSocket Gateway on :7777...")
    t = threading.Thread(target=_start_asyncio_loop, daemon=True)
    t.start()
    
    print("[MCC] Starting Web UI on http://127.0.0.1:5173 ...")
    frontend_dir = os.path.expanduser("~/Schreibtisch/Work-OS/40_Products/Vox-Voice/frontend/mcc")
    
    cmd = ["python3", "-m", "http.server", "5173", "--bind", "127.0.0.1"]
    subprocess.Popen(cmd, cwd=frontend_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(1) # wait for servers to bind
    try:
        subprocess.Popen(["xdg-open", "http://127.0.0.1:5173"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
