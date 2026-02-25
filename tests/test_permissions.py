from wandavoice.config import Config
from wandavoice.permissions import PermissionManager

def test_permissions_ask_then_persist(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    pm = PermissionManager(cfg, safe_mode=False, interactive=True)

    calls = {"n": 0}
    def prompt(msg):
        calls["n"] += 1
        return True

    assert pm.is_allowed("window_inject", prompt=prompt, reason="test") is True
    assert calls["n"] == 1
    # second time should not ask
    assert pm.is_allowed("window_inject", prompt=prompt, reason="test") is True
    assert calls["n"] == 1

def test_permissions_safe_mode_denies(tmp_path):
    cfg = Config(base_dir=str(tmp_path))
    pm = PermissionManager(cfg, safe_mode=True, interactive=True)
    assert pm.is_allowed("window_inject", prompt=lambda _: True, reason="x") is False
    assert pm.is_allowed("audio_record", prompt=lambda _: True, reason="x") is True
