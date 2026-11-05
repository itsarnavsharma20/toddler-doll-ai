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

    def test_greeting_and_name_are_dropped(self):
        result = chat.respond("Hey Kiko, twinkle twinkle little star")
        self.assertEqual(result["source"], "rhyme:twinkle_twinkle")
        chat.respond("Hi Kiko, what is your name")
        self.assertEqual(self.calls[-1][0], "what is your name")

    def test_hindi_request_with_name(self):
        result = chat.respond("Kiko tumhara naam kya hai")
        self.assertEqual(result["language"], "hi")
        self.assertEqual(self.calls[-1], ("tumhara naam kya hai", "hi"))

    def test_roman_hindi_story_request_plays_a_hindi_story(self):
        result = chat.respond("Kiko mujhe kahani sunao")
        self.assertEqual(result["language"], "hi")
        self.assertTrue(result["source"].startswith("story:"))
        self.assertEqual(self.calls, [])

    def test_name_alone_still_gets_a_reply(self):
        result = chat.respond("Hey Kiko")
        self.assertEqual(result["source"], "llm")
        self.assertEqual(self.calls[-1][0], "Hey Kiko")

    def test_story_request_plays_a_story_without_llm(self):
        result = chat.respond("Hi Kiko, can you tell me a story please?")
        self.assertTrue(result["source"].startswith("story:"))
        self.assertEqual(self.calls, [])

    def test_hindi_story_request_with_speech_to_text_spelling(self):
        result = chat.respond("की को मुझे कानियो सुननी है")
        self.assertEqual(result["language"], "hi")
        self.assertIn(result["source"], {"story:chhota_tara", "story:nanhi_chidiya"})
        self.assertEqual(self.calls, [])

    def test_abc_and_numbers(self):
        self.assertEqual(chat.respond("Hey Kiko, can we learn ABCD?")["source"], "basics:abc")
        self.assertEqual(chat.respond("let us count")["source"], "basics:numbers")
        self.assertEqual(chat.respond("गिनती सुनाओ")["source"], "basics:numbers")
        self.assertEqual(self.calls, [])

    def test_abc_song_is_abc_not_a_random_rhyme(self):
        self.assertEqual(chat.respond("sing the abc song")["source"], "basics:abc")

    def test_general_rhyme_request_still_works(self):
        self.assertTrue(chat.respond("tell me a rhyme")["source"].startswith("rhyme:"))
        self.assertTrue(chat.respond("sing a song")["source"].startswith("rhyme:"))

    def test_named_rhyme_beats_story_word(self):
        self.assertEqual(chat.respond("story of twinkle twinkle little star")["source"], "rhyme:twinkle_twinkle")

    def test_continue_source(self):
        result = chat.respond("up above the world so high")
        self.assertEqual(result["source"], "rhyme:twinkle_twinkle:continue")

    def test_llm_reply_passes_through_safety(self):
        result = chat.respond("what is your name")
        self.assertEqual(result["source"], "llm")
        self.assertEqual(result["reply"], "Hello little friend!")
        self.assertEqual(self.calls, [("what is your name", "en")])

    def test_roman_hindi_goes_to_llm_as_hindi(self):
        result = chat.respond("tumhara naam kya hai")
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
