# ADR 0004: Voice stack

Status: accepted for prototype. Text to speech must be revisited before launch.

## Context

- The toy needs to hear a child (speech to text) and speak back (text to speech).
- Budget: free tools only. Dev machine: CPU only, 16 GB RAM, limited disk.
- The child's audio is the most sensitive data in the product.

## Decision

| Part | Choice | Notes |
| --- | --- | --- |
| Speech to text | faster-whisper, model `small`, int8, CPU | Local. Audio stays in memory (`BytesIO`) and is never written to disk. Model files go to `models/whisper` (git ignored). |
| Language detection (voice) | Whisper's own detection | Detected language not enabled in config means a second pass in the default language. |
| Low confidence | Mean `avg_logprob` below -1.0 or `no_speech_prob` above 0.6 | The toy asks the child to say it again. Values are in `config/settings.json` and must be tuned on real child audio. |
| Text to speech | `edge-tts` behind a provider interface | Prototype only. |
| Production TTS | Piper (offline) is the candidate | Needs a Hindi and an English voice check. |

## Measurements that shaped this (dev laptop, 2026-11-05)

- Laptop power mode matters a lot. "Best Performance" with the charger plugged in made the LLM and Whisper about 2 to 3 times faster.
- Whisper pads every clip to a 30 second window, so a 4 second clip costs about the same as a 10 second clip.
- A clear Hindi sentence ("Kiko, mujhe kahani sunni hai") was heard wrongly by Whisper small and still marked confident. The name and "kahani" were wrong.
- Every LLM call had about 2 seconds outside Ollama's own timing. The URL now uses `127.0.0.1` instead of `localhost` (a known Windows IPv6 delay). Verify with the "other" column of `scripts/benchmark.py`.

## STT tuning (in `config/settings.json` and `data/<lang>/stt_hints.json`)

- Hotwords and an initial prompt per language bias Whisper toward the toy's name and common requests.
- `temperature` 0.0 and `condition_on_previous_text` false: one pass, no slow retries or loops.
- `beam_size` 5 for accuracy. Compare with `--beam 1` in the benchmark.
- Confidence thresholds are still loose. Use the `logprob` and `no_speech` columns of the benchmark on real clips to set them.
- A bigger or Hindi tuned model (for example `large-v3-turbo`) is the next step if Hindi stays weak. It costs about 2 GB RAM.

## Privacy notes

- Child audio is never sent anywhere. Speech to text is local.
- `edge-tts` sends only the toy's reply text to Microsoft's service. The reply can repeat words the child said. That is a data flow to a third party, so it is acceptable for prototyping only.
- `edge-tts` is an unofficial endpoint: no SLA, and its terms may not allow commercial use. Do not ship it in a product.

## Consequences

- Voice route `POST /v1/voice` takes raw audio and returns transcript, reply, and base64 mp3.
- If TTS fails, the text reply is still returned.
- LLM streaming with sentence level safety is not built yet. First measure real latency with `scripts/benchmark.py`, then decide.
- RAM: the LLM and Whisper together on 16 GB must be measured before enabling both.
