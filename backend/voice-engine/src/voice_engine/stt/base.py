from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, AsyncIterator

@dataclass
class STTResult:
    text: str
    confidence: float
    is_final: bool = False
    language: Optional[str] = None
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None

class STTAdapter(ABC):
    @abstractmethod
    async def transcribe_stream(self, audio_generator: AsyncIterator[bytes]) -> AsyncIterator[STTResult]:
        """Transcribe an incoming stream of audio bytes."""
        pass

    @abstractmethod
    async def transcribe_file(self, file_path: str) -> STTResult:
        """Transcribe a full audio file."""
        pass
