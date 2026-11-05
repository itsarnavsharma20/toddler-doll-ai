"""Speech to text. faster-whisper, local, CPU. Audio stays in memory and is never written to disk."""
import io
import os
import threading

from playmate.core import config, languages

# Keep every download (model files and the Hugging Face cache) inside the project folder.
os.environ.setdefault("HF_HOME", str(config.ROOT / "models" / "hf"))


class STTError(Exception):
    """Speech to text failed."""


_model = None
_lock = threading.Lock()


def _get_model():
    """Load the model once. The first call downloads it into the project models folder."""
    global _model
    with _lock:
        if _model is None:
            from faster_whisper import WhisperModel

            s = config.load_settings()["stt"]
            _model = WhisperModel(
                s["model"],
                device=s["device"],
                compute_type=s["compute_type"],
                download_root=str(config.ROOT / s["download_dir"]),
            )
        return _model


def _run(model, audio_bytes, stt_language, settings):
    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),
        language=stt_language,
        beam_size=settings["beam_size"],
        vad_filter=settings["vad_filter"],
    )
    return list(segments), info


def transcribe(audio_bytes, language=None):
    """Return {"text", "language", "confident", "avg_logprob"}. language is one of our codes.

    If no language is given, the model detects it. A language that is not enabled is
    replaced by the default language and the audio is transcribed again.
    """
    settings = config.load_settings()["stt"]
    try:
        model = _get_model()
        code = languages.resolve(language)
        code = code if code and languages.is_enabled(code) else None
        segments, info = _run(model, audio_bytes, languages.stt_code(code) if code else None, settings)
        if code is None:
            code = languages.code_from_stt(info.language)
            if code is None:
                code = languages.detect("")
                segments, info = _run(model, audio_bytes, languages.stt_code(code), settings)
    except Exception as exc:
        raise STTError(str(exc)) from exc

    text = " ".join(segment.text.strip() for segment in segments).strip()
    if not segments or not text:
        return {"text": "", "language": code, "confident": False, "avg_logprob": None}
    avg_logprob = sum(s.avg_logprob for s in segments) / len(segments)
    no_speech = max(s.no_speech_prob for s in segments)
    confident = avg_logprob >= settings["min_avg_logprob"] and no_speech <= settings["max_no_speech_prob"]
    return {"text": text, "language": code, "confident": confident, "avg_logprob": avg_logprob}
