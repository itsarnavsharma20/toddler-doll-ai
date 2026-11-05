"""LLM client. Talks to a local Ollama server. Model name comes from config/settings.json."""
import json
import urllib.request

from playmate.core import config

SYSTEM_PROMPT = (
    "You are a friendly toy for a 3 year old child. "
    "Use only safe, simple, short words. "
    "Reply in 1 or 2 short sentences. Be kind and happy. Never scold the child. "
    "Never talk about scary, violent, or grown-up things. "
    "If asked about them, gently change the topic to a rhyme, a number, or a letter. "
    "Reply in {language}."
)


class LLMError(Exception):
    """The LLM could not be reached or gave no answer."""


def ask_llm(text, language="english"):
    settings = config.load_settings()["llm"]
    body = {
        "model": settings["model"],
        "stream": False,
        "think": settings.get("think", False),  # no hidden reasoning: slow and uses up max_tokens
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.format(language=language)},
            {"role": "user", "content": text},
        ],
        "options": {"num_predict": settings["max_tokens"], "num_ctx": settings.get("num_ctx", 2048)},
    }
    request = urllib.request.Request(
        settings["url"].rstrip("/") + "/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=settings["timeout_seconds"]) as response:
            reply = json.load(response)["message"]["content"]
    except Exception as exc:
        raise LLMError(str(exc)) from exc
    if not reply or not reply.strip():
        raise LLMError("empty reply")
    return reply.strip()
