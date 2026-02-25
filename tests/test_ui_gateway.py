import asyncio
import websockets
import json
import threading
import time
from wandavoice import mcc_server

async def test_gateway_logic():
    print("[TEST] Starting MCC Gateway Validation...")
    
    # 1. Start MCC Server in background
    # We mock the command callback to verify commands reach the engine
    received_commands = []
    def cmd_callback(cmd):
        received_commands.append(cmd)
        print(f"[TEST] Engine received command: {cmd['type']}")

    # Start server (we don't need the web UI for this logic test)
    mcc_server.start_mcc_server(cmd_callback=cmd_callback)
    time.sleep(2) # Wait for bind
    
    try:
        # 2. Connect as a client to /ws/events
        async with websockets.connect("ws://127.0.0.1:7777/ws/events") as ws_e:
            print("[TEST] Connected to Events WebSocket.")
            
            # 3. Connect as a client to /ws/command
            async with websockets.connect("ws://127.0.0.1:7777/ws/command") as ws_c:
                print("[TEST] Connected to Command WebSocket.")
                
                # 4. Test Broadcast (Engine -> UI)
                mcc_server.broadcast("test_event", {"val": 42})
                
                # Read from events socket
                # The first message is always session_start from our handler
                msg1 = await ws_e.recv()
                msg2 = await ws_e.recv()
                
                event_data = json.loads(msg2)
                if event_data['type'] == 'test_event' and event_data['payload']['val'] == 42:
                    print("[OK] Broadcast Event received by Client.")
                else:
                    print(f"[FAIL] Unexpected event: {event_data}")

                # 5. Test Command (UI -> Engine)
                cmd = {"type": "set_llm_profile", "payload": {"profile": "fast"}}
                await ws_c.send(json.dumps(cmd))
                
                # Wait for response from server
                resp = await ws_c.recv()
                if json.loads(resp).get("ok"):
                    print("[OK] Command acknowledgement received.")
                
                # Check if callback was triggered
                time.sleep(0.5)
                if any(c['type'] == 'set_llm_profile' for c in received_commands):
                    print("[OK] Engine callback triggered with correct data.")
                else:
                    print("[FAIL] Engine callback NOT triggered.")

    except Exception as e:
        print(f"[ERROR] Gateway Test failed: {e}")
    finally:
        # Cleanup: we can't easily stop the mcc_server thread without force
        print("[TEST] Validation complete.")

if __name__ == "__main__":
    asyncio.run(test_gateway_logic())
