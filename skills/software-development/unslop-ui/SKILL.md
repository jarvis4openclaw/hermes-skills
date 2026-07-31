---
name: unslop-ui
description: >-
  Strips the cues that make a website read as AI-generated and forces a deliberate,
  project-specific design choice instead of the model's default. It does not impose a
  look or hand you taste. It removes tells (default shadcn/Tailwind, AI-purple
  gradients, gradient heading text, unprompted neon glow, emoji-as-icons, the centered
  hero plus three feature cards) AND the newer cream-plus-serif-plus-sage "tasteful
  default" that trading one default for another creates. Grounded in a 47-subreddit,
  3.2M-post Reddit analysis of what people flag as AI slop. Use whenever building,
  styling, reviewing, refactoring, or auditing any website, landing page, web app UI,
  dashboard, or front-end component, especially when the user wants a site to look
  custom or human rather than AI-generated, or mentions AI slop, looks AI-made,
  generic, vibe-coded, Tailwind, or shadcn. Trigger even if they never say vibe-coded.
version: 1.0.0
metadata:
  hermes:
    tags: [ai-slop, web-design, frontend, audit, unslop]
    trigger_conditions:
      - "this site looks AI-generated"
      - "de-slop this UI / landing page"
      - "make this website look human"
      - "vibe-coded design"
      - "too generic / looks like a template"
      - "audit a website for AI tells"
      - "make it not look AI-made"
      - "stop using the default Tailwind/shadcn look"
      - "cream serif sage design is a tell"
      - "review this frontend before shipping"
---
# unslop-ui
Read this first, because the most common misunderstanding sinks the whole thing.
**This skill does not give you a good design, and it does not have a preferred look.**
It removes the specific cues that make a site read as AI-generated, and it forces a deliberate, project-specific choice where the model would otherwise reach for its default. Taste, brand, and layout judgment are still yours. A guardrail is not a designer.

## When to Use

- User asks to make a site/UI "not look AI" or "de-slop this landing page."
- Auditing a website or front-end for AI tells before shipping.
- Building any UI where the brief is missing — to force a deliberate design decision instead of the model default.
- Reviewing whether a new "tasteful default" (cream + serif + sage) is just traded slop.
- Running the scanner (`scripts/devibe_scan.py`) in CI as a gate.

## Not For

- Designing from scratch with no reference → use `claude-design` / `design-an-interface` / `popular-web-designs` to generate concepts first; this skill audits and unslops, it does not generate.
- Stripping AI tells from code logic → use `unslop-code` instead.
- Rewriting copy/prose to sound human → use `unslop-text` / `no-ai-slop` instead.
- Accessibility or UX correctness reviews → use the appropriate UX review skill instead.
- Enforcing a specific brand palette → that is a deliberate choice, not slop; `unslop-ignore` it.

## The trap to avoid (this is the whole point)
The failure mode of every anti-slop effort is replacing one default look with another.
The 2024 tell was the purple gradient on a dark hero. The 2026 tell is a warm
cream background with a serif display font (Instrument Serif, Fraunces) and a sage or
forest green accent, which is the current Claude/Anthropic house style. Swapping the
first for the second is not unslopping. It just resets the clock, and people clock it
just as fast.
So this skill never prescribes a palette, a font, or a layout. Prescribing one is how
you become next year's slop. What it does instead: detect the defaults (old AND new),
and require that any replacement be a specific choice the user or project actually made,
not the model's next-most-likely guess. The only universal rule here is "make a
deliberate choice and be able to say why," which is the one thing a default never is.
If the user genuinely wants purple, neon, a serif, or a cream background as a real brand
decision, that is not slop and the skill leaves it alone. A tell is an *unspecified
default*, not a banned color. Honor `unslop-ignore` (see Audit mode) for anything chosen
on purpose.
## How this differs from the built-in frontend-design skill
Claude already ships a frontend-design skill, and it is good, but it produces the cream
+ serif + green house look that this skill now flags as a tell. unslop-ui is
complementary and adds three things that one does not: a deterministic scanner you can
run in CI (exit code gates a build), a data-grounded ranking so effort goes where real
complaints are, and an explicit check against the new "tasteful default" so you do not
launder slop into a different slop. Use both. Let the design skill build; let this one
keep it honest.
## Mode 1: Build (the important one)
Most "looks AI" outcomes are a specification problem, not a styling problem. An
unspecified prompt gets the median of the training data, and everyone's median is
identical. So before generating any UI, establish the brief. Either pull it from the
user, or if they have not given one, state the choices you are making and why, then
proceed. Do not silently fall back to defaults.
Establish, concretely:
- **A reference.** One real site, screenshot, brand, or product whose design language to
follow. This single input does more than every other rule combined. If the user has
one, anchor to it. If not, ask for or pick a specific named direction (editorial,
brutalist, utilitarian-dense, warm-consumer, technical-mono, and so on), not "modern
and clean," which means nothing.
- **A color decision.** A real brand color or a deliberately chosen one, stated. Not the
framework default, and not the cream/sage default either.
- **A type decision.** A specific typeface or pairing chosen for this project, with a
reason. Avoid the top-50 defaults reached for on autopilot (Inter, Geist on the sans
side; Instrument Serif, Fraunces, Playfair on the "tasteful" side) unless they are a
real choice.
- **A layout intent.** What the page is actually for and what the user should do first,
which determines structure. This is how you avoid the hero + three-card skeleton: the
structure follows the goal, not a template.
When the user gives no brief and wants you to just build, do not produce one median
result. Produce a deliberate one and say what you chose, or offer two or three genuinely
distinct directions. The value is breaking the monoculture, so vary away from the
center on purpose.
Then, while building, avoid the specific tells in [references/tells.md](references/tells.md).
[references/choosing-a-look.md](references/choosing-a-look.md) is a process for making the
color/type/layout choices deliberately, written as a method rather than a prescription,
precisely so it does not become the next default.
## Mode 2: Audit (the guardrail)
When reviewing or cleaning existing code, or when the user says "does this look AI,"
"de-slop this," "make it not look vibe-coded," run the scanner first, then fix in
priority order.
```bash
python3 scripts/devibe\_scan.py  # full report + vibe score
python3 scripts/devibe\_scan.py  --severity high # only the strongest signals
python3 scripts/devibe\_scan.py  --json # machine-readable, for CI
```
It scans .html .css .scss .js .jsx .ts .tsx .vue .svelte .astro, reports each finding
with file, line, and fix, and gives a vibe score. Exit code is the high-severity count,
so CI can gate on it. The scanner catches the mechanical tells (colors, fonts,
gradients, the cream+serif combo). It cannot see layout coherence, spacing consistency,
or whether text overflows its container, and those are also what make a site read as AI,
so after the scan, check those by eye against the catalog.
**Respecting intentional choices.** A line with the comment `unslop-ignore` is skipped.
Use it when a flagged value is a real decision, so the audit stays trustworthy and does
not nag about a chosen brand color.
**Fixing well.** Do not fix `bg-purple-600` by swapping in `bg-emerald-700`, which is
just a different default. Fix it by applying the project's actual color, or by asking
what the color should be. A fix that introduces a new unspecified default is not a fix.
## What this deliberately does not flag
Grounded in the data, not vibes. Mesh, aurora, and blob backgrounds barely register as
real complaints (mostly a keyword artifact). Bento grids and glassmorphism are low and
contested. Dark mode itself is fine; only unprompted glow is a tell. shadcn and Tailwind
themselves are fine; their untouched defaults are the tell. Over-flagging trains people
to ignore the tool, so the scanner stays narrow.
## Reporting an audit
Lead with the verdict and the single highest-impact change. Then findings by priority
with file:line and the fix. Close with the vibe score and the top three changes. Plain
and specific. The goal is a site that looks like a person made a decision, which is the
one thing the scanner cannot do for them.

## Pitfalls

1. **Trading one default for another** — Replacing the 2024 purple-gradient hero with the 2026 cream + serif + sage "tasteful default" just resets the clock; people clock it just as fast. The only universal rule is "make a deliberate choice and be able to say why." Never prescribe a palette, font, or layout as *the* fix.

2. **Trusting the scanner for layout judgment** — `scripts/devibe_scan.py` catches mechanical tells (colors, fonts, gradients, cream+serif combos) but cannot see layout coherence, spacing consistency, or text overflow — which are also what makes a site read as AI. After the scan, check those by eye against the catalog.

3. **Fixing a default with another default** — Swapping `bg-purple-600` for `bg-emerald-700` is just a different default. Fix with the project's actual color or ask what the color should be. A fix that introduces a new unspecified default is not a fix.

4. **Designing with no reference** — An unspecified prompt gets the median of training data. Pull one real site/screenshot/brand to anchor to, or pick a specific named direction; "modern and clean" means nothing. This single input does more than every other rule combined.

5. **Flagging deliberate brand choices** — If the user genuinely wants purple, neon, a serif, or a cream background as a real brand decision, that is not slop. Honor `unslop-ignore` for anything chosen on purpose so the audit stays trustworthy.

6. **Over-flagging trains users to ignore the tool** — The scanner deliberately leaves alone mesh/aurora/blob backgrounds, bento grids, glassmorphism, dark mode itself, and the presence of Tailwind/shadcn (only their untouched defaults are tells). Stay narrow or the audit loses credibility.

7. **Skipping the deliberate-choice fallback when the user gives no brief** — If they say "just build it," do not produce one median result. Produce a deliberate one and say what you chose, or offer 2-3 genuinely distinct directions — the value is breaking the monoculture, so vary away from the center on purpose.
