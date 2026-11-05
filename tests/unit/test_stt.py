"""Unit tests for speech to text logic. The Whisper model is replaced by a fake."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.services import stt  # noqa: E402


def segment(text, logprob=-0.3, no_speech=0.05):
    return SimpleNamespace(text=text, avg_logprob=logprob, no_speech_prob=no_speech)


class FakeModel:
    """Returns planned results and records the options it was called with."""

    def __init__(self, plan):
        self.plan = list(plan)
        self.calls = []

    @property
    def asked(self):
        return [call.get("language") for call in self.calls]

    def transcribe(self, audio, **options):
        self.calls.append(options)
        segments, detected = self.plan.pop(0)
        language = options.get("language")
        return segments, SimpleNamespace(language=language or detected, language_probability=0.9)


class SttTests(unittest.TestCase):
    def setUp(self):
        self.original = stt._get_model
        stt.OVERRIDES.clear()

    def tearDown(self):
        stt._get_model = self.original
        stt.OVERRIDES.clear()

    def use(self, model):
        stt._get_model = lambda: model

    def test_confident_result(self):
        self.use(FakeModel([([segment("hello there")], "en")]))
        heard = stt.transcribe(b"audio")
        self.assertEqual(heard["text"], "hello there")
        self.assertEqual(heard["language"], "en")
        self.assertTrue(heard["confident"])
        self.assertAlmostEqual(heard["avg_logprob"], -0.3)
        self.assertAlmostEqual(heard["no_speech_prob"], 0.05)

    def test_requested_language_is_passed_to_model(self):
        model = FakeModel([([segment("नमस्ते")], "hi")])
        self.use(model)
        heard = stt.transcribe(b"audio", "hindi")
        self.assertEqual(model.asked, ["hi"])
        self.assertEqual(heard["language"], "hi")

    def test_known_language_gets_hotwords_and_initial_prompt(self):
        model = FakeModel([([segment("नमस्ते")], "hi")])
        self.use(model)
        stt.transcribe(b"audio", "hi")
        options = model.calls[0]
        self.assertIn("किको", options["hotwords"])
        self.assertIn("कहानी", options["initial_prompt"])

    def test_auto_detect_gets_hotwords_but_no_initial_prompt(self):
        model = FakeModel([([segment("hello")], "en")])
        self.use(model)
        stt.transcribe(b"audio")
        options = model.calls[0]
        self.assertIsNone(options["language"])
        self.assertIn("Kiko", options["hotwords"])
        self.assertIn("कहानी", options["hotwords"])
        self.assertNotIn("initial_prompt", options)

    def test_single_pass_settings(self):
        model = FakeModel([([segment("hello")], "en")])
        self.use(model)
        stt.transcribe(b"audio", "en")
        options = model.calls[0]
        self.assertEqual(options["temperature"], 0.0)
        self.assertFalse(options["condition_on_previous_text"])
        self.assertEqual(options["beam_size"], 5)

    def test_override_changes_beam(self):
        stt.OVERRIDES["beam_size"] = 1
        model = FakeModel([([segment("hello")], "en")])
        self.use(model)
        stt.transcribe(b"audio", "en")
        self.assertEqual(model.calls[0]["beam_size"], 1)

    def test_low_logprob_is_not_confident(self):
        self.use(FakeModel([([segment("mumble", logprob=-2.0)], "en")]))
        self.assertFalse(stt.transcribe(b"audio")["confident"])

    def test_high_no_speech_is_not_confident(self):
        self.use(FakeModel([([segment("noise", no_speech=0.9)], "en")]))
        self.assertFalse(stt.transcribe(b"audio")["confident"])

    def test_no_segments(self):
        self.use(FakeModel([([], "en")]))
        heard = stt.transcribe(b"audio")
        self.assertEqual(heard["text"], "")
        self.assertFalse(heard["confident"])

    def test_disabled_detected_language_is_transcribed_again_in_default(self):
        model = FakeModel([([segment("vanakkam")], "ta"), ([segment("hello")], "en")])
        self.use(model)
        heard = stt.transcribe(b"audio")
        self.assertEqual(model.asked, [None, "en"])
        self.assertEqual(heard["language"], "en")
        self.assertEqual(heard["text"], "hello")

    def load_with(self, fail_local):
        calls = []

        class FakeWhisper:
            def __init__(self, name, **options):
                calls.append(options["local_files_only"])
                if options["local_files_only"] and fail_local:
                    raise RuntimeError("not on disk")

        stt._models.clear()
        try:
            with patch.dict(sys.modules, {"faster_whisper": SimpleNamespace(WhisperModel=FakeWhisper)}):
                self.original()
                self.original()  # second call must reuse the loaded model
        finally:
            stt._models.clear()
        return calls

    def test_model_on_disk_never_goes_online(self):
        self.assertEqual(self.load_with(fail_local=False), [True])

    def test_model_not_on_disk_is_downloaded(self):
        self.assertEqual(self.load_with(fail_local=True), [True, False])

    def test_model_error_becomes_stt_error(self):
        class Broken:
            def transcribe(self, *args, **kwargs):
                raise RuntimeError("boom")

        self.use(Broken())
        with self.assertRaises(stt.STTError):
            stt.transcribe(b"audio")


if __name__ == "__main__":
    unittest.main(verbosity=2)
