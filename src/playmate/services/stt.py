"""Speech to text. faster-whisper, local, CPU. Audio stays in memory and is never written to disk."""
import io
import os
import threading

from playmate.content import hints
from playmate.core import config, languages

# Keep every download (model files and the Hugging Face cache) inside the project folder.
os.environ.setdefault("HF_HOME", str(config.ROOT / "models" / "hf"))


class STTError(Exception):
    """Speech to text failed."""


# Values here replace config/settings.json for this process (used by scripts/benchmark.py).
OVERRIDES = {}

_models = {}
_lock = threading.Lock()


def _settings():
    return {**config.load_settings()["stt"], **OVERRIDES}


def _load(settings, local_files_only):
    from faster_whisper import WhisperModel

    return WhisperModel(
        settings["model"],
        device=settings["device"],
        compute_type=settings["compute_type"],
        download_root=str(config.ROOT / settings["download_dir"]),
        local_files_only=local_files_only,
    )


def _get_model():
    """Load a model once per name. Uses the files on disk first and never touches the internet
    for that. Only if the model is not on disk yet, it is downloaded into the project models folder."""
    s = _settings()
    with _lock:
        if s["model"] not in _models:
            try:
                _models[s["model"]] = _load(s, local_files_only=True)
            except Exception:
                _models[s["model"]] = _load(s, local_files_only=False)
        return _models[s["model"]]


def _run(model, audio_bytes, code, settings):
    """Transcribe once. code is one of our language codes, or None to let the model detect it."""
    options = {
        "language": languages.stt_code(code) if code else None,
        "beam_size": settings["beam_size"],
        "vad_filter": settings["vad_filter"],
        "temperature": settings.get("temperature", 0.0),  # one pass, no slow retries
        "condition_on_previous_text": settings.get("condition_on_previous_text", False),
    }
    words = hints.hotwords(code)
    if words:
        options["hotwords"] = words
    prompt = hints.initial_prompt(code) if code else ""
    if prompt:
        options["initial_prompt"] = prompt
    segments, info = model.transcribe(io.BytesIO(audio_bytes), **options)
    return list(segments), info


def transcribe(audio_bytes, language=None):
    """Return {"text", "language", "confident", "avg_logprob", "no_speech_prob"}. language is one of our codes.

    If no language is given, the model detects it. A language that is not enabled is
    replaced by the default language and the audio is transcribed again.
    """
    settings = _settings()
    try:
        model = _get_model()
        code = languages.resolve(language)
        code = code if code and languages.is_enabled(code) else None
        segments, info = _run(model, audio_bytes, code, settings)
        if code is None:
            code = languages.code_from_stt(info.language)
            if code is None:
                code = languages.detect("")
                segments, info = _run(model, audio_bytes, code, settings)
    except Exception as exc:
        raise STTError(str(exc)) from exc

    text = " ".join(segment.text.strip() for segment in segments).strip()
    if not segments or not text:
        return {"text": "", "language": code, "confident": False, "avg_logprob": None, "no_speech_prob": None}
    avg_logprob = sum(s.avg_logprob for s in segments) / len(segments)
    no_speech = max(s.no_speech_prob for s in segments)
    confident = avg_logprob >= settings["min_avg_logprob"] and no_speech <= settings["max_no_speech_prob"]
    return {"text": text, "language": code, "confident": confident,
            "avg_logprob": avg_logprob, "no_speech_prob": no_speech}
