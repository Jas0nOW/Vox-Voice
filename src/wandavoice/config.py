import os
from pathlib import Path
from copy import deepcopy
from typing import Any, Dict, Optional, List

try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG: Dict[str, Any] = {
    "voice": {
        "assistant": {
            "name": "VOX",
            "briefing_style": "jarvis_de",
            "briefing_include_last": True,
            # Wake/command handling (push-to-talk is still the MVP trigger)
            "idle_requires_wake": True,
            "strip_wake_prefix": True,
            "llm_system_prompt": (
                "Du bist VOX, ein loyaler, trockener, leicht sarkastischer Voice-Assistent im Jarvis-Stil. "
                "Bleib hilfreich, präzise und kurz. Keine beleidigenden Inhalte.\n"
                "Antwort-Format:\n"
                "- Beginne mit 'SAY:' (1-3 kurze gesprochene Sätze).\n"
                "- Optional 'SHOW:' für Details/Listen/Code.\n"
                "- Kein unnötiges Markdown.\n"
            ),
        },
        "audio": {
            "sample_rate": 16000,
            "frame_ms": 30,
            "vad_enabled": True,
            "vad_mode": 2,  # 0-3 (webrtcvad)
            "silence_ms": 900,
            # Fine-tuning for "pause-and-continue" dictation:
            # After silence_ms is reached, keep listening for another grace window.
            "post_silence_grace_ms": 1200,
            # Debounce: require a few consecutive VAD frames to count as "real" speech
            # (helps ignoring small clicks).
            "speech_onset_ms": 120,
            "speech_resume_ms": 90,
            "min_speech_ms": 400,
            "device_index": None,
            "fixed_record_s": 8,  # used when VAD is off
            "max_record_s": 20,
            "vad_threshold": 0.55,  # Silero VAD start threshold (speech: 0.8+, noise: 0.1-0.4)
        },
        "stt": {
            "provider": "faster_whisper",
            "model": "small",  # tiny|base|small|medium
            "compute_type": "int8",
            "lang": "auto",  # de|en|auto
        },
        "routing": {
            "target": "cli:gemini",  # insert|stdout|cli:gemini|cli:ollama
            "insert": "active",  # active|clipboard|off
            "tts": "seraphina",  # auto|none|seraphina|orpheus
            "history_turns": 8,
            "improve": "off",  # off|basic (MVP)
        },
        "permissions": {
            "audio_record": "allow",  # allow|deny|ask
            "window_inject": "ask",
            "clipboard_write": "ask",
            "exec_external_cli": "deny",
            "network": "ask",
        },
        "privacy": {
            "log_text": True,
        },
        "tts": {
            "seraphina": {
                "voice": "de-DE-SeraphinaMultilingualNeural",
                "rate": "+15%",
            },
            "azure": {
                "voice": "",  # e.g. 'de-DE-SeraphinaNeural'
            },
            "kokoro": {
                "voice": "de_01",
                "lang": "de",
            },
            "orpheus": {
                "voice": "default",
                "emotion": "neutral",
            },
        },
        "llm": {
            "ollama": {
                "base_url": "http://127.0.0.1:11434",
                "model": "",
            }
        },
        "ui": {
            "orb_enabled": True,
            "orb": {
                "size": 72,
                "alpha": 0.85,
                "always_on_top": True,
                "position": "top-right",
                "padding": 18,
            },
            "ptt_enabled": True,
            "ptt_key": "right_ctrl",  # right_ctrl | ctrl_r | none
        },
        "azure": {
            "speech_key": None,
            "speech_region": None,
        },
    }
}


def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def _get_by_path(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _set_by_path(data: Dict[str, Any], path: str, value: Any) -> None:
    cur: Any = data
    parts = path.split(".")
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


class Config:
    """Persistent voice-only config with safe defaults.

    Config file:
      ~/.vox/config.yaml

    Data files:
      ~/.vox/session.jsonl
      ~/.vox/audit.jsonl
    """

    def __init__(
        self, config_path: Optional[str] = None, base_dir: Optional[str] = None
    ):
        self.base_dir = base_dir or os.path.expanduser("~/.vox")
        self.config_path = config_path or os.path.join(self.base_dir, "config.yaml")
        self.data: Dict[str, Any] = deepcopy(DEFAULT_CONFIG)
        self._load_or_init()

    # ---------- persistence ----------
    def _load_or_init(self) -> None:
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)
        if os.path.exists(self.config_path):
            self.load()
        else:
            self.save()

    def load(self) -> None:
        if not yaml:
            raise RuntimeError("PyYAML is required to load config.yaml")
        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if not isinstance(raw, dict):
            raw = {}
        _deep_merge(self.data, raw)

    def save(self) -> None:
        if not yaml:
            raise RuntimeError("PyYAML is required to save config.yaml")
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.data, f, sort_keys=False)

    # ---------- generic get/set ----------
    def get(self, key_path: str, default: Any = None) -> Any:
        return _get_by_path(self.data, key_path, default)

    def set(self, key_path: str, value: Any) -> None:
        _set_by_path(self.data, key_path, value)

    # ---------- paths ----------
    @property
    def SESSION_FILE(self) -> str:
        return os.path.join(self.base_dir, "session.jsonl")

    @property
    def AUDIT_FILE(self) -> str:
        return os.path.join(self.base_dir, "audit.jsonl")

    def ensure_dirs(self) -> None:
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)

    # ---------- permissions ----------
    def get_permission(self, scope: str) -> str:
        return str(self.data["voice"]["permissions"].get(scope, "ask"))

    def set_permission(self, scope: str, value: str) -> None:
        self.data["voice"]["permissions"][scope] = value
        # Persist immediately to keep permission decisions stable
        try:
            self.save()
        except Exception:
            pass

    # ---------- privacy ----------
    @property
    def LOG_TEXT(self) -> bool:
        return bool(self.data["voice"]["privacy"].get("log_text", True))

    # ---------- audio (compat attrs) ----------
    @property
    def SAMPLE_RATE(self) -> int:
        return int(self.data["voice"]["audio"]["sample_rate"])

    @property
    def FRAME_DURATION_MS(self) -> int:
        return int(self.data["voice"]["audio"]["frame_ms"])

    @property
    def VAD_ENABLED(self) -> bool:
        return bool(self.data["voice"]["audio"].get("vad_enabled", True))

    @property
    def VAD_MODE(self) -> int:
        return int(self.data["voice"]["audio"]["vad_mode"])

    @property
    def SILENCE_THRESHOLD_MS(self) -> int:
        return int(self.data["voice"]["audio"]["silence_ms"])

    @property
    def MIN_SPEECH_MS(self) -> int:
        return int(self.data["voice"]["audio"]["min_speech_ms"])

    @property
    def DEVICE_INDEX(self) -> Optional[int]:
        return self.data["voice"]["audio"].get("device_index", None)

    @property
    def FIXED_RECORD_S(self) -> int:
        return int(self.data["voice"]["audio"].get("fixed_record_s", 8))

    @property
    def POST_SILENCE_GRACE_MS(self) -> int:
        return int(self.data["voice"]["audio"].get("post_silence_grace_ms", 1200))

    @property
    def SPEECH_ONSET_MS(self) -> int:
        return int(self.data["voice"]["audio"]["speech_onset_ms", 120])

    @property
    def SPEECH_RESUME_MS(self) -> int:
        return int(self.data["voice"]["audio"]["speech_resume_ms", 90])

    @property
    def MAX_RECORD_S(self) -> int:
        return int(self.data["voice"]["audio"]["max_record_s", 20])

    # ---------- STT (compat attrs) ----------
    @property
    def WHISPER_MODEL_SIZE(self) -> str:
        return str(self.data["voice"]["stt"]["model"])

    @property
    def WHISPER_MODEL(self) -> str:
        return self.WHISPER_MODEL_SIZE

    @property
    def COMPUTE_TYPE(self) -> str:
        return str(self.data["voice"]["stt"]["compute_type"])

    @property
    def LANGUAGE(self) -> Optional[str]:
        lang = str(self.data["voice"]["stt"].get("lang", "auto"))
        return None if lang == "auto" else lang

    @property
    def LANG(self) -> str:
        return str(self.data["voice"]["stt"].get("lang", "auto"))

    # ---------- routing ----------
    @property
    def TARGET(self) -> str:
        return str(self.data["voice"]["routing"].get("target", "cli:gemini"))

    @property
    def INSERT_MODE(self) -> str:
        return str(self.data["voice"]["routing"].get("insert", "active"))

    @property
    def HISTORY_TURNS(self) -> int:
        return int(self.data["voice"]["routing"].get("history_turns", 8))

    @property
    def TTS_MODE(self) -> str:
        return str(self.data["voice"]["routing"].get("tts", "seraphina"))

    @property
    def IMPROVE_MODE(self) -> str:
        return str(self.data["voice"]["routing"].get("improve", "off"))

    # ---------- Azure ----------
    @property
    def AZURE_KEY(self) -> Optional[str]:
        return os.getenv("AZURE_SPEECH_KEY") or self.data["voice"]["azure"].get(
            "speech_key"
        )

    @property
    def AZURE_REGION(self) -> Optional[str]:
        return os.getenv("AZURE_SPEECH_REGION") or self.data["voice"]["azure"].get(
            "speech_region"
        )

    @property
    def AZURE_VOICE(self) -> str:
        return str(self.get("voice.tts.azure.voice", ""))

    @property
    def tts_enabled(self) -> bool:
        mode = self.TTS_MODE
        if mode == "none":
            return False
        if mode == "azure":
            return bool(self.AZURE_KEY and self.AZURE_REGION)
        if mode == "kokoro" or mode == "orpheus":
            return True
        return True  # auto-detect

    # ---------- CLI overrides ----------
    def update_from_args(
        self,
        *,
        model: Optional[str] = None,
        vad: Optional[bool] = None,
        vad_mode: Optional[int] = None,
        silence_ms: Optional[int] = None,
        device: Optional[int] = None,
        lang: Optional[str] = None,
        target: Optional[str] = None,
        insert: Optional[str] = None,
        tts: Optional[str] = None,
        history_turns: Optional[int] = None,
        improve: Optional[str] = None,
        ollama_model: Optional[str] = None,
        persist: bool = False,
    ) -> None:
        """Apply CLI overrides. Not persisted unless persist=True."""
        v = self.data["voice"]

        if model:
            v["stt"]["model"] = model
        if vad is not None:
            v["audio"]["vad_enabled"] = bool(vad)
        if vad_mode is not None:
            v["audio"]["vad_mode"] = int(vad_mode)
        if silence_ms is not None:
            v["audio"]["silence_ms"] = int(silence_ms)
        if device is not None:
            v["audio"]["device_index"] = int(device)
        if lang:
            v["stt"]["lang"] = lang
        if target:
            v["routing"]["target"] = target
        if insert:
            v["routing"]["insert"] = insert
        if tts:
            v["routing"]["tts"] = tts
        if history_turns is not None:
            v["routing"]["history_turns"] = int(history_turns)
        if improve is not None:
            v["routing"]["improve"] = improve
        if ollama_model is not None:
            v["llm"]["ollama"]["model"] = ollama_model

        if persist:
            self.save()
