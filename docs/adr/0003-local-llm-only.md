# ADR 0003: Local LLM only

Status: accepted

## Context

- The product is used by small children. What they say is sensitive data.
- India's DPDP Act and COPPA (if sold abroad) require care and parental consent for children's data.
- Free tiers of hosted LLM APIs often use inputs to improve their models.
- A proposal was to add a cloud mode (Groq or Gemini API) to save RAM.

## Decision

- Use a local model only (Ollama). No child text or audio is sent to a third party.
- Keep a small provider interface in `services/llm.py` (`PROVIDERS`), so another local provider can be added with a config change.
- Do not add a cloud provider until there is a privacy and consent plan.

## Consequences

- Needs free RAM on the machine. Close heavy apps while the model runs.
- Privacy story is simple and strong.
- If a cloud mode is ever added, it needs parental consent, a data processing agreement, and a no-training guarantee first.
