"""Safety filters. Input and output both pass through here. Never skip either."""
import re
from functools import lru_cache

from playmate.content import messages
from playmate.core.config import DATA_DIR, data_languages, read_json
from playmate.core.text import normalize, strip_symbols

MAX_REPLY_CHARS = 500


@lru_cache(maxsize=1)
def _blocked_words():
    """Blocked words from every data/<lang>/safety.json. Children mix languages, so lists are merged."""
    words = []
    for code in data_languages():
        path = DATA_DIR / code / "safety.json"
        if path.exists():
            words.extend(read_json(path)["words"])
    return tuple(normalize(word, leet=True) for word in words)


def contains_blocked(text):
    padded = " " + normalize(text, leet=True) + " "
    return any(" " + word + " " in padded for word in _blocked_words())


def redirect_message(language):
    """Gentle redirect. Never scold the child."""
    return messages.get(language, "redirect")


def clean_output(reply, language):
    """Return a safe reply. Falls back to a fixed safe message if anything looks wrong."""
    fallback = messages.get(language, "output_fallback")
    reply = strip_symbols(re.sub(r"https?://\S+", "", reply or ""))
    if not reply or contains_blocked(reply):
        return fallback
    if len(reply) > MAX_REPLY_CHARS:
        cut = reply[:MAX_REPLY_CHARS]
        end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "), cut.rfind("। "))
        reply = cut[: end + 1] if end > 0 else cut
    return reply
