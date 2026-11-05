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

## Privacy notes

- Child audio is never sent anywhere. Speech to text is local.
- `edge-tts` sends only the toy's reply text to Microsoft's service. The reply can repeat words the child said. That is a data flow to a third party, so it is acceptable for prototyping only.
- `edge-tts` is an unofficial endpoint: no SLA, and its terms may not allow commercial use. Do not ship it in a product.

## Consequences

- Voice route `POST /v1/voice` takes raw audio and returns transcript, reply, and base64 mp3.
- If TTS fails, the text reply is still returned.
- LLM streaming with sentence level safety is not built yet. First measure real latency with `scripts/benchmark.py`, then decide.
- RAM: the LLM and Whisper together on 16 GB must be measured before enabling both.
