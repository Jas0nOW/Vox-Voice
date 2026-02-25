#!/usr/bin/env python3
import threading
import subprocess
import os
import time
import atexit

_backend_proc = None
_frontend_proc = None

def _cleanup():
    global _backend_proc, _frontend_proc
    if _backend_proc:
        try:
            _backend_proc.terminate()
            _backend_proc.wait(timeout=2)
        except Exception:
            pass
        finally:
            try:
                _backend_proc.kill()
            except Exception:
                pass
    if _frontend_proc:
        try:
            _frontend_proc.terminate()
            _frontend_proc.wait(timeout=2)
        except Exception:
            pass
        finally:
            try:
                _frontend_proc.kill()
            except Exception:
                pass

atexit.register(_cleanup)

def start_backend():
    global _backend_proc
    print("[MCC] Starting WebSocket Backend on :7777...")
    backend_dir = os.path.expanduser("~/Schreibtisch/Work-OS/40_Products/Vox-Voice/backend/voice-engine")
    venv_python = os.path.join(backend_dir, ".venv/bin/python")
    cmd = [
        venv_python, "-m", "voice_engine.cli",
        "--mode", "sim", 
        "--config", "config/default.json",
        "--ws-host", "127.0.0.1", 
        "--ws-port", "7777",
        "--autostart"
    ]
    _backend_proc = subprocess.Popen(cmd, cwd=backend_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_frontend():
    global _frontend_proc
    print("[MCC] Starting Web UI on http://127.0.0.1:5173 ...")
    frontend_dir = os.path.expanduser("~/Schreibtisch/Work-OS/40_Products/Vox-Voice/frontend/mcc")
    cmd = ["python3", "-m", "http.server", "5173", "--bind", "127.0.0.1"]
    _frontend_proc = subprocess.Popen(cmd, cwd=frontend_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Try to open the browser
    time.sleep(1.5) # Give backend and frontend time to bind
    try:
        subprocess.Popen(["xdg-open", "http://127.0.0.1:5173"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

if __name__ == "__main__":
    start_backend()
    start_frontend()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
