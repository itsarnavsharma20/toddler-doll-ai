"""Voice pipeline: speech to text, chat pipeline, text to speech. Audio is never stored."""
import asyncio
import base64
import time

from playmate.content import messages
from playmate.core import config, languages, metrics
from playmate.pipeline import chat
from playmate.services import stt, tts


async def handle(audio_bytes, language=None):
    """Return {"transcript", "reply", "language", "source", "audio_base64", "tts_error", "audio_format", "timings"}.

    audio_base64 is None and tts_error says why if text to speech failed. The reply text is still returned.
    timings holds seconds spent in each stage: stt_s, chat_s, tts_s, total_s.
    """
    started = time.perf_counter()
    heard = None
    if audio_bytes:
        try:
            heard = await asyncio.to_thread(stt.transcribe, audio_bytes, language)
        except stt.STTError:
            heard = None
    stt_done = time.perf_counter()

    if heard is None or not heard["confident"]:
        code = heard["language"] if heard else languages.detect("", language)
        result = {"reply": messages.get(code, "not_heard"), "language": code, "source": "low_confidence"}
        metrics.record("low_confidence")
        transcript = ""
    else:
        result = await asyncio.to_thread(chat.respond, heard["text"], heard["language"])
        transcript = heard["text"]
    chat_done = time.perf_counter()

    tts_error = None
    try:
        audio = base64.b64encode(await tts.synthesize(result["reply"], result["language"])).decode("ascii")
    except tts.TTSError as exc:
        audio, tts_error = None, str(exc)
    finished = time.perf_counter()
    return {
        "transcript": transcript,
        **result,
        "audio_base64": audio,
        "tts_error": tts_error,
        "audio_format": config.load_settings()["tts"]["audio_format"],
        "timings": {
            "stt_s": stt_done - started,
            "chat_s": chat_done - stt_done,
            "tts_s": finished - chat_done,
            "total_s": finished - started,
        },
    }
