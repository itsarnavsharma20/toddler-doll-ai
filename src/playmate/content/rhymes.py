"""Rhyme lookup. Rhymes come from data/content/rhymes.json and are played back exactly."""
import json
import random
import re
from functools import lru_cache

from playmate.core.config import DATA_DIR

RHYMES_FILE = DATA_DIR / "content" / "rhymes.json"
GENERIC_WORDS = {"rhyme", "rhymes", "poem", "song", "sing", "gaana", "gana", "kavita"}


def _normalize(text):
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(text.split())


@lru_cache(maxsize=1)
def load_rhymes():
    with open(RHYMES_FILE, encoding="utf-8") as f:
        return tuple(json.load(f)["rhymes"])


def find_rhyme(text, language="english"):
    """Return a rhyme dict if the text names a rhyme or asks for one, else None."""
    words = _normalize(text)
    padded = " " + words + " "
    for rhyme in load_rhymes():
        for trigger in rhyme["triggers"]:
            if " " + _normalize(trigger) + " " in padded:
                return rhyme
    if GENERIC_WORDS & set(words.split()):
        same_language = [r for r in load_rhymes() if r["language"] == language]
        return random.choice(same_language or list(load_rhymes()))
    return None
