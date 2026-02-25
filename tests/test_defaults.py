from wandavoice.config import Config


def test_default_improve_is_basic(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    assert cfg.IMPROVE_MODE == "basic"


def test_default_hotkey_is_right_ctrl(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    assert cfg.HOTKEY == "right_ctrl"
