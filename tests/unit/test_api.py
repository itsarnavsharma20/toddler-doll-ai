"""Unit tests for API route functions. Called directly, so no server and no model are needed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from playmate.api import main  # noqa: E402
from playmate.core import metrics  # noqa: E402


class ApiTests(unittest.TestCase):
    def test_languages_endpoint(self):
        codes = {item["code"]: item["enabled"] for item in main.get_languages()}
        self.assertTrue(codes["en"])
        self.assertTrue(codes["hi"])
        self.assertFalse(codes["ta"])

    def test_chat_endpoint_rhyme(self):
        result = main.chat(main.ChatRequest(text="twinkle twinkle little star"))
        self.assertEqual(result["source"], "rhyme:twinkle_twinkle")
        self.assertEqual(result["language"], "en")

    def test_chat_routes_exist(self):
        paths = {route.path for route in main.app.routes}
        self.assertTrue({"/v1/chat", "/chat", "/v1/health", "/v1/languages", "/v1/warmup", "/v1/stats"} <= paths)

    def test_stats_counts_sources_only(self):
        main.chat(main.ChatRequest(text="twinkle twinkle little star"))
        snapshot = metrics.snapshot()
        self.assertGreaterEqual(snapshot.get("rhyme:twinkle_twinkle", 0), 1)
        for key in snapshot:
            self.assertNotIn("little star", key)


if __name__ == "__main__":
    unittest.main(verbosity=2)
