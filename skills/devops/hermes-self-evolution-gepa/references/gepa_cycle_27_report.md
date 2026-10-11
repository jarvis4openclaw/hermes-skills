# Cycle 27 — Key Learnings

**Date:** 2026-06-14 | **Branch:** `gepa/phase1-skill-optimization-cycle-27`

## Selection

- 1 delta candidate (youtube-content, partially evolved: had triggers + pitfalls, missing When to Use + Not For)
- 4 word-count fallback: ponytail, songsee, ponytail-review, nano-pdf
- `github-sync-script-preflight` skipped — contains "do NOT re-create or re-update" marker
- `ponytail-help` skipped — companion reference card best evolved alongside ponytail

## Results

| Skill | Baseline | Evolved | Δ |
|-------|----------|---------|---|
| youtube-content | 32 | 42 | +10 |
| ponytail | 19 | 36 | +17 |
| songsee | 18 | 34 | +16 |
| ponytail-review | 17 | 33 | +16 |
| nano-pdf | 16 | 31 | +15 |

**Avg: +14.8** | Strategy: A (patch-based direct execution)

## New Files in Repo

- `skills/software-development/ponytail/SKILL.md` — new to hermes-agent repo
- `skills/software-development/ponytail-review/SKILL.md` — new to hermes-agent repo

## Issues

- `software-development/` directory didn't exist in hermes-agent repo — created with `mkdir -p`
- Upstream commits (gif-search, github-auth, obsidian) present in working tree — only staged our 5 skills
- `.gitignore` had no `output/` entry — old cycle artifacts were appearing as untracked; added to gitignore

## Hermes Dojo Integration (added post-Cycle 27)

Cycle 28+ integrates `hermes-dojo` as a data-driven pre-filter in Step 0. The Dojo reads `state.db` to find skills with actual tracked failures rather than just structural gaps. Key details:

- **Dojo path:** `~/.hermes/skills/devops/hermes-dojo/`
- **Bridge command:** `python3 scripts/dojo-bridge.py --days 3 --gepa-only`
- **Empty output is normal:** when all failures are in core tools (terminal, read_file, etc.), the Dojo correctly returns nothing — skills are healthy
- **Target count:** Dojo reserves up to 3 of the 5 GEPA candidate slots; if Dojo returns >3, pick top 3 by failure count; if 0, normal heuristics fill all 5
