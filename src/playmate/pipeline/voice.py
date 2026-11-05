"""Voice pipeline: speech to text, chat pipeline, text to speech. Audio is never stored."""
import asyncio
import base64

from playmate.content import messages
from playmate.core import config, languages, metrics
from playmate.pipeline import chat
from playmate.services import stt, tts


async def handle(audio_bytes, language=None):
    """Return {"transcript", "reply", "language", "source", "audio_base64", "audio_format"}.

    audio_base64 is None if text to speech failed. The reply text is still returned.
    """
    heard = None
    if audio_bytes:
        try:
            heard = await asyncio.to_thread(stt.transcribe, audio_bytes, language)
        except stt.STTError:
            heard = None

    if heard is None or not heard["confident"]:
        code = heard["language"] if heard else languages.detect("", language)
        result = {"reply": messages.get(code, "not_heard"), "language": code, "source": "low_confidence"}
        metrics.record("low_confidence")
        transcript = ""
    else:
        result = await asyncio.to_thread(chat.respond, heard["text"], heard["language"])
        transcript = heard["text"]

    try:
        audio = base64.b64encode(await tts.synthesize(result["reply"], result["language"])).decode("ascii")
    except tts.TTSError:
        audio = None
    return {
        "transcript": transcript,
        **result,
        "audio_base64": audio,
        "audio_format": config.load_settings()["tts"]["audio_format"],
    }
