# GEPA Cycle 61 — condensed learnings (2026-10-18)

**Branch:** `gepa/phase1-skill-optimization-cycle-20261018-61` · hermes-agent commit `af4991c923`

## Selection
- Fast path did **not** trigger (7 days since Cycle 60 + Oct 12–17 user sessions).
- Dojo empty → healthy (pitfall #44).
- `git log --since -- skills/` returned 0 (repo tracks ~no live skills); the `find -newer
  <cycle-start>` supplement surfaced **14** candidates → **2 actionable**, **12 already evolved**.
- Word-count filled the other 3 slots. `missing>=3` was junk-dominated; `missing>=2` held the
  real delta (pitfall #54 again).

## Result
| Skill | Δ |
|---|---|
| github | 26 → 42 (+16) |
| hermes-plugin-authoring | 35 → 43 (+8) |
| bitcoin-payment-rails | 33 → 40 (+7) |
| blogwatcher | 37 → 44 (+7) |
| vault-cli-cron | 42 → 45 (+3) |

**Avg +8.2** — deliberately low because 2 of 5 were near-complete delta targets.

## New lesson: validate frontmatter with `yaml.safe_load`, not `grep`
`research/blogwatcher` *looked* fully triggered (12 `trigger_conditions` lines), but line 18 was

```yaml
      - phrases: "check my feeds", "any new posts", ...
```

A sequence entry that opens a mapping and then hits bare commas → `ParserError: expected
<block end>, but found ','`. The whole trigger block fails to load, so **all 12 triggers were
being silently dropped** — a skill that scores well on a `grep -c trigger_conditions` check can
still be delivering zero triggers. Pre-existing defect, not introduced by the cycle.

**Add to the verification checklist:** after evolving any skill, run
`python3 -c "import yaml,pathlib; yaml.safe_load(open(P).read().split('---',2)[1])"` and assert
the trigger count is non-zero. Cheap, and it catches a class of defect `grep` cannot see.

## Other notes
- Third-party exclusions now standing: Television pack, `taproot-skill/*` pack, Spark
  `recipe-*`/`persona-*`, `node_modules`.
- 4 of 5 targets were live-path-only (absent from the hermes-agent repo) → worktree +
  `mkdir -p` + `git add` as usual (pitfalls #33/#47).
