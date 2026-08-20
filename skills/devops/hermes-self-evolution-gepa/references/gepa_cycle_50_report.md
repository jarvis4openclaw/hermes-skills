# GEPA Cycle 50 Learnings (2026-08-20)

Condensed notes from cycle 50 for future cycles.

## Selection reality check

- **Delta-driven found 5 skills, all already evolved** — exactly cycle 49's own writes (findmy, shell-timezone-date, vault-cli-cron, embedded-firmware-porting, texas-electricity). This is the *expected* steady-state pattern: with the daily cron + manual re-runs, delta-driven almost always returns the previous cycle's own writes. Do not report "found 0" — report "found N, all already evolved, fell back to word-count."
- **Word-count scan false positive:** `mlops/local-llm-intel-arc` (7,948 B, biggest file, 3 "gaps") is actually fully evolved — it uses `## NOT for` (uppercase) instead of `## Not For` and has 10 numbered pitfalls under `## Critical pitfalls (these bite every time)` instead of the standard `## Pitfalls` heading. The 4-gap grep misses it. Before selecting a top word-count candidate, always read it — heading case and custom section names vary.
- `openhue` (4-gap, top of list) is a smart-home third-party skill, similar in spirit to recipe-*/persona-* (pitfall #46) — prefer skipping it for diversity.

## What worked

- **5 skill patches, 590 lines, avg Δ +12.8** via Strategy A (patch tool, pitfall #30).
- Worktree + byte-verify (pitfall #47/#48) — clean commit `153d563044`.
- Push flow: `gh auth switch --user jarvis4openclaw` → push both repos → verify via API → switch back to `wahidsaleemi`. Remote verified: hermes-skills `6c443821`, self-evolution `9bf9d5e`.

## Skills now fully evolved (4-gap)

All 5 evolved this cycle (linux-lfs-build-troubleshooting, homelab-browser-backends, agent-wikis, windows-service-config, polymarket) are at 1.1.0 with trigger_conditions + When to Use + Not For + numbered Pitfalls. They will appear as "found but already evolved" in the next cycle's delta scan.
