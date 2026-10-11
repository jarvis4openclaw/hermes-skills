# Cycle 19 Learnings (2026-06-08)

**Method:** LLM-as-Judge (Strategy A, direct parent execution)
**Branch:** gepa/phase1-skill-optimization-cycle-19
**Delta:** +75 across 5 skills

## Skills Evolved

| Skill | Version | Δ |
|-------|---------|---|
| mlops/training/flash-attention | 1.0.0 → 1.1.0 | +15 |
| mlops/evaluation/nemo-curator | 1.0.0 → 1.1.0 | +15 |
| devops/windows-ssh | 1.0.0 → 1.1.0 | +15 |
| creative/architecture-diagram | 1.0.0 → 1.1.0 | +15 |
| productivity/ocr-and-documents | 2.3.0 → 2.4.0 | +15 |

## Selection

- Delta-driven: 0 candidates (no skills modified in hermes-agent repo since cycle 18)
- Word-count fallback: 30 candidates with ≥3 gaps, top 5 selected by word count + category diversity

## New Files Created in Repo

Three skills (flash-attention, nemo-curator, windows-ssh) existed only in the live path (`~/.hermes/skills/`) and were NOT tracked in the hermes-agent repo. They were created as new files with `git add` + `--cached` diff.

## Cumulative

95 skills / 1291 delta / 13.6 avg across 19 cycles.