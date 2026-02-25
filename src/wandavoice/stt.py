import os
import sys
import logging
import torch
import numpy as np
from faster_whisper import WhisperModel
from typing import Optional

# Suppress spammy logs
logging.getLogger("faster_whisper").setLevel(logging.ERROR)


class STTEngine:
    def __init__(self, config):
        self.config = config
        model_size = config.WHISPER_MODEL_SIZE  # 'large-v3' or 'large-v3-turbo'

        print(
            f"Loading Whisper '{model_size}' ({config.COMPUTE_TYPE})...",
            end="",
            flush=True,
        )
        try:
            # Point to local cache or download
            model_path = os.path.join(config.base_dir, "models", "whisper", model_size)

            # Note: device="cuda" if you have enough VRAM, otherwise "cpu"
            # Using 'auto' allows it to use GPU if available
            self.model = WhisperModel(
                model_size,
                device="auto",
                compute_type=config.COMPUTE_TYPE,
                download_root=os.path.join(config.base_dir, "models", "whisper"),
            )
            print(" Done.")
        except Exception as e:
            print(f"\nError loading Whisper: {e}")
            sys.exit(1)

        # Initialize Silero VAD v5
        print("Loading Silero VAD v5...", end="", flush=True)
        try:
            self.vad_model, self.utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )
            (self.get_speech_timestamps, _, self.read_audio, _, _) = self.utils
            print(" Done.")
        except Exception as e:
            print(f"\nError loading Silero VAD: {e}")
            # Fallback to simple logic if VAD fails
            self.vad_model = None

    def transcribe(self, audio_data: np.ndarray) -> str:
        if audio_data is None or len(audio_data) == 0:
            return ""

        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.float64:
            audio_float = audio_data.astype(np.float32)
        else:
            audio_float = audio_data

        # Optional: Use Silero VAD to trim audio before Whisper (already filtered in recorder, but safer here)

        segments, _ = self.model.transcribe(
            audio_float,
            beam_size=5,
            language=self.config.LANGUAGE,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            initial_prompt="Wanda. Jannis. AERIS. n8n. Supabase. Krypto. Stop. Stopp. Abbrechen. Neu aufnehmen. Von vorne."
        )

        text = " ".join([segment.text for segment in segments])
        return text.strip()
