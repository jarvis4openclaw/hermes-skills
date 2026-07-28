---
name: creative-ideation
title: Creative Ideation — Routed Library of Creative Methods
description: "Generate ideas via named methods from creative practice."
version: 2.2.0
author: SHL0MS
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Creative, Ideation, Brainstorming, Methods, Inspiration]
    category: creative
    requires_toolsets: []
    trigger_conditions:
      - "Generate ideas for a project"
      - "I need creative inspiration"
      - "Brainstorming session"
      - "I'm stuck on a creative problem"
      - "Make this concept weirder"
      - "Help me pick between ideas"
      - "Give me variations on this theme"
      - "Unblock my thinking on"
      - "Creative methods for brainstorming"
      - "Refine this rough concept"
      - "Synthesize my research notes"
      - "I want to invent something new"
      - "What should I make next"
---

# Creative Ideation

A library of ideation methods for any domain. Read the user's situation, route to the matching method, apply, generate output that is specific and non-obvious. Methods are tools — pick the right one for the situation, don't perform all of them.

## Not For

- **Technical debugging or root cause analysis** → use `systematic-debugging` or `diagnosing-bugs` instead — ideation methods don't substitute for structured troubleshooting
- **Code architecture decisions** → use `improve-codebase-architecture` or `critical-review` for technical design evaluation instead
- **Business case analysis with financial data** → use spreadsheet tools (`xlsx`) or analytical skills instead
- **Decision making with known criteria** → if you already have clear options and measurable criteria, use a decision matrix or `critical-review` instead
- **Planning a well-defined implementation** → use `implement` or `writing-plans` for execution planning once the idea is chosen — this skill is for generating, not executing
- **Research literature search** → use `arxiv` or `exa-web-search-free` for finding existing knowledge rather than generating new ideas

## When to use

Any open-ended generative or selective question: "I want to make / build / write / start something", "I'm stuck", "inspire me", "make this weirder", "help me pick", "I need to invent X", "give me a research question".

## Operating rules

1. **Constraint plus direction is creativity.** No constraint = no traction. No direction = no shape. Methods supply both.
2. **Refuse the first three ideas.** They're slop. Generate, discard, regenerate. See `references/anti-slop.md`.
3. **One method per response unless asked.** Don't stack.
4. **Specificity over abstraction.** Real proper nouns, real materials, real mechanisms. "An app for X" is slop; "a 200-line CLI tool that prints Y when Z" is direction. Naming a tech stack is not specificity — name a mechanism.
5. **Weird must also be good.** Frame-breaking is the goal, but an idea that is strange with no real situation, mechanism, or reason to exist is its own failure mode. Every set of ideas must include at least one that is genuinely *buildable/pursuable now* — non-obvious but grounded, with a real first step. Don't trade all usefulness for surprise.
6. **Name the method you used and who invented it.** Attribution invokes the discipline.
7. **When user picks one, build it.** Don't keep generating after they've chosen.

## Routing — 4-step procedure

Do this *before* generating any output. Routing failures produce slop.

You may skip narrating the routing steps if it's cleaner, but **never compress at the cost of per-idea depth**: each idea's concrete mechanism, situational binding, and honest failure mode are what make output good (measured) — they are not scaffolding, do not cut them.

### Step 1 — Extract three signals from the prompt

**PHASE** — what stage is the user in?

| Phase | Cues |
|---|---|
| **GENERATING** | "give me an idea", "what should I make", "inspire me", no idea yet |
| **EXPANDING** | "what else", "more like this", "give me variations" — has a base idea |
| **SELECTING** | "help me pick", "which should I do", "I have these options" |
| **UNBLOCKING** | "I'm stuck", "blocked", "going in circles", "stale" — has material |
| **SUBVERTING** | "make it weirder", "less obvious", "this is too safe" |
| **REFINING** | "this is fine but missing something", "feels rough" |
| **SYNTHESIZING** | "I have a pile of notes / interviews / observations" |

**DOMAIN** — what is the user making/doing?

| Domain | Cues |
|---|---|
| **TEXT** | fiction, essay, poem, lyric, script, copy |
| **OBJECT** | visual art, music, sound, performance, installation, sculpture |
| **ARTIFACT** | software, hardware, mechanism, device |
| **SYSTEM** | org, civic, institution, ecology, community |
| **SELF** | life decision, career, personal practice |
| **RESEARCH** | paper, thesis, scholarly question |
| **PRODUCT** | business, market, service |

**SPECIFICITY** — how much constraint is in the prompt?

| Level | Cues |
|---|---|
| **NONE** | "I'm bored", "inspire me" — no domain, no project |
| **DOMAIN** | "I want to write something" — knows the field, no project |
| **PROJECT** | "I'm working on this specific X" |
| **PROBLEM** | "I have this specific friction within X" |

### Step 2 — Apply overrides (highest priority, fire first)

Override rules beat the routing table:

- **Mood signal** — user says "weird", "strange", "surprising", "less obvious", "more interesting" → `references/methods/lateral-provocations.md` or `references/methods/pataphysics.md`, regardless of domain.
- **User names a method** — use it.
- **User asks for a method recommendation** ("which method") → surface 2–3 candidates with one-line each, ask which to apply. Don't silently default.
- **High-slop terrain** — "AI ideas", "startup ideas", "habit tracker", "productivity / wellness / fitness / food / travel app" → force `references/methods/lateral-provocations.md` or `references/methods/pataphysics.md` over the obvious method. Refuse the first **5** ideas, not 3.

### Step 3 — Route by phase first, then domain

**By phase (applies regardless of domain):**

| Phase | Default route |
|---|---|
| GENERATING + SPECIFICITY=NONE | `references/full-prompt-library.md` **General** section (constraint dispatch) |
| GENERATING + DOMAIN known | route by domain (next table) |
| EXPANDING | `references/methods/scamper.md` |
| SELECTING | `references/methods/premortem-and-inversion.md` (or `references/methods/compression-progress.md` for upside) |
| UNBLOCKING | `references/methods/oblique-strategies.md` |
| SUBVERTING | `references/methods/lateral-provocations.md` (fallback `references/methods/pataphysics.md`) |
| REFINING (text) | `references/methods/defamiliarization.md` |
| REFINING (other) | `references/methods/creative-discipline.md` (Tharp's spine) |
| SYNTHESIZING | `references/methods/affinity-diagrams.md` |
| Volume needed fast | `references/methods/volume-generation.md` |

**By domain (when GENERATING with DOMAIN known):**

| Domain | Default route |
|---|---|
| TEXT — formal / poetry | `references/methods/oulipo.md` |
| TEXT — narrative | `references/methods/story-skeletons.md` |
| TEXT — has source material to remix | `references/methods/chance-and-remix.md` |
| OBJECT (music, visual, performance) | `references/methods/oblique-strategies.md` |
| OBJECT — physical maker / wants a starting constraint | `references/full-prompt-library.md` **Physical / object** section |
| ARTIFACT — wants a starting constraint | `references/full-prompt-library.md` **Software / artifact** section |
| ARTIFACT — engineering invention with parameter conflict | `references/methods/triz-principles.md` |
| ARTIFACT — software architecture | `references/methods/pattern-languages.md` |
| ARTIFACT — has natural-system analog | `references/methods/biomimicry.md` |
| ARTIFACT — accumulated assumptions to question | `references/methods/first-principles.md` |
| SYSTEM (civic, org, institutional) | `references/methods/leverage-points.md` |
| SYSTEM — collective / participatory | `references/full-prompt-library.md` **Social / collective** section |
| SELF (life, career, what-to-study) | `references/methods/derive-and-mapping.md` |
| RESEARCH — picking a question | `references/methods/compression-progress.md` |
| RESEARCH — attacking a known problem | `references/methods/polya.md` |
| PRODUCT (business, service) | `references/methods/jobs-to-be-done.md` |
| Need to break a frame / find analogy | `references/methods/analogy-and-blending.md` |

### Step 4 — Handle ambiguity and contradiction

- **Multiple paths plausible** → pick the one closest to the user's actual phrasing. Don't pick the most interesting method to seem sophisticated.
- **Genuinely ambiguous** → ask ONE clarifying question, don't silently guess. Examples: *"Are you generating ideas or picking between ones you have?"* / *"Is this for fiction, essay, or something else?"*
- **Signals contradict** (e.g., "weird startup ideas" → product domain + weird mood) → **stack two methods explicitly**. State what you're doing: *"Using `jobs-to-be-done` for the product framing + `lateral-provocations` to break the obvious shape."*
- **No match** → constraint dispatch (`references/full-prompt-library.md`) is the safe fallback.
- **Same question asked again** → switch methods. Variation in method = variation in idea distribution.

### Anti-default check (run before generating)

- About to write "Here are 5 ideas:" or a bare numbered list? → STOP. Pick a method first.
- About to default to generic LLM-mode brainstorming? → STOP. Pick a path above.
- Output looks like what an unrouted LLM would produce? → routing failed, redo.

The default LLM mode is exactly what this skill exists to displace. If you generate without routing, you've defeated the skill.

For deeper edge cases (mood signals, stacking, anti-patterns) see `references/heuristics.md`.

## Output format

For the constraint-dispatch default path:

```
## Constraint: [Name] — from [Source]
> [The constraint, one sentence]

### Ideas

1. **[One-line pitch]**
   [2-3 sentences — what specifically is made, why it's interesting]
   ⏱ [weekend/week/month]  •  🔧 [stack/medium/materials]

2. ...
3. ...
```

For other methods, use the format the method specifies (TRIZ produces a contradiction analysis; OuLiPo produces constrained text; Oblique Strategies produces a single applied card → next move). Don't force every method into the constraint template.

**Every idea set, regardless of method:**
- Name the method used. On slop terrain, name the obvious ideas you refused.
- Give each idea its concrete mechanism and its honest failure mode / tradeoff / who-it's-for. This depth is what makes ideas land — measured, not decorative.
- Mark at least one idea as the **grounded** one — buildable/pursuable now, non-obvious but with a real first step. The others can run further toward the strange; this one has to be genuinely doable. Don't let the whole set be weird-but-impractical.

## File map

- `references/full-prompt-library.md` — constraint library, sectioned by domain (General, Software, Physical, Social, Lists). Default path for SPECIFICITY=NONE.
- `references/method-catalog.md` — one-line summary + when-to-use per method
- `references/heuristics.md` — extended decision tree for edge cases
- `references/anti-slop.md` — anti-slop rules; apply to every output
- `references/exercises.md` — time-boxed exercises (5min / 30min / 1hr / day / week)
- `references/methods/` — 22 named methods, one file each, load only the one you're using

## Attribution

Constraint-dispatch core adapted from [wttdotm.com/prompts.html](https://wttdotm.com/prompts.html). Methods drawn from primary sources cited in each method file.

## Pitfalls

1. **Routing failure produces generic slop** — The most common failure mode is skipping the routing step and defaulting to LLM-mode brainstorming (5 numbered ideas with no method, no depth, no mechanism). If the output looks like what an unrouted LLM would produce, the routing was skipped — redo with a named method. See "Anti-default check" above.

2. **Stacking too many methods in one response** — Operating rule #3 says one method per response unless asked. Stacking multiple methods without being asked overloads the user with incompatible output formats and dilutes each method's value.

3. **Refusing only 3 ideas on slop terrain** — In high-slop terrain (AI ideas, startup ideas, habit trackers), the override rules require refusing the first **5** ideas, not 3. The first 3 are almost always derivative — the 4th and 5th refusals are where genuinely non-obvious ideas start.

4. **No grounded idea in the set** — Every idea set must include at least one grounded (buildable/pursuable now) idea. If all ideas are weird but impractical, the output is useless for action. The grounded idea doesn't have to be the most exciting — it just needs a real first step.

5. **Forcing every method into the constraint template** — The constraint-dispatch output format (## Constraint → > constraint → numbered ideas with ⏱ 🔧) is for the default SPECIFICITY=NONE path only. Other methods (TRIZ, OuLiPo, Oblique Strategies) have their own formats. Don't force-fit them.

6. **Missing the reference file dependency** — Many methods reference files under `references/methods/`. Each method file contains crucial detail not reproduced in the main SKILL.md. Skipping the file load means skipping critical method-specific instructions.

7. **Guessing instead of asking** — Step 4 of routing says "ask ONE clarifying question" when genuinely ambiguous. Silently guessing the wrong phase or domain wastes the entire response. A single question costs one turn but prevents an entire reroute.

8. **Reusing the same method for repeated questions** — When the user asks the same question again, switching methods is required by Step 4. Variation in method = variation in idea distribution. Repeating the same method will produce ideas clustered in the same region of possibility space.

9. **Claiming attribution without naming the source** — Operating rule #6 says "name the method you used and who invented it." Basic citation (e.g., "SCAMPER, from Bob Eberle") invokes the discipline and signals the skill was actually applied, not just guessed.

10. **Letting the user's high-slopeness overwhelm the process** — When a user says "AI startup ideas" or "app ideas," the override rules force specific reference files regardless of the user's plain-language prompt. Following the user's surface request without applying overrides is a routing failure.
