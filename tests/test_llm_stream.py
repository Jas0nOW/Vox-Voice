import unittest
import json
import io
import os
from unittest.mock import patch, MagicMock
from wandavoice.llm import GeminiLLM

class TestLLMStream(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock()
        # Mock shutil.which to return a path so initialization succeeds
        with patch("shutil.which", return_value="/usr/bin/gemini"):
            self.llm = GeminiLLM(self.config)

    @patch("subprocess.Popen")
    def test_generate_stream_json(self, mock_popen):
        """Test that generate_stream correctly parses stream-json output."""
        # Mocking the process and its stdout
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        # Simulate stream-json lines
        json_lines = [
            json.dumps({"content": "Hello"}) + "\n",
            json.dumps({"content": " world"}) + "\n",
            json.dumps({"response": "!"}) + "\n"
        ]
        mock_process.stdout = io.StringIO("".join(json_lines))
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_process.poll.return_value = 0

        # Run the generator
        chunks = list(self.llm.generate_stream("test prompt", []))
        
        self.assertEqual(chunks, ["Hello", " world", "!"])

    @patch("subprocess.Popen")
    def test_generate_stream_fallback(self, mock_popen):
        """Test that generate_stream handles non-json lines gracefully."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        
        # Mixed output
        output_lines = [
            "Just a plain line\n",
            json.dumps({"content": "Part 2"}) + "\n"
        ]
        mock_process.stdout = io.StringIO("".join(output_lines))
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_process.poll.return_value = 0

        chunks = list(self.llm.generate_stream("test prompt", []))
        
        self.assertEqual(chunks, ["Just a plain line\n", "Part 2"])

    def test_parse_response_say_show(self):
        """Test the SAY/SHOW parsing logic."""
        raw = "SAY: Hello there. SHOW: Here is some code."
        say, show = self.llm.parse_response(raw)
        self.assertEqual(say, "Hello there.")
        self.assertEqual(show, "Here is some code.")

    def test_parse_response_heuristic(self):
        """Test fallback parsing when SAY/SHOW are missing."""
        raw = "This is a simple response without tags. It has multiple sentences."
        say, show = self.llm.parse_response(raw)
        self.assertEqual(say, raw)
        self.assertEqual(show, "")

if __name__ == "__main__":
    unittest.main()
