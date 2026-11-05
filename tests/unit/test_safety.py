"""Unit tests for safety filters. No network, no model needed.

Run all unit tests: python -m unittest discover -s tests/unit -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import messages  # noqa: E402
from playmate.safety import filters  # noqa: E402


class SafetyTests(unittest.TestCase):
    def test_blocks_english_bad_words(self):
        self.assertTrue(filters.contains_blocked("you are stupid"))
        self.assertTrue(filters.contains_blocked("You are STUUUPID!"))
        self.assertTrue(filters.contains_blocked("shut up"))

    def test_blocks_roman_hindi_bad_words(self):
        self.assertTrue(filters.contains_blocked("tu bewakoof hai"))

    def test_blocks_devanagari_bad_words(self):
        self.assertTrue(filters.contains_blocked("तुम बेवकूफ हो"))
        self.assertTrue(filters.contains_blocked("बंदूक"))

    def test_allows_normal_words(self):
        self.assertFalse(filters.contains_blocked("Twinkle twinkle little star"))
        self.assertFalse(filters.contains_blocked("I like my teddy bear"))
        self.assertFalse(filters.contains_blocked("assistant"))
        self.assertFalse(filters.contains_blocked("मछली जल की रानी है"))

    def test_animal_words_are_allowed(self):
        self.assertFalse(filters.contains_blocked("kutta"))
        self.assertFalse(filters.contains_blocked("कुत्ता"))

    def test_redirect_is_gentle(self):
        for language in ("en", "hi"):
            message = filters.redirect_message(language)
            self.assertEqual(message, messages.get(language, "redirect"))
        self.assertNotIn("not good", filters.redirect_message("en").lower())

    def test_output_fallback(self):
        self.assertEqual(filters.clean_output("you are stupid", "en"), messages.get("en", "output_fallback"))
        self.assertEqual(filters.clean_output("", "hi"), messages.get("hi", "output_fallback"))
        self.assertEqual(filters.clean_output("तुम बेवकूफ हो", "hi"), messages.get("hi", "output_fallback"))

    def test_output_strips_links_and_emoji(self):
        self.assertNotIn("http", filters.clean_output("Hello friend https://x.example/y", "en"))
        self.assertEqual(filters.clean_output("Hello \U0001F60A friend!", "en"), "Hello friend!")

    def test_output_limits_length(self):
        long_reply = "Hello there. " * 100
        self.assertLessEqual(len(filters.clean_output(long_reply, "en")), filters.MAX_REPLY_CHARS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
