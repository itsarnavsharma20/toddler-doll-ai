"""Language registry (config/languages.json) and language detection for text."""
import re

from playmate.core import config
from playmate.core.text import normalize

DEVANAGARI = re.compile(r"[ऀ-ॿ]")

# Common Roman-script Hindi words. English words are left out on purpose.
HINGLISH_HINTS = frozenset({
    "namaste", "kya", "hai", "hain", "mujhe", "tum", "tumhara", "tumhari", "kahani", "sunao",
    "gaana", "gana", "nahi", "nahin", "haan", "aap", "mera", "meri", "bolo", "kaise", "chahiye",
    "beta", "achha", "accha", "khelna", "batao", "kaun", "kyun", "chalo", "dost", "naam", "kahan",
})


def _registry():
    return config.load_languages()


def enabled_codes():
    return [code for code, entry in _registry().items() if entry.get("enabled")]


def is_enabled(code):
    return code in enabled_codes()


def resolve(value):
    """Accept a code ("hi") or a name ("hindi"). Return the code or None."""
    if not value:
        return None
    wanted = value.strip().lower()
    for code, entry in _registry().items():
        if wanted == code or wanted == entry.get("name"):
            return code
    return None


def prompt_name(code):
    entry = _registry().get(code, {})
    return entry.get("prompt_name") or entry.get("name") or code


def tts_voice(code):
    """Voice for the language that matches the toy's gender (toy_gender in settings).

    Falls back to the other gender if only one voice is listed, so a language is never silent."""
    voices = _registry().get(code, {}).get("tts_voices") or {}
    gender = config.load_settings().get("toy_gender", "male")
    return voices.get(gender) or next(iter(voices.values()), None)


def stt_code(code):
    """Language code used by the speech to text model for one of our codes."""
    return _registry().get(code, {}).get("stt") or code


def code_from_stt(stt_language):
    """Our enabled language code for a speech to text language code, or None."""
    for code, entry in _registry().items():
        if entry.get("enabled") and (entry.get("stt") or code) == stt_language:
            return code
    return None


def describe():
    return [
        {"code": code, "name": entry.get("name"), "enabled": bool(entry.get("enabled")),
         "stt": entry.get("stt"), "tts_voice": tts_voice(code)}
        for code, entry in _registry().items()
    ]


def detect(text, requested=None):
    """Pick the reply language: a valid request, else script, else Hindi word hints, else default."""
    code = resolve(requested)
    if code and is_enabled(code):
        return code
    if is_enabled("hi"):
        if DEVANAGARI.search(text or ""):
            return "hi"
        if set(normalize(text).split()) & HINGLISH_HINTS:
            return "hi"
    default = resolve(config.load_settings()["default_language"])
    return default if default and is_enabled(default) else "en"
