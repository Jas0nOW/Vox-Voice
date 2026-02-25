import os
import sys

PID_FILE = os.path.expanduser("~/Schreibtisch/Work-OS/40_Products/Vox-Voice/.runtime/vox.pid")

def acquire_lock():
    """
    Acquires a single-instance lock for the Voice Engine.
    Returns True if acquired, False if another instance is already running.
    """
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)

    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            
            # Check if process is still running
            # In UNIX, os.kill(pid, 0) does not kill the process but checks if we can send signals
            # which essentially checks if the process exists and is accessible.
            os.kill(old_pid, 0)
            
            # If we reach here, the process is alive
            return False
            
        except (ValueError, OSError, ProcessLookupError):
            # Process is dead or file is corrupt, we can take over
            pass

    # Write our own PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
        
    return True

def release_lock():
    """
    Removes the PID file on clean shutdown.
    """
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass
