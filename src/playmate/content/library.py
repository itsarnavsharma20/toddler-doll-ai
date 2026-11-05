"""Learning content: stories and basics (abc, numbers) from data/<lang>/. Played back exactly."""
import random
from functools import lru_cache

from playmate.core.config import DATA_DIR, read_json


@lru_cache(maxsize=None)
def _load(code, name):
    path = DATA_DIR / code / name
    return read_json(path) if path.exists() else {}


def stories(code):
    return _load(code, "stories.json").get("stories", [])


def basics(code):
    return {key: value for key, value in _load(code, "basics.json").items() if isinstance(value, dict)}


def pick(intent, code):
    """Return {"id", "title", "text"} for the intent in the language, or in English if missing. None if none."""
    for lang in (code, "en"):
        if intent == "story":
            items = stories(lang)
            if items:
                story = random.choice(items)
                return {"id": story["id"], "title": story["title"], "text": story["text"]}
        else:
            item = basics(lang).get(intent)
            if item:
                return {"id": intent, "title": item["title"], "text": item["text"]}
    return None
