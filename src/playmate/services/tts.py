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
    async def synthesize(self, text, voice):
        import edge_tts

        chunks = []
        async for chunk in edge_tts.Communicate(text, voice).stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        audio = b"".join(chunks)
        if not audio:
            raise TTSError("no audio returned")
        return audio


PROVIDERS = {"edge": EdgeProvider}


async def synthesize(text, language):
    """Return audio bytes (mp3) for the text, in the voice set for the language."""
    settings = config.load_settings()["tts"]
    provider_class = PROVIDERS.get(settings["provider"])
    voice = languages.tts_voice(language)
    if provider_class is None:
        raise TTSError("unknown TTS provider: %s" % settings["provider"])
    if not voice:
        raise TTSError("no voice set for language: %s" % language)
    try:
        return await asyncio.wait_for(provider_class().synthesize(text, voice), settings["timeout_seconds"])
    except TTSError:
        raise
    except Exception as exc:
        raise TTSError(str(exc) or exc.__class__.__name__) from exc
