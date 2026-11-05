"""Text helpers shared by safety and content. Safe for Devanagari: combining marks are kept."""
import re
import unicodedata

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s"})
_EMOJI_PARTS = "️‍"


def normalize(text, leet=False):
    """Lowercase, drop punctuation and symbols, collapse spaces and long letter repeats."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    if leet:
        text = text.translate(_LEET)
    out = []
    for ch in text:
        category = unicodedata.category(ch)
        if category == "Cf":
            continue
        out.append(" " if category[0] in "PS" else ch)
    text = re.sub(r"(.)\1{2,}", r"\1", "".join(out))  # "stuuupid" -> "stupid"
    return " ".join(text.split())


def strip_symbols(text):
    """Remove emoji and pictograms. Keeps letters, marks, punctuation and newlines."""
    kept = [
        ch for ch in text
        if unicodedata.category(ch) not in ("So", "Sk", "Cs", "Co", "Cn") and ch not in _EMOJI_PARTS
    ]
    return re.sub(r"[ \t]{2,}", " ", "".join(kept)).strip()
