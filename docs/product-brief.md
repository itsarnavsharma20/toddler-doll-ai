# Playmate: Toddler Talking Toy, Product Brief

## Goal
Build a talking toy for toddlers (1 to 5 years).
Shape can be a doll, duck, or any soft toy.
Talks in Hindi and English first. More languages later.

## Core Features
- Listen to the toddler's voice
- Reply in Hindi or English
- Tell rhymes, stories, ABC, numbers
- Safe language only
- Block bad words
- Online mode for now

## Example
Child says: "Twinkle twinkle little star..."
The toy replies with the same rhyme and continues.

## Model Choice
See `docs/adr/0001-llm-choice.md`.

## Architecture
See `docs/architecture.md`.

1. STT: faster-whisper (small), not built yet
2. Input safety check
3. Rhyme database lookup, else LLM
4. Output safety check
5. TTS: free option first (edge-tts or Piper), not built yet

Stack: Python and FastAPI.

## Safety Rules
- Bad words list in English, Hindi (Roman and Devanagari) and Hinglish
- Moderation check on output, not only a word list
- System prompt: friendly toy for a 3 year old, safe and simple words
- If the child says a bad word, redirect gently. Never scold.
- Do not store child audio.

## Content and Model Separation
- Content (rhymes, stories) lives in `data/content/`.
- The model is the LLM brain.
- They update separately.
- Rhymes are played back exactly from content, not generated.

## Languages
- Now: English, Hindi
- Later: French, Spanish, Tamil, Telugu
- Toggle in `config/languages.json`

## OTA (Future)
- The toy checks Wi-Fi for new content.
- Download at night.
- Content and model are updated separately.

## Open Items
- Hardware plan (mic, speaker, board)
- Privacy and consent (India DPDP Act, COPPA if selling abroad)
- Devanagari support in safety lists and rhyme triggers
- Romanized Hindi detection
- Tamil and Telugu approach
- Voice layer: STT, then TTS

## Dev Machine
i7-1260P, 16 GB RAM, Intel Iris Xe (no NVIDIA GPU), limited free disk.
CPU only. Keep models small. Close heavy apps while the model runs.
