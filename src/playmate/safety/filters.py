"""Safety filters. Input and output both pass through here. Never skip either."""
import json
import re
import unicodedata
from functools import lru_cache

from playmate.core.config import DATA_DIR

BLOCKED_FILE = DATA_DIR / "safety" / "blocked_words.json"
MAX_REPLY_CHARS = 500

# Gentle redirects. Never scold the child.
REDIRECT = {
    "english": "Let's use a happy word instead! Do you want to hear a rhyme?",
    "hindi": "Chalo koi achha sa shabd bolte hain! Kya tum rhyme sunoge?",
}
OUTPUT_FALLBACK = {
    "english": "Let's sing a song together! Do you want to hear Twinkle Twinkle?",
    "hindi": "Chalo ek gaana gaate hain! Kya tum Machli Jal Ki Rani Hai sunoge?",
}

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s"})


def _normalize(text):
    text = unicodedata.normalize("NFKC", text).lower().translate(_LEET)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"(.)\1{2,}", r"\1", text)  # "stuuupid" -> "stupid"
    return " ".join(text.split())


@lru_cache(maxsize=1)
def _blocked_words():
    with open(BLOCKED_FILE, encoding="utf-8") as f:
        words = json.load(f)["words"]
    return tuple(_normalize(w) for w in words)


def contains_blocked(text):
    padded = " " + _normalize(text) + " "
    return any(" " + word + " " in padded for word in _blocked_words())


def redirect_message(language):
    return REDIRECT.get(language, REDIRECT["english"])


def clean_output(reply, language):
    """Return a safe reply. Falls back to a fixed safe message if anything looks wrong."""
    fallback = OUTPUT_FALLBACK.get(language, OUTPUT_FALLBACK["english"])
    reply = re.sub(r"https?://\S+", "", reply or "").strip()
    if not reply or contains_blocked(reply):
        return fallback
    if len(reply) > MAX_REPLY_CHARS:
        cut = reply[:MAX_REPLY_CHARS]
        end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
        reply = cut[: end + 1] if end > 0 else cut
    return reply
