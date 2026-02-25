import unittest
import os
import shutil
import tempfile
from wandavoice.config import Config
from wandavoice.skills.manager import SkillManager
from wandavoice.permissions import PermissionManager

class TestSkills(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cfg = Config(base_dir=self.test_dir)
        self.skill_mgr = SkillManager(self.cfg)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_shell_skill_execution(self):
        """Prüft, ob ein einfacher Echo-Befehl funktioniert."""
        self.cfg.set_permission("exec_external_cli", "allow")
        result = self.skill_mgr.run_skill("shell", command="echo 'WANDA_TEST'")
        self.assertIn("WANDA_TEST", result)
        self.assertIn("Success", result)

    def test_shell_skill_denied(self):
        """Prüft, ob der Skill bei 'deny' blockiert wird."""
        self.cfg.set_permission("exec_external_cli", "deny")
        result = self.skill_mgr.run_skill("shell", command="echo 'SECRET'")
        self.assertIn("Error: Permission denied", result)
        self.assertNotIn("SECRET", result)

if __name__ == "__main__":
    unittest.main()
