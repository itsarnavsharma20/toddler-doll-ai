"""Unit tests for rhyme content and lookup."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import rhymes  # noqa: E402
from playmate.safety import filters  # noqa: E402


class RhymeTests(unittest.TestCase):
    def test_ten_rhymes_with_required_fields(self):
        items = rhymes.load_rhymes()
        self.assertEqual(len(items), 10)
        for rhyme in items:
            for key in ("id", "language", "title", "triggers", "text"):
                self.assertIn(key, rhyme)

    def test_every_rhyme_is_safe(self):
        for rhyme in rhymes.load_rhymes():
            self.assertFalse(filters.contains_blocked(rhyme["text"]), rhyme["id"])

    def test_find_named_rhyme(self):
        self.assertEqual(rhymes.find_rhyme("sing twinkle twinkle little star")["id"], "twinkle_twinkle")
        self.assertEqual(rhymes.find_rhyme("machli jal ki rani hai", "hindi")["id"], "machli_jal_ki_rani")

    def test_generic_request_and_unknown(self):
        self.assertIsNotNone(rhymes.find_rhyme("tell me a rhyme", "english"))
        self.assertIsNone(rhymes.find_rhyme("what is your name"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
