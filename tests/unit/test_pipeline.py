"""Unit tests for the chat pipeline. The LLM is replaced by a fake, so no model is needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import messages, rhymes  # noqa: E402
from playmate.pipeline import chat  # noqa: E402
from playmate.safety import filters  # noqa: E402
from playmate.services import llm  # noqa: E402


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.original = llm.ask_llm
        self.calls = []

        def fake(text, language="en"):
            self.calls.append((text, language))
            return "Hello little friend!"

        llm.ask_llm = fake

    def tearDown(self):
        llm.ask_llm = self.original

    def test_bad_word_skips_llm(self):
        result = chat.respond("you are stupid")
        self.assertEqual(result["source"], "safety_input")
        self.assertEqual(self.calls, [])

    def test_devanagari_bad_word_skips_llm(self):
        result = chat.respond("तुम बेवकूफ हो")
        self.assertEqual(result["source"], "safety_input")
        self.assertEqual(result["language"], "hi")
        self.assertEqual(self.calls, [])

    def test_rhyme_skips_llm_and_is_exact(self):
        result = chat.respond("twinkle twinkle little star")
        self.assertEqual(result["source"], "rhyme:twinkle_twinkle")
        self.assertEqual(result["reply"], rhymes.find_rhyme("twinkle twinkle")["text"])
        self.assertEqual(self.calls, [])

    def test_continue_source(self):
        result = chat.respond("up above the world so high")
        self.assertEqual(result["source"], "rhyme:twinkle_twinkle:continue")

    def test_llm_reply_passes_through_safety(self):
        result = chat.respond("what is your name")
        self.assertEqual(result["source"], "llm")
        self.assertEqual(result["reply"], "Hello little friend!")
        self.assertEqual(self.calls, [("what is your name", "en")])

    def test_roman_hindi_goes_to_llm_as_hindi(self):
        result = chat.respond("mujhe kahani sunao")
        self.assertEqual(result["language"], "hi")
        self.assertEqual(self.calls[-1][1], "hi")

    def test_unsafe_llm_reply_is_replaced(self):
        llm.ask_llm = lambda text, language="en": "you are stupid"
        result = chat.respond("what is your name")
        self.assertEqual(result["reply"], messages.get("en", "output_fallback"))

    def test_emoji_in_llm_reply_is_removed(self):
        llm.ask_llm = lambda text, language="en": "Namaste! \U0001F60A Let us play!"
        self.assertEqual(chat.respond("what is your name")["reply"], "Namaste! Let us play!")

    def test_llm_down_gives_fallback(self):
        def broken(text, language="en"):
            raise llm.LLMError("down")

        llm.ask_llm = broken
        result = chat.respond("what is your name")
        self.assertEqual(result["source"], "fallback")
        self.assertEqual(result["reply"], messages.get("en", "llm_down"))

    def test_empty_input(self):
        self.assertEqual(chat.respond("   ")["source"], "empty")

    def test_requested_language_is_used(self):
        self.assertEqual(chat.respond("hello", "hindi")["language"], "hi")


if __name__ == "__main__":
    unittest.main(verbosity=2)
