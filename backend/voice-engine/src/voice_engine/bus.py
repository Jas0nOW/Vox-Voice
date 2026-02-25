from __future__ import annotations

import asyncio
from typing import AsyncIterator, List
from voice_engine.events import EventEnvelope

class EventBus:
    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue[EventEnvelope]] = []

    def subscribe(self) -> asyncio.Queue[EventEnvelope]:
        q: asyncio.Queue[EventEnvelope] = asyncio.Queue(maxsize=10_000)
        self._subscribers.append(q)
        return q

    async def publish(self, ev: EventEnvelope) -> None:
        # fan-out with backpressure isolation (drop oldest per-subscriber if needed)
        for q in list(self._subscribers):
            try:
                q.put_nowait(ev)
            except asyncio.QueueFull:
                try:
                    _ = q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    q.put_nowait(ev)
                except asyncio.QueueFull:
                    pass
