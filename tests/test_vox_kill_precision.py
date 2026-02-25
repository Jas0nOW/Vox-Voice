import unittest
import subprocess
import os
import signal
from unittest.mock import patch, MagicMock
from wandavoice.main import cli
from click.testing import CliRunner

class TestVoxKillPrecision(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("subprocess.check_output")
    @patch("os.kill")
    def test_kill_spares_interactive_gemini(self, mock_kill, mock_pgrep):
        """Testet, dass eine normale Gemini-Sitzung verschont bleibt."""
        
        # Intelligenter pgrep Mock:
        # Nur wenn nach 'gemini' gesucht wird, geben wir 100 und 200 zurück.
        # Bei anderen Suchen (wandavoice etc.) geben wir nichts zurück.
        def pgrep_side_effect(cmd, **kwargs):
            pattern = cmd[2]
            if pattern == "gemini":
                return b"100 200"
            return b"" # Nichts gefunden für andere Muster
            
        mock_pgrep.side_effect = pgrep_side_effect
        
        with patch("builtins.open") as m:
            def side_effect(path, mode='rb'):
                mock = MagicMock()
                if "100" in path:
                    # Interactive Gemini (Verschonen!)
                    mock.__enter__.return_value.read.return_value = b"gemini\0--interactive\0"
                else:
                    # WANDA Gemini (Killen!)
                    mock.__enter__.return_value.read.return_value = b"gemini\0.runtime/gemini_home\0--output-format\0stream-json\0"
                return mock
            m.side_effect = side_effect
            
            result = self.runner.invoke(cli, ["kill"])
            
            # Verifizierung
            killed_pids = [call[0][0] for call in mock_kill.call_args_list]
            
            # PID 200 muss in den Abschüssen sein
            self.assertIn(200, killed_pids)
            # PID 100 darf NICHT abgeschossen worden sein
            self.assertNotIn(100, killed_pids)
            print("\n[OK] Precision Kill Test bestanden (100/100).")

if __name__ == "__main__":
    unittest.main()
