import os
import unittest
from unittest.mock import patch, MagicMock
from wandavoice.process_manager import acquire_lock, release_lock, PID_FILE

class TestProcessManager(unittest.TestCase):

    def setUp(self):
        # Ensure PID file doesn't exist before each test
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

    def tearDown(self):
        # Clean up after each test
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

    def test_acquire_lock_fresh(self):
        """Test that we can acquire the lock when no PID file exists."""
        result = acquire_lock()
        self.assertTrue(result)
        self.assertTrue(os.path.exists(PID_FILE))
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        self.assertEqual(pid, os.getpid())

    @patch("os.kill")
    def test_acquire_lock_already_running(self, mock_kill):
        """Test that acquire_lock returns False if the process in the PID file is alive."""
        # Setup: Create a fake PID file
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write("999999")
        
        # Mock os.kill(999999, 0) to succeed (meaning process exists)
        mock_kill.return_value = None
        
        result = acquire_lock()
        self.assertFalse(result)
        mock_kill.assert_called_with(999999, 0)

    @patch("os.kill")
    def test_acquire_lock_zombie_cleanup(self, mock_kill):
        """Test that acquire_lock takes over if the process in the PID file is dead."""
        # Setup: Create a fake PID file
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write("999999")
        
        # Mock os.kill(999999, 0) to raise ProcessLookupError (meaning process is dead)
        mock_kill.side_effect = ProcessLookupError()
        
        result = acquire_lock()
        self.assertTrue(result)
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        self.assertEqual(pid, os.getpid())

    def test_release_lock(self):
        """Test that release_lock removes the PID file."""
        acquire_lock()
        self.assertTrue(os.path.exists(PID_FILE))
        release_lock()
        self.assertFalse(os.path.exists(PID_FILE))

if __name__ == "__main__":
    unittest.main()
