from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import AsyncIterator, Optional

@dataclass
class LLMRequest:
    session_id: str
    prompt: str
    model: str
    auto_reasoning: bool = False

@dataclass
class LLMChunk:
    text: str

class LLMAdapter(abc.ABC):
    @abc.abstractmethod
    async def healthcheck(self) -> bool: ...

    @abc.abstractmethod
    async def generate(self, req: LLMRequest) -> AsyncIterator[LLMChunk]:
        ...

    @abc.abstractmethod
    async def cancel(self, session_id: str) -> None:
        ...
