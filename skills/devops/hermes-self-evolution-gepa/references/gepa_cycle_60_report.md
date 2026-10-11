# GEPA Cycle 60 — condensed learnings (2026-10-11)

**Branch:** `gepa/phase1-skill-optimization-cycle-20261011-60` · **hermes-agent commit:** `e0bcd01559`
**Mode:** Strategy A (direct parent execution), 0 API calls · **Avg delta: +7.8/skill**

## Fast path
Did NOT trigger: last cycle (59) was 7 days earlier and TUI/desktop sessions ran Oct 5–10.
Session index read from `~/.hermes/state.db` (pitfall #52), not `sessions.json`.

## Dojo
Empty output (exit 0) → **no targets** — healthy, expected (pitfall #44).

## Selection (1 delta + 4 word-count)
Delta scan (`-newermt "2026-10-04 02:00"`) → **31 candidates → 26 already evolved → 5 with gaps → 1 selected**.
Word-count fallback filled the other 4 slots.

**Television pack is now a standing exclusion.** `television`, `tv-tasks`, `tv-calendar`, `tv-table`
dominated the 4-gap scan, but `tv-tasks/` ships a `THIRD-PARTY-NOTICES.txt`, the skills carry
vendor-minimal frontmatter with no `version`, and they reference `/canonical/v2/` app assets that the
Television app re-installs on upgrade. Treat them like the Spark `recipe-*`/`persona-*` set (pitfall #46):
skip, don't evolve. Same for the `taproot-skill/*` packs.

**Bulk-install clusters to ignore:** `2026-10-06 17:13:18.787` (tv-calendar/table/tasks) and
`2026-10-09 11:53:05.315–.323` (6 skills, all already evolved).

## Evolved (all → 1.1.0, 13 triggers, When to Use, Not For, 11 numbered pitfalls)
| Skill | Route | Bytes | Delta |
|---|---|---|---|
| `devops/hermes-pm-dependency-stamp-churn` | delta | 7483 → 10352 | +8 |
| `web/web-ia-planning` | word-count | 4827 → 7970 | +7 |
| `creative/design-delivery-verification` | word-count | 3644 → 7650 | +9 |
| `software-development/static-site-integration` | word-count | 3792 → 7428 | +7 |
| `creative/print-layout-design` | word-count | 5528 → 9170 | +8 |

## New operational lessons
1. **`git diff --cached` returns 0 lines AFTER the commit lands.** When patching new files, generate the
   patch with `git diff HEAD^ HEAD -- <path>` once the worktree commit exists — staging then equals HEAD,
   so the post-commit `--cached` diff is empty. (Extends pitfall #7.)
2. **Stale sibling names are a real defect worth repairing in passing.** `design-delivery-verification`
   still pointed at `popular-web-designs` and `claude-design` (both now in `.archive/`), and
   `static-site-integration` listed `blocked-page-recovery` + `dogfood` in `related_skills`. Verify every
   sibling name against the live tree before writing a `Not For` entry — the archive moves skills between
   cycles.
3. **+7.8 is the honest ceiling when procedures are already strong.** Four of five candidates had good
   `## Procedure`/`## Workflow` sections and 8–9 command accuracy; only trigger_clarity, Not For, and
   pitfall numeralisation were left. Do not inflate scores to hit the +12–17 template average.
4. **Deferred head for Cycle 61:** `devops/bitcoin-payment-rails` and `software-development/qr-code-verification`
   — both already carry 13 triggers and only lack `When to Use` + `Not For` (the cheapest gap pair).
