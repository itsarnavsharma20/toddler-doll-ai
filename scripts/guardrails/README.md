# Guardrails

One shared script, `guard.py`, checks every tool call from any AI coding tool.

## How it works

- The tool sends the call as JSON on stdin.
- Exit code 0 means allow. Exit code 2 means block, with the reason on stderr.
- Any error blocks the call (fail closed).
- Blocks are logged in `logs/guardrails.log`.

## What it blocks

| Rule | Blocked |
| --- | --- |
| 2 | `git` and `gh` in any form |
| 3 | Database clients, destructive SQL, database files, delete tools and actions |
| 4 | Delete commands and delete functions |
| 5 | Paths outside the project folder, `..`, home and temp folders |
| Secrets | `.env` files (not `.env.example`), key files |
| Hidden code | `python -c`, `node -e`, encoded commands, `iex` |
| Protected | Edits to this folder and to tool hook configs |

Rules 1 and 6 (approval first, plan then go) are enforced by the permission prompts in `.claude/settings.json` and by `AGENTS.md`.

## Unlock for the owner

To change a protected file, the owner creates an empty file named `.guardrails_unlock` in the project root. Delete it when done. Agents cannot create it.

## Wiring other tools

| Tool | Status |
| --- | --- |
| Claude Code | Wired in `.claude/settings.json` |
| Cursor, Codex, Gemini, Antigravity, Grok | Not wired yet. Each needs a small config that calls `guard.py` |

## Limits

Hooks are a safety net, not a perfect wall. A command can be written in ways a pattern check cannot see. The rules in `AGENTS.md` and the approval prompts are the main defense.
