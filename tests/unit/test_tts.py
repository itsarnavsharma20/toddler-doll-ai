"""Unit tests for text to speech. The speech provider is replaced by a fake, so no internet is needed."""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.core import config  # noqa: E402
from playmate.services import tts  # noqa: E402


class FlakyProvider:
    """Fails the first `failures` times, then returns audio."""

    failures = 0
    calls = 0
    voices = []
    styles = []

    def __init__(self):
        pass

    async def synthesize(self, text, voice, rate, pitch):
        FlakyProvider.calls += 1
        FlakyProvider.voices.append(voice)
        FlakyProvider.styles.append((rate, pitch))
        if FlakyProvider.calls <= FlakyProvider.failures:
            raise OSError("[WinError 64] The specified network name is no longer available")
        return b"mp3-bytes"


class TtsTests(unittest.TestCase):
    def setUp(self):
        self.original_providers = dict(tts.PROVIDERS)
        self.original_delay = tts.RETRY_DELAY_SECONDS
        tts.PROVIDERS["edge"] = FlakyProvider
        tts.RETRY_DELAY_SECONDS = 0
        FlakyProvider.failures, FlakyProvider.calls = 0, 0
        FlakyProvider.voices, FlakyProvider.styles = [], []
        self.original_load = config.load_settings

    def tearDown(self):
        tts.PROVIDERS.clear()
        tts.PROVIDERS.update(self.original_providers)
        tts.RETRY_DELAY_SECONDS = self.original_delay
        config.load_settings = self.original_load

    def speak(self, language="en"):
        return asyncio.run(tts.synthesize("hello", language))

    def test_works_first_time(self):
        self.assertEqual(self.speak(), b"mp3-bytes")
        self.assertEqual(FlakyProvider.calls, 1)

    def test_dropped_connection_is_retried(self):
        FlakyProvider.failures = 2
        self.assertEqual(self.speak(), b"mp3-bytes")
        self.assertEqual(FlakyProvider.calls, 3)

    def test_gives_up_after_retries_with_the_reason(self):
        FlakyProvider.failures = 99
        with self.assertRaises(tts.TTSError) as caught:
            self.speak()
        self.assertEqual(FlakyProvider.calls, 3)
        self.assertIn("network name", str(caught.exception))

    def test_kiko_speaks_with_a_male_voice(self):
        self.speak("hi")
        self.speak("en")
        self.assertEqual(FlakyProvider.voices, ["hi-IN-MadhurNeural", "en-IN-PrabhatNeural"])

    def test_voice_follows_toy_gender(self):
        base = self.original_load()
        config.load_settings = lambda: dict(base, toy_gender="female")
        self.speak("hi")
        self.speak("en")
        self.assertEqual(FlakyProvider.voices, ["hi-IN-SwaraNeural", "en-IN-NeerjaNeural"])

    def test_rate_and_pitch_come_from_settings(self):
        base = self.original_load()
        config.load_settings = lambda: dict(base, tts=dict(base["tts"], rate="-10%", pitch="+20Hz"))
        self.speak()
        self.assertEqual(FlakyProvider.styles, [("-10%", "+20Hz")])

    def test_language_without_a_voice_is_an_error(self):
        with self.assertRaises(tts.TTSError):
            self.speak("fr")
        self.assertEqual(FlakyProvider.calls, 0)

    def test_unknown_provider_is_an_error(self):
        tts.PROVIDERS.clear()
        with self.assertRaises(tts.TTSError):
            self.speak()


if __name__ == "__main__":
    unittest.main(verbosity=2)
