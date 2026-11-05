"""Measure LLM speed, optional speech to text speed, and free RAM on this machine.

Run: python scripts/benchmark.py [--audio path/to/clip.wav]

Needs Ollama running with the model pulled. With --audio, the speech model is used. On the
first run it is downloaded into models/whisper (about 500 MB for "small").
"""
import argparse
import ctypes
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from playmate.services import llm, stt  # noqa: E402

PROMPTS = [
    ("en", "hello"),
    ("en", "what is your name"),
    ("hi", "tumhara naam kya hai"),
]


class MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
        ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
        ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
        ("avail_ext", ctypes.c_ulonglong),
    ]


def free_ram_gb():
    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.avail_phys / 1024 ** 3


def timed(function, *args):
    start = time.perf_counter()
    result = function(*args)
    return result, time.perf_counter() - start


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", help="optional audio file to time speech to text")
    args = parser.parse_args()

    print("Free RAM before: %.1f GB" % free_ram_gb())
    print("\nLLM (first call includes model load)")
    for language, text in PROMPTS:
        try:
            reply, seconds = timed(llm.ask_llm, text, language)
            print("  %5.1f s  [%s] %s -> %s" % (seconds, language, text, reply))
        except llm.LLMError as exc:
            print("  FAILED  [%s] %s: %s" % (language, text, exc))
    print("Free RAM after LLM: %.1f GB" % free_ram_gb())

    if args.audio:
        audio = Path(args.audio).read_bytes()
        print("\nSpeech to text (first call includes model load)")
        for attempt in (1, 2):
            try:
                heard, seconds = timed(stt.transcribe, audio)
                print("  run %d: %5.1f s  lang=%s confident=%s text=%s"
                      % (attempt, seconds, heard["language"], heard["confident"], heard["text"]))
            except stt.STTError as exc:
                print("  FAILED: %s" % exc)
                break
        print("Free RAM after STT: %.1f GB" % free_ram_gb())


if __name__ == "__main__":
    main()
