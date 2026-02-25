from __future__ import annotations

import asyncio
import json
import os
import time
import traceback
from typing import Optional, Dict, Any

from ulid import ULID

from voice_engine.bus import EventBus
from voice_engine.events import EventEnvelope, Command, now_unix_ms
from voice_engine.trace import TraceRecorder
from voice_engine.runs import cas_put, write_run_manifest
from voice_engine.config import RootConfig, config_snapshot_dict
from voice_engine.llm import GeminiCLIAdapter, OllamaAdapter
from voice_engine.llm.base import LLMRequest

class CancelToken:
    def __init__(self) -> None:
        self._evt = asyncio.Event()

    def cancel(self) -> None:
        self._evt.set()

    async def wait(self) -> None:
        await self._evt.wait()

    def is_cancelled(self) -> bool:
        return self._evt.is_set()

class VoiceEngine:
    def __init__(self, mode: str, runs_dir: str, cas_dir: str, config: RootConfig) -> None:
        self.mode = mode
        self.bus = EventBus()
        self.runs_dir = runs_dir
        self.cas_dir = cas_dir
        self.config = config

        self.trace = TraceRecorder(pid=1)
        self._current_session: Optional[str] = None
        self._cancel = CancelToken()

        # Dev context buffer (untrusted)
        self._dev_context: str = ""
        self._dev_auto_attach: bool = True
        self._dev_mode: str = "once"  # once|persistent

        # LLM bridge selection
        self._llm_backend = self.config.llm.backend
        self._llm_profile = self.config.llm.active_profile

        # Runtime mode tracking
        self._vad_profile: str = "chat"
        self._routing_mode: str = "GEMINI"
        self._console_mode: str = "cli"

        # Runtime overrides (MVP: set via MCC Settings; persistence comes later)
        self._ollama_model = self.config.llm.ollama.model
        self._tts_voice = self.config.tts.default_voice
        self._stt_profile = getattr(self.config, "stt", None).active_profile if hasattr(self.config, "stt") else "fast"

        self._gemini = GeminiCLIAdapter(
            cmd=self.config.llm.gemini_cli.cmd,
            cwd=self.config.llm.gemini_cli.cwd,
            isolated_home=self.config.llm.gemini_cli.isolated_home,
            rules_file=self.config.llm.gemini_cli.rules_file,
            restart_on_exit=self.config.llm.gemini_cli.restart_on_exit,
        )
        self._ollama = OllamaAdapter(
            base_url=self.config.llm.ollama.base_url,
            model=self._ollama_model,
            stream=self.config.llm.ollama.stream,
        )

        # Real Engines
        from voice_engine.stt.faster_whisper import FasterWhisperAdapter
        from voice_engine.tts.f5_tts import F5TTSAdapter
        
        self._stt = FasterWhisperAdapter(
            model_size=self.config.stt.profiles[self._stt_profile].model,
            device="cuda"
        )
        self._tts = F5TTSAdapter()

    async def _emit(self, session_id: str, component: str, typ: str, payload: Optional[Dict[str, Any]] = None) -> None:
        ev = EventEnvelope(session_id=session_id, component=component, type=typ, payload=payload or {})
        await self.bus.publish(ev)

    def _active_llm_profile(self) -> Dict[str, Any]:
        prof = self.config.llm.profiles.get(self._llm_profile) or self.config.llm.profiles.get("fast")
        return prof.model_dump() if prof else {"model": "unknown"}

    async def start_sim_session(self) -> str:
        session_id = str(ULID())
        started_at = now_unix_ms()
        self._current_session = session_id
        self._cancel = CancelToken()

        # Bootstrap events
        await self._emit(session_id, "system", "session_start", {
            "llm_backend": self._llm_backend,
            "llm_profile": self._llm_profile,
        })

        await self._emit(session_id, "audio", "audio_device_changed", {
            "input": "default",
            "output": "default",
            "backend": self.config.audio.backend,
            "sample_rate_hz": self.config.audio.sample_rate_hz,
        })

        await self._emit(session_id, "dsp", "dsp_state", {
            "aec_on": self.config.dsp.aec.enabled,
            "ns_level": self.config.dsp.ns.level,
            "agc_mode": self.config.dsp.agc.mode if self.config.dsp.agc.enabled else "off",
            "echo_likelihood": 0.12,
        })

        vad_cfg = getattr(self.config, "vad", None)
        if vad_cfg:
            prof = getattr(vad_cfg, self._vad_profile, vad_cfg.chat)
            await self._emit(session_id, "vad", "vad_state", {
                "profile": self._vad_profile,
                "min_speech_ms": prof.min_speech_ms,
                "end_silence_ms": prof.end_silence_ms,
                "continue_window_ms": prof.continue_window_ms,
            })

        # Auto-attach dev context (untrusted) at request start when routing to LLM/chat.
        # In sim we always route to chat.
        if self._dev_context.strip() and self._dev_auto_attach:
            await self._emit(session_id, "devctx", "dev_context_attached", {
                "mode": self._dev_mode,
                "bytes": len(self._dev_context.encode("utf-8")),
            })

        # Simulated pipeline timeline
        self.trace.span_begin("system", "session")

        self.trace.span_begin("wake", "wakeword")
        await self._emit(session_id, "wake", "wake_detected", {"word": "wanda", "confidence": 0.92})
        await asyncio.sleep(0.05)
        self.trace.span_end("wake", "wakeword")

        self.trace.span_begin("vad", "vad")
        await self._emit(session_id, "vad", "vad_start", {"profile": "chat"})
        for i in range(20):
            if self._cancel.is_cancelled():
                break
            await self._emit(session_id, "audio", "audio_level", {"rms": 0.05 + i * 0.01})
            await asyncio.sleep(0.02)
        await self._emit(session_id, "vad", "vad_end", {"speech_ms": 420})
        self.trace.span_end("vad", "vad")

        if self._cancel.is_cancelled():
            await self._emit(session_id, "system", "cancel_done", {"reason": "barge_in"})
            await self._emit(session_id, "system", "session_end")
            self.trace.span_end("system", "session")
            return session_id

        self.trace.span_begin("stt", "stt")
        await self._emit(session_id, "stt", "stt_partial", {"text": "wie", "profile": self._stt_profile})
        await asyncio.sleep(0.05)
        await self._emit(session_id, "stt", "stt_partial", {"text": "wie geht", "profile": self._stt_profile})
        await asyncio.sleep(0.05)
        await self._emit(session_id, "stt", "stt_final", {"text": "wie geht es dir", "confidence": 0.86, "profile": self._stt_profile})
        self.trace.span_end("stt", "stt")

        self.trace.span_begin("router", "router")
        await self._emit(session_id, "router", "router_decision", {"mode": "chat", "why": ["no hard command"]})
        self.trace.span_end("router", "router")

        self.trace.span_begin("llm", "llm")
        for chunk in ["Mir geht", " es gut.", " Was brauchst du?"]:
            if self._cancel.is_cancelled():
                break
            await self._emit(session_id, "llm", "llm_stream_chunk", {"text": chunk})
            await asyncio.sleep(0.04)
        await self._emit(session_id, "llm", "llm_done", {"tokens": 42, "backend": self._llm_backend, "profile": self._llm_profile})
        self.trace.span_end("llm", "llm")

        if self._cancel.is_cancelled():
            await self._emit(session_id, "system", "cancel_done", {"reason": "user_stop"})
            await self._emit(session_id, "system", "session_end")
            self.trace.span_end("system", "session")
            return session_id

        self.trace.span_begin("tts", "tts")
        await self._emit(session_id, "tts", "tts_start", {"voice": self._tts_voice})
        for i in range(15):
            if self._cancel.is_cancelled():
                break
            await self._emit(session_id, "tts", "tts_chunk", {"pcm_ms": 40})
            await self._emit(session_id, "audio", "audio_level_out", {"rms": 0.06 + (i % 5) * 0.01})
            await asyncio.sleep(0.04)
        await self._emit(session_id, "tts", "tts_stop", {"reason": "done" if not self._cancel.is_cancelled() else "cancel"})
        self.trace.span_end("tts", "tts")

        ended_at = now_unix_ms()
        await self._emit(session_id, "system", "session_end")
        self.trace.span_end("system", "session")

        # Write artifacts: transcripts + trace + config snapshot (+ devctx marker only, not content)
        transcripts = {"user": "wie geht es dir", "assistant": "Mir geht es gut. Was brauchst du?"}
        tr_hash = cas_put(self.cas_dir, json.dumps(transcripts, ensure_ascii=False).encode("utf-8"))

        trace_path = os.path.join(self.runs_dir, time.strftime("%Y-%m-%d"), session_id, "trace.json")
        os.makedirs(os.path.dirname(trace_path), exist_ok=True)
        self.trace.export_json(trace_path)
        with open(trace_path, "rb") as f:
            trace_hash = cas_put(self.cas_dir, f.read())

        cfg_hash = cas_put(self.cas_dir, json.dumps(config_snapshot_dict(self.config), ensure_ascii=False).encode("utf-8"))

        manifest = {
            "schema_version": "1.0",
            "session_id": session_id,
            "started_at_unix_ms": started_at,
            "ended_at_unix_ms": ended_at,
            "mode": self.mode,
            "llm": {"backend": self._llm_backend, "profile": self._llm_profile, "profile_cfg": self._active_llm_profile()},
            "dev_context": {"attached": bool(self._dev_context.strip()) and self._dev_auto_attach, "mode": self._dev_mode},
            "artifacts": {
                "transcripts_json_sha256": tr_hash,
                "trace_json_sha256": trace_hash,
                "config_json_sha256": cfg_hash,
            },
        }
        manifest_path = write_run_manifest(self.runs_dir, session_id, manifest)
        await self._emit(session_id, "system", "run_manifest_written", {"path": manifest_path, "trace_sha256": trace_hash})

        # attach-once semantics
        if self._dev_mode == "once":
            self._dev_context = ""

        return session_id

    async def _set_llm_backend(self, backend: str) -> None:
        if backend not in ("gemini_cli", "ollama"):
            return
        self._llm_backend = backend

    async def _set_llm_profile(self, profile: str) -> None:
        if profile not in self.config.llm.profiles:
            return
        self._llm_profile = profile

    async def _set_ollama_model(self, model: str) -> None:
        m = (model or "").strip()
        if not m:
            return
        self._ollama_model = m
        self._ollama.model = m

    async def _set_tts_voice(self, voice: str) -> None:
        v = (voice or "").strip()
        if not v:
            return
        self._tts_voice = v

    async def _set_stt_profile(self, profile: str) -> None:
        p = (profile or "").strip()
        stt_cfg = getattr(self.config, "stt", None)
        if not stt_cfg:
            return
        if p not in stt_cfg.profiles:
            return
        self._stt_profile = p

    async def handle_command(self, cmd: Command) -> None:
        typ = cmd.type

        if typ in ("stop", "cancel"):
            if self._current_session:
                await self.bus.publish(EventEnvelope(
                    session_id=self._current_session,
                    component="system",
                    type="cancel_request",
                    payload={"reason": "user_stop"},
                ))
            self._cancel.cancel()
            return

        if typ == "start_sim":
            await self.start_sim_session()
            return

        if typ == "set_llm_backend":
            await self._set_llm_backend(str(cmd.payload.get("backend", "")))
            return

        if typ == "set_llm_profile":
            await self._set_llm_profile(str(cmd.payload.get("profile", "")))
            return

        if typ == "set_ollama_model":
            await self._set_ollama_model(str(cmd.payload.get("model", "")))
            return

        if typ == "set_tts_voice":
            await self._set_tts_voice(str(cmd.payload.get("voice", "")))
            return

        if typ == "set_stt_profile":
            await self._set_stt_profile(str(cmd.payload.get("profile", "")))
            return

        if typ == "set_dev_context":
            self._dev_context = str(cmd.payload.get("text", ""))
            self._dev_auto_attach = bool(cmd.payload.get("auto_attach", True))
            self._dev_mode = str(cmd.payload.get("mode", "once"))
            return

        if typ == "raise_error":
            # Useful for wiring MCC error panel
            sid = self._current_session or str(ULID())
            stack = "".join(traceback.format_stack(limit=10))
            await self._emit(sid, "system", "error_raised", {"component": "system", "stack": stack, "code": "SIM_ERROR"})
            return

        if typ == "watchdog_restart":
            sid = self._current_session or str(ULID())
            await self._emit(sid, "system", "watchdog_restart", {"component": cmd.payload.get("component","llm_bridge"), "reason": cmd.payload.get("reason","manual")})
            return

        if typ == "mute":
            sid = self._current_session or str(ULID())
            self._cancel.cancel()
            await self._emit(sid, "system", "muted", {"reason": "user_mute"})
            return

        if typ == "sleep":
            sid = self._current_session or str(ULID())
            self._cancel.cancel()
            await self._emit(sid, "system", "sleep_ack", {})
            await self._emit(sid, "system", "session_end", {})
            return

        if typ == "set_routing_mode":
            sid = self._current_session or str(ULID())
            mode = str(cmd.payload.get("mode", "GEMINI"))
            await self._emit(sid, "system", "set_routing_mode", {"mode": mode})
            return

        if typ == "set_console_mode":
            sid = self._current_session or str(ULID())
            mode = str(cmd.payload.get("mode", "cli"))
            await self._emit(sid, "system", "set_console_mode", {"mode": mode})
            return

        if typ == "mark_golden":
            sid = self._current_session or str(ULID())
            await self._emit(sid, "system", "golden_marked", {"session_id": sid})
            return

        if typ == "set_vad_profile":
            sid = self._current_session or str(ULID())
            p = str(cmd.payload.get("profile", "chat"))
            vad_cfg = getattr(self.config, "vad", None)
            if vad_cfg and hasattr(vad_cfg, p):
                self._vad_profile = p
                prof = getattr(vad_cfg, p)
                await self._emit(sid, "vad", "vad_state", {
                    "profile": p,
                    "min_speech_ms": prof.min_speech_ms,
                    "end_silence_ms": prof.end_silence_ms,
                    "continue_window_ms": prof.continue_window_ms,
                })
            return

        if typ == "set_dsp_mode":
            sid = self._current_session or str(ULID())
            mode = str(cmd.payload.get("mode", self.config.dsp.mode))
            self.config.dsp.mode = mode
            await self._emit(sid, "dsp", "dsp_state", {
                "aec_on": self.config.dsp.aec.enabled,
                "ns_level": self.config.dsp.ns.level,
                "agc_mode": self.config.dsp.agc.mode if self.config.dsp.agc.enabled else "off",
                "echo_likelihood": 0.0,
                "mode": mode,
            })
            return

        if typ == "set_wake_words":
            sid = self._current_session or str(ULID())
            words = cmd.payload.get("words", [])
            if isinstance(words, list):
                self.config.wakeword.words = [str(w) for w in words if w]
            await self._emit(sid, "system", "wake_words_updated", {
                "words": self.config.wakeword.words,
            })
            return

        if typ == "set_skill_allowlist":
            sid = self._current_session or str(ULID())
            allowlist = cmd.payload.get("allowlist", [])
            permissions = cmd.payload.get("permissions", {})
            if isinstance(allowlist, list):
                self.config.skills.allowlist = [str(s) for s in allowlist if s]
            if isinstance(permissions, dict):
                self.config.skills.permissions.update(permissions)
            await self._emit(sid, "system", "skill_allowlist_updated", {
                "allowlist": self.config.skills.allowlist,
                "permissions": self.config.skills.permissions,
            })
            return

        if typ == "set_llm_profile_cmd":
            await self._set_llm_profile(str(cmd.payload.get("profile", "")))
            return

        if typ == "ptt_start":
            sid = self._current_session or str(ULID())
            await self._emit(sid, "vad", "vad_start", {"profile": self._vad_profile, "source": "ptt"})
            return

        if typ == "ptt_stop":
            sid = self._current_session or str(ULID())
            await self._emit(sid, "vad", "vad_end", {"speech_ms": 0, "source": "ptt"})
            await self._emit(sid, "stt", "stt_final", {"text": "", "confidence": 1.0, "profile": self._stt_profile})
            return

        if typ == "test_barge_in":
            sid = self._current_session or str(ULID())
            self._cancel.cancel()
            await self._emit(sid, "system", "cancel_request", {"reason": "barge_in_test"})
            await self._emit(sid, "system", "cancel_done", {"reason": "barge_in_test"})
            return

        # UI stats (orb dropped frames) – optional
        if typ == "orb_frame_stats":
            sid = self._current_session or str(ULID())
            await self._emit(sid, "orb", "orb_frame_stats", cmd.payload)
            return
