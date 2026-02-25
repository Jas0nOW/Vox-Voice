import os
from wandavoice.config import Config

def test_config_creates_file(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    assert os.path.exists(os.path.join(tmp_path, "config.yaml"))

def test_cli_overrides_not_persisted_by_default(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    assert cfg.WHISPER_MODEL_SIZE == "large-v3-turbo"
    cfg.update_from_args(model="large-v3", persist=False)
    assert cfg.WHISPER_MODEL_SIZE == "large-v3"
    # reload from disk should still be default large-v3-turbo
    cfg2 = Config(base_dir=str(tmp_path))
    assert cfg2.WHISPER_MODEL_SIZE == "large-v3-turbo"

def test_permission_persist(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    cfg.set_permission("clipboard_write", "allow")
    cfg2 = Config(base_dir=str(tmp_path))
    assert cfg2.get_permission("clipboard_write") == "allow"
