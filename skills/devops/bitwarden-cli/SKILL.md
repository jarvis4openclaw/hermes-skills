---
name: bitwarden-cli
description: Install and operate the Bitwarden CLI (bw) on headless Linux/homelab hosts. Covers the CRITICAL gotcha that `bw sync` lies about success (exit 0 even when unreachable), the headless unlock keyring limitation, and a verified daily-sync cron watchdog pattern (Hermes + Telegram failure-only alerts). Use when installing bw, automating `bw sync`, or running bw without an interactive TTY.
version: 1.1.0
metadata:
  hermes:
    trigger_conditions:
      - "install bitwarden cli"
      - "bw sync not working"
      - "bw unlock headless"
      - "bitwarden vault sync cron"
      - "BW_SESSION export"
      - "vaultwarden mirror"
      - "bw import passwordless"
      - "bitwarden self-signed certificate"
      - "bw config server"
      - "bitwarden master password age"
      - "bw export plaintext json"
      - "headless bitwarden unlock"
      - "bitwarden sync watchdog"
---

# Bitwarden CLI (bw) — headless operation & automation

## When to Use

- Installing `bw` on a Linux VM / Proxmox CT / container.
- Automating `bw sync` (Hermes cron, systemd timer, watchdog).
- Any task where `bw` runs without an interactive TTY or OS keyring.
- Mirroring cloud Bitwarden to a self-hosted VaultWarden (Model B, one-way).
- Secret injection into unattended jobs (age-encrypted master password).

## Not For

- Interactive desktop vault use → use the Bitwarden desktop app or browser extension instead
- Team password sharing workflows → use Bitwarden orgs / SSO instead of CLI scripting
- Storing secrets in plaintext configs → use `vault-cli-cron` patterns with age/encrypted envelopes instead
- High-frequency API token access → use Bitwarden Secrets Manager (separate product) instead

## Install (npm global + PATH fix)
```bash
npm install -g @bitwarden/cli
# npm global bin (~/.npm-global/bin) is NOT on PATH by default on this host.
# Symlink into a user-owned dir on PATH — avoids sudo:
ln -sf "$(npm prefix -g)/bin/bw" ~/.local/bin/bw
bw --version   # should report e.g. 2026.6.0
```

## CRITICAL: `bw sync` cannot be trusted for success
**Verified 2026-07-19 (bw 2026.6.0, Debian 13):** `bw sync` returns exit `0` and prints
`"Syncing complete."` EVEN when the server is unreachable (tested against RFC5737
`192.0.2.1`, where TCP returns rc=124) AND even with no session token. `lastSync`
advances on every attempt regardless.

**Never gate alerting on `bw sync`'s exit code or on `lastSync` age as a success signal.**
The only honest signals available:
1. Network/service reachable → check yourself with `curl https://api.bitwarden.com`
   (bw gives NO usable signal for outages).
2. Vault `unauthenticated` → `bw status` honestly reports this string (rare; server
   token expiry). A merely `locked` vault still syncs fine.

## Headless unlock — VERIFIED (2026-07-19, bw 2026.6.0)
`bw unlock --passwordenv BW_MP` / `--passwordfile FILE` / `--password "$MP"` **WORKS in a
headless shell** (no OS keyring needed). Our account has no 2FA, so unattended
login+unlock+decrypt is fully possible if the master password is available (e.g. decrypted
from an `age`-encrypted file at runtime).

**THE REAL TRAP (cost a full debugging cycle):** `bw unlock --raw` prints the session key to
stdout — it does NOT auto-apply it. If you discard that output, the next `bw list` /
`bw import` / `bw delete` **re-prompts for the master password** (interactive → fails under
cron / swallows to nothing). You MUST capture it and export `BW_SESSION`:

```bash
S=$(BITWARDENCLI_APPDATA_DIR="$HOME" bw unlock --passwordenv BW_MP --raw 2>/dev/null)
export BW_SESSION="$S"
# now bw list/import/delete run non-interactively
```

`bw login --passwordenv BW_MP <email>` returns "You are logged in!" but does NOT set a
session — still export `BW_SESSION` from a follow-up `bw unlock --raw` for any decrypting cmd.

`bw sync` while **locked** downloads the encrypted blob with no password (fine for sync-only
jobs). Decrypting commands (`list`/`export`/`import`) need `BW_SESSION`.

> Past mistake baked into this skill (now corrected): it claimed `bw unlock --raw` *prompts*
> for the password in headless shells and that unattended decryption is impossible. That was
> WRONG — the flag works; the only failure was not capturing `BW_SESSION`. Do not repeat.

## Cron watchdog pattern (Hermes)
- Use a `no_agent: true` script job; `deliver: telegram:CHATID`.
- **A `no_agent` job delivers STDOUT verbatim.** Failure reasons MUST go to STDOUT
  (use `tee /dev/stderr` if you also want them in logs). Text on stderr is NOT delivered.
- Silent on success (empty stdout → no delivery); emit a reason line on failure.
- Gate failure detection on: (1) `bw status` == `unauthenticated`, (2) curl reachability
  to `api.bitwarden.com`. NOT on `bw sync` exit code.
- Script path in `cronjob create` must be relative to `~/.hermes/scripts/`
  (e.g. `bw-sync.sh`, not an absolute path).
- Run once to verify: `cronjob(action='run', job_id=...)`; confirm `last_status` and that
  you did NOT receive a success message.

## Testing methodology (headless simulation)
- Fresh cron shell: `env -i HOME=$HOME PATH=/usr/bin:/bin /bin/bash script.sh`
- Isolate bw state without touching the real vault: `BW_DATA_HOME=/tmp/bw-test ...`
- Force unreachable server: `BW_SYNC_API_HOST=https://192.0.2.1 script.sh` (RFC5737,
  curl rc=28). (Reproduce the `unauthenticated` state safely is hard — a fresh
  `BW_DATA_HOME` reports `locked`, not `unauthenticated` — so that branch is code-correct
  but not runtime-proven. Say so if asked.)

## Pitfalls
1. **`bw config server` prints a plain URL** (`https://bitwarden.com`), NOT JSON — grepping
   its output for `"baseUrl"` silently fails and falls through to the default. Parse the URL
   directly; default server is `https://vault.bitwarden.com`.
2. **`/usr/local/bin` needs sudo here** — use `~/.local/bin` for the symlink instead.
3. **`bw sync`'s "Syncing complete." is not evidence of a successful sync** — exit code and
   `lastSync` both lie when the server is unreachable. Gate alerting on `bw status` +
   `curl https://api.bitwarden.com` only (see CRITICAL section).
4. **Encrypted export + passwordless import = silent item loss (verified 2026-07-26).**
   `bw export --password "$BW_MP"` produces a `passwordProtected: true` JSON file.
   `bw import bitwardenjson <file>` has NO `--password` flag — it prompts interactively
   for the import password. In cron (no TTY), the prompt silently fails and **newly
   created items are dropped** while older items import fine (the count appears stable
   because the missing items are always the newest ones). The script's `>/dev/null 2>&1`
   hides the error. **FIX:** omit `--password` from `bw export` to get a plaintext JSON
   (the file is already `chmod 600` and `shred`-ed after import, so encryption at rest is
   unnecessary for the ephemeral window). See `references/vw-mirror-debug-2026-07.md`
   for the full investigation.
5. **`bw unlock --raw` output must be captured** — it prints the session key to stdout and
   does NOT auto-apply it. Discarding it makes the next `bw list`/`import`/`delete`
   re-prompt for the master password (interactive → fails under cron). Always
   `export BW_SESSION="$(... bw unlock --raw ...)"`.
6. **`BW_DATA_HOME` does NOT relocate the logged-in account** — use
   `BITWARDENCLI_APPDATA_DIR` for per-server isolation; verify with `bw status`
   showing the new `serverUrl` (see Cross-server section).
7. **Self-signed TLS chains are rejected by default** — `bw status` looks fine (reads local
   state) but login/sync/export/import fail with `self-signed certificate in certificate
   chain`. Export the full chain with `openssl s_client -showcerts` and set
   `NODE_EXTRA_CA_CERTS`. Do NOT reach for `NODE_TLS_REJECT_UNAUTHORIZED=0`.
8. **`bw import encrypted_json` is rejected** — the importer label is `bitwardenjson`
   (one word). `encrypted_json` exports can't be re-imported by the CLI at all; always
   export plain `json` for mirroring.
9. **Per-item `bw delete item <id>` times out on large vaults** (4604 items > 180s cron
   window, even parallel). Wipe via the VaultWarden SQLite DB on StartOS instead
   (instant, atomic; back up the DB first). `bw import` appends — never dedupes.
10. **Master password at rest** — `age`-encrypt to `~/.bitwarden/master.age`, decrypt at
    runtime with the age key, `chmod 600`, and `shred` the decrypted export after import.
    NEVER plaintext in chat or a world-readable file.
11. **Wipe-then-import is destructive** — it makes cloud authoritative; anything added
    directly to VW is erased each run. For a non-destructive copy use Model A (export-only).
12. **VaultWarden admin REST API routes returned 404/401 on this build** — do NOT rely on
    them; use `bw` against VW or the SQLite DB directly. Admin token lives in `config.json`
    on StartOS (read via `ssh`/`sudo cat`).

## Cross-server sync / VaultWarden mirror (Model B, one-way cloud -> self-hosted)
Bitwarden servers are independent; there is NO native merge. `bw import` **appends** (no
dedupe) — repeated imports pile up duplicates. Verified working recipe (2026-07-19):

- **Per-server isolation uses `BITWARDENCLI_APPDATA_DIR`, NOT `BW_DATA_HOME`.** The latter
  does NOT relocate the logged-in account; the former does. Real cloud store stays at
  `~/.config/Bitwarden CLI`. Set the VW home's server once:
  `BITWARDENCLI_APPDATA_DIR=~/.bitwarden/vaultwarden bw config server https://VW_HOST:PORT`
  (this works ONLY on a home with no logged-in account; if "Logout required" appears, the
  env var isn't taking effect — verify with `bw status` showing the new `serverUrl`).
- **Self-signed StartOS TLS is NOT accepted by default.** `bw status` reads local state and
  never hits the cert, so it looks fine — but `bw login`/`sync`/`export`/`import` then fail
  with `self-signed certificate in certificate chain`. FIX: export the **full cert chain**
  (leaf + intermediate + root) via
  `openssl s_client -connect HOST:PORT -servername NAME -showcerts` and point
  `NODE_EXTRA_CA_CERTS=/path/to/chain.pem`. (Do NOT use `NODE_TLS_REJECT_UNAUTHORIZED=0`
  if the targeted chain works — it does here.)
- **Export flag:** `bw export --format json --output f.json` — omit `--password` for
  plaintext export (required for unattended import). See pitfall below.
  (NOT `--passwordenv` — export does not accept it; NOT `encrypted_json`, see below.)
- **Import label is `bitwardenjson` (one word).** `bw import encrypted_json f.json` is
  REJECTED ("Proper importer type required"). Use `bw import bitwardenjson f.json`.
  `encrypted_json` exports can't be re-imported by the CLI at all — export **json** (the
  standard bitwarden json) for mirroring.
- **Capture `BW_SESSION`** after every `unlock`/`login` (see Headless unlock section) or
  `list`/`import` re-prompt for the password.
- **WIPE before import (destructive):** `bw import` appends, so to *replace* the vault you
  must wipe VW first. **Per-item `bw delete item <id>` TIMES OUT** for large vaults
  (4604 items > the 180s Hermes cron window, even parallel). FAST fix: delete directly in
  the VaultWarden SQLite DB on StartOS (instant, atomic):
  ```bash
  ssh start9@VW_HOST sudo sqlite3 /path/db.sqlite3 "BEGIN; \
    DELETE FROM favorites WHERE user_uuid=(SELECT uuid FROM users WHERE Email='U'); \
    DELETE FROM folders_ciphers WHERE folder_uuid IN (SELECT uuid FROM folders WHERE user_uuid=(SELECT uuid FROM users WHERE Email='U')); \
    DELETE FROM folders WHERE user_uuid=(SELECT uuid FROM users WHERE Email='U'); \
    DELETE FROM ciphers_collections WHERE cipher_uuid IN (SELECT uuid FROM ciphers WHERE user_uuid=(SELECT uuid FROM users WHERE Email='U')); \
    DELETE FROM ciphers WHERE user_uuid=(SELECT uuid FROM users WHERE Email='U'); \
    DELETE FROM sends WHERE user_uuid=(SELECT uuid FROM users WHERE Email='U'); \
    COMMIT;"
  ```
  Table PKs are `uuid`/`user_uuid` (not `Id`/`UserId`). Back up the DB first.
- **Master password at rest:** `age`-encrypt to `~/.bitwarden/master.age`; decrypt at runtime
  with `age --decrypt -i ~/.bitwarden/keys/age-key.txt`. NEVER plaintext in chat or a
  world-readable file (`chmod 600`). The decrypted plaintext export must be `shred`-ed after
  import (master pw never persists on disk).
- **Destructive default:** wiping-then-import makes cloud authoritative. Anything added
  directly to VW is erased each run. For a non-destructive copy, use Model A (export-only
  backup, no import).
- VaultWarden admin token lives in `config.json` on StartOS at
  `/media/startos/data/package-data/volumes/vaultwarden/data/main/config.json`
  (read via `ssh`/`sudo cat`). LAN-only; acceptable for read-only inventory. NOTE: the
  admin REST API routes on this build returned 404/401 — do NOT rely on them; use `bw`
  against VW or the SQLite DB instead.

## Files in this skill
- `scripts/bw-sync.sh` — verified daily-sync watchdog (silent on success, Telegram on failure).
- `references/vaultwarden-sync.md` — instance details + corrected mirror recipe.
- `references/bw-quirks.md` — reproduced quirks + reproduction recipes.
- `references/secret-injection.md` — age-encrypt a master password for unattended cron
  (quoted-here-doc method; why `echo -n "$PW"` fails; runtime decrypt pattern).
- `references/vw-mirror-debug-2026-07.md` — full investigation of silent item loss in the
  VW mirror (encrypted export + passwordless import in cron = dropped items).
- `scripts/bw-vw-mirror.sh` — verified one-way cloud->VaultWarden mirror (wipe via SQLite +
  import `bitwardenjson`). Copy to `~/.hermes/scripts/`; requires `~/.bitwarden/master.age`.
