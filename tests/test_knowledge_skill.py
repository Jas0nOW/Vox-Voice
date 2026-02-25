import unittest
import os
import shutil
from wandavoice.skills.knowledge import knowledge_op
from wandavoice.config import Config

class TestKnowledgeSkill(unittest.TestCase):
    def setUp(self):
        self.cfg = Config()
        self.test_note_dir = os.path.expanduser("~/Documents/WANDA_Notes")
        if os.path.exists(self.test_note_dir):
            shutil.rmtree(self.test_note_dir)

    def test_notebooklm_sync(self):
        """Testet das Speichern einer Notiz für NotebookLM."""
        content = "Das ist eine Test-Notiz für NotebookLM."
        title = "Test Note"
        result = knowledge_op(op="sync_notebooklm", content=content, title=title)
        
        self.assertIn("Successfully synced", result)
        # Filename will be Test_Note.md
        file_path = os.path.join(self.test_note_dir, "Test_Note.md")
        self.assertTrue(os.path.exists(file_path))
        
        with open(file_path, "r") as f:
            data = f.read()
            self.assertIn(content, data)
            self.assertIn("# Test Note", data)

    def test_read_file(self):
        """Testet das Lesen einer Datei."""
        test_file = "/tmp/wanda_test.txt"
        with open(test_file, "w") as f:
            f.write("Hello WANDA")
            
        result = knowledge_op(op="read", path=test_file)
        self.assertEqual(result, "Hello WANDA")
        os.remove(test_file)

if __name__ == "__main__":
    unittest.main()
