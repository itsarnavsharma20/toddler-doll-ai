"""Project paths and configuration loading."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_settings():
    return read_json(CONFIG_DIR / "settings.json")


def load_languages():
    return read_json(CONFIG_DIR / "languages.json")


def data_languages():
    """Language codes that have a folder under data/ (for example data/en, data/hi)."""
    return sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir() and len(p.name) == 2 and p.name.isalpha())
