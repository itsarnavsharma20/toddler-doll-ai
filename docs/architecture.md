# Architecture

## Chat flow

```
child voice -> STT -> input safety -> rhyme lookup -> LLM -> output safety -> TTS -> toy speaker
                          |               |
                          v               v
                   gentle redirect   exact rhyme text
```

STT and TTS are not built yet. Today the flow starts from text.

## Layers

| Layer | Package | Responsibility |
| --- | --- | --- |
| API | `playmate.api` | HTTP endpoints. Thin. No logic. |
| Pipeline | `playmate.pipeline` | Orders the steps of one conversation turn. |
| Services | `playmate.services` | Talk to outside capabilities: LLM, later STT and TTS. |
| Safety | `playmate.safety` | Input and output filters for child safety. |
| Content | `playmate.content` | Read rhymes and later stories from `data/content/`. |
| Core | `playmate.core` | Paths and configuration loading. |

Dependencies point one way: API, then pipeline, then services, safety, content, then core.

## Data and config

| Folder | Holds |
| --- | --- |
| `config/` | Settings: model, timeouts, language toggles. |
| `data/content/` | Rhymes and later stories. Updated without touching code. |
| `data/safety/` | Blocked words list. |

Content and model are separate so each can be updated on its own (future OTA).

## Rules that shape the design

- Known rhymes are played back exactly from data. The LLM never rewrites them.
- Safety runs on input and on output. Neither can be skipped.
- Model name and language toggles live in config, not in code.
- No child audio is stored.

## Run and test

| Task | Command |
| --- | --- |
| Install | `pip install -r requirements.txt` |
| Run | `uvicorn playmate.api.main:app --app-dir src --reload` |
| Unit tests | `python -m unittest discover -s tests/unit -v` |
| Guardrail tests | `python tests/guardrails/test_guard.py` |
