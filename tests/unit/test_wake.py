"""Unit tests for speech hints and for dropping a greeting plus the toy's name."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.content import hints  # noqa: E402
from playmate.pipeline import wake  # noqa: E402


class HintsTests(unittest.TestCase):
    def test_hotwords_per_language_and_merged(self):
        self.assertEqual(hints.hotwords("en"), "Kiko")
        self.assertIn("किको", hints.hotwords("hi"))
        merged = hints.hotwords()
        self.assertIn("Kiko", merged)
        self.assertIn("कहानी", merged)

    def test_initial_prompt(self):
        self.assertIn("rhyme", hints.initial_prompt("en"))
        self.assertIn("कहानी", hints.initial_prompt("hi"))
        self.assertEqual(hints.initial_prompt("ta"), "")

    def test_name_variants_longest_first(self):
        variants = hints.name_variants()
        self.assertIn(("kiko",), variants)
        self.assertIn(("की", "को"), variants)
        self.assertEqual(len(variants[0]), 2)

    def test_greetings(self):
        self.assertTrue({"hey", "hi", "नमस्ते"} <= hints.greetings())


class WakeTests(unittest.TestCase):
    def test_greeting_and_name(self):
        self.assertEqual(wake.strip_name("Hey Kiko, can we learn ABCD?"), "can we learn ABCD?")
        self.assertEqual(wake.strip_name("Hi Kiko, can you tell me a story please?"),
                         "can you tell me a story please?")

    def test_name_only(self):
        self.assertEqual(wake.strip_name("Kiko mujhe kahani sunao"), "mujhe kahani sunao")
        self.assertEqual(wake.strip_name("kiku, sing a rhyme"), "sing a rhyme")

    def test_devanagari_name(self):
        self.assertEqual(wake.strip_name("किको मुझे कहानी सुनाओ"), "मुझे कहानी सुनाओ")
        self.assertEqual(wake.strip_name("हे किको, गाना सुनाओ"), "गाना सुनाओ")

    def test_misheard_name_in_two_words(self):
        self.assertEqual(wake.strip_name("की को मुझे गानियो सुनती है"), "मुझे गानियो सुनती है")

    def test_name_alone_is_kept(self):
        self.assertEqual(wake.strip_name("Hey Kiko"), "Hey Kiko")
        self.assertEqual(wake.strip_name("Kiko!"), "Kiko!")

    def test_no_name_no_change(self):
        for text in ("hello there", "what is your name", "sing twinkle twinkle", ""):
            self.assertEqual(wake.strip_name(text), text)

    def test_name_in_the_middle_is_kept(self):
        self.assertEqual(wake.strip_name("I love Kiko very much"), "I love Kiko very much")

    def test_greeting_alone_is_kept(self):
        self.assertEqual(wake.strip_name("hello friend"), "hello friend")


if __name__ == "__main__":
    unittest.main(verbosity=2)
