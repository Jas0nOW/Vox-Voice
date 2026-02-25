from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional
import numpy as np
from faster_whisper import WhisperModel

from voice_engine.stt.base import STTAdapter, STTResult

class FasterWhisperAdapter(STTAdapter):
    def __init__(self, model_size: str = "large-v3-turbo", device: str = "cuda", compute_type: str = "float16"):
        # RTX 3070 has 8GB VRAM, float16 is perfect for large-v3-turbo
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    async def transcribe_stream(self, audio_generator: AsyncIterator[bytes]) -> AsyncIterator[STTResult]:
        # This is a simplified chunk-based implementation.
        # Real-time streaming with Faster Whisper usually requires a rolling buffer or VAD-based slicing.
        # For the MVP, we assume the engine slices audio by VAD.
        
        audio_data = b""
        async for chunk in audio_generator:
            audio_data += chunk
            # In a real implementation, we would do partial transcriptions here.
            # Faster Whisper doesn't natively support "partial" results in a simple way without re-running.
            
        # Final transcription for the accumulated audio
        result = await self._transcribe_bytes(audio_data)
        if result:
            yield result

    async def transcribe_file(self, file_path: str) -> STTResult:
        segments, info = await asyncio.to_thread(self.model.transcribe, file_path, beam_size=5, language="de")
        full_text = "".join([s.text for s in segments]).strip()
        return STTResult(text=full_text, confidence=info.language_probability, is_final=True, language=info.language)

    async def _transcribe_bytes(self, audio_bytes: bytes) -> Optional[STTResult]:
        if not audio_bytes:
            return None
            
        # Convert bytes to float32 numpy array (assuming 16kHz mono)
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        segments, info = await asyncio.to_thread(self.model.transcribe, audio_np, beam_size=1, language="de")
        full_text = "".join([s.text for s in segments]).strip()
        
        return STTResult(text=full_text, confidence=info.language_probability, is_final=True, language=info.language)
