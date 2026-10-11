# GEPA Cycle 26 — Condensed Learnings

**Date:** 2026-06-13 | **Branch:** `gepa/phase1-skill-optimization-cycle-26`

## Selection

- **Delta-driven:** 0 actionable (6 found but all fully evolved from prior cycles)
- **Word-count fallback:** Scanned 23 skills with ≥3 of 4 gaps missing; picked top 5 by size
- Selected: `nostrx`, `yuanbao`, `exa-web-search-free`, `mcporter`, `code-review`
- Skipped: `github-sync-script-preflight` (has "do NOT re-update" marker)

## Results

| Skill | Pitfalls | Key additions |
|-------|----------|--------------|
| nostrx | 5→10 | CT 202 SSH recovery, sync_state corruption, rate limits |
| yuanbao | 0→10 | @mention workflow, DM vs send_message confusion, group_code sourcing |
| exa-web-search-free | 0→10 | mcporter config, fast vs deep tradeoffs, non-English fallback |
| mcporter | 0→10 | npx missing, auto-discovery limits, JSON quoting |
| code-review | 0→12 | SQL injection detection, secret scanning, PR chunking |

**Average improvement:** +14.8 points (+60%)

## Issues

- **yuanbao patch came out empty** — tracked file synced but not staged; `git diff --cached` only sees staged changes
- **4 of 5 skills were new files** in hermes-agent repo (not tracked in HEAD)
- **All 5 skills used Strategy A** (direct parent execution, 3-4 patch calls each)

## Commits

- hermes-agent: `8fde13808`
- self-evolution: `8ca1576`
- hermes-skills: `261c4ce`
