from __future__ import annotations

import asyncio
import os
import shlex
import time
from typing import AsyncIterator, Optional

from voice_engine.llm.base import LLMAdapter, LLMRequest, LLMChunk

class GeminiCLIAdapter(LLMAdapter):
    """
    Persistent subprocess wrapper.

    Notes:
    - This is a *skeleton*: actual Gemini CLI flags / IO protocol may vary.
    - We treat the CLI as an untrusted boundary. Only the engine decides on skill invocations.
    """

    def __init__(self, cmd: str = "gemini", cwd: str = ".", isolated_home: str = ".runtime/gemini_home", rules_file: str = "", restart_on_exit: bool = True) -> None:
        # Base command only. Model/profile selection is done by adding args at spawn time.
        # Required by MASTER prompt:
        #   auto:      gemini
        #   fast:      gemini --model gemini-3-flash-preview
        #   reasoning: gemini --model gemini-3-pro-preview
        self.cmd = cmd
        self.cwd = cwd
        self.isolated_home = isolated_home
        self.rules_file = rules_file
        self.restart_on_exit = restart_on_exit
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._proc_cmdline: Optional[list[str]] = None
        self._lock = asyncio.Lock()
        self._cancelled_sessions: set[str] = set()

    def _build_cmdline(self, model: str) -> list[str]:
        base = shlex.split(self.cmd)
        if not base:
            base = ["gemini"]
        # auto => exactly "gemini" (no model flag)
        if model and model not in ("auto", ""):
            return base + ["--model", model]
        return base

    async def _ensure_proc(self, model: str) -> asyncio.subprocess.Process:
        desired = self._build_cmdline(model)
        if self._proc and self._proc.returncode is None and self._proc_cmdline == desired:
            return self._proc

        # Model/profile changed => restart process with the new cmdline.
        if self._proc and self._proc.returncode is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None
            self._proc_cmdline = None

        os.makedirs(self.isolated_home, exist_ok=True)
        env = dict(os.environ)
        env["HOME"] = os.path.abspath(self.isolated_home)
        self._proc = await asyncio.create_subprocess_exec(
            *desired,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.cwd,
            env=env,
        )
        self._proc_cmdline = desired
        return self._proc

    async def healthcheck(self) -> bool:
        try:
            proc = await self._ensure_proc("auto")
            return proc.returncode is None
        except Exception:
            return False

    async def generate(self, req: LLMRequest) -> AsyncIterator[LLMChunk]:
        async with self._lock:
            self._cancelled_sessions.discard(req.session_id)
            proc = await self._ensure_proc(req.model)
            assert proc.stdin and proc.stdout

            # Compose a safe "voice-only" wrapper prompt.
            # Rules file (if provided) is inserted as plain text header.
            header = ""
            if self.rules_file:
                try:
                    header = open(self.rules_file, "r", encoding="utf-8").read().strip() + "\n\n"
                except Exception:
                    header = ""

            payload = header + req.prompt.strip() + "\n"
            proc.stdin.write(payload.encode("utf-8"))
            await proc.stdin.drain()

            # Stream lines from stdout as chunks (skeleton).
            # Replace with the CLI's actual streaming protocol when integrating.
            start = time.time()
            while True:
                if req.session_id in self._cancelled_sessions:
                    break
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")
                yield LLMChunk(text=text)

            # If proc exited unexpectedly, clear it so watchdog can respawn.
            if proc.returncode is not None:
                self._proc = None

    async def cancel(self, session_id: str) -> None:
        self._cancelled_sessions.add(session_id)
