import unittest
import subprocess
from unittest.mock import patch, MagicMock, call
from click.testing import CliRunner
from wandavoice.main import cli

class TestVoxKill(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    @patch("subprocess.check_output")
    @patch("os.kill")
    def test_vox_kill_normal(self, mock_kill, mock_pgrep):
        """Test that normal vox kill preserves the dashboard."""
        # Setup pgrep to return PIDs for everything
        def pgrep_side_effect(cmd, **kwargs):
            pattern = cmd[2]
            if pattern == "http.server 5173":
                return b"5173"
            return b"1234"
            
        mock_pgrep.side_effect = pgrep_side_effect
        
        result = self.runner.invoke(cli, ["kill"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Dashboard preserved", result.output)
        
        # Verify that PID 1234 was killed, but 5173 was NOT
        mock_kill.assert_any_call(1234, 9)
        # Check that 5173 was never killed
        for call_args in mock_kill.call_args_list:
            self.assertNotEqual(call_args[0][0], 5173)

    @patch("subprocess.check_output")
    @patch("os.kill")
    def test_vox_kill_force(self, mock_kill, mock_pgrep):
        """Test that vox kill --force kills everything."""
        mock_pgrep.side_effect = lambda cmd, **kwargs: b"5173" if cmd[2] == "http.server 5173" else b"1234"
        
        result = self.runner.invoke(cli, ["kill", "--force"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Force=True", result.output)
        
        # Verify that 5173 was killed
        mock_kill.assert_any_call(5173, 9)

if __name__ == "__main__":
    unittest.main()
