---
name: clawd-workspace-backup
description: Use when the clawd nightly GitHub backup fails or needs rotating.
version: 1.1.0
category: devops
tags: [backup, git, github, cron, clawd, deploy-key, durability]
metadata:
  hermes:
    related_skills: [unattended-git-sync-durability, scheduled-job-decommissioning, hermes-config-management, ssh-file-deploy]
    trigger_conditions:
      - "clawd backup"
      - "gitclaw-backup"
      - "nightly backup failing"
      - "signal-scheduler-auto-sync"
      - "clawd-workspace-backup"
      - "b390289f506d"
      - "clawd workspace not on GitHub"
      - "cron reports ok but nothing was pushed"
      - "deploy key for the backup repo"
      - "rotate the backup deploy key"
      - "backup remote is behind"
      - "why is the clawd repo so large"
      - "backup pushed nothing overnight"
---

# clawd workspace → GitHub nightly backup

Off-box copy of the entire `/home/wahid/clawd` workspace, pushed nightly to the **private** repo
`jarvis4openclaw/gitclaw-backup`.

| Detail | Value |
|---|---|
| Cron job | `b390289f506d` (`clawd-workspace-backup`), `0 0 * * *`, no_agent, deliver local |
| Script | `/home/wahid/.hermes/scripts/clawd-workspace-backup.sh` |
| Repo | `/home/wahid/clawd` (remote `origin`, branch `master`) |
| Remote | `git@github.com:jarvis4openclaw/gitclaw-backup.git` (no credential in the URL) |
| Auth | SSH deploy key `~/.ssh/id_ed25519_gitclaw_backup`, write-enabled, pinned per-repo via `core.sshCommand` in `/home/wahid/clawd/.git/config` |

**The old name lied.** The script was formerly `signal-scheduler-auto-sync.sh` but was renamed to
`clawd-workspace-backup.sh` (2026-09-10) to match what it actually does. It `cd`s into
`/home/wahid/clawd/signal-scheduler`, which has **no `.git` of its own** — `git rev-parse --show-toplevel`
resolves to `/home/wahid/clawd`. So every run commits and pushes the **whole clawd workspace**, not the
Signal Scheduler subfolder. Do not reason about this backup as if it were scoped to `signal-scheduler/`.

## When to Use

- The nightly `clawd-workspace-backup` cron job reports a failure, or you suspect it has been silently failing.
- You need to prove the clawd workspace commit is actually **off-box** (on `jarvis4openclaw/gitclaw-backup`), not just committed locally.
- The remote is behind local `HEAD` and you need to find out why the push is not landing.
- You are **rotating the SSH deploy key** used by `/home/wahid/clawd/.git/config` (`core.sshCommand`).
- You are auditing a `cron` job whose `last_status` is `ok` but whose side effect never happened.
- You are reasoning about the rename from `signal-scheduler-auto-sync.sh` and need to know what the job actually pushes.
- You need to know the on-disk cost and caveats of the backup repo before proposing a rebuild or restore.

## Not For

- **General durability patterns for unattended git sync jobs** → use `unattended-git-sync-durability` instead
- **Retiring or disabling a scheduled job** → use `scheduled-job-decommissioning` instead
- **Editing Hermes config / cron definitions generally** → use `hermes-config-management` instead
- **Getting files onto a remote host with verification** → use `ssh-file-deploy` instead
- **Handling the non-interactive approval gate in cron runs** → use `cron-noninteractive-guardrails` instead

## Verify (do this instead of trusting local git state)

```bash
cd /home/wahid/clawd
git status -sb                 # expect '## master...origin/master' with no [ahead N]
git ls-remote origin           # expect the same SHA as: git rev-parse HEAD
GH_TOKEN=$(gh auth token --user jarvis4openclaw) \
  gh api repos/jarvis4openclaw/gitclaw-backup/commits/master --jq '{sha,date:.commit.committer.date}'
hermes cron runs b390289f506d  # recent runs must be 'completed', not masking a dead push
```

The API check is the only one that proves the commit is really *off-box*. `git status -sb` compares
against a stale `origin/master` ref and will happily say "up to date" while the remote is behind.

## Rules

1. **Never embed a credential in the remote URL.** A `<user>:ghp_...@github.com` URL silently rots
   when the token dies — it went unnoticed for four nights (2026-09-07..09-10) before anyone looked.
   Keep the URL credential-free (SSH deploy key, or HTTPS + the `gh auth git-credential` helper).
2. **A backup script must exit non-zero when the push fails.** The old script ran a bare
   `git push` and then echoed "Changes pushed to GitHub" unconditionally, so cron recorded
   `last_status: ok` on every failed night. `set -euo pipefail` + an explicit `if ! git push` check is
   the fix; proof of the fix is a *failure-path* test (run the script against an unreachable remote and
   confirm non-zero exit and no success line), not a reading of the code.
3. **Never reuse an account-wide SSH key as a deploy key.** GitHub scopes a deploy key to exactly one
   repository, and `~/.ssh/id_ed25519_gitwahidsaleemi` is mapped to `github.com` globally so that
   `wahidsaleemi/timelock-gift` can be pushed. Registering that key as a deploy key would hijack the
   global identity and break those pushes. Use a dedicated per-repo key + `core.sshCommand`.
4. **Deploy keys need admin on the repo to register.** The `jarvis4openclaw` gh token has admin here;
   `gh auth token --user jarvis4openclaw` must be used explicitly, since `wahidsaleemi` gets 404 on
   this repo. Deploy-key registration is an external write — confirm with the user first.
5. **Failure belongs in the cron status, not in a chat message.** A non-zero exit surfaces in
   `hermes cron list` as a non-ok run; do not paper over it with a wrapper that always exits 0.

## Rotating the deploy key

```bash
ssh-keygen -t ed25519 -N '' -C "clawd-nightly-backup@$(hostname)" -f ~/.ssh/id_ed25519_gitclaw_backup
export GH_TOKEN=$(gh auth token --user jarvis4openclaw)
gh api --method POST repos/jarvis4openclaw/gitclaw-backup/keys \
  -f title="clawd nightly backup" -f key="$(cat ~/.ssh/id_ed25519_gitclaw_backup.pub)" -F read_only=false
gh api repos/jarvis4openclaw/gitclaw-backup/keys --jq '.[] | {id,title,read_only,last_used}'
```

Then update `core.sshCommand` in the repo config and delete the superseded key by id
(`gh api --method DELETE repos/jarvis4openclaw/gitclaw-backup/keys/<id>`).

## Pitfalls

**Environment wrinkles already observed on this host:**

1. **`/home/wahid/clawd/.git` is ~15 GB** — far larger than the working tree warrants. Not a defect of
  this backup path, but it makes every clone/restore expensive; flag it before proposing a rebuild.
2. **`SETUP.md` points at a dead remote** — `/home/wahid/clawd/SETUP.md` still documents `wahidsaleemi/gitclaw-backup.git` (404s) instead of `jarvis4openclaw/gitclaw-backup`. Fix the doc, not just the config.
3. **A dead `ghp_` token is quoted in tracked history** — `memory/archive/2026-02-14.md` contains the now-dead `ghp_` token (it returns 401). Rewriting history to remove it is not worth the cost while the token stays dead — but do not re-introduce it anywhere new.
4. **Legacy `/home/wahid/.local/bin/backup-openclaw.sh` is dormant** — it claims its tarball is "picked up by daily workspace backup (1 AM)", but no cron entry schedules it any more. Do not assume it runs.
5. **A stale `~/.git-credentials` entry is silently shadowed** — `credential.helper=store` holds an old github.com entry, shadowed by the `gh` helper in this setup. Only the active `gh` account matters for HTTPS pushes; do not "fix" pushes by editing that file.

**Failure modes this job has actually hit (read these before touching the remote):**

6. **A credential embedded in the remote URL rots silently** — a `<user>:ghp_...@github.com` URL keeps working until the token dies, then fails unnoticed. It went undetected for four nights (2026-09-07…09-10). Keep the URL credential-free: SSH deploy key, or HTTPS + the `gh auth git-credential` helper.
7. **A backup script that exits 0 when the push fails** — the old script ran a bare `git push` then echoed "Changes pushed to GitHub" unconditionally, so cron recorded `last_status: ok` every night. Fix with `set -euo pipefail` plus an explicit `if ! git push` check, and prove it with a *failure-path* test (run against an unreachable remote, confirm non-zero exit and no success line) — not by reading the code.
8. **Trusting `git status -sb`** — it compares against a stale `origin/master` ref and will happily print "up to date" while the remote is behind. Only `git ls-remote origin` plus the GitHub API commit lookup proves the commit is off-box.
9. **Reading `hermes cron runs b390289f506d` as success without an off-box check** — a run can be `completed` and still mask a dead push; pair the run status with the API check.
10. **Reusing an account-wide SSH key as a deploy key** — GitHub scopes a deploy key to exactly one repository, and `~/.ssh/id_ed25519_gitwahidsaleemi` is mapped to `github.com` globally so `wahidsaleemi/timelock-gift` can push. Registering it as a deploy key hijacks that global identity and breaks those pushes. Use a dedicated per-repo key with `core.sshCommand`.
11. **Using the wrong gh account for the backup repo** — the `jarvis4openclaw` token has admin; `wahidsaleemi` gets 404. Always be explicit: `GH_TOKEN=$(gh auth token --user jarvis4openclaw) gh api repos/jarvis4openclaw/gitclaw-backup/...`.
12. **Registering a deploy key without confirming first** — deploy-key registration is an external write on a repo. Confirm with the user before running the `POST .../keys` call.
13. **Deleting the old deploy key before the new one is proven** — rotate in order: generate the key, register it, confirm `last_used` on the new key id, update `core.sshCommand`, then delete the superseded key by id.
14. **Papering over failure with a wrapper that always exits 0** — failure belongs in the cron status (visible in `hermes cron list`), not in a chat message that hides it.

## Verification

- [ ] `git ls-remote origin` SHA equals `git rev-parse HEAD` in `/home/wahid/clawd`.
- [ ] The GitHub API commit lookup returns the same SHA with a recent committer date.
- [ ] `hermes cron runs b390289f506d` shows recent runs `completed` (not merely present).
- [ ] The failure path was exercised at least once (unreachable remote → non-zero exit).
- [ ] No credential appears in the remote URL of `/home/wahid/clawd`.
