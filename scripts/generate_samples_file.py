import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from wandavoice.config import Config
from wandavoice.tts import OrpheusSOTA, EdgeSeraphina
import soundfile as sf
import sounddevice as sd

# We monkey-patch sd.play to just save to file instead
original_play = sd.play

output_dir = "/home/jannis/Schreibtisch/Work-OS/40_Products/wandavoice/samples/"
current_name = ""


def mock_play(data, samplerate, blocking=False, **kwargs):
    out_path = os.path.join(output_dir, f"{current_name}_sample.wav")
    sf.write(out_path, data, samplerate)
    print(f"Saved {out_path}")


sd.play = mock_play


def test_engine(name, engine_class, text):
    global current_name
    current_name = name
    print(f"\n--- Saving {name} ---")
    cfg = Config()
    engine = engine_class(cfg)
    if not engine.enabled:
        print(f"{name} is not enabled or failed to load.")
        return

    print(f"Generating sample for {name}...")
    engine.speak(text)
    engine.stop()
    print(f"Finished {name}")


def main():
    text = (
        "Hallo Jannis, hier spricht WANDA. Dies ist ein Test der neuen Sprachausgabe."
    )

    test_engine("Seraphina", EdgeSeraphina, text)
    test_engine("Orpheus", OrpheusSOTA, text)


if __name__ == "__main__":
    main()
