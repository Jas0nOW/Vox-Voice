from __future__ import annotations

import httpx
from typing import AsyncIterator

from voice_engine.llm.base import LLMAdapter, LLMRequest, LLMChunk

class OllamaAdapter(LLMAdapter):
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "llama3", stream: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.stream = stream
        self._cancelled: set[str] = set()

    async def healthcheck(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as c:
                r = await c.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def generate(self, req: LLMRequest) -> AsyncIterator[LLMChunk]:
        self._cancelled.discard(req.session_id)
        payload = {"model": self.model if req.model in ("", "auto") else req.model, "prompt": req.prompt, "stream": True}
        async with httpx.AsyncClient(timeout=None) as c:
            async with c.stream("POST", f"{self.base_url}/api/generate", json=payload) as r:
                async for line in r.aiter_lines():
                    if req.session_id in self._cancelled:
                        break
                    if not line:
                        continue
                    # Ollama streams JSON lines
                    try:
                        import json
                        obj = json.loads(line)
                        if "response" in obj and obj["response"]:
                            yield LLMChunk(text=obj["response"])
                        if obj.get("done"):
                            break
                    except Exception:
                        continue

    async def cancel(self, session_id: str) -> None:
        self._cancelled.add(session_id)
