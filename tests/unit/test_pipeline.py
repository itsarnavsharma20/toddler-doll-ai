"""Unit tests for the chat pipeline. The LLM is replaced by a fake, so no model is needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import rhymes  # noqa: E402
from playmate.pipeline import chat  # noqa: E402
from playmate.safety import filters  # noqa: E402
from playmate.services import llm  # noqa: E402


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.original = llm.ask_llm
        self.calls = []

        def fake(text, language="english"):
            self.calls.append(text)
            return "Hello little friend!"

        llm.ask_llm = fake

    def tearDown(self):
        llm.ask_llm = self.original

    def test_bad_word_skips_llm(self):
        result = chat.respond("you are stupid")
        self.assertEqual(result["source"], "safety_input")
        self.assertEqual(self.calls, [])

    def test_rhyme_skips_llm_and_is_exact(self):
        result = chat.respond("twinkle twinkle little star")
        self.assertTrue(result["source"].startswith("rhyme:"))
        self.assertEqual(result["reply"], rhymes.find_rhyme("twinkle twinkle")["text"])
        self.assertEqual(self.calls, [])

    def test_llm_reply_passes_through_safety(self):
        result = chat.respond("what is your name")
        self.assertEqual(result["source"], "llm")
        self.assertEqual(result["reply"], "Hello little friend!")

    def test_unsafe_llm_reply_is_replaced(self):
        llm.ask_llm = lambda text, language="english": "you are stupid"
        result = chat.respond("what is your name")
        self.assertEqual(result["reply"], filters.OUTPUT_FALLBACK["english"])

    def test_llm_down_gives_fallback(self):
        def broken(text, language="english"):
            raise llm.LLMError("down")

        llm.ask_llm = broken
        self.assertEqual(chat.respond("what is your name")["source"], "fallback")

    def test_empty_input(self):
        self.assertEqual(chat.respond("   ")["source"], "empty")

    def test_devanagari_means_hindi(self):
        self.assertEqual(chat.pick_language("नमस्ते"), "hindi")


if __name__ == "__main__":
    unittest.main(verbosity=2)
