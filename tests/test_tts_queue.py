import unittest
import time
import os
import queue
from unittest.mock import patch, MagicMock
from wandavoice.tts import EdgeSeraphina

class TestTTSQueue(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock()
        # Mock threads to not start them automatically if we want to test workers manually,
        # but here we'll let them start and mock the subprocesses they call.
        with patch("threading.Thread"):
             # We patch Thread so it doesn't actually run the workers in background 
             # during init if we want fine-grained control, but EdgeSeraphina starts them in __init__.
             pass

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("os.remove")
    def test_tts_pipeline(self, mock_remove, mock_popen, mock_run):
        """Test that text put into the queue is processed and played."""
        # Initialize with mocked workers for better control
        with patch("threading.Thread") as mock_thread:
            tts = EdgeSeraphina(self.config)
            
            # Manually get the worker functions from the mock calls
            # Thread(target=self._generator_worker)
            gen_worker = mock_thread.call_args_list[0][1]['target']
            play_worker = mock_thread.call_args_list[1][1]['target']

        # 1. Test Generator Worker
        tts.text_queue.put("Hello world")
        
        # We need to stop the loop after one item
        tts.running = True
        
        # Mock subprocess.run to succeed
        mock_run.return_value = MagicMock(returncode=0)
        
        # Run one iteration of gen_worker manually (simulated)
        # We'll just put a stop sentinel in the queue
        tts.text_queue.put(None)
        gen_worker() # This will process "Hello world" then "None" and exit
        
        # Check if wav path was put into audio_queue
        self.assertEqual(tts.audio_queue.qsize(), 1)
        wav_path = tts.audio_queue.get()
        self.assertTrue(wav_path.endswith(".wav"))
        
        # 2. Test Player Worker
        tts.audio_queue.put(wav_path)
        tts.audio_queue.put(None)
        
        # Mock Popen
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        play_worker() # This will process wav_path then None and exit
        
        mock_popen.assert_called()
        self.assertIn("pw-play", mock_popen.call_args[0][0])
        mock_process.wait.assert_called()

    @patch("subprocess.Popen")
    def test_stop_cleanup(self, mock_popen):
        """Test that stop() clears queues and kills playback."""
        tts = EdgeSeraphina(self.config)
        tts._playback_process = MagicMock()
        
        tts.text_queue.put("Queue item")
        tts.audio_queue.put("temp.wav")
        
        tts.stop()
        
        self.assertTrue(tts.text_queue.empty())
        self.assertTrue(tts.audio_queue.empty())
        tts._playback_process.terminate.assert_called()

if __name__ == "__main__":
    unittest.main()
