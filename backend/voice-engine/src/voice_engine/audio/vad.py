from __future__ import annotations

import torch
import numpy as np
from typing import Optional

class SileroVAD:
    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        # Load Silero VAD model
        self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                          model='silero_vad',
                                          force_reload=False,
                                          onnx=False)
        self.threshold = threshold
        self.sample_rate = sample_rate
        self._is_speaking = False

    def is_speech(self, audio_chunk: bytes) -> bool:
        # Convert bytes back to float32 for Silero
        audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        
        # Add batch dimension
        tensor = torch.from_numpy(audio_float32)
        
        # Get probability
        speech_prob = self.model(tensor, self.sample_rate).item()
        
        return speech_prob > self.threshold
