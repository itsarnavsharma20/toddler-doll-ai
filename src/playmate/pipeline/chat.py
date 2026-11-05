"""Chat pipeline: input safety, rhyme lookup, LLM, output safety."""
import re

from playmate.content import rhymes
from playmate.core import config
from playmate.safety import filters
from playmate.services import llm

DEVANAGARI = re.compile(r"[ऀ-ॿ]")

NOT_HEARD = {
    "english": "I did not hear you. Can you say it again?",
    "hindi": "Mujhe suna nahi. Kya tum phir se bologe?",
}
LLM_DOWN = {
    "english": "Hmm, let me think. Can you say it again?",
    "hindi": "Hmm, main soch raha hoon. Kya tum phir se bologe?",
}


def enabled_languages():
    return {name for name, on in config.load_languages().items() if on}


def pick_language(text, requested=None):
    default = config.load_settings()["default_language"]
    language = requested or ("hindi" if DEVANAGARI.search(text) else default)
    return language if language in enabled_languages() else "english"


def respond(text, language=None):
    """Return {"reply", "language", "source"}. source tells which step produced the reply."""
    text = (text or "").strip()
    language = pick_language(text, language)
    if not text:
        return {"reply": NOT_HEARD.get(language, NOT_HEARD["english"]), "language": language, "source": "empty"}
    if filters.contains_blocked(text):
        return {"reply": filters.redirect_message(language), "language": language, "source": "safety_input"}
    rhyme = rhymes.find_rhyme(text, language)
    if rhyme:
        return {"reply": rhyme["text"], "language": language, "source": "rhyme:" + rhyme["id"]}
    try:
        reply = llm.ask_llm(text, language)
    except llm.LLMError:
        return {"reply": LLM_DOWN.get(language, LLM_DOWN["english"]), "language": language, "source": "fallback"}
    return {"reply": filters.clean_output(reply, language), "language": language, "source": "llm"}
