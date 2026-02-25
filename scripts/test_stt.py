import os
import soundfile as sf
import numpy as np
from wandavoice.config import Config
from wandavoice.stt import STTEngine

def test_transcription():
    cfg = Config()
    cfg.update_from_args(model='large-v3-turbo')
    
    stt = STTEngine(cfg)
    
    test_file = 'tests/data/arecord_test.wav'
    if not os.path.exists(test_file):
        print(f"File not found: {test_file}")
        return

    print(f"Reading {test_file}...")
    audio_data, samplerate = sf.read(test_file)
    
    # Ensure float32 and normalization
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32)
    
    # Transcription directly via Whisper model inside engine
    print("Transcribing (Direct)...")
    segments, info = stt.model.transcribe(audio_data, beam_size=5, language="de")
    
    text = " ".join([segment.text for segment in segments])
    
    print("\n--- RESULT ---")
    print(f"Detected Language: {info.language} (p={info.language_probability:.2f})")
    print(f"Transcription: {text}")
    print("--------------")

if __name__ == "__main__":
    test_transcription()
