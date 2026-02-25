from click.testing import CliRunner

from wandavoice.cli import wanda


def test_cli_accepts_vad_webrtc(tmp_path):
    runner = CliRunner()
    res = runner.invoke(
        wanda,
        ["voice", "--text", "Hallo", "--target", "stdout", "--safe", "--vad", "webrtc", "--no-orb", "--no-preview"],
        env={"HOME": str(tmp_path)},
    )
    assert res.exit_code == 0, res.output


def test_cli_accepts_vad_silero(tmp_path):
    runner = CliRunner()
    res = runner.invoke(
        wanda,
        ["voice", "--text", "Hallo", "--target", "stdout", "--safe", "--vad", "silero", "--no-orb", "--no-preview"],
        env={"HOME": str(tmp_path)},
    )
    assert res.exit_code == 0, res.output

