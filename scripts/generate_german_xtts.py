import os
import sys
import torch
import numpy as np
import soundfile as sf

# Wir nutzen die TTS Library direkt, ignorieren aber die Transformers-Warnung für diesen einen Lauf
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

def generate_real_german_xtts():
    from TTS.api import TTS
    print("Loading XTTS v2 (The real German capable model)...")
    
    # Init XTTS v2
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")

    text = "Hallo Jannis, ich bin WANDA. Dies ist mein echtes deutsches XTTS Modell. Es ist viel menschlicher als die anderen Versuche zuvor."
    out_path = "research/voice_samples/XTTS_v2_DEUTSCH_PREMIUM.wav"
    
    # 'Claribel Dervla' ist eine der besten Stimmen für Deutsch in XTTS
    tts.tts_to_file(text=text, speaker="Claribel Dervla", language="de", file_path=out_path)
    print(f"✅ REAL GERMAN SAMPLE SAVED TO: {out_path}")

if __name__ == "__main__":
    try:
        generate_real_german_xtts()
    except Exception as e:
        print(f"XTTS failed: {e}")
