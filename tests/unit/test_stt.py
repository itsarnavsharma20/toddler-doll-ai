"""Unit tests for speech to text logic. The Whisper model is replaced by a fake."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.services import stt  # noqa: E402


def segment(text, logprob=-0.3, no_speech=0.05):
    return SimpleNamespace(text=text, avg_logprob=logprob, no_speech_prob=no_speech)


class FakeModel:
    """Returns planned results and records which language it was asked for."""

    def __init__(self, plan):
        self.plan = list(plan)
        self.asked = []

    def transcribe(self, audio, language=None, beam_size=1, vad_filter=True):
        self.asked.append(language)
        segments, detected = self.plan.pop(0)
        return segments, SimpleNamespace(language=language or detected, language_probability=0.9)


class SttTests(unittest.TestCase):
    def setUp(self):
        self.original = stt._get_model

    def tearDown(self):
        stt._get_model = self.original

    def use(self, model):
        stt._get_model = lambda: model

    def test_confident_result(self):
        self.use(FakeModel([([segment("hello there")], "en")]))
        heard = stt.transcribe(b"audio")
        self.assertEqual(heard["text"], "hello there")
        self.assertEqual(heard["language"], "en")
        self.assertTrue(heard["confident"])

    def test_requested_language_is_passed_to_model(self):
        model = FakeModel([([segment("नमस्ते")], "hi")])
        self.use(model)
        heard = stt.transcribe(b"audio", "hindi")
        self.assertEqual(model.asked, ["hi"])
        self.assertEqual(heard["language"], "hi")

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

    def test_model_error_becomes_stt_error(self):
        class Broken:
            def transcribe(self, *args, **kwargs):
                raise RuntimeError("boom")

        self.use(Broken())
        with self.assertRaises(stt.STTError):
            stt.transcribe(b"audio")


if __name__ == "__main__":
    unittest.main(verbosity=2)
