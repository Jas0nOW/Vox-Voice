# VOX Mission Control Center — startup summary (terminal)
# Live status is handled by WandaOrb (tkinter MCC window)
class MissionControl:
    def __init__(self, config):
        self.config = config

    def start_dashboard(self):
        print("\n" + "=" * 50)
        print("   VOX MISSION CONTROL CENTER")
        print("=" * 50)

        print("\n[TTS Engine]")
        tts_mode = self.config.TTS_MODE
        print(f"  Mode: {tts_mode}")

        if tts_mode == "seraphina":
            voice = self.config.get(
                "voice.tts.seraphina.voice", "de-DE-SeraphinaMultilingualNeural"
            )
            rate = self.config.get("voice.tts.seraphina.rate", "+15%")
            print(f"  Voice: {voice}")
            print(f"  Rate:  {rate}")
        elif tts_mode == "orpheus":
            voice = self.config.get("voice.tts.orpheus.voice", "default")
            emotion = self.config.get("voice.tts.orpheus.emotion", "neutral")
            print(f"  Voice: {voice}")
            print(f"  Emotion: {emotion}")

        print("\n[STT Engine]")
        model = self.config.get("voice.stt.model", "small")
        lang = self.config.get("voice.stt.lang", "auto")
        print(f"  Model: {model}")
        print(f"  Language: {lang}")

        print("\n[Audio]")
        vad = self.config.get("voice.audio.vad_enabled", True)
        sample_rate = self.config.get("voice.audio.sample_rate", 16000)
        threshold = self.config.get("voice.audio.vad_threshold", 0.3)
        print(f"  VAD Enabled: {vad}")
        print(f"  VAD Threshold: {threshold}")
        print(f"  Sample Rate: {sample_rate}Hz")

        print("\n[Routing]")
        target = self.config.get("voice.routing.target", "insert")
        insert = self.config.get("voice.routing.insert", "active")
        history = self.config.get("voice.routing.history_turns", 8)
        print(f"  Target: {target}")
        print(f"  Insert Mode: {insert}")
        print(f"  History Turns: {history}")

        print("\n[UI]")
        orb = self.config.get("voice.ui.orb_enabled", True)
        ptt = self.config.get("voice.ui.ptt_enabled", True)
        print(f"  Orb Enabled: {orb}")
        print(f"  Hotkey: {'Right Ctrl (toggle)' if ptt else 'VAD only'}")

        print("\n" + "=" * 50 + "\n")

    def update_tts(self, mode: str):
        self.config.set("voice.routing.tts", mode)
        self.config.save()
        print(f"TTS mode updated to: {mode}")

    def update_model(self, model: str):
        self.config.set("voice.stt.model", model)
        self.config.save()
        print(f"STT model updated to: {model}")

    def toggle_orb(self, enabled: bool):
        self.config.set("voice.ui.orb_enabled", enabled)
        self.config.save()
        print(f"Orb UI {'enabled' if enabled else 'disabled'}")
