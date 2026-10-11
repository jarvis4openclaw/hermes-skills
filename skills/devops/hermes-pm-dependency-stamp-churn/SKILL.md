---
name: hermes-pm-dependency-stamp-churn
description: "Use when Hermes cron workers fail: ruamel import error."
version: 1.1.0
category: devops
author: Jarvis
license: Apache-2.0
tags: [hermes, cron, pm, dependencies, cron-worker, ruamel, install-out-of-sync]
metadata:
  hermes:
    tags: [hermes, cron, pm, ruamel]
    related_skills: [hermes-config-management, cron-noninteractive-guardrails, hermes-core-architecture]
    trigger_conditions:
      - "No module named 'ruamel'"
      - "Restart-safe cron worker exited with status 1"
      - "completing source-update dependencies"
      - "install out of sync (venv: out of sync with uv.lock)"
      - "cron worker exited before ownership acknowledgement"
      - "hermes pm install did not stop the churn"
      - "hermes prints completing source-update dependencies on every command"
      - "cron jobs fail in bursts while other jobs on the same box stay green"
      - "members_stamp changed with no code edit"
      - "hermes pm doctor says install out of sync"
      - "the plugin db got copied into every install generation"
      - "hermes pm gc reclaimed nothing right after the churn"
      - "a cron worker died importing a package that is clearly installed"
---

# PM dependency-stamp churn → cron worker import failures

## When to Use

- Cron jobs fail with `ModuleNotFoundError: No module named 'ruamel'` in the worker stderr.
- `hermes` prints `completing source-update dependencies...` on every invocation.
- `hermes pm doctor` / startup warns `install out of sync (venv: out of sync with uv.lock)`.
- A fix for `ruamel` in the venv does not stop the cron failures.
- Cron failures arrive in **bursts** (the jobs that fire during a sync) while sibling jobs stay green.
- `members_stamp()` returns a **different hash on two consecutive runs with no code edit**.
- A plugin keeps live runtime state inside its own directory (`db/*.sqlite`, `*.jsonl` logs) and
  `~/.hermes/installs/*/environments/*/` has grown one large generation per sync.
- `hermes pm gc` reclaims nothing immediately after the churn (the 24 h gate — expected, see Pitfalls).

## Not For

- **A cron job that fails for its own task-specific reason** (bad path, missing input file, failing
  remote call) — read that job's own output first; a `ruamel`-shaped import error is the only signal
  that points here. → use `durable-unattended-jobs` instead.
- **Config drift, provider/model wiring, or a broken `config.yaml`** → use `hermes-config-management` instead.
- **A job that behaves differently under cron than in an interactive shell** (approval gates, no TTY,
  blocked `execute_code`) → use `cron-noninteractive-guardrails` instead.
- **Choosing or rotating the model a cron job runs on to cut cost** → use `cron-model-optimization` instead.
- **The Hermes web UI or MCP servers failing to start** (not cron workers) → use `hermes-web-and-mcp-import-failures` instead.
- **Shipping an air-gapped/offline bundle of Hermes and its plugins** → use `offline-deploy-bundles` instead.
- **A job that must survive restarts without a supervisor at all** → use `durable-unattended-jobs` instead.

## Symptom

Several cron jobs fail intermittently with:

```
Restart-safe cron worker exited with status 1 after adopting this execution,
without writing a durable terminal state; whether side effects ran is unknown.
worker stderr: ... ModuleNotFoundError: No module named 'ruamel'
```

…and **every** `hermes <anything>` prints `hermes: completing source-update dependencies...`
before doing its work. Failures come in bursts — the jobs that fire while a sync runs —
while other jobs on the same box stay green.

## Why

`venv_is_current()` (pm/install.py) compares the recorded dependency stamp against
`Venv.expected_stamp()`, which hashes the *member plugin directories* via
`pm.workspace.members_stamp()`. That walk honoured only a tiny exclude set
(`.git .venv venv node_modules __pycache__`) and **did not read the member's own
`.gitignore`**. A plugin that keeps runtime state in its own directory therefore moves
the stamp on every write.

Real case: `~/.hermes/plugins/hermes-mneme/db/plugin.db` (250 MB live SQLite) plus
`trace.jsonl`. Every Mnemosyne write changed the stamp → the install was never
`current` → each launch re-synced dependencies, committed a **new generation**, and
collected the previous one — including the generation a running cron worker had pinned
on its `PYTHONPATH`. The worker then died importing `ruamel` (upstream #122222).

Same bug also copied the live DB into every generation (~250 MB × N).

## Diagnose

```bash
# 1. is the churn real?  any hermes command prints it on stderr
hermes --version 2>&1 | grep -i "completing source-update"

# 2. recorded vs expected stamp (committed site-packages must be on PYTHONPATH)
REPO=~/.hermes/hermes-agent
SP=$(PYTHONPATH=$REPO python3 -c "from pathlib import Path;from pm.environments import committed_venv,site_packages;print(site_packages(committed_venv(Path('$REPO'))))")
PYTHONPATH="$REPO:$SP" python3 - <<'EOF'
from pathlib import Path
from pm.lock import Facts
from pm.environments import runtime_facts_path
from pm.packages import Venv
root=Path.home()/'.hermes/hermes-agent'
fact=Facts(runtime_facts_path(root), strict=True).get('venv')
v=Venv(root)
print('recorded:', fact['stamp'])
print('expected:', v.expected_stamp(sorted(set(fact['extras']))))
EOF

# 3. runtime files living inside member dirs (what git ignores)
for d in ~/.hermes/plugins/*/; do git -C "$d" status --porcelain --ignored 2>/dev/null | grep '^!!'; done
```

A stamp that differs from the recorded one — and **changes between two runs with no code
edit** — is the churn. Do not chase the `ruamel` import: the venv is fine; the worker's
pinned generation is what vanished.

## Fix

Patch `pm/workspace.py` (back it up first; `hermes update` reverts it):

1. `_git_member_files(entry)` — `git -C <entry> ls-files -z --cached --others --exclude-standard`,
   filtered to paths that still exist; `None` when the member is not its own work tree.
2. `_member_ignore_for(entry)` — a `copytree` ignore keeping exactly that file set (plus its
   parent dirs); falls back to `_member_ignored` when the member is not a work tree.
3. `members_stamp()` — when the member has a `pyproject.toml` **and** `_git_member_files`
   returns a set, hash that set (name + bytes) instead of walking the tree.
4. `_workspace_member()` — `ignore=_member_ignore_for(plugin_dir)`.

Then commit a matching generation:

```bash
hermes pm install      # re-resolves and commits the stamp; minutes — run backgrounded
```

## Cleanup (no gateway stop needed)

A burst of churn leaves one generation per sync. `hermes pm gc` reclaims them **online** —
`collect_generations()` skips a generation when it is

1. the recorded *selected* one, or
2. not marked `.lease-managed`, or
3. younger than **24 h** (`min_age_seconds=86400`), or
4. holding a **live lease** — a kernel-locked file under `<generation>/.leases/`, taken by
   `activate_dependencies` for the lifetime of the process that booted from it.

So a running gateway/worker protects its own generation automatically; there is nothing to
stop. `hermes pm gc` is idempotent and safe to re-run.

Inspect the state first:

```bash
for g in ~/.hermes/installs/*/environments/*/; do
  printf '%s  leases=%s  age_h=%.1f  %s\n' "$(basename "$g")" \
    "$(ls "$g/.leases" 2>/dev/null | wc -l)" \
    "$(python3 -c "import os,time;print((time.time()-os.path.getmtime('$g'))/3600)")" \
    "$(du -sh "$g" | cut -f1)"
done
```

Because of the 24 h gate, a single pass right after churn reclaims almost nothing — the
fix is a **second pass a day later**. Schedule it once; do not lower `min_age_seconds`
(that gate is the shipped guard against a generation whose reader has not leased yet).

## Verify

- [ ] `venv_is_current(project_root=repo)` is `True`.
- [ ] `hermes --version` prints no `completing source-update dependencies`.
- [ ] `members_stamp()` twice around a write to the plugin's runtime file → **same** hash.
- [ ] The new generation's `workspace/plugin-sources/<member>/` has no `db/`/runtime log and is small.
- [ ] A previously failing agent cron job re-runs to `completed`.

## Pitfalls

1. **`hermes update` reverts the patch** — re-apply after updating or land it upstream; keep the
   `.bak-cronfix-*` backup path and re-check `venv_is_current()` after any update.
2. **`hermes cron doctor` reports history, not liveness** — it keeps showing a job's last failure
   until that job runs again; fixing the cause does not clear it retroactively.
3. **Never run `hermes cron run` from a command you will let time out** — the record lands `unknown`
   ("owner exited before a durable terminal state") even when the job itself was fine. Background it.
4. **A plugin `db/` copy under `plugin-sources/` is a snapshot, not the live store** — its mtime
   freezes at generation build time; the live DB is under `~/.hermes/plugins/<name>/`. Check mtimes
   before assuming you must migrate data.
5. **Do not "fix" this by symlinking the plugin's DB** — a symlinked directory is not walked, which
   hides the bug instead of fixing the stamp.
6. **Other profiles fail identically** (`~/.hermes/profiles/*/cron/`) — fix the shared install once,
   not per profile.
7. **`venv_is_current()` can read `True` while a worker still dies** — a worker already booted against
   a collected generation keeps failing until it restarts; let the gateway/worker recycle after the fix.
8. **`hermes pm gc` right after the fix reclaims almost nothing — that is correct** — the 24 h
   `min_age_seconds` gate plus live-lease protection. Schedule the second pass a day later; do not
   lower `min_age_seconds`.
9. **Chasing the `ruamel` import wastes the session** — the module is present; the generation the
   worker pinned vanished. Confirm with the stamp diff in §Diagnose before touching the venv.
10. **`git status --ignored` gives false negatives when the plugin dir is not its own work tree** —
    `_git_member_files()` returns `None` for non-work-tree members; fall back to the exclude-list
    behaviour and say so rather than reporting "no ignored files".
11. **`hermes pm install` is minutes-long and prints little** — run it backgrounded; a foreground run
    under a short timeout lands the job record `unknown` even when it succeeded.
