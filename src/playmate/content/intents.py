"""Find what the child is asking for (story, abc, numbers) from words in data/<lang>/intents.json.

Speech to text makes small mistakes, so a word also matches an alias with a small spelling slip.
Aliases from all languages are used together, because children mix languages.
"""
from difflib import SequenceMatcher
from functools import lru_cache

from playmate.core.config import DATA_DIR, data_languages, read_json
from playmate.core.text import normalize

SIMILARITY = 0.8
MIN_FUZZY_LENGTH = 5  # shorter words must match exactly, to avoid false matches


@lru_cache(maxsize=1)
def _aliases():
    """{intent: [alias word tuples]} merged from every language."""
    found = {}
    for code in data_languages():
        path = DATA_DIR / code / "intents.json"
        if not path.exists():
            continue
        for intent, entry in read_json(path).items():
            if not isinstance(entry, dict):
                continue  # skips the "note" field
            for alias in entry.get("aliases", []):
                words = tuple(normalize(alias).split())
                if words:
                    found.setdefault(intent, []).append(words)
    return found


def _same_word(word, alias):
    if word == alias:
        return True
    if min(len(word), len(alias)) < MIN_FUZZY_LENGTH:
        return False
    return SequenceMatcher(None, word, alias).ratio() >= SIMILARITY


def _alias_at(words, position, alias):
    end = position + len(alias)
    return end <= len(words) and all(_same_word(words[position + i], alias[i]) for i in range(len(alias)))


def detect(text):
    """Return the intent name ("story", "abc", "numbers") or None. The earliest match in the text wins."""
    words = normalize(text).split()
    for position in range(len(words)):
        for intent, aliases in _aliases().items():
            if any(_alias_at(words, position, alias) for alias in aliases):
                return intent
    return None
