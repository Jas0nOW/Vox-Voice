import subprocess
import time
import sys

def insert_text(text: str, mode: str = "active"):
    """
    Inserts text into the active window.
    For Wayland/COSMIC, 'wtype' is preferred.
    Fallback: 'xdotool' for X11, or 'ydotool'.
    """
    if mode == "clipboard":
        try:
            import pyperclip
            pyperclip.copy(text)
            print(f"[Insert] Copied to clipboard: {text}")
        except ImportError:
            print("[Insert Error] pyperclip not installed.")
        return

    # Mode == active (typing)
    # 1. Try wtype (Wayland)
    try:
        subprocess.run(["wtype", text], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # 2. Try xdotool (X11 / Xwayland)
    try:
        # --clearmodifiers prevents stuck shift/ctrl keys
        subprocess.run(["xdotool", "type", "--clearmodifiers", text], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
        
    # 3. Try pynput (fallback, often buggy on Wayland)
    try:
        from pynput.keyboard import Controller
        keyboard = Controller()
        keyboard.type(text)
        return
    except Exception as e:
        print(f"[Insert Error] All insertion methods failed: {e}")
