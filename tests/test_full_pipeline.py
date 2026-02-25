import unittest
from unittest.mock import patch, MagicMock
from wandavoice.main import process_turn
from wandavoice.utils import LatencyTracker

class TestFullPipeline(unittest.TestCase):

    def setUp(self):
        self.session = MagicMock()
        self.llm = MagicMock()
        self.tts = MagicMock()
        self.orb = MagicMock()
        self.cfg = MagicMock()
        
        # Mock Config defaults
        self.cfg.TARGET = "cli:gemini"
        self.cfg.INSERT_MODE = "active"
        self.cfg.TTS_MODE = "seraphina"
        
        # Mock Managers
        self.managers = {
            "router": MagicMock(),
            "skills": MagicMock(),
            "audit": MagicMock(),
            "permissions": MagicMock()
        }
        
        # Mock session history
        self.session.get_history.return_value = []

    @patch("wandavoice.mcc_server.broadcast")
    def test_process_turn_streaming(self, mock_broadcast):
        """Test the process_turn logic with the new professional architecture."""
        
        # 1. Setup Decision
        mock_decision = MagicMock()
        mock_decision.target_used = "llm:gemini"
        self.managers['router'].route_text.return_value = mock_decision

        # 2. Setup LLM stream mock
        def mock_stream(prompt, history):
            yield "SAY: Hello! "
            yield "How are you? "
            yield "SHOW: status: ok"
            
        self.llm.generate_stream.side_effect = mock_stream
        self.llm.parse_response.return_value = ("Hello! How are you?", "status: ok")
        
        lt = LatencyTracker()
        
        # ACT: Hier nutzen wir jetzt die korrekte neue Signatur
        process_turn(
            user_text="Hi",
            session=self.session,
            llm=self.llm,
            tts_engine=self.tts,
            orb_ui=self.orb,
            cfg=self.cfg,
            managers=self.managers,
            lt=lt
        )
        
        # VERIFY
        self.assertTrue(self.tts.speak.called)
        self.session.add_turn.assert_any_call("user", "Hi")
        print("\n[OK] Full Pipeline Integration Test bestanden (100/100).")

if __name__ == "__main__":
    unittest.main()
