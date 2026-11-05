"""Run audio clips through the whole voice flow and show the time of each stage.

Run:
  python scripts/voice_test.py --audio samples
  python scripts/voice_test.py --audio samples/sample1.m4a --save-audio --out reports/voice.txt

Needs Ollama running. Text to speech (edge-tts, prototype only) goes online and sends the toy's
reply text, never the clip, to Microsoft. Clips are only read, never written.
--save-audio writes the toy's spoken reply (mp3) into reports/voice so you can listen to it.
--out also saves the results as a UTF-8 text file (open it in VS Code to read Hindi).
"""
import argparse
import asyncio
import base64
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from benchmark import AUDIO_SUFFIXES, Tee, audio_files, audio_seconds, free_ram_gb  # noqa: E402
from playmate.pipeline import voice  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True, help="audio file or folder (%s)" % ", ".join(sorted(AUDIO_SUFFIXES)))
    parser.add_argument("--language", help="force a language code (en, hi). Default: detected from the speech")
    parser.add_argument("--save-audio", action="store_true", help="save the spoken replies as mp3 in reports/voice")
    parser.add_argument("--no-warmup", action="store_true", help="do not run the first clip once before timing")
    parser.add_argument("--out", help="also write the results to this UTF-8 text file")
    args = parser.parse_args()

    files = audio_files(args.audio)
    if not files:
        print("No audio files found in %s" % args.audio)
        return

    report = None
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        report = open(args.out, "w", encoding="utf-8")
        sys.stdout = Tee(sys.stdout, report)
    try:
        print("Free RAM before: %.1f GB" % free_ram_gb())
        if not args.no_warmup:
            print("Warming up (first clip, not timed)...")
            asyncio.run(voice.handle(files[0].read_bytes(), args.language))
        totals = []
        for path in files:
            length = audio_seconds(path)
            result = asyncio.run(voice.handle(path.read_bytes(), args.language))
            t = result["timings"]
            totals.append(t["total_s"])
            audio_kb = len(base64.b64decode(result["audio_base64"])) / 1024 if result["audio_base64"] else 0
            print("\n%s  (%.1fs of audio)" % (path.name, length or 0))
            print("  heard   : %s" % (result["transcript"] or "(nothing clear)"))
            print("  language: %s   source: %s" % (result["language"], result["source"]))
            print("  reply   : %s" % result["reply"].replace("\n", " ")[:160])
            print("  time    : stt %.1fs + chat %.1fs + tts %.1fs = %.1fs total   audio: %.0f KB%s"
                  % (t["stt_s"], t["chat_s"], t["tts_s"], t["total_s"], audio_kb,
                     "" if result["audio_base64"] else "  (TTS FAILED, text only)"))
            if result["tts_error"]:
                print("  tts error: %s" % result["tts_error"])
            if args.save_audio and result["audio_base64"]:
                out_dir = Path("reports") / "voice"
                out_dir.mkdir(parents=True, exist_ok=True)
                target = out_dir / (path.stem + "_reply." + result["audio_format"])
                target.write_bytes(base64.b64decode(result["audio_base64"]))
                print("  saved   : %s" % target)
        print("\nWhole voice turn: median %.1fs, best %.1fs, worst %.1fs"
              % (statistics.median(totals), min(totals), max(totals)))
        print("Free RAM after: %.1f GB" % free_ram_gb())
    finally:
        if report:
            sys.stdout = sys.__stdout__
            report.close()
            print("\nResults also saved to %s" % args.out)


if __name__ == "__main__":
    main()
