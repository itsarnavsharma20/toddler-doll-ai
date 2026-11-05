"""Unit tests for stories and basics content."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import library  # noqa: E402
from playmate.safety import filters  # noqa: E402


class LibraryTests(unittest.TestCase):
    def test_each_language_has_stories(self):
        for code in ("en", "hi"):
            items = library.stories(code)
            self.assertGreaterEqual(len(items), 2, code)
            for story in items:
                for key in ("id", "title", "text"):
                    self.assertTrue(story[key], "%s %s" % (code, key))

    def test_story_ids_are_unique(self):
        ids = [story["id"] for code in ("en", "hi") for story in library.stories(code)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_language_has_abc_and_numbers(self):
        for code in ("en", "hi"):
            self.assertEqual(set(library.basics(code)), {"abc", "numbers"})

    def test_hindi_content_is_devanagari(self):
        self.assertIn("अनार", library.basics("hi")["abc"]["text"])
        self.assertIn("एक, दो, तीन", library.basics("hi")["numbers"]["text"])

    def test_all_content_is_safe(self):
        for code in ("en", "hi"):
            texts = [s["text"] for s in library.stories(code)] + [b["text"] for b in library.basics(code).values()]
            for text in texts:
                self.assertFalse(filters.contains_blocked(text), "%s: %s" % (code, text[:40]))

    def test_pick_story_in_language(self):
        story = library.pick("story", "hi")
        self.assertIn(story["id"], {s["id"] for s in library.stories("hi")})

    def test_pick_basics(self):
        item = library.pick("abc", "en")
        self.assertEqual(item["id"], "abc")
        self.assertIn("A is for Apple", item["text"])

    def test_missing_language_falls_back_to_english(self):
        self.assertEqual(library.pick("numbers", "ta")["text"], library.basics("en")["numbers"]["text"])

    def test_unknown_intent_gives_none(self):
        self.assertIsNone(library.pick("dance", "en"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
