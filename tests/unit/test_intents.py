"""Unit tests for request detection (story, abc, numbers) that forgives small spelling slips."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import intents  # noqa: E402


class IntentTests(unittest.TestCase):
    def test_story_in_english(self):
        self.assertEqual(intents.detect("can you tell me a story please"), "story")
        self.assertEqual(intents.detect("tell me stories"), "story")

    def test_story_in_hindi(self):
        self.assertEqual(intents.detect("मुझे कहानी सुनाओ"), "story")
        self.assertEqual(intents.detect("mujhe kahani sunao"), "story")

    def test_story_spellings_speech_to_text_produced(self):
        self.assertEqual(intents.detect("मुझे कानियो सुननी है"), "story")
        self.assertEqual(intents.detect("मुझे कानी हो सुननी है"), "story")

    def test_small_typos_are_forgiven(self):
        self.assertEqual(intents.detect("tell me a stoory"), "story")
        self.assertEqual(intents.detect("let us learn the alphabat"), "abc")

    def test_abc(self):
        self.assertEqual(intents.detect("can we learn ABCD"), "abc")
        self.assertEqual(intents.detect("एबीसीडी सिखाओ"), "abc")
        self.assertEqual(intents.detect("वर्णमाला सुनाओ"), "abc")

    def test_numbers(self):
        self.assertEqual(intents.detect("let us count"), "numbers")
        self.assertEqual(intents.detect("गिनती सुनाओ"), "numbers")
        self.assertEqual(intents.detect("ginti sikhao"), "numbers")
        self.assertEqual(intents.detect("one two three"), "numbers")

    def test_ordinary_chat_is_not_an_intent(self):
        for sentence in ("what is your name", "hello", "i like my teddy", "how are you", "तुम कैसे हो", "this is great"):
            self.assertIsNone(intents.detect(sentence), sentence)

    def test_short_words_need_an_exact_match(self):
        self.assertIsNone(intents.detect("abe"))
        self.assertIsNone(intents.detect("a b"))

    def test_empty(self):
        self.assertIsNone(intents.detect(""))
        self.assertIsNone(intents.detect("!!!"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
