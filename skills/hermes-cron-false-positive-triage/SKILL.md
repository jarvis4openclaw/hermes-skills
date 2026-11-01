---
name: hermes-cron-false-positive-triage
description: Use when a Hermes cron alert contradicts observed behavior, or a scheduled job fires or falls silent wrongly.
version: 1.1.0
author: jarvis
license: MIT
metadata:
  hermes:
    tags: [hermes, cron, alerts, triage, watchdog, false-positive]
    related_skills: [cron-noninteractive-guardrails, durable-unattended-jobs, scheduled-job-decommissioning, hermes-dojo]
    trigger_conditions:
      - "cron job false positive"
      - "the cron alert is wrong"
      - "why did this cron job alert"
      - "cron watchdog fired"
      - "cron alert contradicting observed behavior"
      - "cron job reported a regression"
      - "triage a cron alert"
      - "silence a cron alert"
      - "cron alarm false alarm"
      - "scheduled job alert noise"
      - "cron job says X but actually Y"
      - "cron script detection bug"
      - "job alert vs reality"
---

# Triage a cron false positive

## When to Use

- A cron job raised an alert (regression, failure, unhealthy) that observed behavior contradicts.
- A watchdog job fires repeatedly on a condition you can see is fine.
- A job that used to alert has fallen silent and you need to know whether that is health or breakage.
- A cron script reports "install regression" or "missing dependency" while the tool demonstrably works.
- You are about to patch a cron script's detection logic and want to reproduce the alert first.
- You need to decide whether a single failed tick is a real outage or a self-healing race.
- A job's alert says the environment is wrong and you need the authoritative source of truth for that environment.

## Not For

- **Writing or hardening the cron script itself** (non-interactive guardrails, TTY, approval gates) → use `cron-noninteractive-guardrails` instead
- **Designing a job that survives reboots, outages, or races** → use `durable-unattended-jobs` instead
- **Retiring a job that is no longer wanted** → use `scheduled-job-decommissioning` instead
- **Choosing which model a job should run** → use `cron-model-optimization` instead
- **Finding which skills are really failing in use** → use `hermes-dojo` instead
- **A provider or model pin error rather than a detection bug** → use `commandcode-provider` instead
- **Backup/restore coverage questions** → use `hermes-backup-audit` instead

## Procedure

1. `hermes cron list` → find the job by id; note script + mode. The runs/history CLI shows status only — read the *script* to understand what it actually checks.
2. Run the script manually with the pinned interpreter (`/usr/bin/python3` — cron scripts don't inherit interactive PATH) to reproduce the alert.
3. Verify ground truth independently before trusting either side — e.g. `ls` the actual site-packages, `readlink` the installed binary, check what the tool actually uses.
4. Hermes dependency generations live under `~/.hermes/installs/<root>/environments/*/venv`. NEVER discover the active one by glob-sorting — multiple generations exist and the lexicographic winner may be an empty/unrelated one. The authoritative venv is `~/.hermes/installs/<root>/facts.json` → `packages.venv.environment` (pick the newest root that owns facts.json).
5. When patching the cron script: backup with `.bak` suffix, patch, then re-run and confirm the alert disappears (silent-ok) without breaking its real signal path. Sanity-test new helper path logic standalone before running.
6. End-of-run: store facts to Mnemosyne (importance ≥0.8).

## Pitfalls

1. **Trusting the alert over ground truth** — the cron script is a heuristic; verify the underlying fact independently (list the real directory, resolve the real binary) before believing either side. Case study: a provider-health check glob-sorted venv generations and cried "install regression" daily while memory worked fine (2026-10-31).
2. **Glob-sorting to find the active venv** — `sorted(glob(...))[-1]` picks the lexicographically last generation, which may be an *empty* one. Read `~/.hermes/installs/<root>/facts.json` → `packages.venv.environment` instead, picking the newest root that owns a facts.json.
3. **Reading only job status via the CLI** — `hermes cron list` and the runs history show status, not logic. You must read the script file to know what it asserts.
4. **Running the script under the interactive interpreter** — cron uses a pinned interpreter and a minimal PATH. Reproduce with `/usr/bin/python3` (or the job's exact command line) or you will not reproduce the failure.
5. **Patching without a `.bak`** — copy the script to `<name>.bak` (or a timestamped variant) first; an un-backed-up cron-script edit is unrecoverable.
6. **Declaring victory on "no alert" alone** — confirm the *signal* path still fires: force the failure condition once, check the alert returns, then revert.
7. **Assuming a now-silent job is healthy** — a job can stop alerting because it crashed before reaching the alert. Check last-run status and exit code, not just the absence of mail.
8. **Fixing the symptom instead of the detector** — if the detector's logic is wrong, patch the detector and record why; suppressing the notification only hides the next real alert.
9. **Leaving the finding un-annotated** — when a false positive is proven, store the fact (Mnemosyne, importance ≥0.8) with the job id and date so the next triage does not re-derive it.
10. **Editing a job while it is mid-run** — check for a running execution first; concurrent edits race the job's own state writes and produce spurious "database is locked" failures.
11. **Not sanity-testing new path logic standalone** — run the new resolver/helper as a one-off snippet against known-good fixtures before wiring it into the script.
12. **Treating one failed tick as a real outage** — single-tick races (db-locked, dispatch race) self-heal on the next run; require two or more consecutive failures before escalating.

## References

- `cron-noninteractive-guardrails` — the non-interactive constraints any patch must respect.
