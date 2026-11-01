# GEPA Cycle 63 — condensed learnings

**Date:** 2026-11-01 · **Branch:** `gepa/phase1-skill-optimization-cycle-20261101-63` · hermes-agent commit `dbb8eb0018` · **avg +16.0**

## Selection

Fast path did NOT trigger (7 days since Cycle 62; 57 desktop / 6 tui / 20 kanban / 1 telegram sessions since 2026-10-25).
Dojo bridge empty (healthy, pitfall #44).

Delta-driven: `git log --name-only --since="2026-10-25 02:00" -- skills/` → 0 (pitfall #37, only 58 bundled files tracked).
`find ~/.hermes/skills/ -name SKILL.md -newermt "2026-10-25 02:00"` → **19 candidates**:
1 archived (`.archive/`) · 11 already fully evolved · **7 actionable**.

Selected the five that were missing **all four** gaps (maximum delta class):

| Skill | Δ | Bytes |
|---|---|---|
| `devops/commandcode-provider` | +16 | 2,285 → 6,333 |
| `hermes-cron-false-positive-triage` | +16 | 1,293 → 5,999 |
| `devops/hermes-subprofile-config` | +17 | 1,767 → 5,554 |
| `devops/hermes-backup-audit` | +17 | 1,849 → 5,114 |
| `tailscale-acl-lockdown` | +14 | 2,404 → 5,573 |

Deferred (2/4 gaps, outranked): `full-security-audit`, `social-media/mdfromx`.

## Learnings

1. **Freshly authored skills are the best targets.** Check `.curator_ledger.jsonl` for `before: []` / `before: 1`
   entries during the delta scan. Three of this cycle's five picks were newly authored and carried a
   duplicated H1 (`# Title` twice) in addition to missing every gap. Two days old is the ideal age to fix them.
2. **After 60+ cycles, most delta hits are the previous cycles' own writes.** The 4-gap check is the only thing
   separating a real work list from 11 empty patches.
3. **≥2-gap skills accumulate indefinitely** under a 5-slot cycle that prioritises 0-gap skills. Pitfall #54's
   second scan (`missing >= 2`, sorted by bytes) is the mechanism to reach them; schedule it deliberately.
4. **`git worktree` is the only way to commit in hermes-agent** (pitfall #47) — the live checkout is detached
   (`bf0203a794`) and rejects branch ops. Worktree → `git add` → commit → `git worktree remove --force`. Clean.
5. **Cron edit path (pitfall #58) held for all 5 skills** — `python3 <<'PY'` heredoc, `assert anchor in s`,
   single `p.write_text(s)`, `SKILL.md.bak` first. No `patch`/`write_file` calls attempted.
6. **Verify with `yaml.safe_load`, never `grep`** (pitfall #57) — all five asserted `triggers == 13`, `uniq == 13`.
