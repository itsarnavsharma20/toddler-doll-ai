"""Unit tests for shared text helpers."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.core import text  # noqa: E402


class TextTests(unittest.TestCase):
    def test_normalize_keeps_devanagari_marks(self):
        self.assertEqual(text.normalize("मछली जल की रानी!"), "मछली जल की रानी")

    def test_normalize_drops_punctuation_and_repeats(self):
        self.assertEqual(text.normalize("Twinkle, twinkle!! Stuuupid"), "twinkle twinkle stupid")

    def test_leet_is_optional(self):
        self.assertEqual(text.normalize("st00pid", leet=True), "stoopid")
        self.assertEqual(text.normalize("a1"), "a1")

    def test_strip_symbols_removes_emoji(self):
        self.assertEqual(text.strip_symbols("Hello \U0001F60A friend!"), "Hello friend!")
        self.assertEqual(text.strip_symbols("नमस्ते \U0001F44B"), "नमस्ते")

    def test_strip_symbols_keeps_newlines(self):
        self.assertEqual(text.strip_symbols("line one\nline two"), "line one\nline two")


if __name__ == "__main__":
    unittest.main(verbosity=2)
