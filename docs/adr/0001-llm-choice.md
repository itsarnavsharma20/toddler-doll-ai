# ADR 0001: LLM choice

Status: accepted

## Context

- The toy needs a small, free model that handles English and Hindi.
- Budget: free models only. No paid APIs for now.
- Dev machine: i7-1260P, 16 GB RAM, no NVIDIA GPU, limited disk.
- The first plan named Gemma 2 2B. A newer free Gemma generation now exists.

## Decision

- Model: `gemma4:e2b-it-qat` (Gemma 4 E2B, quantization aware build, about 4.3 GB).
- Runner: Ollama on the local machine, called over HTTP.
- Settings that matter on CPU: `num_ctx` 2048 and `think` off. Both are in `config/settings.json`.

## Consequences

- Free and runs offline on the dev machine.
- Needs free RAM. Closing heavy apps fixed an allocation failure during setup.
- Hindi output is good in a first test. The script can be Roman or Devanagari, so safety lists must cover both.
- Swapping models only needs a config change.

## Alternatives considered

| Option | Why not now |
| --- | --- |
| Gemma 4 E4B | Heavier on CPU and RAM. Upgrade path if quality is low. |
| Qwen3 (1.7B or 4B) | Backup for Indian languages. |
| SmolLM3 3B | Backup. |
| Hosted paid APIs | Out of budget. |
