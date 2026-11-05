"""Unit tests for the voice pipeline and route. STT, TTS and the LLM are replaced by fakes."""
import asyncio
import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fastapi import HTTPException  # noqa: E402

from playmate.api import main  # noqa: E402
from playmate.content import messages  # noqa: E402
from playmate.pipeline import voice  # noqa: E402
from playmate.services import llm, stt, tts  # noqa: E402


class FakeRequest:
    def __init__(self, data):
        self.data = data

    async def body(self):
        return self.data


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.originals = (stt.transcribe, tts.synthesize, llm.ask_llm)
        self.llm_calls = []
        self.heard = {"text": "twinkle twinkle little star", "language": "en", "confident": True}

        def fake_stt(audio, language=None):
            if isinstance(self.heard, Exception):
                raise self.heard
            return self.heard

        async def fake_tts(text, language):
            return b"fake-mp3"

        def fake_llm(text, language="en"):
            self.llm_calls.append(text)
            return "Hello little friend!"

        stt.transcribe, tts.synthesize, llm.ask_llm = fake_stt, fake_tts, fake_llm

    def tearDown(self):
        stt.transcribe, tts.synthesize, llm.ask_llm = self.originals

    def run_voice(self, audio=b"audio", language=None):
        return asyncio.run(voice.handle(audio, language))

    def test_rhyme_by_voice(self):
        result = self.run_voice()
        self.assertEqual(result["source"], "rhyme:twinkle_twinkle")
        self.assertEqual(result["transcript"], "twinkle twinkle little star")
        self.assertEqual(base64.b64decode(result["audio_base64"]), b"fake-mp3")
        self.assertEqual(result["audio_format"], "mp3")
        self.assertEqual(self.llm_calls, [])

    def test_timings_are_reported(self):
        timings = self.run_voice()["timings"]
        self.assertEqual(set(timings), {"stt_s", "chat_s", "tts_s", "total_s"})
        self.assertTrue(all(value >= 0 for value in timings.values()))
        self.assertGreaterEqual(timings["total_s"], timings["stt_s"] + timings["chat_s"] + timings["tts_s"] - 0.01)

    def test_llm_chat_by_voice(self):
        self.heard = {"text": "what is your name", "language": "en", "confident": True}
        result = self.run_voice()
        self.assertEqual(result["source"], "llm")
        self.assertEqual(result["reply"], "Hello little friend!")

    def test_low_confidence_asks_again_and_skips_llm(self):
        self.heard = {"text": "mumble", "language": "hi", "confident": False}
        result = self.run_voice()
        self.assertEqual(result["source"], "low_confidence")
        self.assertEqual(result["reply"], messages.get("hi", "not_heard"))
        self.assertEqual(result["transcript"], "")
        self.assertEqual(self.llm_calls, [])

    def test_stt_failure_asks_again(self):
        self.heard = stt.STTError("boom")
        self.assertEqual(self.run_voice()["source"], "low_confidence")

    def test_empty_audio_asks_again(self):
        self.assertEqual(self.run_voice(audio=b"")["source"], "low_confidence")

    def test_bad_word_by_voice_is_redirected(self):
        self.heard = {"text": "you are stupid", "language": "en", "confident": True}
        result = self.run_voice()
        self.assertEqual(result["source"], "safety_input")
        self.assertEqual(self.llm_calls, [])

    def test_tts_failure_still_returns_text(self):
        async def broken(text, language):
            raise tts.TTSError("offline")

        tts.synthesize = broken
        result = self.run_voice()
        self.assertIsNone(result["audio_base64"])
        self.assertEqual(result["tts_error"], "offline")
        self.assertTrue(result["reply"])

    def test_route_rejects_large_audio(self):
        limit = main.config.load_settings()["voice"]["max_audio_bytes"]
        with self.assertRaises(HTTPException) as caught:
            asyncio.run(main.voice(FakeRequest(b"x" * (limit + 1))))
        self.assertEqual(caught.exception.status_code, 413)

    def test_route_returns_result(self):
        result = asyncio.run(main.voice(FakeRequest(b"audio"), "en"))
        self.assertEqual(result["source"], "rhyme:twinkle_twinkle")

    def test_voice_route_exists(self):
        self.assertIn("/v1/voice", {route.path for route in main.app.routes})


if __name__ == "__main__":
    unittest.main(verbosity=2)
