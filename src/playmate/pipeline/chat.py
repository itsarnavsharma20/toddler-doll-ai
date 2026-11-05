"""Chat pipeline: input safety, rhyme lookup, learning requests, LLM, output safety."""
from playmate.content import intents, library, messages, rhymes
from playmate.core import languages, metrics
from playmate.pipeline import wake
from playmate.safety import filters
from playmate.services import llm


def _result(reply, language, source):
    metrics.record(source)
    return {"reply": reply, "language": language, "source": source}


def _rhyme_result(match, code):
    source = "rhyme:" + match["id"] + (":continue" if match["mode"] == "continue" else "")
    return _result(match["text"], code, source)


def respond(text, language=None):
    """Return {"reply", "language", "source"}. source tells which step produced the reply.

    Order: input safety, a named rhyme or a line of one, a story or abc or numbers request,
    a general rhyme request, then the LLM. Stored content is played back exactly.
    """
    text = wake.strip_name((text or "").strip())
    code = languages.detect(text, language)
    if not text:
        return _result(messages.get(code, "not_heard"), code, "empty")
    if filters.contains_blocked(text):
        return _result(filters.redirect_message(code), code, "safety_input")

    match = rhymes.find_rhyme(text, code, generic=False)
    if match:
        return _rhyme_result(match, code)

    intent = intents.detect(text)
    item = library.pick(intent, code) if intent else None
    if item:
        prefix = "story" if intent == "story" else "basics"
        return _result(item["text"], code, "%s:%s" % (prefix, item["id"]))

    match = rhymes.find_rhyme(text, code)
    if match:
        return _rhyme_result(match, code)

    try:
        reply = llm.ask_llm(text, code)
    except llm.LLMError:
        return _result(messages.get(code, "llm_down"), code, "fallback")
    return _result(filters.clean_output(reply, code), code, "llm")
