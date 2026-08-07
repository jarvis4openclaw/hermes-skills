---
name: github-sync-script-preflight
description: Prevent false-success Git sync runs by validating script permissions, repository root, and submodule state before commit/push automation. Use when a sync-to-github.sh/auto-commit job reports "No changes to commit" suspiciously, when setting up a new cron-driven git sync, or when a git sync script fails silently.
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Git, Automation, Cron, Reliability, Submodules]
    related_skills: [github-auth, github-repo-management]
    trigger_conditions:
      - "sync script says no changes to commit"
      - "sync-to-github.sh not working"
      - "false success git sync"
      - "git sync script failed silently"
      - "unpopulated submodule"
      - "sync job reports NOT_EXECUTABLE"
      - "set up cron git sync with preflight"
      - "submodule missing in sync"
      - "auto-commit job runs from wrong repo"
      - "git status empty but work exists"
      - "preflight check before git push"
      - "wrapper script for sync-to-github"
      - "verify git sync before trusting no changes"
---

# GitHub Sync Script Preflight

Use this before running any `sync-to-github.sh`/auto-commit job.

## When to Use

- Setting up or repairing a cron-driven `sync-to-github.sh` / auto-commit job
- A sync run printed "No changes to commit" but you know work exists
- Diagnosing `NOT_EXECUTABLE`, `NOT_GIT_REPO`, or `UNPOPULATED_SUBMODULE` failures
- Auditing any script that decides whether to commit/push based on `git status`
- Adding a preflight wrapper to a repo with submodules

## Not For

- **Interactive one-off commits** → use `github-pr-workflow` or plain `git` instead
- **PR review / code review workflows** → use `github-code-review` instead
- **Managing remotes, branches, releases** → use `github-repo-management` instead
- **Creating or triaging issues** → use `github-issues` instead
- **Backing up config/skills without git semantics** → use `hermes-config-backup` instead

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

## Pitfalls

1. **Trusting "No changes to commit" from a broken script** — A non-executable or wrong-directory script prints the same message as a real no-change run. Always run the preflight checklist first; the failure codes (`NOT_EXECUTABLE`, `NOT_GIT_REPO`, `UNPOPULATED_SUBMODULE`) are the only trustworthy signal. Recovery: wire the wrapper so the sync script never runs without a passing preflight.
2. **Submodule check silently skipped** — `git submodule status` prints nothing if the repo has no submodules, and `grep -qE '^-'` exits 1 (no match) which is fine under `set -e` only if it's the last command. If you add more checks after it, the exit code is masked. Recovery: capture the grep result explicitly (`if git submodule status 2>/dev/null | grep -qE '^-'; then ... fi`) as shown in the wrapper.
3. **Preflight and sync run from different directories** — If the cron line `cd`s to a different repo than the preflight checked, the checks are meaningless. Recovery: resolve `REPO_DIR` from the script's own path and `cd` once in the wrapper before both preflight and exec.
4. **Wrapper not executable, cron silently skips it** — cron runs the wrapper via its shebang; a non-executable wrapper produces a "Permission denied" in the mail log and the sync never happens. Recovery: `chmod +x` the wrapper and verify with `test -x` in the same change-set as deploying it.
5. **`exec bash "$SCRIPT"` without `set -e` in the wrapper** — If the wrapper omits `set -euo pipefail`, a failing preflight exits the `if` block but the script may continue to the real run with a partial state. Recovery: keep `set -euo pipefail` at the top of the wrapper exactly as in the Cron Integration section.
6. **Submodule init needed but only `update` run** — `git submodule update --init signal-scheduler` inside the parent repo resolves the `^-` state only if the submodule URL is registered. If `.gitmodules` is missing or the submodule was added as a plain directory, the update fails with "not a git repository". Recovery: verify `.gitmodules` exists and lists the path before attempting `update --init`.
7. **Checking the wrong repo's status after a cd failure** — `cd "$REPO_DIR" || exit 1` guards the wrapper, but a cron environment may not have the same HOME/PATH, so `git` invocations can target a different repo. Recovery: print `REPO_ROOT` and compare it to the expected path in the preflight output before trusting the run.
8. **Empty `git status --porcelain` from an untracked-dir quirk** — A `.git` file (worktree) or nested repo can make `--porcelain` show nothing while work exists in a submodule. Recovery: also run `git submodule status` and check for unmerged paths (`git diff --name-only --diff-filter=U`) before concluding "true no-change".
9. **Cron MAILTO swallows preflight failures** — If the cron line has no `MAILTO` and output isn't redirected, failure codes land in `/var/log/syslog` or the local mail spool where nobody reads them. Recovery: redirect to a log file (`>> /var/log/sync-with-preflight.log 2>&1`) and alert on non-zero exit.
10. **Re-evolving this skill loops on a documented blocker** — The adoption items (chmod, submodule init, wrapper deploy) are manual environment fixes, not skill gaps. If they're still unresolved, escalate to the operator instead of re-running the cycle on this skill.

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
