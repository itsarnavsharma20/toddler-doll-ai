# Project Journey: How Kiko Was Built

A version by version story of this project, written so that anyone can follow it, even without a technical background. It records the ideas, the architecture, what we built, what went wrong, what we fixed and what we learned.

## How to read this file

- It is a story, not a manual. For how to run the project, see `README.md`. For the current design, see `docs/architecture.md`. For single decisions, see the decision records in `docs/adr/`.
- The work happened over a few days (4 and 5 November 2026) in a long conversation between the project owner and an AI coding assistant (Claude). The owner made every decision and ran every git command.
- The story is split into three versions by phase of work. If your commit history splits the work in a different way, move the section boundaries to match.
- Numbers (seconds, test counts) come from the actual runs on the owner's laptop. Where something was a guess, the text says so.
- Hindi words are written in English letters here, for example "kahani" (story).

---

## 1. The big idea in plain words

**Kiko** is a talking toy for toddlers (1 to 5 years old). A child says something, and Kiko answers out loud, in Hindi or English.

Kiko should:

- Listen to a toddler's voice.
- Reply in Hindi or English.
- Sing rhymes, tell short stories, say the ABC and count numbers.
- Use only safe, kind, simple language. It must never scold a child.
- Keep working and improving for 4 or 5 years (new content, new languages, better brains), because a one year old will use it for years.

Constraints that shaped every choice:

| Constraint | Why it matters |
| --- | --- |
| Free tools only | No budget for paid AI services |
| Safe for a 3 year old | A child product has no room for mistakes |
| Child data must stay private | Children's voices are sensitive data |
| Small laptop for development | 16 GB RAM, no graphics card, limited disk |
| Hindi and English first | Real families mix both languages |

### The kitchen picture

Think of Kiko as a small kitchen with five helpers:

| Helper | Real name | Job |
| --- | --- | --- |
| Ears | Speech to text (STT) | Turns the child's voice into written words |
| Safety guard | Safety filters | Checks what comes in and what goes out |
| Bookshelf | Content library | Holds rhymes, stories, ABC and counting, word for word |
| Brain | Language model (LLM) | Chats about anything not on the shelf |
| Mouth | Text to speech (TTS) | Turns written words into a spoken voice |

A big lesson of the whole project is: **use the bookshelf whenever possible, and the brain only when needed.** A rhyme must be the same every time, so it is read from the shelf, never invented by the brain.

---

## 2. Words you will meet

| Word | Plain meaning |
| --- | --- |
| LLM (language model) | The "brain". A program that reads text and writes a reply. Ours is Gemma 4 E2B. |
| Ollama | A free program that runs the brain on your own computer, so nothing goes to the internet. |
| Model size ("2B") | How big the brain is. 2B means about 2 billion numbers. Bigger is smarter but slower and needs more memory. |
| Token | A small piece of a word. The brain reads and writes in tokens. More tokens means more time. |
| STT | Speech to text. We use Whisper (the `faster-whisper` version). |
| TTS | Text to speech. We use `edge-tts` for now. |
| RAM | The computer's working memory. When it is full, everything slows down. |
| CPU / GPU | The computer's main chip / its graphics chip. Our laptop has no strong GPU, so everything runs on the CPU. |
| Latency | How long you wait for an answer. |
| Devanagari | The script used to write Hindi. |
| Hinglish / Roman Hindi | Hindi written in English letters ("mujhe kahani sunao"). |
| Fuzzy matching | Matching words even when there are small spelling mistakes. |
| Intent | What the child is asking for (a story, the ABC, counting). |
| Guardrails | Rules and checks that stop the AI assistant, and the toy, from doing risky things. |
| Hook | A small program that runs before every action of an AI tool and can say no. |
| ADR | Architecture Decision Record. A short note saying what was decided and why. |
| Benchmark | A test that measures speed and memory use. |
| API | The "front door" other programs use to talk to our program. |

---

## 3. The three versions at a glance

| | Version 1: Foundation | Version 2: Clean house, smarter text brain | Version 3: Making it real |
| --- | --- | --- | --- |
| Headline | Rules, guardrails, first text chatbot | Professional structure, language aware data, voice code written | Kiko gets a name and a voice, tested with real audio, and made fast |
| Input | Typed text | Typed text (voice code written, untested) | Typed text and real recorded voice |
| Works with | English, some Hindi | English and Hindi (Roman and Devanagari) | Same, plus stories, ABC, counting |
| Typical reply time | About 12 seconds | About 6 seconds | LLM reply about 1.8 seconds, whole voice turn 6 to 14 seconds |
| Biggest problem | Out of memory, Hindi script gaps | Plan could not be saved (guardrail), speed unknown | Slow speech to text, flaky network, wrong gender voice |
| Tests | 44 guardrail, 16 unit | 60 guardrail, 74 unit | 60 guardrail, 135 unit |

---

## 4. Version 0: before any code

### The original brief

The owner started with a written brief:

- A talking doll for ages 1 to 5, in Hindi and English, with rhymes, stories, ABC and numbers.
- Block bad words. Never scold the child.
- Model chosen: Gemma 2 2B. Flow: speech to text, safety check, brain, safety check, text to speech.
- Stack: Python and FastAPI.
- Future: updates over the air (OTA), content kept separate from the model, more languages later (French, Spanish, Tamil, Telugu).
- A rule: every file in the repository stays in English.

### The first review (problems spotted before building)

| Concern | Why it matters |
| --- | --- |
| Gemma 2 2B is weak in Hindi | Hindi is a core requirement |
| Rhymes should not come from the brain | A small brain garbles rhymes. A toddler needs the same rhyme every time. |
| Toddler speech is hard for STT | Small children speak unclearly |
| A 1000 word bad-word list is not enough | Hindi, Hinglish and different spellings slip through |
| "Never scold" versus "this word is not good" | The reply wording needs a decision |
| Privacy law (India's DPDP Act, COPPA abroad) | Children's voice data needs consent and care |
| "Online mode" was unclear | Where does the brain run? |
| No hardware plan | The toy's body was not decided |

### Early decisions

- **Free only.** Search of free models found that a newer Gemma generation (Gemma 4) exists, is free and needs no approval (Apache 2.0 license). We chose **Gemma 4 E2B**, in a compressed (quantized) build of about 4.3 GB, run locally with Ollama.
- **Development machine:** Intel i7-1260P, 16 GB RAM, no NVIDIA graphics, about 40 GB free disk. Everything runs on the CPU.
- **Order of work:** text chat first, voice later.

---

## 5. Version 1: Foundation

### Goal

Set up safe working rules for the AI assistants, then build the smallest chatbot that works.

### Architecture (Version 1)

```
typed text
   |
   v
[ input safety check ]  --bad word-->  gentle redirect
   |
   v
[ rhyme lookup ]  --found-->  exact rhyme text
   |
   v
[ LLM (Gemma via Ollama) ]
   |
   v
[ output safety check ]
   |
   v
reply
```

All code sat flat in the project folder: `app.py`, `pipeline.py`, `brain.py`, `safety.py`, `content.py`, plus `config.json`, `languages.json`, and a `content/` folder with 10 rhymes and a starter list of bad words.

### What we built

- Project documents: a brief, a README, `.gitignore`.
- **One rulebook for every AI tool.** `AGENTS.md` is the single source of rules. `CLAUDE.md` and `GEMINI.md` only point to it. This way Claude, Codex, Cursor, Gemini, Antigravity and Grok all read the same rules.
- **Guardrails** (see below).
- A working text chatbot with safety checks and 10 rhymes (6 English, 4 Hindi in English letters).
- Ollama installed, the model downloaded, and the first real chat working.

### The six hard rules

The owner set six absolute rules for every AI agent:

1. Do nothing (run, install, start) without the owner's permission.
2. Never run git or GitHub commands. The owner runs all of them.
3. Never delete from, or directly touch, a database without instruction.
4. Never delete any file or folder.
5. Never go outside the project folder.
6. Make a plan, get approval, and only then create or change anything.

### How the rules are enforced (two layers)

| Layer | How it works |
| --- | --- |
| Written rules | `AGENTS.md` tells every agent the rules |
| Hooks (a safety net) | `scripts/guardrails/guard.py` is a small program that checks every tool call and blocks anything that breaks a rule |

Details of the hook:

- It blocks git and GitHub commands, delete commands, database tools and destructive SQL, paths outside the project, `.env` secret files, and hidden inline code.
- It protects its own files. Only the owner can unlock edits, by creating an empty file named `.guardrails_unlock` and deleting it afterwards.
- It "fails closed": if the hook itself breaks, the action is blocked.
- Every block is logged in `logs/guardrails.log`.
- Claude Code also asks permission before writing files or running commands.
- Hook formats for Cursor, Codex, Gemini, Antigravity and Grok were researched in their official documents and config files were written. Only Claude Code and Codex are installed on the owner's machine, so the others are untested.

**The guardrail proved itself.** During the work it blocked the assistant from editing its own hook file and from saving a plan file outside the project. The assistant did not look for a way around it, it told the owner and asked.

### Problems faced in Version 1

| Problem | What we saw | Cause | Fix |
| --- | --- | --- | --- |
| Ollama command not found | `ollama` not recognized in the terminal | The terminal had been opened before the install | Restart the terminal or VS Code fully |
| Model would not load | Error 500: "unable to allocate buffer" | Not enough free RAM | Close heavy apps, later lowered the model's memory use (`num_ctx` 2048) |
| Slow, rambling replies | The model printed long "Thinking..." text first | Gemma 4 reasons before answering by default | Turned thinking off (`think: false`) |
| Browser showed "Not Found" | Opening the root address of the app | There is no page at `/`. The test page is `/docs`. | Use `/docs` |
| Hindi looked like garbage | Strange characters in PowerShell | The terminal shows UTF-8 Hindi badly | Display problem only. Use a browser or file to read it. |
| Hindi not recognized from Roman letters | "namaste" got an English reply | Language was detected only from Devanagari script | Planned for Version 2 |
| Emoji in replies | The smiley face in a Hindi reply | The model likes emoji | Planned for Version 2 |
| Safety gap | The bad-word list had only Roman spellings | No Devanagari words | Planned for Version 2 |

### What we learned

- Memory (RAM) is the first limit on a small laptop. Plan for it from day one.
- A terminal that cannot show Hindi does not mean the program is wrong. Check the real data.
- Write the rules first. They paid off many times later.

### State at the end of Version 1

Typed chat worked: bad words got a gentle redirect, rhyme requests got the stored rhyme, everything else went to the brain. Guardrail tests: 44. Unit tests: 16.

---

## 6. Version 2: Cleaner house, smarter text brain

### Goal

Make the project look and work like a professional product, and make the text side smarter in Hindi and English. Also write the voice code.

### The naming and structure discussion

The first structure was flat and the owner found it "clumsy and hard to read". They also pointed out that the package name `doll` did not sound professional. After a naming discussion the package became **`playmate`**, and the project moved to an industry style layout:

```
src/playmate/      all the program code, split into layers
  api/             the front door (web routes)
  core/            settings, languages, text helpers
  pipeline/        the order of steps for one conversation turn
  services/        outside helpers (the brain, ears, mouth)
  safety/          safety filters
  content/         rhymes and fixed phrases
config/            settings and language list
data/<language>/   content per language (one folder each for en and hi)
docs/              brief, architecture, decision records
tests/             unit tests and guardrail tests
scripts/           guardrail hook, benchmark tools
```

The folders `.claude`, `.cursor`, `.codex`, `.gemini`, `.agents`, `.grok` must stay in the project root because each tool looks for its own folder there. They are hidden in the VS Code file list so the project looks tidy.

Rules for the layers: the front door only passes messages along, the pipeline decides the order, and helpers do one job each. Adding a new language means adding a folder under `data/` and switching it on in `config/languages.json`.

### Reviewing an outside improvement proposal

The owner brought a document of proposed fixes (`ARCHITECTURE-FIX.md`). We reviewed every item against the real project and our rules:

| Proposal | Decision | Why |
| --- | --- | --- |
| Hindi rhymes in Devanagari | Adopted | Whisper writes Hindi in Devanagari |
| Both scripts accepted ("twinkle" and its Hindi spelling) | Adopted | Cheap and valuable |
| Embedding search for rhymes (a heavy method) | Deferred | Needs about 2 GB extra and more RAM. Simple fuzzy text matching is enough for a small library. |
| Language folders per language | Adopted, with ISO codes (`en`, `hi`) | Easy to add languages |
| Extra "judge" model to check replies | Deferred | A small model judging itself is weak and doubles the time |
| "This word is not good" reply | Rejected | The owner chose a gentle redirect, never a correction |
| Cloud AI (Groq, Gemini) to save memory | Rejected for now | A child's words would go to a third party, and free tiers may train on that data |
| Versioned API (`/v1/...`) | Adopted | Old toys keep working when new ones appear |
| Admin endpoint to update content | Rejected | Signed content packs are safer (later) |
| `langdetect` library | Rejected | Poor on short and Roman Hindi text |
| Edge TTS | Prototype only | It is an unofficial service, not fit for a commercial product |

The review also corrected the document itself: it said Hindi was weak (the first test was actually good), mentioned an outdated model, and said the bad-word list was English only (the real gap was Devanagari).

### What we built (text side)

| Feature | Plain explanation |
| --- | --- |
| Language list (`languages.json`) | Each language has a code, a name, and settings. New language is a config change. |
| Data per language | `data/en/` and `data/hi/` hold rhymes, safety words and fixed phrases |
| Fuzzy rhyme matching | "twinkel twinkel" still finds Twinkle Twinkle |
| Continue a rhyme | If the child sings the middle of a rhyme, the toy continues from the next line |
| Devanagari safety | Bad words are checked in Roman and Devanagari letters |
| Emoji removal | Replies never contain emoji, which a speaker would read aloud |
| Language detection | Devanagari letters, or common Roman Hindi words, mean Hindi |
| Brain provider interface | The brain can be swapped by a settings change. Only local brains are allowed. |
| Warm-up and keep-alive | Loads the model early so the first answer is not slow |
| `/v1` front door | `/v1/chat`, `/v1/health`, `/v1/languages`, `/v1/warmup`, `/v1/stats` |
| Anonymous counters | Counts which kind of reply was given. Never stores what a child said. |
| Decision records | ADR 0001 (brain choice), 0002 (rhyme search), 0003 (local brain only) |

### The voice code (written, not yet tested with real audio)

- `stt.py` with `faster-whisper` (model "small", compressed, on the CPU). Audio stays in memory and is never written to disk.
- `tts.py` with `edge-tts`, behind a small interface so an offline voice (Piper) can replace it later.
- A voice pipeline and a `/v1/voice` door: audio in, spoken reply out.
- The speech model (about 464 MB) was downloaded into the project's `models/` folder, which is not pushed to git.
- Packages installed: `faster-whisper` and `edge-tts`.
- A benchmark tool to measure speed and memory.
- ADR 0004 (voice stack).

### Architecture (Version 2)

```
voice or text
     |
     v
 [ speech to text ]   (voice only)
     |
     v
 [ language detect ] -> [ input safety ] -> [ rhyme lookup (fuzzy) ]
                                                |        |
                                            found      not found
                                                |        |
                                           exact text   [ LLM ]
                                                |        |
                                                v        v
                                          [ output safety ]
                                                |
                                                v
                                    [ text to speech ] (voice only)
```

### Problems faced in Version 2

| Problem | What we saw | Cause | Fix |
| --- | --- | --- | --- |
| Plan file could not be saved | The assistant's own guardrail blocked a write outside the project | Rule 5 works as designed | The plan was given in chat instead. The rule stayed strict. |
| "namaste" got an English reply | Language said English | Roman Hindi was not detected | Added a small list of common Roman Hindi words |
| Hindi reply looked broken in the terminal | Garbled letters | Terminal font, plus the web request tool misreading UTF-8 | Read it in the browser page `/docs` |
| Two animal words were blocked | "kutta" (dog) and "gadha" (donkey) would redirect a child who names an animal | They were on the bad-word list as insults | Removed them. Animal names must be allowed. |
| Only 4 Hindi rhymes, not 20 | The plan said 20 | Only 4 classic rhymes were known with confidence | Kept 4. More must come from a reviewed source, not from guessing. |
| Free disk shrank | From about 40 GB to about 18 GB | Models and caches | Kept all downloads inside the project `models/` folder and watched the size |
| Slow replies | About 12 seconds per answer | RAM nearly full, laptop power settings (found in Version 3) | See Version 3 |

### What we learned

- A rule that stays strict even when it is inconvenient is worth it.
- Test with small, honest data. Do not claim more content than you really have.
- A heavier technique is not always better. Fuzzy matching on a small library beat embeddings for cost and simplicity.
- Do not send a child's words to outside services.

### State at the end of Version 2

A clean structure, a smart text brain, and voice code that passed fake tests. Guardrail tests: 60. Unit tests: 74. Still no proof that voice works with real audio, and replies were slow.

---

## 7. Version 3: Making it real

### Goal

Give the toy its identity and test it with real recorded voices, and make it fast enough to feel alive.

### Kiko gets a name and a personality

After brainstorming friendly, easy-to-say names, the owner chose **Kiko**, and decided Kiko is **male**.

- The name and gender live in settings (`toy_name`, `toy_gender`), not in code.
- The brain's instructions (prompt) say "You are Kiko, a boy". In Hindi this matters, because words change with gender ("tumhara dost" for a boy, "tumhari dost" for a girl).
- The spoken voice follows the same gender setting.
- The brand name of the product is still undecided. Do a trademark and domain search before deciding.

### The speed detective story

At the start of this version, one answer took **about 12 seconds**. A toddler will not wait that long. We measured, guessed, tested and fixed, one step at a time.

| Step | What we found | Reply time (warm) |
| --- | --- | --- |
| Start | Memory 85 percent used, Windows compressing memory, many apps open | about 12 s (first reply 70 s) |
| Restart the PC, close apps | Freed memory | about 6.5 s |
| Plug in the charger, set "Best Performance" power mode | The laptop had been running slowly to save power. Reading and writing both became 2 to 3 times faster. | about 4.3 s |
| Use `127.0.0.1` instead of `localhost`, and shorten the brain's instructions | On Windows, `localhost` first tries a path that does not exist and waits about 2 seconds before giving up. The prompt was also long (about 150 tokens). | **about 1.8 s** |

A second model, Gemma 3 1B, was tried because it is smaller. It was only a little faster and its Hindi was poor (mixed languages, English translations in brackets, emoji), so **Gemma 4 E2B stayed**.

How we found each clue: the benchmark tool reports where time goes (reading the prompt, writing the reply, loading the model, and "other"). When "other" was a steady 2 seconds for every model, we knew the delay was not the model.

### The hearing (speech to text) detective story

Five recorded clips of the owner were used (`samples/`, not pushed to git):

| Clip | What was said | What Whisper wrote (after tuning) |
| --- | --- | --- |
| 1 | "Hey Kiko, can we learn ABCD?" | Correct |
| 2 | "Hi Kiko, can you tell me a story please?" | Correct |
| 3 | "Hey, can you sing a rhyme with me please?" | Correct |
| 4 | "Kiko, mujhe kahani sunni hai" (Kiko, I want to hear a story) | Close, but "kahani" came out wrong and "Kiko" came out as two words |
| 5 | "Kiko, tumhara naam kya hai, tum kaise ho?" | Close, "tumhara" came out as "tumara" |

What we learned and did:

- Whisper always works on a 30 second window, so a 4 second clip costs about the same as a 10 second clip. Speech to text takes about 4 seconds per clip on this laptop.
- One clip took 37 seconds. Whisper was retrying on bad audio. Turning off the retry ("temperature fallback") brought it to about 6 seconds.
- **Hints help.** Telling Whisper that "Kiko" and words like "kahani" are likely made the name appear correctly. Hints live in `data/<language>/stt_hints.json`.
- Two search settings (beam 1 and beam 5) cost almost the same time, but beam 5 was slightly better, so beam 5 is kept.
- **The confidence number was useless for Hindi.** A clearly wrong sentence scored the same as a correct one. We cannot trust it to catch mistakes yet.
- Whisper asked the internet every time it loaded, and failed when the connection dropped. Now it loads from the disk and only downloads if the model is missing.

### Teaching Kiko to understand requests

Because speech to text makes mistakes, the toy must be forgiving. We built a small "intent" layer:

- A child asks for a **story**, the **ABC**, or **counting**. A list of words and common misspellings (including the ones Whisper actually produced) decides what was asked. Small spelling slips are forgiven.
- "Hey Kiko" and misheard forms of the name are removed before the request is handled.
- The order of steps became: safety, named rhyme, story or ABC or counting, general rhyme request, and only then the brain.
- Real result: clip 4, where Whisper wrote "kahani" wrongly, still played a Hindi story.

New content, written originally for this project and marked for review by a Hindi speaker:

| Content | English | Hindi |
| --- | --- | --- |
| Stories | 2 | 2 |
| ABC | A for Apple to Z for Zebra | Full varnamala (vowels and consonants) |
| Counting | 1 to 10 | 1 to 10 |

All content passes the same safety filter as the brain's replies (checked by tests).

### The speaking (text to speech) detective story

- **Failures:** In the first full test, 3 of 5 spoken replies failed with "The specified network name is no longer available". This was the internet connection dropping, the same kind of failure Hugging Face had shown earlier. Fix: try again up to 2 more times. The code now also reports the reason for a failure.
- **Wrong gender voice:** The owner listened and said a female voice was saying "Mera naam Kiko hai" as a boy. The voices were chosen from the registry by gender. Now Kiko uses a male Hindi voice (`hi-IN-MadhurNeural`) and a male Indian English voice (`en-IN-PrabhatNeural`). The names were checked against the real voice list.
- Speaking speed and pitch can now be tuned in settings.
- **Privacy note:** `edge-tts` sends the toy's reply text (never the child's audio) to Microsoft's service. This is acceptable for a prototype only. A product needs an offline voice.

### The real voice test (five clips, full flow)

| Clip | Asked for | Kiko replied with | Speech to text | Chat | Voice | Total |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ABC | The ABC | 4.2 s | 0.0 s | 10.0 s | 14.2 s |
| 2 | A story | An English story | 4.0 s | 0.0 s | 6.0 s | 10.1 s |
| 3 | A rhyme | An English rhyme | 4.0 s | 0.0 s | 5.2 s | 9.3 s |
| 4 | A story (Hindi) | A Hindi story | 4.4 s | 0.0 s | 8.4 s | 12.8 s |
| 5 | "What is your name?" (Hindi) | An answer from the brain: Kiko, and happy | 4.7 s | 0.8 s | 1.6 s | 7.0 s |

Reading the table:

- Every request was understood and answered correctly.
- Stored content costs 0 seconds of "thinking". Only open questions use the brain (about 1 second).
- The slowest parts now are speech to text (about 4.5 s) and text to speech, which varies from 1.4 to 10 seconds depending on the internet.

### Problems faced in Version 3

| Problem | Cause | Fix or status |
| --- | --- | --- |
| Replies took 12 seconds | Full memory, power saving mode, `localhost` delay, long prompt | Fixed, now about 1.8 s |
| Whisper took 37 seconds on one clip | Retries on bad audio | Retry turned off, now about 6 s |
| Whisper mishears Hindi words | Small model, short unclear clips | Hints, intent spellings, forgiving matching. A bigger model is a later option. |
| Confidence score cannot catch mistakes | Score is similar for right and wrong text | Open |
| Speech model failed to load | It checked the internet each time and the connection dropped | Loads from disk first |
| 3 of 5 spoken replies failed | Connection dropped | Retries, error reasons shown |
| Female voice for a male toy | Voices were fixed | Voices follow the gender setting |
| Hindi unreadable in the terminal | Terminal shaping of Devanagari | Results can be saved to a UTF-8 text file and read in VS Code |
| Voice time unstable (1.4 to 10 s) | Network | Open. Planned fix: prepare the audio of stored content in advance. |

### What we learned in Version 3

- **Measure before guessing.** Two of the biggest wins (power mode and `localhost`) were not where we first looked.
- Power settings and plugging in the charger can change speed by 2 to 3 times.
- Every long instruction costs time on every single answer. Keep prompts short.
- Real recordings found problems that tests with typed text could never find.
- A forgiving matcher plus content on a bookshelf makes the toy feel smart even when hearing is imperfect.
- Network services fail. Retry, show the reason, and prefer offline where possible.

### State at the end of Version 3

Voice works end to end with real recordings, for English and Hindi, in a male voice. Guardrail tests: 60. Unit tests: 135.

---

## 8. Mistakes we made and corrected

Being honest about mistakes is part of the learning.

| Mistake | What happened | Correction |
| --- | --- | --- |
| Misread a screenshot | One clip was called "perfect" when it had small errors | Re-read the text and corrected the claim |
| Promised too much content | The plan said 20 Hindi rhymes. Only 4 were reliable. | Delivered 4 and said so |
| Blocked innocent words | Dog and donkey were on the bad-word list | Removed them |
| Hidden failures | TTS errors were swallowed, so we could not see why voices failed | Errors are now reported |
| Hid a real bug | Whisper required the internet to load a model already on disk | Loads from disk first |
| An old screenshot was compared as new | It had the old column layout | Asked for a new run |
| Guessed a cause | The "localhost" delay was a guess | Confirmed by the benchmark: the gap went to 0.0 s |

---

## 9. Decisions log

| Decision | Status | Why |
| --- | --- | --- |
| Free tools only | Active | No budget |
| Gemma 4 E2B (compressed) through Ollama | Active | Free, local, good Hindi, fits the laptop |
| Local brain only, no cloud | Active | A child's words must not leave the machine |
| Known rhymes and stories come from stored content | Active | Same every time, safe, fast |
| Gentle redirect for bad words | Active | Never scold a child |
| Fuzzy text matching instead of embeddings | Active | Light and enough for a small library |
| Package named `playmate`, character named Kiko, male | Active | Chosen by the owner |
| Brand name | Undecided | Needs trademark and domain checks |
| `edge-tts` for the voice | Prototype only | Unofficial service, not for products |
| Piper for the production voice | Planned | Offline and free |
| Cloud brain | Rejected for now | Privacy |
| Embedding rhyme search | Deferred | Revisit above about 200 items |
| LLM judge for replies | Deferred | Weak and slow on this machine |
| `pyproject.toml` | Declined by the owner | `requirements.txt` is kept |

---

## 10. How the system works today

```
child's voice
     |
     v
[1] Speech to text (Whisper small, hints for Kiko and common words)
     |   unclear? -> Kiko asks the child to say it again
     v
[2] Remove "Hey Kiko" from the start
     v
[3] Detect the language (Hindi letters, Roman Hindi words, or English)
     v
[4] Input safety check -> bad word? gentle redirect, stop
     v
[5] Named rhyme, or part of a rhyme line -> play it (or continue it)
     v
[6] Story, ABC or counting request -> play stored content
     v
[7] General rhyme request -> play a rhyme
     v
[8] Otherwise ask the brain (Gemma 4 E2B)
     v
[9] Output safety check (no bad words, no links, no emoji, short)
     v
[10] Text to speech (male voice for Kiko)
     v
Kiko speaks
```

Example turns:

| The child says | Kiko does |
| --- | --- |
| "Hey Kiko, can we learn ABCD?" | Recites the ABC (stored, no brain) |
| "Kiko, mujhe kahani sunni hai" | Tells a Hindi story (stored) |
| "Twinkle twinkle little star" | Recites the rhyme exactly |
| Sings the middle of Twinkle Twinkle | Continues from the next line |
| "What is your name?" | Asks the brain: "My name is Kiko." |
| A bad word | Says something happy and offers a rhyme |

---

## 11. What is still open and what comes next

### Open problems

| Area | Detail |
| --- | --- |
| Speed | Speech to text about 4.5 s, voice 1.4 to 10 s. A whole turn is 6 to 14 s. Target 3 to 4 s. |
| Hindi hearing | Small model makes mistakes on Hindi words. A larger model needs about 2 GB more memory. |
| Confidence | We cannot yet tell a good transcript from a bad one. |
| Voice | `edge-tts` is not fit for a product. |
| Content | Few Hindi rhymes. All Hindi content needs review by a Hindi speaker. |
| Safety | Starter word lists are mild. They need review and extension, plus a set of tricky test sentences in English, Hindi and Hinglish. |
| Privacy and law | A consent and privacy plan (India DPDP Act, COPPA) is needed before testing with real children. |
| Hardware | Not decided. The software needs about 10 GB of RAM in total (system, brain, hearing). |
| Where the code runs | Toy, home hub or cloud server is not decided. |
| Name | Trademark and domain search for "Kiko". |

### Next steps (suggested order)

1. Prepare the audio of all stored content in advance (rhymes, stories, ABC, counting). Then the voice step costs 0 seconds, works offline and avoids network failures.
2. Speak long replies sentence by sentence so the toy starts talking sooner.
3. Evaluate Piper (offline voice) for Hindi and English.
4. Improve hearing speed and accuracy.
5. Review all Hindi content with a Hindi speaker. Add more rhymes from a reviewed source.
6. Collect more recordings, ideally child voices, with parent consent.
7. Write the privacy and consent plan. Decide the hardware plan.
8. Later: updates over the air (signed content packs), more languages (Tamil, Telugu).

---

## 12. Where things live

| Path | What is there |
| --- | --- |
| `AGENTS.md` | The rules for every AI tool |
| `src/playmate/` | The program |
| `config/settings.json` | Brain, hearing, voice, name, gender |
| `config/languages.json` | Language list and voices |
| `data/en/`, `data/hi/` | Rhymes, stories, ABC and counting, safety words, request words, phrases, hearing hints |
| `docs/architecture.md` | Current design |
| `docs/adr/` | Decision records |
| `docs/project-journey.md` | This file |
| `scripts/guardrails/` | The safety hook for AI tools |
| `scripts/benchmark.py` | Speed and memory test |
| `scripts/voice_test.py` | Runs recordings through the whole voice flow |
| `scripts/download_models.py` | Downloads the speech model |
| `tests/unit/`, `tests/guardrails/` | Automatic tests |
| `samples/`, `reports/`, `models/` | Local only. Not pushed to git (recordings, results, big model files). |

---

## 13. Ten lessons to remember

1. Write the safety rules first, and enforce them with a program, not only with words.
2. Use stored content for anything that must be the same every time. Use the brain only for open chat.
3. Measure before you guess. The real cause was rarely the first suspect.
4. Memory and power settings can matter more than the model you choose.
5. Short instructions make every answer faster.
6. Real recordings reveal what typed tests cannot.
7. Be forgiving about spelling and mishearing. Children are not clear and the ears are small.
8. Keep a child's data on the machine. Treat every outside service as a risk.
9. Networks drop. Retry, report the reason, and prefer offline.
10. Say honestly what is not done, and keep a record of why each decision was made.
