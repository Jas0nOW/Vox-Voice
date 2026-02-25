from wandavoice.voice_control import parse_voice_control


def test_wake_strips_prefix_only_when_leading():
    r = parse_voice_control("Hey Wanda mach das bitte")
    assert r.command == "wake"
    assert r.remainder == "mach das bitte"

    r2 = parse_voice_control("Danke Wanda")
    assert r2.command == "wake"
    assert r2.remainder == ""


def test_pause_sleep_stop():
    assert parse_voice_control("pause").command == "pause"
    assert parse_voice_control("Gute Nacht Wanda").command == "sleep"
    assert parse_voice_control("stopp").command == "stop"
    assert parse_voice_control("stopp jetzt").command == "stop"


def test_briefing_variants():
    assert parse_voice_control("Status Update").command == "briefing"
    assert parse_voice_control("was gibt es neues").command == "briefing"
    assert parse_voice_control("Guten Morgen Wanda").command == "briefing"


def test_repeat_and_read_aloud():
    assert parse_voice_control("wiederholen").command == "repeat"
    assert parse_voice_control("kannst du mir das vorlesen").command == "read_aloud"
    assert parse_voice_control("kannst du mir das noch mal vorlesen").command == "read_aloud"


def test_shutdown_is_conservative():
    assert parse_voice_control("ausschalten").command == "shutdown"
    assert parse_voice_control("das war es für heute").command == "shutdown"

    # Should NOT trigger inside longer dictation without wake
    assert parse_voice_control("ich will nicht ausschalten sondern weiter schreiben").command == "none"


def test_ambiguous_wander_in_greeting():
    assert parse_voice_control("hey wander").command == "ambiguous_wake"
