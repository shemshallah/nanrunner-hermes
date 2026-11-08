"""Hermes/Gemma bridge regression tests, no cloud credential required."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hermes_gemma_session as bridge


class BridgeTests(unittest.TestCase):
    def test_normalized_phrase(self):
        self.assertTrue(bridge.recalled("It's COBALT, HERON.", "cobalt heron"))
        self.assertFalse(bridge.recalled("HERON COBALT", "cobalt heron"))

    def test_secret_validation(self):
        self.assertFalse(bridge.valid_key({}))
        self.assertFalse(bridge.valid_key({"OLLAMA_API_KEY": "bad\nkey"}))
        self.assertTrue(bridge.valid_key({"OLLAMA_API_KEY": "placeholder"}))

    @patch.object(bridge, "choose_phrase", return_value="cobalt heron")
    @patch.object(bridge.uuid, "uuid4")
    @patch.object(bridge, "call_hermes")
    def test_resumes_previous_session_without_repeating_phrase(self, call, uuid4, phrase):
        uuid4.return_value.hex = "1234567890abcdef1234567890abcdef"
        call.side_effect = ["ACK", "cobalt heron"]
        with patch.dict(os.environ, {"OLLAMA_API_KEY": "placeholder"}, clear=True):
            self.assertEqual(bridge.main(), 0)
        self.assertEqual(call.call_count, 2)
        first = call.call_args_list[0].args[0]
        second = call.call_args_list[1].args[0]
        self.assertIn("ollama-cloud", first)
        self.assertIn("gemma4:31b", first)
        self.assertIn("cobalt heron", first[-1])
        self.assertEqual(second[:2], ["--resume", "nanrunner-gemma-1234567890abcdef"])
        self.assertNotIn("cobalt heron", str(second))
        self.assertNotIn("--provider", second)
        self.assertNotIn("--model", second)

    @patch.object(bridge, "choose_phrase", return_value="cobalt heron")
    @patch.object(bridge, "call_hermes", side_effect=["ACK", "I forgot"])
    def test_broken_session_fails(self, call, phrase):
        with patch.dict(os.environ, {"OLLAMA_API_KEY": "placeholder"}, clear=True):
            self.assertEqual(bridge.main(), 1)

    @patch.object(bridge.subprocess, "run")
    def test_error_does_not_expose_provider_stderr(self, run):
        run.return_value = SimpleNamespace(returncode=7, stdout="", stderr="SENSITIVE")
        with self.assertRaisesRegex(RuntimeError, "exited 7") as err:
            bridge.call_hermes(["-q", "test"], {"OLLAMA_API_KEY": "placeholder"})
        self.assertNotIn("SENSITIVE", str(err.exception))


if __name__ == "__main__":
    unittest.main()
