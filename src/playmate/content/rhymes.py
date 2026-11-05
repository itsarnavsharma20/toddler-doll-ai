"""Rhyme lookup. Rhymes come from data/<lang>/rhymes.json and are played back exactly.

Matching is fuzzy text matching (stdlib difflib), in Roman and Devanagari:
  1. A rhyme name (trigger) in the child's words plays the whole rhyme.
  2. Part of a rhyme line plays the rest of the rhyme from the next line.
  3. A general request ("sing a song") plays a rhyme in the child's language.
"""
import random
from difflib import SequenceMatcher
from functools import lru_cache

from playmate.core.config import DATA_DIR, data_languages, read_json
from playmate.core.text import normalize

TRIGGER_THRESHOLD = 0.82
LINE_THRESHOLD = 0.85
MIN_LINE_WORDS = 3
MIN_COVERAGE = 0.6  # a short query must cover this much of a longer phrase
GENERIC_WORDS = frozenset({
    "rhyme", "rhymes", "poem", "song", "sing", "gaana", "gana", "kavita",
    "गाना", "गीत", "कविता", "राइम",
})


@lru_cache(maxsize=1)
def load_rhymes():
    items = []
    for code in data_languages():
        path = DATA_DIR / code / "rhymes.json"
        if not path.exists():
            continue
        for rhyme in read_json(path)["rhymes"]:
            rhyme = dict(rhyme, language=code)
            rhyme["_lines"] = tuple(line for line in rhyme["text"].split("\n") if line.strip())
            items.append(rhyme)
    return tuple(items)


def _score(query_words, phrase_words):
    """Best similarity between the query and the phrase, sliding the shorter over the longer."""
    if not query_words or not phrase_words:
        return 0.0
    query_is_short = len(query_words) < len(phrase_words)
    short, long_ = (query_words, phrase_words) if query_is_short else (phrase_words, query_words)
    if query_is_short and len(short) / len(long_) < MIN_COVERAGE:
        return 0.0
    target = " ".join(short)
    size = len(short)
    return max(
        SequenceMatcher(None, target, " ".join(long_[i:i + size])).ratio()
        for i in range(len(long_) - size + 1)
    )


def _match(rhyme, text, mode):
    return {"id": rhyme["id"], "title": rhyme["title"], "language": rhyme["language"], "text": text, "mode": mode}


def find_rhyme(text, language="en", generic=True):
    """Return {"id", "title", "language", "text", "mode"} or None. mode is "full" or "continue".

    generic=False skips the general request step ("sing a song"), so other requests can be checked first."""
    words = normalize(text).split()
    if not words:
        return None
    rhymes = load_rhymes()

    best, best_score = None, 0.0
    for rhyme in rhymes:
        for trigger in rhyme["triggers"]:
            score = _score(words, normalize(trigger).split())
            if score > best_score:
                best, best_score = rhyme, score
    if best and best_score >= TRIGGER_THRESHOLD:
        return _match(best, best["text"], "full")

    if len(words) >= MIN_LINE_WORDS:
        candidate = None  # (score, line index, rhyme). Later lines win ties.
        for rhyme in rhymes:
            for index, line in enumerate(rhyme["_lines"]):
                score = _score(words, normalize(line).split())
                if score >= LINE_THRESHOLD and (candidate is None or (score, index) >= candidate[:2]):
                    candidate = (score, index, rhyme)
        if candidate:
            _, index, rhyme = candidate
            rest = rhyme["_lines"][index + 1:]
            if rest:
                return _match(rhyme, "\n".join(rest), "continue")
            return _match(rhyme, rhyme["text"], "full")

    if generic and GENERIC_WORDS & set(words):
        same_language = [r for r in rhymes if r["language"] == language]
        pick = random.choice(same_language or list(rhymes))
        return _match(pick, pick["text"], "full")
    return None
