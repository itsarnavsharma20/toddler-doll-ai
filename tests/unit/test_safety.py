"""Unit tests for safety filters. No network, no model needed.

Run all unit tests: python -m unittest discover -s tests/unit -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.safety import filters  # noqa: E402


class SafetyTests(unittest.TestCase):
    def test_blocks_bad_words(self):
        self.assertTrue(filters.contains_blocked("you are stupid"))
        self.assertTrue(filters.contains_blocked("You are STUUUPID!"))
        self.assertTrue(filters.contains_blocked("tu bewakoof hai"))
        self.assertTrue(filters.contains_blocked("shut up"))

    def test_allows_normal_words(self):
        self.assertFalse(filters.contains_blocked("Twinkle twinkle little star"))
        self.assertFalse(filters.contains_blocked("I like my teddy bear"))
        self.assertFalse(filters.contains_blocked("assistant"))

    def test_redirect_is_gentle(self):
        for language in ("english", "hindi"):
            message = filters.redirect_message(language).lower()
            self.assertNotIn("bad", message)
            self.assertNotIn("not good", message)

    def test_output_fallback(self):
        self.assertEqual(filters.clean_output("you are stupid", "english"), filters.OUTPUT_FALLBACK["english"])
        self.assertEqual(filters.clean_output("", "hindi"), filters.OUTPUT_FALLBACK["hindi"])

    def test_output_strips_links_and_limits_length(self):
        self.assertNotIn("http", filters.clean_output("Hello friend https://x.example/y", "english"))
        long_reply = "Hello there. " * 100
        self.assertLessEqual(len(filters.clean_output(long_reply, "english")), filters.MAX_REPLY_CHARS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
