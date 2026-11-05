"""Unit tests for rhyme content and fuzzy lookup."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import rhymes  # noqa: E402
from playmate.safety import filters  # noqa: E402


class RhymeDataTests(unittest.TestCase):
    def test_ten_rhymes_with_required_fields(self):
        items = rhymes.load_rhymes()
        self.assertEqual(len(items), 10)
        for rhyme in items:
            for key in ("id", "language", "title", "triggers", "text"):
                self.assertIn(key, rhyme)

    def test_languages_come_from_folders(self):
        self.assertEqual({r["language"] for r in rhymes.load_rhymes()}, {"en", "hi"})

    def test_every_rhyme_is_safe(self):
        for rhyme in rhymes.load_rhymes():
            self.assertFalse(filters.contains_blocked(rhyme["text"]), rhyme["id"])


class RhymeMatchTests(unittest.TestCase):
    def test_exact_name(self):
        match = rhymes.find_rhyme("sing twinkle twinkle little star")
        self.assertEqual(match["id"], "twinkle_twinkle")
        self.assertEqual(match["mode"], "full")

    def test_typos_still_match(self):
        self.assertEqual(rhymes.find_rhyme("twinkel twinkel little star")["id"], "twinkle_twinkle")
        self.assertEqual(rhymes.find_rhyme("machli jal ki raani hai")["id"], "machli_jal_ki_rani")

    def test_devanagari_names(self):
        self.assertEqual(rhymes.find_rhyme("मछली जल की रानी है")["id"], "machli_jal_ki_rani")
        self.assertEqual(rhymes.find_rhyme("ट्विंकल ट्विंकल लिटिल स्टार")["id"], "twinkle_twinkle")
        self.assertEqual(rhymes.find_rhyme("चंदा मामा दूर के")["id"], "chanda_mama_door_ke")

    def test_roman_hindi_name(self):
        self.assertEqual(rhymes.find_rhyme("chanda mama door ke")["id"], "chanda_mama_door_ke")

    def test_continue_from_next_line(self):
        match = rhymes.find_rhyme("up above the world so high")
        self.assertEqual(match["id"], "twinkle_twinkle")
        self.assertEqual(match["mode"], "continue")
        self.assertTrue(match["text"].startswith("Like a diamond in the sky."))

    def test_continue_from_half_a_line(self):
        match = rhymes.find_rhyme("up above the world")
        self.assertEqual(match["mode"], "continue")
        self.assertTrue(match["text"].startswith("Like a diamond in the sky."))

    def test_generic_request_prefers_language(self):
        self.assertEqual(rhymes.find_rhyme("tell me a rhyme", "en")["language"], "en")
        self.assertEqual(rhymes.find_rhyme("एक गाना सुनाओ", "hi")["language"], "hi")

    def test_generic_step_can_be_skipped(self):
        self.assertIsNone(rhymes.find_rhyme("tell me a rhyme", "en", generic=False))
        self.assertIsNotNone(rhymes.find_rhyme("sing twinkle twinkle", "en", generic=False))

    def test_ordinary_chat_does_not_match(self):
        for sentence in ("what is your name", "i like my teddy", "how are you today", "hello", "star"):
            self.assertIsNone(rhymes.find_rhyme(sentence), sentence)

    def test_empty(self):
        self.assertIsNone(rhymes.find_rhyme(""))
        self.assertIsNone(rhymes.find_rhyme("!!!"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
