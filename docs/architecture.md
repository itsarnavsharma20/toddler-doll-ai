# Architecture

## Chat flow

```
text -> language detect -> input safety -> rhyme lookup -> LLM -> output safety -> reply
                                |               |
                                v               v
                         gentle redirect   exact rhyme text (full or continued)
```

Voice flow (`POST /v1/voice`):

```
audio -> speech to text -> (low confidence? ask again) -> chat flow above -> text to speech -> audio
```

Child audio stays in memory and is never written to disk.

## Layers

| Layer | Package | Responsibility |
| --- | --- | --- |
| API | `playmate.api` | HTTP endpoints. Thin. No logic. |
| Pipeline | `playmate.pipeline` | Orders the steps of one conversation turn. |
| Services | `playmate.services` | Outside capabilities: LLM now, speech to text and text to speech later. |
| Safety | `playmate.safety` | Input and output filters for child safety. |
| Content | `playmate.content` | Rhyme lookup and fixed toy phrases from `data/`. |
| Core | `playmate.core` | Paths, config, language registry, text helpers, anonymous counters. |

Dependencies point one way: API, pipeline, services / safety / content, core.

## Data and config

| Path | Holds |
| --- | --- |
| `config/settings.json` | LLM model, timeouts, default language. |
| `config/languages.json` | ISO keyed registry: name, prompt name, enabled, STT language, TTS voice. |
| `data/<lang>/rhymes.json` | Rhymes. Triggers in Roman and Devanagari. |
| `data/<lang>/safety.json` | Blocked words for that language. All lists are merged at runtime. |
| `data/<lang>/messages.json` | Fixed toy phrases: redirect, fallback, not heard, model down. |

Add a language: create `data/<code>/`, add its files, set `enabled` to true in `config/languages.json`.

Content and model are separate so each can be updated on its own (future OTA).

## API

| Route | Purpose |
| --- | --- |
| `POST /v1/chat` | `{text, language?}` returns `{reply, language, source}`. `/chat` is an old alias. |
| `POST /v1/voice` | Raw audio body, optional `?language=`. Returns `{transcript, reply, language, source, audio_base64, audio_format}`. |
| `GET /v1/health` | Service and LLM reachability. |
| `GET /v1/languages` | Registry with enabled flags. |
| `POST /v1/warmup` | Load the model into memory. |
| `GET /v1/stats` | Anonymous counts by reply source. No child text. |

`source` values: `empty`, `safety_input`, `rhyme:<id>`, `rhyme:<id>:continue`, `llm`, `fallback`, `low_confidence` (voice only).

## Rules that shape the design

- Known rhymes are played back exactly from data. The LLM never rewrites them.
- Safety runs on input and on output. Neither can be skipped. Lists cover Roman and Devanagari.
- Bad words get a gentle redirect, never a scolding.
- Model name and language toggles live in config, not in code.
- No child audio or text is stored. Metrics are counters only.
- Local LLM only (ADR 0003).

## Run and test

| Task | Command |
| --- | --- |
| Install | `pip install -r requirements.txt` |
| Run | `uvicorn playmate.api.main:app --app-dir src --reload` |
| Unit tests | `python -m unittest discover -s tests/unit -v` |
| Guardrail tests | `python tests/guardrails/test_guard.py` |

## Decision records

- [0001 LLM choice](adr/0001-llm-choice.md)
- [0002 Rhyme search](adr/0002-rhyme-search.md)
- [0003 Local LLM only](adr/0003-local-llm-only.md)
- [0004 Voice stack](adr/0004-voice-stack.md)
