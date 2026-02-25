from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional
from pathlib import Path

from voice_engine.tts.base import TTSAdapter

class F5TTSAdapter(TTSAdapter):
    def __init__(self, ref_audio_path: Optional[str] = None, ref_text: str = ""):
        # F5-TTS will be lazily loaded to avoid overhead if not used
        self.model = None
        self.ref_audio_path = ref_audio_path
        self.ref_text = ref_text
        self._stop_requested = False

    def _ensure_model(self):
        if self.model is None:
            from f5_tts.api import F5TTS
            self.model = F5TTS()

    async def synthesize_stream(self, text_generator: AsyncIterator[str]) -> AsyncIterator[bytes]:
        # F5-TTS natively supports chunked inference, but for the MVP 
        # we will process sentence by sentence to maintain quality.
        
        full_text = ""
        async for chunk in text_generator:
            if self._stop_requested:
                break
            full_text += chunk
            
            # Simple sentence splitting logic
            if any(p in chunk for p in [".", "!", "?", "\\n"]):
                audio_bytes = await self.synthesize_text(full_text)
                yield audio_bytes
                full_text = ""

        if full_text.strip() and not self._stop_requested:
            audio_bytes = await self.synthesize_text(full_text)
            yield audio_bytes

    async def synthesize_text(self, text: str) -> bytes:
        if not text.strip():
            return b""
            
        await asyncio.to_thread(self._ensure_model)
        
        import soundfile as sf
        import io
        
        # If no ref_audio_path is given, we need a dummy or the infer function will fail.
        # F5TTS requires a real file. If missing, we'll try to find any small wav or raise.
        ref_file = self.ref_audio_path
        if not ref_file or not Path(ref_file).exists():
            # Fallback to a local sample if available
            fallback = Path(__file__).parent.parent.parent.parent.parent.parent / "tests" / "data" / "arecord_test.wav"
            if fallback.exists():
                ref_file = str(fallback)
            else:
                raise ValueError("F5TTS requires a valid ref_audio_path.")
        
        ref_text = self.ref_text if self.ref_text else "Test."
        
        # Run inference in a thread to not block the event loop
        wav, sr, spect = await asyncio.to_thread(
            self.model.infer,
            ref_file=ref_file,
            ref_text=ref_text,
            gen_text=text
        )
        
        # Convert to bytes
        with io.BytesIO() as wav_io:
            sf.write(wav_io, wav, sr, format='WAV', subtype='PCM_16')
            wav_bytes = wav_io.getvalue()
            
        return wav_bytes

    def stop(self) -> None:
        self._stop_requested = True
        # In a more advanced implementation, we would kill the inference process if possible.
