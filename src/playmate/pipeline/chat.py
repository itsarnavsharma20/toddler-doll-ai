"""Chat pipeline: input safety, rhyme lookup, LLM, output safety."""
from playmate.content import messages, rhymes
from playmate.core import languages, metrics
from playmate.safety import filters
from playmate.services import llm


def _result(reply, language, source):
    metrics.record(source)
    return {"reply": reply, "language": language, "source": source}


def respond(text, language=None):
    """Return {"reply", "language", "source"}. source tells which step produced the reply."""
    text = (text or "").strip()
    code = languages.detect(text, language)
    if not text:
        return _result(messages.get(code, "not_heard"), code, "empty")
    if filters.contains_blocked(text):
        return _result(filters.redirect_message(code), code, "safety_input")
    match = rhymes.find_rhyme(text, code)
    if match:
        source = "rhyme:" + match["id"] + (":continue" if match["mode"] == "continue" else "")
        return _result(match["text"], code, source)
    try:
        reply = llm.ask_llm(text, code)
    except llm.LLMError:
        return _result(messages.get(code, "llm_down"), code, "fallback")
    return _result(filters.clean_output(reply, code), code, "llm")
