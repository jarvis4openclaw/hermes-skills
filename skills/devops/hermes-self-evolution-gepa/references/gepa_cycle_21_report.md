# GEPA Cycle 21 — Condensed Learnings

**Date:** 2026-06-11  
**Method:** Strategy A (Direct Parent Execution) — LLM-as-Judge  
**Selection:** Word-count-driven (all 5 skills live-path only, not tracked in repo)

## Key Observations

1. **Live path is source of truth** — All 5 target skills existed only in `~/.hermes/skills/` (live path), not in `~/.hermes/hermes-agent/skills/` (repo). `git ls-files` was empty for all. The evolved content lives in the live path; repo is a secondary copy.

2. **`cron-noninteractive-guardrails` already had v1.1.0** — Live path version was already evolved from a prior session. If we had read from the repo first (v1.0.0), we would have regressed it. **Always read live path first.**

3. **`git log` returns 0 for live-path-only skills** — Delta-driven heuristic via `git log --since=<date> -- skills/` finds nothing when skills aren't tracked. The `find -newer` supplement is essential.

3. **Strategy A is zero-cost and reliable** — 5 skills evolved via targeted `patch` calls, no API calls, no CLI timeouts, no subagent overhead. Total wall time < 2 minutes.

4. **Patch generation requires `--cached` for new files** — All 5 skills were untracked. `git diff HEAD` produces empty patches. Must `git add` first, then `git diff --cached`.

5. **Hermes-agent repo may need jarvis4openclaw remote** — The `origin` points to NousResearch (read-only). Must add `jarvis4openclaw` remote for push. If it doesn't exist, local commits are the source of truth.

## Skills Evolved

| Skill | Path | Delta | Key Pitfalls Added |
|-------|------|-------|-------------------|
| llava | mlops/models | +13 | GPU OOM on 34B, tokenizer mismatch, image preprocessing, CUDA cache |
| simpo-training | mlops/training | +11 | hinge loss on small data, gamma/beta ratio, LR sensitivity, Flash Attn |
| cron-noninteractive | devops | +12 | post-success ioctl, masked .env, brv --detach, urllib IPv6 |
| calcom-api | openclaw-imports | +13 | 401 auth, timezone off-by-hours, UID vs ID, cursor pagination |
| nostrx | social-media | +11 | SSH key auth, pkill matching, stale creds, sync_state desync, thread limit |

## Repo State After Cycle

- `~/.hermes/skills/` — 5 evolved SKILL.md files (live path, source of truth)
- `~/.hermes/hermes-agent/` — branch `gepa/phase1-skill-optimization-cycle-21`, 5 new files committed
- `~/hermes-skills/` — 5 files synced, pushed to `jarvis4openclaw/hermes-skills`
- `~/hermes-agent-self-evolution/` — patches + report + metrics, pushed to `jarvis4openclaw/hermes-agent-self-evolution`

## Next Cycle Expectations

- Delta-driven should surface these 5 skills (now tracked in hermes-agent repo)
- If other work hasn't touched them, they'll be "already evolved" — fall back to word-count
- Session-based eval (`--eval-source sessiondb`) becomes viable after more cycles