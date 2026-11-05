"""LLM service. A small provider interface, with a local Ollama provider.

Only local providers are allowed for now (child data must not leave the machine).
Model name and settings come from config/settings.json.
"""
import json
import urllib.request

from playmate.core import config, languages

SYSTEM_PROMPT = (
    "You are {name}, a friendly toy for a 3 year old child. "
    "If asked your name, say {name}. "
    "Use only safe, simple, short words. "
    "Reply in 1 or 2 short sentences. Be kind and happy. Never scold the child. "
    "Never use emojis. "
    "Never talk about scary, violent, or grown-up things. "
    "If asked about them, gently change the topic to a rhyme, a number, or a letter. "
    "Reply in {language}."
)


class LLMError(Exception):
    """The LLM could not be reached or gave no answer."""


class OllamaProvider:
    def __init__(self, settings):
        self.settings = settings
        self.base = settings["url"].rstrip("/")

    def _post(self, path, body, timeout):
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)

    def generate(self, text, language):
        s = self.settings
        body = {
            "model": s["model"],
            "stream": False,
            "think": s.get("think", False),  # no hidden reasoning: slow and uses up max_tokens
            "keep_alive": s.get("keep_alive", "30m"),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.format(
                    name=config.load_settings()["toy_name"], language=languages.prompt_name(language))},
                {"role": "user", "content": text},
            ],
            "options": {"num_predict": s["max_tokens"], "num_ctx": s.get("num_ctx", 2048)},
        }
        try:
            reply = self._post("/api/chat", body, s["timeout_seconds"])["message"]["content"]
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        if not reply or not reply.strip():
            raise LLMError("empty reply")
        return reply.strip()

    def warmup(self):
        """Load the model into memory so the first real question is fast."""
        body = {"model": self.settings["model"], "keep_alive": self.settings.get("keep_alive", "30m")}
        try:
            self._post("/api/generate", body, self.settings["timeout_seconds"])
        except Exception as exc:
            raise LLMError(str(exc)) from exc

    def is_reachable(self):
        try:
            with urllib.request.urlopen(self.base + "/api/tags", timeout=2):
                return True
        except Exception:
            return False


PROVIDERS = {"ollama": OllamaProvider}


def get_provider():
    settings = config.load_settings()["llm"]
    provider_class = PROVIDERS.get(settings["provider"])
    if provider_class is None:
        raise LLMError("unknown LLM provider: %s" % settings["provider"])
    return provider_class(settings)


def ask_llm(text, language="en"):
    return get_provider().generate(text, language)


def warmup():
    get_provider().warmup()


def health():
    settings = config.load_settings()["llm"]
    return {
        "provider": settings["provider"],
        "model": settings["model"],
        "reachable": get_provider().is_reachable(),
    }
