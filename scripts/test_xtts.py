import os
import torch
from TTS.api import TTS

# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"

def generate_xtts_sample():
    print(f"Loading XTTS v2 on {device}...")
    # Model path is where we downloaded it
    model_path = os.path.expanduser("~/.wanda/models/xtts_v2")
    
    # Initialize TTS with the downloaded model
    # (Note: TTS api usually expects a model name, but we can point to local)
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    text = "Hallo Jannis, hier ist WANDA. Ich nutze jetzt das XTTS Modell für maximale Menschlichkeit. Wie gefällt dir dieser Klang?"
    
    out_path = "research/voice_samples/xtts_v2_sample.wav"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    print("Synthesizing Premium German Voice...")
    # We use 'Claribel Dervla' as a high-quality female reference speaker included in XTTS
    tts.tts_to_file(text=text, speaker="Claribel Dervla", language="de", file_path=out_path)
    print(f"✅ XTTS Sample saved to {out_path}")

if __name__ == "__main__":
    generate_xtts_sample()
