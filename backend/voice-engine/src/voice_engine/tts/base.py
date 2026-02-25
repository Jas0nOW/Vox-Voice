from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional

class TTSAdapter(ABC):
    @abstractmethod
    async def synthesize_stream(self, text_generator: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """Synthesize incoming text chunks into audio bytes (streaming)."""
        pass

    @abstractmethod
    async def synthesize_text(self, text: str) -> bytes:
        """Synthesize a full block of text into audio bytes."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop any ongoing synthesis immediately (barge-in)."""
        pass
