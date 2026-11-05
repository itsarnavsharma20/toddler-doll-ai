# ADR 0002: Rhyme search

Status: accepted

## Context

- Toddlers speak unclearly. Speech to text may give typos or Devanagari spellings of English names ("ट्विंकल").
- The brief's example: the child says the first words of a rhyme and the toy continues it.
- A proposal was to use sentence embeddings (multilingual MiniLM, threshold 0.75).
- Embeddings need torch (about 2 GB or more) and extra RAM next to the LLM on a 16 GB machine.
- Rhyme lookup is name and line matching, not meaning matching.

## Decision

- Fuzzy text matching with the Python standard library (`difflib`). No new dependency.
- Texts are normalized (Devanagari safe) before matching.
- Order: rhyme name (trigger) plays the whole rhyme. Part of a line plays the rest of the rhyme from the next line. A general request ("sing a song") plays a rhyme in the child's language.
- Triggers hold Roman and Devanagari spellings per rhyme.
- Thresholds are constants in `content/rhymes.py` and covered by unit tests.

## Consequences

- Light and fast. Works offline.
- It matches spelling, not meaning. "The song with the star" will not match.
- Revisit embeddings when the library passes about 200 items, or when real STT output shows many misses. Keep `find_rhyme` as the single entry point so the engine can be swapped.
