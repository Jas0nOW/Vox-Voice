import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from wandavoice.config import Config
from wandavoice.tts import ParlerPremium, OrpheusSOTA, EdgeSeraphina, PiperFast
import sounddevice as sd

def test_engine(name, engine_class, text):
    print(f"\n--- Testing {name} ---")
    cfg = Config()
    engine = engine_class(cfg)
    if not engine.enabled:
        print(f"{name} is not enabled or failed to load.")
        return
        
    print(f"Generating sample for {name}...")
    engine.speak(text)
    time.sleep(8) # Wait for audio to finish playing (roughly)
    engine.stop()
    print(f"Finished {name}")

def main():
    text = "Hallo Jannis, hier spricht WANDA. Dies ist ein Test der neuen Sprachausgabe."
    
    # test_engine("Parler", ParlerPremium, text)
    test_engine("Seraphina", EdgeSeraphina, text)
    test_engine("Piper", PiperFast, text)
    test_engine("Orpheus", OrpheusSOTA, text)
    
if __name__ == "__main__":
    main()
