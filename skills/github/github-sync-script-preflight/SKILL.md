---
name: github-sync-script-preflight
description: Prevent false-success Git sync runs by validating script permissions, repository root, and submodule state before commit/push automation.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Git, Automation, Cron, Reliability, Submodules]
    related_skills: [github-auth, github-repo-management]
---

# GitHub Sync Script Preflight

Use this before running any `sync-to-github.sh`/auto-commit job.

## Why
A sync script can print "No changes to commit" even when work exists if:
1. the script is not executable,
2. it runs from the wrong repository,
3. a referenced submodule is unpopulated.

## Preflight Checklist (run in order)

```bash
# 1) Script exists and is executable
SCRIPT="/path/to/sync-to-github.sh"
test -f "$SCRIPT" || { echo "MISSING_SCRIPT"; exit 1; }
test -x "$SCRIPT" || { echo "NOT_EXECUTABLE"; exit 1; }

# 2) Resolve target repo and verify it's a git work tree
REPO_DIR="$(dirname "$SCRIPT")"
cd "$REPO_DIR" || exit 1
git rev-parse --is-inside-work-tree >/dev/null || { echo "NOT_GIT_REPO"; exit 1; }

# 3) Verify intended root (avoid parent-repo/submodule confusion)
ROOT="$(git rev-parse --show-toplevel)"
echo "REPO_ROOT=$ROOT"

# 4) Detect unpopulated submodules (hard fail for sync jobs)
if git submodule status 2>/dev/null | grep -qE '^-'; then
  echo "UNPOPULATED_SUBMODULE"
  git submodule status
  exit 1
fi

# 5) Show real change scope before deciding "no changes"
git status --porcelain
```

## Safe Execution Pattern

Only run the sync script if preflight passed:

```bash
bash "$SCRIPT"
```

## Cron Integration (missing step that caused repeats)

Do not call `sync-to-github.sh` directly from cron. Call a wrapper that runs preflight first and fails loudly:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT="/path/to/sync-to-github.sh"

# Preflight
 test -f "$SCRIPT" || { echo "MISSING_SCRIPT"; exit 1; }
 test -x "$SCRIPT" || { echo "NOT_EXECUTABLE"; exit 1; }
 REPO_DIR="$(dirname "$SCRIPT")"
 cd "$REPO_DIR"
 git rev-parse --is-inside-work-tree >/dev/null || { echo "NOT_GIT_REPO"; exit 1; }
 if git submodule status 2>/dev/null | grep -qE '^-'; then
   echo "UNPOPULATED_SUBMODULE"
   git submodule status
   exit 1
 fi

# Real run
exec bash "$SCRIPT"
```

Minimal cron line (example):

```cron
*/30 * * * * /path/to/sync-with-preflight.sh >> /var/log/sync-with-preflight.log 2>&1
```

This removes false-success runs and gives one obvious failure code to fix.

## Failure Interpretation

- `NOT_EXECUTABLE` → `chmod +x /path/to/sync-to-github.sh`
- `NOT_GIT_REPO` → script is in wrong directory; relocate or fix `cd` target
- `UNPOPULATED_SUBMODULE` → initialize/fix submodule before sync
- empty `git status --porcelain` → true no-change run

## Adoption Status (as of 2026-04-10)

**Skill complete. Awaiting manual environment fixes.**

Cycles from April 4–10, 2026 repeatedly flagged this same gap. The skill is ready.
The blockers are environmental (need Boss or manual operator action):
- [ ] `chmod +x /home/wahid/clawd/signal-scheduler/sync-to-github.sh`
- [ ] `git submodule update --init signal-scheduler` (inside parent repo)
- [ ] Deploy wrapper script; point cron at it instead of `sync-to-github.sh` directly

**Self-evolution cycles: do NOT re-create or re-update this skill.** It is complete.
If these three items are still unresolved, escalate to Boss — do not loop on this skill.

## Verification (next run)

A healthy run must show:
1. no preflight errors,
2. valid `REPO_ROOT` for the intended repo,
3. no `^-` lines in `git submodule status`.

Only then trust "No changes to commit" as real.
