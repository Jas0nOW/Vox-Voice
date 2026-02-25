from click.testing import CliRunner

from wandavoice.cli import wanda


def test_mic_test_command_exists_and_has_seconds_option():
    runner = CliRunner()
    res = runner.invoke(wanda, ["voice", "mic-test", "--help"])
    assert res.exit_code == 0, res.output
    assert "--seconds" in res.output
    assert "--vad" in res.output


def test_voice_has_seconds_option_and_vad_off_choice():
    runner = CliRunner()
    res = runner.invoke(wanda, ["voice", "--help"])
    assert res.exit_code == 0, res.output
    assert "--seconds" in res.output
    assert "--vad" in res.output
    # Choice rendering differs by Click versions; just assert "off" is mentioned.
    assert "off" in res.output

