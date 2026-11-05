"""Download the speech to text model into the project models/ folder.

Run: python scripts/download_models.py
The model name comes from config/settings.json (stt.model). Nothing is stored outside the project.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from playmate.core import config  # noqa: E402
from playmate.services import stt  # noqa: E402


def folder_size_mb(path):
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / 1024 ** 2


def main():
    settings = config.load_settings()["stt"]
    target = config.ROOT / "models"
    print("Downloading speech model '%s' into %s ..." % (settings["model"], target))
    stt._get_model()
    print("Done. models/ folder size: %.0f MB" % folder_size_mb(target))


if __name__ == "__main__":
    main()
