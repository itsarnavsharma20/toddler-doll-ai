"""Speech hints per language, read from data/<lang>/stt_hints.json.

Used to help speech to text (hotwords, initial prompt) and to drop a spoken greeting plus
the toy's name ("Hey Kiko, ...") before the request is handled.
"""
from functools import lru_cache

from playmate.core.config import DATA_DIR, data_languages, read_json
from playmate.core.text import normalize


@lru_cache(maxsize=None)
def load_hints(code):
    path = DATA_DIR / code / "stt_hints.json"
    return read_json(path) if path.exists() else {}


def hotwords(code=None):
    """Hotwords as one string. For one language, or merged from all languages if code is None."""
    words = []
    for lang in [code] if code else data_languages():
        for word in load_hints(lang).get("hotwords", []):
            if word not in words:
                words.append(word)
    return " ".join(words)


def initial_prompt(code):
    return load_hints(code).get("initial_prompt", "")


def name_variants():
    """Spellings of the toy's name as token tuples, longest first."""
    variants = set()
    for code in data_languages():
        for spelling in load_hints(code).get("name_variants", []):
            tokens = tuple(normalize(spelling).split())
            if tokens:
                variants.add(tokens)
    return sorted(variants, key=len, reverse=True)


def greetings():
    found = set()
    for code in data_languages():
        for word in load_hints(code).get("greetings", []):
            found.add(normalize(word))
    return found
