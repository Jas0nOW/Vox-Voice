from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

BackendLLM = Literal["gemini_cli", "ollama"]
ProfileName = Literal["fast", "reasoning", "auto"]

class AudioConfig(BaseModel):
    backend: Literal["pipewire"] = "pipewire"
    sample_rate_hz: int = 48000
    channels_in: int = 1
    channels_out: int = 1
    pre_roll_seconds: int = 3

class DSPAEC(BaseModel):
    enabled: bool = True
    method: str = "pipewire-module-echo-cancel"
    aggressiveness: Literal["low", "medium", "high"] = "medium"

class DSPNS(BaseModel):
    enabled: bool = True
    level: int = 2
    profile: str = "balanced"

class DSPAGC(BaseModel):
    enabled: bool = False
    mode: str = "adaptive"
    target_level_dbfs: int = -18

class DSPConfig(BaseModel):
    mode: Literal["headset", "speakers"] = "speakers"
    aec: DSPAEC = Field(default_factory=DSPAEC)
    ns: DSPNS = Field(default_factory=DSPNS)
    agc: DSPAGC = Field(default_factory=DSPAGC)

class WakeWordConfig(BaseModel):
    engine: str = "openWakeWord"
    threshold: float = 0.5
    words: list[str] = Field(default_factory=lambda: ["wanda"])

class VADProfile(BaseModel):
    min_speech_ms: int
    end_silence_ms: int
    continue_window_ms: int

class VADConfig(BaseModel):
    command: VADProfile = VADProfile(min_speech_ms=120, end_silence_ms=350, continue_window_ms=800)
    chat: VADProfile = VADProfile(min_speech_ms=160, end_silence_ms=650, continue_window_ms=1100)

class GeminiCLIConfig(BaseModel):
    cmd: str = "gemini"
    cwd: str = "."
    isolated_home: str = ".runtime/gemini_home"
    rules_file: str = "config/gemini_voice_rules.md"
    restart_on_exit: bool = True

class OllamaConfig(BaseModel):
    base_url: str = "http://127.0.0.1:11434"
    model: str = "llama3"
    stream: bool = True

class LLMProfile(BaseModel):
    model: str
    auto_reasoning: bool = False

class LLMConfig(BaseModel):
    backend: BackendLLM = "gemini_cli"
    profiles: Dict[str, LLMProfile] = Field(default_factory=lambda: {
        # Gemini CLI commands required by MASTER prompt:
        # - auto:      gemini
        # - fast:      gemini --model gemini-3-flash-preview
        # - reasoning: gemini --model gemini-3-pro-preview
        "fast": LLMProfile(model="gemini-3-flash-preview"),
        "reasoning": LLMProfile(model="gemini-3-pro-preview"),
        "auto": LLMProfile(model="auto", auto_reasoning=True),
    })
    active_profile: str = "fast"
    gemini_cli: GeminiCLIConfig = Field(default_factory=GeminiCLIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)

    # Optional UI/Settings helpers (engine may ignore in MVP)
    recommended: Dict[str, Any] = Field(default_factory=lambda: {
        "gemini_profiles": {
            "auto": {"cmd": "gemini"},
            "fast": {"cmd": "gemini --model gemini-3-flash-preview"},
            "reasoning": {"cmd": "gemini --model gemini-3-pro-preview"},
        },
        "ollama_models": [
            "qwen2.5:7b-instruct",
            "llama3.1:8b-instruct",
            "mistral:7b-instruct",
            "phi3:mini",
        ],
    })


class STTProfile(BaseModel):
    adapter: str
    model: str


class STTConfig(BaseModel):
    adapter: str = "faster_whisper"
    profiles: Dict[str, STTProfile] = Field(default_factory=lambda: {
        "fast": STTProfile(adapter="faster_whisper", model="small"),
        "final": STTProfile(adapter="faster_whisper", model="medium"),
    })
    active_profile: str = "fast"
    recommended: Dict[str, Any] = Field(default_factory=lambda: {
        "adapters": ["faster_whisper", "whisper_cpp", "sherpa_onnx"],
        "faster_whisper_models": ["tiny", "base", "small", "medium"],
    })


class TTSConfig(BaseModel):
    default_voice: str = "edge:de-DE-SeraphinaNeural"
    edge_tts: Dict[str, Any] = Field(default_factory=lambda: {"rate_pct": 15})
    local: Dict[str, Any] = Field(default_factory=lambda: {"adapter": "xtts_v2"})


class SkillsConfig(BaseModel):
    allowlist: list[str] = Field(default_factory=list)
    permissions: Dict[str, str] = Field(default_factory=dict)

class LoggingConfig(BaseModel):
    redaction: bool = True
    retention_days: int = 14
    max_runs: int = 500

class RootConfig(BaseModel):
    schema_version: str = "1.0"
    audio: AudioConfig = Field(default_factory=AudioConfig)
    dsp: DSPConfig = Field(default_factory=DSPConfig)
    wakeword: WakeWordConfig = Field(default_factory=WakeWordConfig)
    vad: VADConfig = Field(default_factory=VADConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

def load_config(path: str) -> RootConfig:
    p = Path(path)
    data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    return RootConfig.model_validate(data)

def config_snapshot_dict(cfg: RootConfig) -> Dict[str, Any]:
    # stable, explicit snapshot for run manifests
    return cfg.model_dump()
