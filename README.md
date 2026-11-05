# Playmate

A safe, friendly AI companion for toddlers (1 to 5 years), built on free open models.
The toy's character name is **Kiko** (set in `config/settings.json`).
Talks in Hindi and English first. More languages later.

## Features

- Listens and replies in Hindi or English
- Plays rhymes exactly as stored (not generated)
- Chats with a small local LLM
- Safety checks on every input and every output
- Content and model are updated separately

## Chat flow

1. Input safety check
2. Rhyme lookup
3. LLM (if no rhyme matched)
4. Output safety check

Voice (`POST /v1/voice`) adds speech to text before this flow and text to speech after it.

## Stack

| Part | Choice |
| --- | --- |
| Backend | Python, FastAPI |
| LLM | Gemma 4 E2B (`gemma4:e2b-it-qat`) via Ollama, local, CPU |
| STT | faster-whisper (local, CPU) |
| TTS | edge-tts (prototype only), Piper planned for production |

## Quick start

Prerequisites: Python 3.10 and [Ollama](https://ollama.com) with the model pulled.

```
ollama pull gemma4:e2b-it-qat
pip install -r requirements.txt
uvicorn playmate.api.main:app --app-dir src --reload
```

Open http://127.0.0.1:8000/docs and try `POST /chat`.

Close heavy apps first. The model needs free RAM.

## Tests

```
python -m unittest discover -s tests/unit -v
python tests/guardrails/test_guard.py
```

## Project layout

```
src/playmate/    application code (api, core, pipeline, services, safety, content)
config/          settings and language toggles
data/<lang>/    rhymes, safety words and toy phrases, one folder per language (en, hi)
docs/            product brief, architecture, decision records
tests/           unit and guardrail tests
scripts/         guardrail scripts shared by all AI coding tools
```

## Docs

- [docs/product-brief.md](docs/product-brief.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/adr/0001-llm-choice.md](docs/adr/0001-llm-choice.md)
- [AGENTS.md](AGENTS.md): rules shared by all AI coding tools. [CLAUDE.md](CLAUDE.md) and [GEMINI.md](GEMINI.md) point to it.

## Status

Text chat works end to end. The voice route is built and unit tested with fakes. It has not been run with a real microphone clip yet. More content is next.
