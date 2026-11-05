"""Text to speech with a small provider interface.

The edge provider is for prototyping only: it uses an unofficial Microsoft service, needs the
internet, and sends the toy's reply text (never the child's audio) to Microsoft. For production
replace it with an offline provider such as Piper. See docs/adr/0004-voice-stack.md.
"""
import asyncio

from playmate.core import config, languages


class TTSError(Exception):
    """Text to speech failed."""


class EdgeProvider:
    async def synthesize(self, text, voice, rate="+0%", pitch="+0Hz"):
        import edge_tts

        chunks = []
        async for chunk in edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        audio = b"".join(chunks)
        if not audio:
            raise TTSError("no audio returned")
        return audio


PROVIDERS = {"edge": EdgeProvider}
RETRY_DELAY_SECONDS = 0.5


async def synthesize(text, language):
    """Return audio bytes (mp3) for the text, in the voice set for the language.

    A failed attempt (for example a dropped connection) is tried again settings["retries"] times.
    """
    settings = config.load_settings()["tts"]
    provider_class = PROVIDERS.get(settings["provider"])
    voice = languages.tts_voice(language)
    if provider_class is None:
        raise TTSError("unknown TTS provider: %s" % settings["provider"])
    if not voice:
        raise TTSError("no voice set for language: %s" % language)
    provider = provider_class()
    rate, pitch = settings.get("rate", "+0%"), settings.get("pitch", "+0Hz")
    attempts = 1 + settings.get("retries", 2)
    for attempt in range(attempts):
        try:
            return await asyncio.wait_for(provider.synthesize(text, voice, rate, pitch), settings["timeout_seconds"])
        except Exception as exc:
            error = exc if isinstance(exc, TTSError) else TTSError(str(exc) or exc.__class__.__name__)
            if attempt == attempts - 1:
                raise error from exc
            await asyncio.sleep(RETRY_DELAY_SECONDS)
