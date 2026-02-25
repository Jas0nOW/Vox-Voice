import unittest
import subprocess
import os
import fcntl
from unittest.mock import patch, MagicMock
from wandavoice.audio import AudioRecorder
from wandavoice.config import Config

class TestAudioHardening(unittest.TestCase):
    def setUp(self):
        self.cfg = Config()
        # VAD Model Mocking
        with patch("torch.hub.load") as mock_hub:
            mock_hub.return_value = (MagicMock(), MagicMock())
            self.recorder = AudioRecorder(self.cfg)

    @patch("subprocess.Popen")
    @patch("fcntl.fcntl") # Wir fangen System-Aufrufe ab
    def test_recorder_process_cleanup(self, mock_fcntl, mock_popen):
        """Prüft, ob der pw-record Prozess in jedem Fall terminiert wird."""
        
        # 1. Den Prozess-Mock vorbereiten
        mock_process = MagicMock()
        mock_process.poll.return_value = None # Prozess lebt
        
        # 2. Den stdout-Mock vorbereiten (die 'echte Tasse')
        # Wir geben eine echte Zahl (1) für die Dateinummer zurück
        mock_process.stdout.fileno.return_value = 1 
        mock_popen.return_value = mock_process
        
        # 3. Wir mocken den Lese-Fehler
        with patch.object(self.recorder, "_read_nonblocking", side_effect=RuntimeError("Test crash")):
            try:
                # Dieser Aufruf geht jetzt durch _start_pw_record ohne Fehler durch
                self.recorder.record_phrase()
            except RuntimeError:
                pass
        
        # 4. Die ultimative Verifizierung
        self.assertTrue(mock_process.terminate.called, "CRITICAL: terminate() wurde nicht aufgerufen!")
        print("\n[OK] Audio Hardening Test bestanden (100/100).")

if __name__ == "__main__":
    unittest.main()
