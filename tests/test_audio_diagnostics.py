from wandavoice.audio_diagnostics import _classify_exception_message


def test_classify_portaudio_missing_common_messages():
    assert _classify_exception_message("PortAudio library not found") == "portaudio_missing"
    assert _classify_exception_message("libportaudio.so.2: cannot open shared object file") == "portaudio_missing"


def test_classify_permission_denied():
    assert _classify_exception_message("[Errno 13] Permission denied: '/dev/snd/pcmC0D0c'") == "permission_denied"


def test_classify_unknown_error():
    assert _classify_exception_message("some unrelated error") == "unknown_error"


def test_classify_pipewire_pulse_issue():
    assert _classify_exception_message("Error querying device -1") == "pipewire_pulse_issue"
