# Toddler Talking Doll

AI brain for a talking toy for toddlers (1 to 5 years). Talks in Hindi and English first. More languages later.

This file is the single source of truth for all AI coding tools (Claude Code, Codex, Cursor, Antigravity, Gemini, Grok and others). Tool-specific files only point here. Do not copy rules into them.

Full details: see `docs/product-brief.md` and `docs/architecture.md`.

## Hard Rules (Guardrails)

These rules are absolute. They apply to every agent and every sub-agent. Hooks enforce them as a second layer, but do not rely on the hooks. Follow the rules yourself.

1. **Approval first.** Do not run, execute, install, or start anything without the owner's permission. Always ask first.
2. **No git or GitHub commands. Ever.** Do not run `git` or `gh` in any form (add, commit, push, pull, status, anything). The owner runs all of them. If any agent tries, stop it.
3. **No database access.** Never run a delete operation on any database. Never touch a database directly unless the owner explicitly tells you to.
4. **No deleting.** Never delete any file or folder, by any method.
5. **Stay inside this folder.** Never read, write, or run anything outside this project folder. If you need something from outside, ask the owner.
6. **Plan, then approval, then go.** Do not create or change anything until the owner has seen the plan and approved it with a clear go. Until then, only read and discuss.
7. **Always ask.** If you are unsure or need anything, ask the owner. Do not guess.

When a hook blocks an action, do not look for a way around it. Tell the owner what was blocked and why, and ask.

## Current Decisions

- LLM: `gemma4:e2b-it-qat` (Gemma 4 E2B, free, Apache 2.0) via local Ollama on CPU. Upgrade path: E4B. See `docs/adr/0001-llm-choice.md`.
- Package name: `playmate` (under `src/`).
- Toy character name: Kiko (`toy_name` in `config/settings.json`). The brand name is not decided. Do not rename the package or repo yet.
- Local LLM only. No cloud LLM or cloud speech service receives child data. See `docs/adr/0003-local-llm-only.md`.
- Rhyme search is fuzzy text matching, not embeddings. See `docs/adr/0002-rhyme-search.md`.
- Bad word reply is a gentle redirect, never a correction.
- STT: `faster-whisper` small, int8, CPU. Model files live in `models/whisper` (git ignored).
- TTS: `edge-tts` for prototype only (unofficial service, not for production). Production candidate: Piper. See `docs/adr/0004-voice-stack.md`.
- Backend: Python 3.10 + FastAPI.
- Budget: free models and free tools only. Do not add paid services.
- Build order: text chat first, voice layer after.

## Planned Structure

```
src/playmate/
  api/main.py            FastAPI app (thin, calls the pipeline): /v1/chat, /v1/health, /v1/languages, /v1/warmup, /v1/stats
  core/config.py         paths and config loading
  core/languages.py      language registry and text language detection
  core/text.py           text helpers (normalize, strip emoji), Devanagari safe
  core/metrics.py        anonymous counters (reply source only)
  pipeline/chat.py       chat flow: input safety, rhyme lookup, LLM, output safety
  services/llm.py        LLM provider interface, local Ollama provider
  pipeline/voice.py      voice flow: speech to text, chat flow, text to speech
  services/stt.py        speech to text (faster-whisper, local, audio never stored)
  services/tts.py        text to speech (edge-tts for prototype only, provider interface)
  safety/filters.py      input and output safety filters
  content/rhymes.py      fuzzy rhyme lookup, continue from a line
  content/messages.py    fixed toy phrases per language
config/                  settings.json (model, default language), languages.json (ISO keyed registry)
data/<lang>/             one folder per ISO code (en, hi): rhymes.json, safety.json, messages.json
                         add a language = new folder + enabled in config/languages.json
docs/                    product-brief.md, architecture.md, adr/
tests/unit/              unit tests
tests/guardrails/        guardrail tests
scripts/guardrails/      shared guardrail scripts (used by every tool's hooks)
```

## Rules

### Language
- Every file in the repo must be in English. Code, comments, docs, commit messages.
- One exception: content files under `data/<lang>/` hold the language they are for (for example Devanagari Hindi rhymes, safety words and toy phrases). Code never contains non-English text.
- Language codes are ISO (`en`, `hi`). Never use language names as keys in code or data.
- Chat replies to the owner are in Hinglish (see Communication).

### Safety (child product, highest priority)
- Output must be safe for a 3 year old. Simple, kind words only.
- Run a safety check on user input and on model output. Never skip either.
- Never scold the child. Redirect gently.
- Never store raw child audio. Process and discard.
- Never log personal data about the child.
- Do not weaken or bypass safety checks to make a test pass.

### Content
- Rhymes, stories, ABC, numbers come from the content database, played back exactly. Do not let the LLM rewrite known rhymes.
- The LLM is for open-ended chat only.
- Content and model stay separate so each can be updated alone.

### Code
- Keep it simple. Small functions. No extra abstraction.
- Model name and language toggles come from config, never hardcoded in logic.
- Add or update tests for any change to `safety.py`.
- Do not add dependencies without saying why.

### Secrets
- Never commit API keys or tokens. Use `.env` (git ignored).
- Keep an `.env.example` with names only, no values.

### Disk and resources
- The dev laptop has little free disk (about 40 GB) and no NVIDIA GPU.
- Keep downloaded models in one folder. Keep the total under 10 GB.
- Do not download large models without asking first.

## Communication

- Reply in Hinglish (Hindi + English mix) in chat.
- Short points, bullets, tables. No long paragraphs.
- Simple words. No extra background.
- Do not use em-dashes. Use a comma or a period.

## Guardrails and Hooks

- Hook logic lives in one plain script: `scripts/guardrails/guard.py`.
- Each tool's own config (for example `.claude/settings.json`, `.cursor/`, `.codex/`) only calls that script.
- Rule changes go in this file. Check logic changes go in the script.
- Agents must not edit the guardrail files. They are protected. The owner unlocks them by creating an empty file named `.guardrails_unlock` in the project root, and deletes it after.
- Blocked actions are logged in `logs/guardrails.log` (git ignored).
- Wired so far: Claude Code (`.claude/settings.json`). Other tools still need their config wired to `guard.py`.

## Commands

Ask the owner before running any of these.

| Task | Command |
| --- | --- |
| Install | `pip install -r requirements.txt` |
| Run app | `uvicorn playmate.api.main:app --app-dir src --reload` |
| Unit tests | `python -m unittest discover -s tests/unit -v` |
| Guardrail tests | `python tests/guardrails/test_guard.py` |
| Benchmark (speed, RAM) | `python scripts/benchmark.py [--audio clip.wav]` |
