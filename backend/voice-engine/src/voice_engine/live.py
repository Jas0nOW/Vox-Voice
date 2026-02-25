from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional
from ulid import ULID

from voice_engine.audio.pipeline import AudioPipeline
from voice_engine.audio.vad import SileroVAD
from voice_engine.events import now_unix_ms
from voice_engine.llm.base import LLMRequest

if TYPE_CHECKING:
    from voice_engine.engine import VoiceEngine

class LiveAudioEngine:
    def __init__(self, engine: VoiceEngine):
        self.engine = engine
        self.pipeline = AudioPipeline(
            on_audio_level=self._on_audio_level
        )
        self.vad = SileroVAD()
        self._current_session_id: Optional[str] = None

    def _on_audio_level(self, level: float):
        if self._current_session_id:
            # We don't want to flood the bus, so we might want to throttle this
            pass

    async def run(self):
        print("[LIVE] WANDA Audio Engine starting...")
        self.pipeline.start()
        
        try:
            async for chunk in self.pipeline.stream():
                if self.vad.is_speech(chunk):
                    if not self._current_session_id:
                        await self._start_session()
                    
                    # Here we would collect speech chunks and feed them to STT
                    # This is the core loop that needs careful implementation 
                    # for barge-in and real-time feel.
                else:
                    if self._current_session_id:
                        # Speech ended?
                        pass
        finally:
            self.pipeline.stop()

    async def _start_session(self):
        session_id = str(ULID())
        self._current_session_id = session_id
        await self.engine._emit(session_id, "system", "session_start", {"mode": "live"})
        return session_id
