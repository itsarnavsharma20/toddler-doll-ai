"""Fixed toy phrases per language, read from data/<lang>/messages.json."""
from functools import lru_cache

from playmate.core.config import DATA_DIR, read_json


@lru_cache(maxsize=None)
def _load(code):
    path = DATA_DIR / code / "messages.json"
    return read_json(path) if path.exists() else {}


def get(code, key):
    """Return the phrase in the given language, or in English if it is missing."""
    return _load(code).get(key) or _load("en")[key]
