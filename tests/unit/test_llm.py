"""Unit tests for the LLM provider. The HTTP call is replaced, so no Ollama is needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.core import config  # noqa: E402
from playmate.services import llm  # noqa: E402


class LLMTests(unittest.TestCase):
    def setUp(self):
        self.original_load = config.load_settings
        self.bodies = []

    def tearDown(self):
        config.load_settings = self.original_load

    def provider(self, reply="Hi!"):
        provider = llm.OllamaProvider(config.load_settings()["llm"])

        def fake_post(path, body, timeout):
            self.bodies.append((path, body))
            return {"message": {"content": reply}}

        provider._post = fake_post
        return provider

    def system_prompt(self):
        return self.bodies[-1][1]["messages"][0]["content"]

    def test_toy_name_comes_from_config(self):
        self.assertEqual(config.load_settings()["toy_name"], "Kiko")
        self.provider().generate("hello", "en")
        self.assertIn("You are Kiko", self.system_prompt())

    def test_prompt_stays_short(self):
        self.provider().generate("hello", "hi")
        self.assertLess(len(self.system_prompt().split()), 65)

    def test_url_uses_ip_not_localhost(self):
        self.assertIn("127.0.0.1", config.load_settings()["llm"]["url"])

    def test_changing_config_changes_name(self):
        settings = dict(self.original_load(), toy_name="Zed")
        config.load_settings = lambda: settings
        self.provider().generate("hello", "en")
        self.assertIn("You are Zed", self.system_prompt())
        self.assertNotIn("Kiko", self.system_prompt())

    def test_kiko_is_male_in_hindi(self):
        self.assertEqual(config.load_settings()["toy_gender"], "male")
        self.provider().generate("namaste", "hi")
        self.assertIn("You are a boy", self.system_prompt())
        self.assertIn("masculine", self.system_prompt())

    def test_gender_can_change_or_be_left_out(self):
        base = self.original_load()
        config.load_settings = lambda: dict(base, toy_gender="female")
        self.assertIn("feminine", llm.build_system_prompt("hi"))
        config.load_settings = lambda: {k: v for k, v in base.items() if k != "toy_gender"}
        self.assertNotIn("masculine", llm.build_system_prompt("hi"))
        self.assertNotIn("feminine", llm.build_system_prompt("hi"))

    def test_stats_and_model_override(self):
        provider = llm.OllamaProvider(config.load_settings()["llm"])
        seen = {}

        def fake_post(path, body, timeout):
            seen["model"] = body["model"]
            return {
                "message": {"content": "Hi!"},
                "total_duration": 4_000_000_000, "load_duration": 1_000_000_000,
                "prompt_eval_count": 50, "prompt_eval_duration": 500_000_000,
                "eval_count": 20, "eval_duration": 2_000_000_000,
            }

        provider._post = fake_post
        reply, stats = provider.generate_with_stats("hello", "en", model="other:1b")
        self.assertEqual(seen["model"], "other:1b")
        self.assertEqual(reply, "Hi!")
        self.assertEqual(stats["tokens_per_s"], 10.0)
        self.assertEqual(stats["prompt_tokens"], 50)
        self.assertEqual(stats["load_s"], 1.0)

    def test_hindi_prompt_asks_for_devanagari(self):
        self.provider().generate("namaste", "hi")
        self.assertIn("Devanagari", self.system_prompt())

    def test_request_settings(self):
        self.provider().generate("hello", "en")
        path, body = self.bodies[-1]
        self.assertEqual(path, "/api/chat")
        self.assertFalse(body["think"])
        self.assertFalse(body["stream"])
        self.assertEqual(body["options"]["num_ctx"], 2048)
        self.assertEqual(body["messages"][1], {"role": "user", "content": "hello"})

    def test_empty_reply_is_an_error(self):
        with self.assertRaises(llm.LLMError):
            self.provider(reply="  ").generate("hello", "en")

    def test_unknown_provider_is_an_error(self):
        settings = dict(self.original_load(), llm=dict(self.original_load()["llm"], provider="cloud"))
        config.load_settings = lambda: settings
        with self.assertRaises(llm.LLMError):
            llm.get_provider()


if __name__ == "__main__":
    unittest.main(verbosity=2)
