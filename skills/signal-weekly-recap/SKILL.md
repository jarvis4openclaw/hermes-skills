---
name: signal-weekly-recap
description: >-
  Use when building the weekly Signal recap PPTX deck.
version: 2.1.0
metadata:
  hermes:
    tags: [homelab, signal-scheduler, automation, pptx]
    trigger_conditions:
      - "weekly Signal recap"
      - "Signal weekly deck"
      - "build the Signal recap PPTX"
      - "Thursday Signal recap cron"
      - "one-off recap deck for a past window"
      - "editorial deck for Signal Scheduler"
      - "rebuild the Signal weekly deck"
      - "Signal Scheduler summary deck"
---

# Signal Weekly Recap (editorial deck, v2)

## When to Use

Trigger when Wahid asks for the weekly Signal Scheduler recap, the "Signal
weekly deck", or when the Thursday cron fires for this task. Also use when a
one-off recap deck for any past window is requested (pass --end <Wednesday>).

## Not For

- The Signal scheduler itself (posting, queueing, retries) → use `signal-scheduler` instead.
- Any non-Signal deck, report or document → use `microsoft-office` instead.
- Rendering/QA of a `soffice`-converted PDF that is not this deck → handle it directly; this skill owns only the recap pipeline.
- Deploying or verifying a static site that hosts the deck → use `static-site-deploy-verify` instead.
- Designing new deck visuals from scratch (this skill implements the approved language; it does not invent a new one) → settle the design first, then return here.
- Ad-hoc screenshot/vision QA of unrelated images → use the vision tooling directly.

## What this produces

A fully EDITABLE editorial PPTX per week — every element is a native
PowerPoint shape (text boxes, rectangles, ovals, connectors, pictures), never
a full-bleed slide image. Structure (8-10 slides for a typical week):

1. **Cover** — eyebrow (group), huge "SIGNAL SCHEDULER" title, rules,
   subtitle, date range, console-style status line (watcher/discussions note).
2. **Mem slide** — "Morning Signals & Memes": 2x2 framed white cards, date
   stamp top, meme image contain-fit, centered caption below. Memes are
   morning image posts (< 10:00 US Central); afternoon image posts are
   informational graphics, not memes.
3. **One slide per non-meme post** — the LLM editor distils an editorial
   headline and picks a layout archetype:
   - `stats` — row of stat cards (big value numbers) + full-width callout
   - `places` — two place/resource cards with orange accent bar + link pills
   - `article` — summary lines + link pills + framed attachment image
   - `chips` — summary + platform/label chips row + link pill
   - `quote` — quote card with accent bar + numbered point boxes right
   Status is colour-coded: green dot + SENT, red dot + FAILED (right-aligned
   above the header rule). Links become orange pill buttons with white bold
   text, hyperlinked via SHAPE click_action (never run-level: LO renders
   run hyperlinks with the theme's blue underline).
4. **QR slide** — "Join Bitcoin Study Group", QR plate, "Scan to connect".

NO metrics/KPI slide (Wahid declined it). No emoji, no placeholder icons —
typographic markers only (numbered squares, dots, rules).

## Design system (matches the approved "improved" Gemini deck language)

- Canvas warm cream `#F7F6F2`; ink `#17150F`; muted `#6B675E`; accent
  bitcoin-terracotta `#E8630A`; sent green `#1F7A3D`; failed red `#B3261E`;
  cards white; hairlines `#D9D2C5`; callout fill peach `#F7E9DA`.
- Furniture on every content slide: corner registration crosshairs, tracked
  caps eyebrow "SIGNAL SCHEDULER · WEEKLY RECAP" top-left, date top-right,
  footer hairline rule, "BITCOIN STUDY GROUP" bottom-left, `NN / NN` bottom-right.
- Font `Noto Sans` everywhere (has U+20BF ₿; Arial does not).
- Slide size 13.333 x 7.5 in (16:9).

## How it runs (pipeline)

1. **Fetch (deterministic)** — `run_recap.py` fetches posts + images over
   SSH from CT signal-scheduler (root@192.168.100.47), discussions from
   discussions.db, into `~/signal-weekly/posts_<start>_<end>.json` etc.
2. **Edit (LLM, you are this stage)** — author the spec JSON at
   `~/signal-weekly/editorial_spec_<start>_<end>.json` from the posts data:
   distil an editorial headline per post (a title for the story, NOT the raw
   first sentence), pick a layout archetype, write 1-3 summary lines in the
   group's voice, choose link labels (short domain + ` ↗`), set meme
   captions. Schema: see `editorial_deck.py` docstring. Reference spec:
   `editorial_spec_2026-11-05_2026-11-11.json`.
3. **Render (deterministic)** —
   `/home/wahid/.hermes/cache/scratch/pptx-venv/bin/python ~/signal-weekly/run_recap.py --builder editorial` (default)
   → `editorial_deck.py` maps spec + posts to native shapes →
   `~/wiki/social/summary_<start>_<end>.pptx` (the ONLY deck location).
   If the venv is gone (scratch pruned after 24h idle), recreate:
   `python3 -m venv /home/wahid/.hermes/cache/scratch/pptx-venv &&
   /home/wahid/.hermes/cache/scratch/pptx-venv/bin/pip install python-pptx pypdfium2 Pillow`
4. **QA** — run_recap renders pages on the CT (soffice → pdftoppm) into
   `~/signal-weekly/preview_<start>_<end>/`. YOU must visually verify every
   page: no overlapping text, no clipping, chips/pills inside bounds, dot
   right of its label. Fix the renderer or spec and rebuild until clean.
   (`qa_check.py`/`pixel_audit.py` are legacy-geometry only; skip them for
   editorial decks.)

Then attach the PPTX + the preview page PNGs. No extra checks or adjacent
cleanups unless Wahid asks.

## Pitfalls

1. **Render venv pruned after 24h idle** — scratch is pruned, so `pptx-venv` disappears and the render stage fails. Recreate: `python3 -m venv /home/wahid/.hermes/cache/scratch/pptx-venv && /home/wahid/.hermes/cache/scratch/pptx-venv/bin/pip install python-pptx pypdfium2 Pillow`.
2. **`wrap="none"` textboxes get centered by LibreOffice** — paragraph alignment is ignored when word_wrap is off. Always set `word_wrap=True` on textboxes that rely on left/right alignment (`editorial_deck.text()` does this — do not "optimise" it back).
3. **python-pptx arithmetic returns plain int EMU, not Length** — never call `.inches` on a subtraction result; use `_to_in()`.
4. **Raw float inches silently become ~0 EMU** — pass EMU (via `Inches(...)`) to every shape/connector call; a bare float once painted the footer band on top of the header.
5. **Run-level hyperlinks render blue + underlined** — use shape `click_action.hyperlink.address`, never run-level, regardless of run colour.
6. **Status dot positioned by estimated label width drifts** — pin the dot at the right margin and right-align the label to end short of it.
7. **Stale preview pages are audited as if current** — small decks name pages `page-1.png` (single digit); clear the render dir and re-copy after conversion.
8. **Font substitution breaks the ₿ glyph** — the font must be `Noto Sans` (has U+20BF; Arial does not). Install `fonts-noto-core`, copy `NotoSans-Regular.ttf`/`-Bold.ttf` to `~/signal-weekly/fonts/` for PIL measurement.
9. **Meme classifier misses the morning window** — use `image_path AND scheduled hour < 10 America/Chicago`; posts are stored UTC (14:21Z = 08:21 CST), so a naive UTC hour is wrong.
10. **`sent` status mistaken for Signal success** — the scheduler marks a post `sent` when ANY channel succeeded; a red FAILED chip means every channel failed, not Signal specifically.
11. **Dropping `?timeout=1` from the watcher** — the default blocks ~120s holding the signal-cli config lock. The watcher polls `GET /v1/receive/<number>?timeout=1` every 30s. DB: `/opt/signal-scheduler/data/discussions.db` chmod 600.
12. **Deck written to the wrong path** — the deck must live at exactly `~/wiki/social/summary_<start>_<end>.pptx`. Keep the legacy `build_slide.py` + `qa_check.py` intact for `--builder legacy`.
13. **Running `qa_check.py`/`pixel_audit.py` on editorial decks** — they are legacy-geometry only; for editorial decks you must visually verify every preview PNG yourself.

## Cron behavior

Weekly Thursday 9am; pinned model deepseek/deepseek-v4-flash (commandcode).
Flow: fetch → author spec JSON (the LLM editor stage) → build editorial deck
→ visually verify preview pages → attach PPTX + preview PNGs, report deck
path + one-line summary of posts/memes/status counts. If posts in the window
spanned a group other than Bitcoin Study Group, list groups in reply.
