import pytest

from wandavoice.audio import AudioRecorder, _SileroSegmenter
from wandavoice.config import Config


def test_silero_missing_deps_is_actionable(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    cfg.set("voice.audio.vad_backend", "silero")
    with pytest.raises(RuntimeError) as ei:
        AudioRecorder(cfg)
    # Avoid being too strict about wording, but require install hint.
    assert "silero" in str(ei.value).lower()
    assert "pip install" in str(ei.value).lower()


def test_silero_segmenter_emits_segment_on_end():
    seg = _SileroSegmenter(frame_ms=30, min_speech_ms=60, max_record_s=5)
    # Pre-roll frames before start should be included once start is seen.
    f0 = b"\x00\x00" * 10
    f1 = b"\x01\x00" * 10
    f2 = b"\x02\x00" * 10
    f3 = b"\x03\x00" * 10
    import numpy as np

    a0 = np.frombuffer(f0, dtype=np.int16)
    a1 = np.frombuffer(f1, dtype=np.int16)
    a2 = np.frombuffer(f2, dtype=np.int16)
    a3 = np.frombuffer(f3, dtype=np.int16)

    assert seg.feed(a0, None) is None
    assert seg.feed(a1, None) is None
    assert seg.feed(a2, "start") is None
    out = seg.feed(a3, "end")
    assert out is not None
    assert out.dtype == np.int16
    assert out.ndim == 1

