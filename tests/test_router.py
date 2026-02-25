import unittest
import os
import shutil
import tempfile
from wandavoice.config import Config
from wandavoice.permissions import PermissionManager
from wandavoice.audit import AuditLogger
from wandavoice.router import Router, RuntimeOptions, apply_safe_overrides

class DummyInserter:
    def insert_text(self, text, mode):
        return "clipboard"

class TestRouter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cfg = Config(base_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_apply_safe_overrides(self):
        rt = RuntimeOptions(target="insert", insert_mode="active", tts_mode="auto", safe_mode=True)
        eff = apply_safe_overrides(rt)
        self.assertEqual(eff.target, "stdout")
        self.assertEqual(eff.insert_mode, "off")
        self.assertEqual(eff.tts_mode, "none")

    def test_router_insert_success(self):
        self.cfg.set_permission("window_inject", "allow")
        self.cfg.set_permission("clipboard_write", "allow")
        pm = PermissionManager(self.cfg, safe_mode=False, interactive=False)
        audit = AuditLogger(self.cfg)
        router = Router(self.cfg, permissions=pm, audit=audit, inserter=DummyInserter())

        rt = RuntimeOptions(target="insert", insert_mode="clipboard", tts_mode="none", safe_mode=False)
        res = router.route_text("hello", rt, prompt=None)
        self.assertEqual(res.target_used, "insert")
        self.assertTrue(res.inserted)

    def test_router_insert_permission_denied_fallback_stdout(self):
        self.cfg.set_permission("window_inject", "deny")
        pm = PermissionManager(self.cfg, safe_mode=False, interactive=False)
        audit = AuditLogger(self.cfg)
        router = Router(self.cfg, permissions=pm, audit=audit, inserter=DummyInserter())

        rt = RuntimeOptions(target="insert", insert_mode="clipboard", tts_mode="none", safe_mode=False)
        res = router.route_text("hello", rt, prompt=None)
        self.assertEqual(res.target_used, "stdout")
        self.assertTrue(res.fallback_to_stdout)

if __name__ == "__main__":
    unittest.main()
