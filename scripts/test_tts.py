import os
import sys
from wandavoice.config import Config
from wandavoice.tts import TTSEngine
import time

def test_piper():
    cfg = Config()
    tts = TTSEngine(cfg)
    
    if not tts.enabled:
        print("TTS Engine (Piper) not enabled. Check model path.")
        return

    text = "Hallo Jannis, ich bin WANDA. Deine lokale Sprachausgabe mit Thorsten ist jetzt bereit."
    print(f"Synthesizing: '{text}'")
    
    tts.speak(text)
    
    # Wait for playback to finish
    print("Playing (non-blocking)...")
    time.sleep(6)
    print("Done.")

if __name__ == "__main__":
    test_piper()
