# GEPA Cycle 18 — Key Learnings

**Date:** 2026-06-07
**Skills evolved:** 5 (stable-diffusion, trl-fine-tuning, gguf, macos-computer-use, teams-meeting-pipeline)
**Method:** LLM-as-Judge (Strategy A — direct parent execution)

## What Worked

- Strategy A (direct parent execution) was the right call for 5 skills. No subagent timeouts, clean sequence.
- Delta-driven heuristic correctly identified that all 5 git-log candidates were already fully evolved from Cycle 17. Fallback to word-count picked 5 new skills.
- GitHub auth was already on jarvis4openclaw — no push failures.

## What Broke

### hermes-agent repo on wrong branch
The repo was still on `gepa/phase1-skill-optimization-cycle-17` from the previous cycle. The new commit landed on the wrong branch — had to `git checkout -B` to reset. **Fix:** always `git checkout main && git checkout -b gepa/phase1-skill-optimization-cycle-N` before syncing.

### hermes-skills backup only committed 3 of 5
Only 3 skills had actual diffs to commit. `macos-computer-use` and `teams-meeting-pipeline` were already backed up by Cycle 17 and unchanged. This is correct behavior — the backup is cumulative, not a snapshot. Report should note the discrepancy.

## Metrics
| Metric | Value |
|--------|-------|
| Total delta | +75 |
| Avg delta/skill | +15.0 |
| Cumulative | 90 skills / 1216 delta / 13.5 avg |
| Pitfall coverage | +35 (largest improvement) |
| Trigger clarity | +28 (second largest) |