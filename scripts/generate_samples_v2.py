import os
import wave
import numpy as np
import soundfile as sf

def generate_piper_high():
    print("Generating Piper High (Eva-K)...")
    from piper import PiperVoice
    model_path = os.path.expanduser("~/.wanda/models/tts/piper/eva/de/de_DE/eva_k/x_low/de_DE-eva_k-x_low.onnx")
    if os.path.exists(model_path):
        voice = PiperVoice.load(model_path)
        out = "research/voice_samples/piper_high_sample.wav"
        with wave.open(out, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(voice.config.sample_rate)
            voice.synthesize("Hallo Jannis, das ist Piper in der High Qualität.", f)
        print(f"✅ Saved to {out}")

def generate_kokoro_sota():
    print("Generating Kokoro SOTA (ONNX)...")
    from kokoro_onnx import Kokoro
    model_path = os.path.expanduser("~/.wanda/models/kokoro/kokoro-v1.0.onnx")
    voices_path = os.path.expanduser("~/.wanda/models/kokoro/voices.bin") # We'll try to find a valid bin
    if os.path.exists(model_path):
        try:
            # We use the official bin from the community
            kokoro = Kokoro(model_path, voices_path)
            samples, sample_rate = kokoro.create("Hallo, ich bin die Kokoro SOTA Stimme.", voice="af_heart", speed=1.0, lang="en-us")
            sf.write("research/voice_samples/kokoro_sota_sample.wav", samples, sample_rate)
            print("✅ Saved to research/voice_samples/kokoro_sota_sample.wav")
        except Exception as e:
            print(f"Kokoro failed: {e}")

if __name__ == "__main__":
    generate_piper_high()
    generate_kokoro_sota()
