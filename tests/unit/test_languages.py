"""Unit tests for the language registry and language detection."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.core import languages  # noqa: E402


class LanguageTests(unittest.TestCase):
    def test_enabled_languages(self):
        self.assertEqual(sorted(languages.enabled_codes()), ["en", "hi"])

    def test_resolve_code_and_name(self):
        self.assertEqual(languages.resolve("hi"), "hi")
        self.assertEqual(languages.resolve("Hindi"), "hi")
        self.assertEqual(languages.resolve("english"), "en")
        self.assertIsNone(languages.resolve("klingon"))
        self.assertIsNone(languages.resolve(None))

    def test_detect_requested(self):
        self.assertEqual(languages.detect("hello", "hindi"), "hi")
        self.assertEqual(languages.detect("namaste", "en"), "en")

    def test_detect_disabled_request_falls_back(self):
        self.assertEqual(languages.detect("hello", "ta"), "en")

    def test_detect_devanagari(self):
        self.assertEqual(languages.detect("नमस्ते"), "hi")

    def test_detect_roman_hindi_hints(self):
        self.assertEqual(languages.detect("mujhe kahani sunao"), "hi")
        self.assertEqual(languages.detect("tumhara naam kya hai"), "hi")

    def test_detect_default_english(self):
        self.assertEqual(languages.detect("what is your name"), "en")

    def test_prompt_name_forces_devanagari_for_hindi(self):
        self.assertIn("Devanagari", languages.prompt_name("hi"))

    def test_speech_helpers(self):
        self.assertEqual(languages.tts_voice("hi"), "hi-IN-SwaraNeural")
        self.assertEqual(languages.tts_voice("en"), "en-US-AriaNeural")
        self.assertEqual(languages.stt_code("hi"), "hi")
        self.assertEqual(languages.code_from_stt("hi"), "hi")
        self.assertIsNone(languages.code_from_stt("ta"))

    def test_describe_lists_all(self):
        codes = {item["code"] for item in languages.describe()}
        self.assertTrue({"en", "hi", "ta", "te", "fr", "es"} <= codes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
