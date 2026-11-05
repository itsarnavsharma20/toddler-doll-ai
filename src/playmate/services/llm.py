"""LLM service. A small provider interface, with a local Ollama provider.

Only local providers are allowed for now (child data must not leave the machine).
Model name and settings come from config/settings.json.
"""
import json
import urllib.request

from playmate.core import config, languages

# Keep this prompt short: the model reads all of it before every answer (about 80 tokens now).
SYSTEM_PROMPT = (
    "You are {name}, a friendly toy for a 3 year old child. "
    "{gender}"
    "Reply in {language} only, in 1 short simple sentence. Be kind and happy. "
    "No emojis. Never scold. "
    "No scary or grown-up topics: gently suggest a rhyme instead."
)

GENDER_HINTS = {
    "male": "You are a boy: in Hindi use masculine forms (main khelunga, tumhara dost). ",
    "female": "You are a girl: in Hindi use feminine forms (main khelungi, tumhari dost). ",
}


class LLMError(Exception):
    """The LLM could not be reached or gave no answer."""


def build_system_prompt(language):
    settings = config.load_settings()
    return SYSTEM_PROMPT.format(
        name=settings["toy_name"],
        gender=GENDER_HINTS.get(settings.get("toy_gender"), ""),
        language=languages.prompt_name(language),
    )


def _stats(data):
    """Timing numbers from an Ollama reply (it reports nanoseconds)."""
    def seconds(key):
        return data.get(key, 0) / 1e9

    gen_tokens = data.get("eval_count", 0)
    gen_seconds = seconds("eval_duration")
    return {
        "total_s": seconds("total_duration"),
        "load_s": seconds("load_duration"),
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "prompt_s": seconds("prompt_eval_duration"),
        "gen_tokens": gen_tokens,
        "gen_s": gen_seconds,
        "tokens_per_s": gen_tokens / gen_seconds if gen_seconds else 0.0,
    }


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

    def _chat(self, text, language, model=None):
        s = self.settings
        body = {
            "model": model or s["model"],
            "stream": False,
            "think": s.get("think", False),  # no hidden reasoning: slow and uses up max_tokens
            "keep_alive": s.get("keep_alive", "30m"),
            "messages": [
                {"role": "system", "content": build_system_prompt(language)},
                {"role": "user", "content": text},
            ],
            "options": {"num_predict": s["max_tokens"], "num_ctx": s.get("num_ctx", 2048)},
        }
        try:
            data = self._post("/api/chat", body, s["timeout_seconds"])
            reply = data["message"]["content"]
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        if not reply or not reply.strip():
            raise LLMError("empty reply")
        return reply.strip(), data

    def generate(self, text, language):
        return self._chat(text, language)[0]

    def generate_with_stats(self, text, language, model=None):
        """Same as generate, plus timing numbers. model overrides the configured model."""
        reply, data = self._chat(text, language, model)
        return reply, _stats(data)

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
