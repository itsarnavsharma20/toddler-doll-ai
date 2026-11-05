"""Measure LLM speed (with token numbers), optional speech to text speed, and free RAM.

Run:
  python scripts/benchmark.py
  python scripts/benchmark.py --model gemma3:1b
  python scripts/benchmark.py --audio samples                 (a folder, or one file)
  python scripts/benchmark.py --audio samples --beam 1 --stt-model base

Needs Ollama running. --model must already be pulled and only changes the LLM for this run.
--stt-model and --beam only change speech to text for this run. A speech model that is not
on disk yet is downloaded into models/whisper on first use.
Audio is read from disk here only to time speech to text. Nothing is written.

How to read the LLM table: "wall" is what the caller waits. "ollama" is the time Ollama reports
for itself. "other" = wall - ollama: time spent outside Ollama (connection, Python). If "other"
is large, the delay is not the model.
"""
import argparse
import ctypes
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from playmate.services import llm, stt  # noqa: E402

PROMPTS = [
    ("en", "hello"),
    ("en", "what is your name"),
    ("hi", "tumhara naam kya hai"),
    ("hi", "mujhe khelna hai"),
]
AUDIO_SUFFIXES = {".m4a", ".wav", ".mp3", ".ogg", ".flac"}


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


def audio_seconds(path):
    """Length of an audio file in seconds, or None if it cannot be read."""
    try:
        import av

        with av.open(str(path)) as container:
            return container.duration / 1_000_000
    except Exception:
        return None


def audio_files(target):
    path = Path(target)
    if path.is_dir():
        return sorted(p for p in path.iterdir() if p.suffix.lower() in AUDIO_SUFFIXES)
    return [path]


def bench_llm(model):
    provider = llm.get_provider()
    print("LLM model: %s   url: %s" % (model or llm.health()["model"], provider.base))
    print("  %-5s %-4s %6s %7s %7s %7s %12s %12s %6s  %s" % (
        "call", "lang", "wall", "ollama", "other", "load", "prompt", "gen tok/s", "tokens", "reply"))
    walls, others = [], []
    for index, (language, text) in enumerate(PROMPTS):
        label = "cold" if index == 0 else "warm"
        try:
            start = time.perf_counter()
            reply, s = provider.generate_with_stats(text, language, model)
            wall = time.perf_counter() - start
        except llm.LLMError as exc:
            print("  FAILED  [%s] %s: %s" % (language, text, exc))
            continue
        other = wall - s["total_s"]
        if index > 0:
            walls.append(wall)
            others.append(other)
        print("  %-5s %-4s %5.1fs %6.1fs %6.1fs %6.1fs %5d/%4.1fs %6.1f/%4.1fs %6d  %s" % (
            label, language, wall, s["total_s"], other, s["load_s"], s["prompt_tokens"], s["prompt_s"],
            s["tokens_per_s"], s["gen_s"], s["gen_tokens"], reply.replace("\n", " ")))
    if walls:
        print("  warm: median wall %.1fs (best %.1fs, worst %.1fs), median other %.1fs"
              % (statistics.median(walls), min(walls), max(walls), statistics.median(others)))


def bench_stt(target):
    files = audio_files(target)
    if not files:
        print("No audio files found in %s" % target)
        return
    settings = stt._settings()
    print("Speech model: %s   beam: %s" % (settings["model"], settings["beam_size"]))
    start = time.perf_counter()
    stt._get_model()
    print("Speech model load: %.1fs" % (time.perf_counter() - start))
    print("  %-14s %7s %7s %6s %-4s %-9s %8s %9s  %s" % (
        "file", "length", "time", "speed", "lang", "confident", "logprob", "no_speech", "text"))
    for path in files:
        length = audio_seconds(path)
        try:
            start = time.perf_counter()
            heard = stt.transcribe(path.read_bytes())
            seconds = time.perf_counter() - start
        except stt.STTError as exc:
            print("  %-14s FAILED: %s" % (path.name, exc))
            continue
        speed = "%.1fx" % (length / seconds) if length else "?"
        logprob = "%.2f" % heard["avg_logprob"] if heard["avg_logprob"] is not None else "-"
        no_speech = "%.2f" % heard["no_speech_prob"] if heard["no_speech_prob"] is not None else "-"
        print("  %-14s %6.1fs %6.1fs %6s %-4s %-9s %8s %9s  %s" % (
            path.name, length or 0, seconds, speed, heard["language"], heard["confident"],
            logprob, no_speech, heard["text"]))
    print("  speed above 1.0x means faster than real time")


class Tee:
    """Write everything printed to the screen and to a file."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="also write the results to this UTF-8 text file (open it in VS Code to read Hindi)")
    parser.add_argument("--model", help="LLM model name to test instead of the configured one")
    parser.add_argument("--audio", help="audio file or folder to time speech to text")
    parser.add_argument("--stt-model", help="speech model to test (tiny, base, small, ...)")
    parser.add_argument("--beam", type=int, help="speech to text beam size to test")
    parser.add_argument("--skip-llm", action="store_true", help="only run the speech to text part")
    args = parser.parse_args()

    if args.stt_model:
        stt.OVERRIDES["model"] = args.stt_model
    if args.beam:
        stt.OVERRIDES["beam_size"] = args.beam

    report = None
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report = open(out_path, "w", encoding="utf-8")
        sys.stdout = Tee(sys.stdout, report)
    try:
        print("Free RAM before: %.1f GB\n" % free_ram_gb())
        if not args.skip_llm:
            bench_llm(args.model)
            print("\nFree RAM after LLM: %.1f GB" % free_ram_gb())
        if args.audio:
            print()
            bench_stt(args.audio)
            print("\nFree RAM after speech model: %.1f GB" % free_ram_gb())
    finally:
        if report:
            sys.stdout = sys.__stdout__
            report.close()
            print("\nResults also saved to %s" % args.out)


if __name__ == "__main__":
    main()
