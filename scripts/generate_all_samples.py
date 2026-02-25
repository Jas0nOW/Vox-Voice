import os
import wave
import numpy as np
from kokoro_onnx import Kokoro
import soundfile as sf

# Paths
MODEL_DIR = os.path.expanduser("~/.wanda/models/kokoro")
MODEL_PATH = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODEL_DIR, "voices.json")
OUTPUT_DIR = "/home/jannis/Schreibtisch/Work-OS/40_Products/wandavoice/research/voice_samples"

TEXT = "Hallo Jannis, hier spricht WANDA. Ich teste gerade meine neue deutsche Stimme."

def generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(MODEL_PATH):
        print("Model not found!")
        return

    kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
    
    # German Female Voices
    voices = ["de_01", "de_03", "de_05"]
    
    for v in voices:
        print(f"Generating sample for Kokoro Voice: {v}...")
        try:
            samples, sample_rate = kokoro.create(TEXT, voice=v, speed=1.0, lang="de")
            out_path = os.path.join(OUTPUT_DIR, f"kokoro_{v}_sample.wav")
            sf.write(out_path, samples, sample_rate)
            print(f" -> Saved to {out_path}")
        except Exception as e:
            print(f"Error generating {v}: {e}")

if __name__ == "__main__":
    generate()
