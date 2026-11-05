"""Project paths and configuration loading."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"


def load_settings():
    with open(CONFIG_DIR / "settings.json", encoding="utf-8") as f:
        return json.load(f)


def load_languages():
    with open(CONFIG_DIR / "languages.json", encoding="utf-8") as f:
        return json.load(f)
