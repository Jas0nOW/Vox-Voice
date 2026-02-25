from wandavoice.cli import _record_and_transcribe_once
from wandavoice.config import Config


class _StubRecorder:
    def __init__(self):
        self.fixed_seconds = None
        self.record_called = 0
        self.fixed_called = 0

    def record(self):
        self.record_called += 1
        raise AssertionError("record() must not be called when VAD is off")

    def record_fixed(self, seconds: int):
        self.fixed_called += 1
        self.fixed_seconds = int(seconds)
        return b"fake-audio"


class _StubSTT:
    def __init__(self):
        self.calls = 0
        self.last_audio = None

    def transcribe(self, audio):
        self.calls += 1
        self.last_audio = audio
        return "ok"


def test_vad_off_records_fixed_seconds_then_stt_once(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    cfg.set("voice.audio.vad_enabled", False)
    cfg.set("voice.audio.fixed_record_s", 3)

    rec = _StubRecorder()
    stt = _StubSTT()

    out = _record_and_transcribe_once(cfg, rec, stt)
    assert out == "ok"
    assert rec.fixed_called == 1
    assert rec.fixed_seconds == 3
    assert rec.record_called == 0
    assert stt.calls == 1
    assert stt.last_audio == b"fake-audio"

