---
name: vault-cli-cron
description: Automate credential/secret-manager CLIs (Bitwarden bw, 1Password op, etc.) in unattended Hermes cron jobs as silent watchdogs. Covers the cached-master-key unlock pattern, per-process session tokens, PATH fixes after npm installs, and the cronjob script-path quirk.
version: 1.1.0
author: hermes-curator
metadata:
  hermes:
    tags: [vault, bitwarden, 1password, bw, op, cron, watchdog, secrets, credentials]
    trigger_conditions:
      - "run bw sync unattended"
      - "vault CLI in cron"
      - "bitwarden unlock without password"
      - "1password op item get in script"
      - "secret manager watchdog"
      - "bw session token per process"
      - "credential CLI scheduled job"
      - "cronjob script path relative hermes"
      - "npm global bin not on PATH"
      - "bw sync locked vault"
      - "unattended secret rotation"
      - "silent watchdog success no output"
---

# Vault CLI in Unattended Cron

## When to use
- User wants a scheduled job that runs a secret-manager / credential CLI (`bw sync`, `op item get`, `bw list`, ...) with NO human at the keyboard.
- The CLI normally needs a master password / unlock, but you want it unattended.
- You want failures surfaced but success to stay silent (watchdog pattern) — fits users who prefer low-noise output.

## Not For
- **Interactive vault access** — if a human is at the keyboard, plain `bw login` / `op` interactive flows are simpler → no cron skill needed.
- **Storing secrets in plaintext files** — this skill automates CLIs, it is not a substitute for a vault → use the vault itself.
- **Rotating credentials on a schedule with a human step** — if the rotation requires MFA/approval, it can't be fully unattended → surface it as an alert instead.
- **Managing the Hermes secret store** (`.env` / credential manager) — that's `hermes-config-management` / `vault-cli-cron` only covers external vault CLIs → see `hermes-memory-provider-management` for provider creds.

## Core principle (verified with Bitwarden, 2026-07-19)
Interactive `login` caches the master key locally. Unattended jobs must re-`unlock` each run to mint a fresh **per-process** session token — they do NOT need to re-enter the master password or re-authenticate to the server. A cron shell is always fresh, so:
1. Check `status`; if `locked`, run `unlock --raw` to get a session (no password prompt when the master key is cached).
2. Export the session var (`BW_SESSION` for bw) for that process only.
3. Run the action (`sync`, `list`, ...).
4. Leave it; the session dies with the process. The vault stays `locked` afterward — that is correct and expected.

Do NOT assume "sync works while locked." It only does if a session token is already in the environment. A truly locked vault with no session cannot decrypt. Always unlock first.

## Step-by-step
1. Install the CLI. For npm-based CLIs: `npm install -g @bitwarden/cli`.
   If the binary is not callable after install, npm's global bin (`~/.npm-global/bin` on this host) is likely NOT on PATH. Fix: `ln -sf ~/.npm-global/bin/<bin> ~/.local/bin/<bin>` (user-owned, on PATH, no sudo) — or add `~/.npm-global/bin` to PATH in `.bashrc`.
2. Log in ONCE, interactively, as the user: `bw login`. This caches the master key.
3. Write a watchdog script (see `scripts/bw-sync.sh` for a known-good Bitwarden example). Shape:
   - `#!/usr/bin/env bash`, `set -uo pipefail`.
   - Prepend the CLI to PATH: `export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:$PATH"`.
   - If `status` == locked → `SESSION=$(bw unlock --raw)`; `export BW_SESSION="$SESSION"`.
   - On unlock failure → print to stderr + `exit 1` (becomes the alert).
   - Run the action; on success `exit 0` with NO output (watchdog silence); on failure print to stderr + `exit 1`.
4. Register the cron job with the Hermes `cronjob` tool:
   - `action='create'`, `no_agent=true` (pure script, no LLM spend), `schedule='0 4 * * *'`.
   - **QUIRK:** the `script` parameter MUST be a filename relative to `~/.hermes/scripts/` (e.g. `bw-sync.sh`), NOT an absolute or `~`-prefixed path. An absolute path is rejected with "Script path must be relative to ~/.hermes/scripts/". Place the script there first.
   - `deliver='all'` so a failure alert reaches the user's channels; success stays silent.
5. Test it for real against a locked vault in a stripped environment (mimics cron):
   `env -i HOME=$HOME PATH=/usr/bin:/bin /bin/bash ~/.hermes/scripts/bw-sync.sh`
   Expect: exit 0, NO stdout, vault still `locked` afterward.

## Pitfalls
1. **Assuming no re-unlock needed** — a fresh cron shell has no session. You must `unlock` each run. (Re-login is NOT required — only unlock.)
2. **`bw sync` "succeeds" while locked in your interactive shell** — that is a leftover `BW_SESSION` from earlier, not proof sync works unattended. Recovery: test with `env -i HOME=$HOME PATH=/usr/bin:/bin /bin/bash <script>` to strip the environment.
3. **cronjob `script` absolute path rejected** — the `script` parameter must be a bare filename relative to `~/.hermes/scripts/`. Recovery: place the script there first, then use the bare name.
4. **`/usr/local/bin` needs sudo** — prefer a `~/.local/bin` symlink to avoid permission prompts in cron.
5. **Watchdog must be silent on success** — if the script echoes on success, the user gets daily noise. Recovery: only stderr + non-zero exit on failure.
6. **npm global bin not on PATH** — `npm install -g` succeeds but the binary is not callable because `~/.npm-global/bin` is missing from PATH. Recovery: `ln -sf ~/.npm-global/bin/<bin> ~/.local/bin/<bin>` (user-owned, no sudo) or add it to PATH in `.bashrc`.
7. **Unlock failure swallowed** — if `bw unlock --raw` fails silently and the script continues, the action runs against a locked vault. Recovery: on unlock failure print to stderr + `exit 1` immediately.
8. **Session token leaked to stdout on success** — printing `BW_SESSION` to stdout on a success path violates the watchdog silence contract and exposes the token in logs. Recovery: capture into a variable, never echo; only errors go to stderr.

## Verification
- `bw status` before/after should read `locked` (session is per-process).
- Script run under `env -i` returns exit 0 and prints nothing.
- Check next scheduled run via `cronjob(action='list')`; confirm `last_status` and `next_run_at`.

## Support files
- `references/bitwarden.md` — verified auth-state mechanics, exact command outputs, and the test recipe.
- `scripts/bw-sync.sh` — known-good daily `bw sync` watchdog; copy and adapt for other vault CLIs.
