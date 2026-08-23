---
name: signal-scheduler
description: Manage the Signal Scheduler — a web-based scheduler (Next.js 16) that posts messages to Signal groups and auto cross-posts to Nostr with opt-in LinkedIn cross-posting via Zernio API. Runs on Proxmox CT 200 at 192.168.100.47. Covers the web UI, background scheduler, signal-cli-rest-api Docker container, dual Nostr identity architecture, Blossom image uploads, LinkedIn integration, systemd services, and troubleshooting. Use when asked to inspect, fix, schedule posts, or configure anything on the Signal Scheduler.
version: 1.1.0
category: devops
tags: [signal, nostr, linkedin, scheduler, cross-posting, proxmox, nextjs, docker, zernio]
metadata:
  hermes:
    trigger_conditions:
      - "signal scheduler"
      - "schedule a signal message"
      - "check signal scheduler posts"
      - "fix signal scheduler"
      - "restart signal-scheduler"
      - "cross-post to LinkedIn"
      - "nostr cross-posting"
      - "signal-scheduler logs"
      - "signal-cli-rest-api"
      - "blossom image upload"
      - "192.168.100.47"
      - "CT 200"
      - "signal scheduler service"
---

# Signal Scheduler

Web-based scheduler for posting messages to Signal groups with automatic Nostr cross-posting and opt-in LinkedIn cross-posting via Zernio API. Supports images.

## When to Use

- User says "signal scheduler", "schedule a Signal post", or references CT 200
- User needs to check scheduled posts, their status, or LinkedIn cross-post status
- User wants to restart the scheduler or web UI services
- User needs to debug why posts aren't sending (Signal, Nostr, or LinkedIn)
- User asks about cross-posting architecture (dual Nostr identities, Blossom uploads)
- User needs to rebuild the web UI after code changes
- User is troubleshooting Signal authentication or the signal-cli-rest-api Docker container
- User needs to query the scheduler SQLite database directly

## Not For

- **Posting directly to Nostr from the agent** → use `nostrx` instead (agent's own Nostr identity)
- **Deploying or modifying Proxmox containers** → use `proxmox-host-management` instead
- **Managing SSH keys or connectivity to 192.168.100.47** → this is a private LAN address; verify connectivity first
- **Debugging Zernio API issues outside the scheduler** → Zernio is an external service; the scheduler only calls it
- **Editing scheduler code in the local filesystem** → all code lives on CT 200 at `/opt/signal-scheduler/`; use SSH
- **Managing Docker containers generally** → this skill covers only the `signal-api` container on CT 200
- **Bulk-scheduling or campaign management** → the scheduler handles individual posts, not campaign orchestration

## Quick Reference

| Detail | Value |
|---|---|
| Host | Proxmox CT 200 |
| IP | 192.168.100.47 |
| SSH | root@192.168.100.47 (key auth) |
| App path | /opt/signal-scheduler |
| Nostr path | /opt/nostr-social |
| Web UI port | 3000 |
| Signal API port | 8080 |
| Signal phone number | +17025768110 |
| Scheduler npub | npub156spnmrgn4av0y6qkw3mjhlar0jpwe3ytmmu0guuxx66qsy5g8xqhzkzcm |
| Repo | https://github.com/jarvis4openclaw/signal-scheduler.git |

## Architecture

```
Signal Scheduler CT (192.168.100.47)
├── signal-scheduler-web.service    → Next.js 16 web UI on :3000
├── signal-scheduler.service        → node-cron scheduler (every minute)
├── signal-api (Docker container)   → signal-cli-rest-api on :8080
├── /opt/nostr-social/             → Nostr CLI for cross-posting
└── Zernio API (external)           → LinkedIn cross-posting (opt-in)
```

Database: SQLite at /opt/signal-scheduler/data/scheduler.db

## Backup & Disaster Recovery

The app code lives in a Git repo and is backed up by pushing to GitHub. The SQLite database is also tracked in git, so scheduled/sent posts are protected as long as the DB is committed and pushed. However, secrets and uploaded images are **not** backed up by default.

### What is backed up

| Asset | Backed up? | How |
|---|---|---|
| Source code (app/, scripts/, lib/, config) | ✅ | `git push origin main` |
| SQLite DB (`data/scheduler.db`) | ✅ | Tracked in git; committed and pushed |
| DB schema / empty template | ✅ | `data/schema.sql`, `data/scheduler.db.empty` |
| `.env` secrets (Zernio key, Signal config) | ✅ | Gitignored, but copied nightly to NAS `/archive/vm-backups/signal-scheduler/signal-scheduler.env` |
| Uploaded images (`uploads/`) | ✅ | Gitignored, but copied nightly to NAS `/archive/vm-backups/signal-scheduler/uploads/` |
| Entire CT OS/state | Maybe | Verify Proxmox PBS/VM backup job separately |

### Verify current backup state

```bash
# Git remote, last commit, uncommitted changes
ssh root@192.168.100.47 'cd /opt/signal-scheduler && git remote -v && git log --oneline -3 && git status --short'

# Confirm local DB matches GitHub
ssh root@192.168.100.47 'cd /opt/signal-scheduler && ls -l data/scheduler.db && git ls-tree -r HEAD --long data/scheduler.db'

# Download GitHub copy and compare counts/integrity
ssh root@192.168.100.47 '
  cd /opt/signal-scheduler &&
  TOKEN=$(grep -oP "ghp_[A-Za-z0-9_]{36}" .git/config | head -1) &&
  curl -s -L -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github.v3.raw" \
    https://api.github.com/repos/jarvis4openclaw/signal-scheduler/contents/data/scheduler.db \
    -o /tmp/gh-scheduler.db &&
  sqlite3 /tmp/gh-scheduler.db "PRAGMA integrity_check; SELECT status, COUNT(*) FROM posts GROUP BY status;"
'

# Scheduled-post horizon
ssh root@192.168.100.47 'sqlite3 /opt/signal-scheduler/data/scheduler.db "SELECT MIN(scheduled_at), MAX(scheduled_at), COUNT(*) FROM posts WHERE status = '\''scheduled'\''"'

# DB integrity check
ssh root@192.168.100.47 'sqlite3 /opt/signal-scheduler/data/scheduler.db "PRAGMA integrity_check;"'
```

### Manual backup when you schedule far ahead

After bulk-scheduling posts, commit and push immediately:

```bash
ssh root@192.168.100.47 '
  cd /opt/signal-scheduler &&
  git add data/scheduler.db &&
  git commit -m "backup: update scheduler.db with posts through <month>" &&
  git push origin main
'
```

### Restoring the DB

```bash
# From GitHub
ssh root@192.168.100.47 '
  cd /opt/signal-scheduler &&
  git checkout main -- data/scheduler.db &&
  systemctl restart signal-scheduler signal-scheduler-web
'
```

### Automated NAS backup

A nightly cron job on CT 200 pushes a SQLite-safe snapshot, the `.env` file, and uploaded images to the NAS via rsync over SSH:

```bash
# Runs daily at 03:17
/usr/local/bin/signal-scheduler-backup.sh
```

- Source CT: `192.168.100.47`
- Target NAS: `192.168.100.33:/archive/vm-backups/signal-scheduler`
- Keeps last 14 timestamped DB snapshots as `scheduler.db.YYYYMMDD-HHMMSS.bak`
- Logs to `/var/log/signal-scheduler-backup.log`

Because CT 200 is unprivileged, it cannot mount NFS/CIFS directly; the backup uses an ed25519 SSH key (`/root/.ssh/signal-scheduler-backup`). See `references/backup-disaster-recovery.md` for the full script and setup notes.

### PBS / VM-level backups

- `pvesh` and Proxmox config files are **not visible from inside the CT**.
- To verify PBS scheduling/retention, inspect the Proxmox host directly (Datacenter → Backup).
- Do not assume the CT is in a PBS job just because other CTs are; selection lists are per-job.

See `references/backup-disaster-recovery.md` for the full audit recipe and recovery checklist.

## Services (systemd)

```bash
# Check status
systemctl status signal-scheduler-web
systemctl status signal-scheduler

# Logs
journalctl -u signal-scheduler -n 100 --no-pager
journalctl -u signal-scheduler-web -n 50 --no-pager

# Restart
systemctl restart signal-scheduler
systemctl restart signal-scheduler-web
```

## Key Files

| File | Purpose |
|---|---|
| /opt/signal-scheduler/app/page.tsx | Frontend React/Next.js UI (forms, posts list, LinkedIn checkbox) |
| /opt/signal-scheduler/app/api/posts/route.ts | POST/GET API route (handles linkedin_status in form data) |
| /opt/signal-scheduler/app/api/posts/[id]/route.ts | PATCH/DELETE API route (handles linkedin_status updates) |
| /opt/signal-scheduler/scripts/scheduler.ts | Core scheduler: Signal + Nostr + LinkedIn cross-post logic |
| /opt/signal-scheduler/scripts/nostr.js | Nostr post/directmention/reply CLI |
| /opt/signal-scheduler/scripts/blossom-upload.js | Blossom multi-server image upload |
| /opt/signal-scheduler/scripts/test_scheduler.test.ts | LinkedIn integration tests |
| /opt/signal-scheduler/.env | Environment config (incl. ZERNI0_API_KEY) |
| /opt/signal-scheduler/data/scheduler.db | SQLite database |
| /opt/nostr-social/.nostr/secret.key | Scheduler's Nostr private key |

## X / Twitter Cross-Posting (added 2026-08-22)

Every post can also cross-post to **X/Twitter** via the official API v2 (OAuth 1.0a, HMAC-SHA1 signed inline in scheduler.ts — zero extra dependencies). Opt-in via the "Cross-post to X" checkbox.

- Credentials live in `/opt/signal-scheduler/.env` (`X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`) — these are the @wahiddotmy free-tier creds originally from nostrX on CT 202.
- Per-channel status: `x_status` column in posts table (`pending`/`sent`/`failed`/`disabled`). Same lifecycle as `linkedin_status`.
- **Confirmed (2026-08-22):** X **discontinued the free tier entirely as of 2026-02-06** — pay-per-usage credits only ($0.015/post, $0.20/post with a link, $0.005/read). Free credits no longer exist and do not refresh; @wahiddotmy's 402 credits-depleted is permanent until credits are purchased. The X checkbox therefore defaults OFF in the UI, but all posting code stays ready if credits are ever bought.
- **Zernio also supports platform 'twitter'** but bills per post — user rejected it; keep using direct API.
- User-created app keys exist at CT 200 `/opt/.env` (valid consumer keys, HTTP 200 on request_token) but have NO paired user access tokens. Access tokens are app-bound; pairing nostrX's tokens to that app fails (code 37). Using that app would require the PIN-based OAuth authorize flow.

## Quick Schedule UI (added 2026-08-22)

New-post form has a Morning/Afternoon radio picker: Morning = 8:21 AM, Afternoon = 3:21 PM (local America/Chicago). The datetime defaults to the day AFTER the last already-scheduled post (or tomorrow if none), at the slot time. The field stays editable. Implemented client-side in page.tsx (`computeSlotDatetime`).

## How Cross-Posting Works

Signal + Nostr are always tried. LinkedIn and X are opt-in via checkbox:

1. Post is due (scheduled_at <= now)
2. Image uploaded ONCE to Blossom, URL shared across channels
3. `sendToSignal()` fires via signal-cli-rest-api
4. `sendToNostr()` fires via nostr.js — message piped over STDIN via spawn (shell-injection-safe)
5. If `linkedin_status === 'pending'`, `postToLinkedIn()` fires via Zernio API
6. If `x_status === 'pending'`, `sendToX()` fires via Twitter API v2
7. If ANY succeed → post marked "sent"; per-channel columns record each outcome
8. Only if ALL fail → post marked "failed"

### LinkedIn Cross-Posting

LinkedIn integration uses Zernio's unified social API. It is opt-in — users must check the "Cross-post to LinkedIn" checkbox when scheduling a post.

- Endpoint: `POST https://api.zernio.com/v1/posts`
- Auth: `Bearer <ZERNI0_API_KEY>` from .env (`ZERNI0` contains a zero)
- Account ID: Zernio SocialAccount `_id` `6a26f3c92b2567671a2dcbf4` (Wahid X LinkedIn), override with `ZERNI0_LINKEDIN_ACCOUNT_ID`
- Payload shape: `{ content, platforms: [{ platform: 'linkedin', accountId }], publishNow: true, mediaItems?: [{ type: 'image', url }] }`
- Image support: images uploaded to Blossom first, then passed as `mediaItems`
- Status tracking: `linkedin_status` column in DB (`pending` = will post, `disabled` = skip)

### Image Cross-Posting

When a post has an image:
1. Image uploaded to Blossom (blossom.primal.net) via `blossom-cli`
2. Nostr post includes `--image <url>` and `--ox <sha256>` flags
3. Signal receives image as base64 attachment
4. LinkedIn receives image as `image_url` in Zernio payload

## Nostr Identity Architecture

Dual identity setup for resilience:

| Identity | Location | npub | Purpose |
|---|---|---|---|
| Agent | ~/clawd/skills/nostr-social | npub1xgcxx... | Direct agent use, independent |
| Scheduler | /opt/nostr-social on CT 200 | npub156spnm... | Auto cross-posts only |

Agent identity lives on clawd and is independent of the CT. If the VM goes down, agent can still post directly.

## Common Operations

### Check if services are running
```bash
ssh root@192.168.100.47 'systemctl status signal-scheduler signal-scheduler-web signal-api 2>/dev/null || docker ps'
```

### Check Signal API health
```bash
ssh root@192.168.100.47 'curl -s http://localhost:8080/v1/about && echo && curl -s http://localhost:8080/v1/accounts'
```

### Check scheduled posts (including LinkedIn status)
```bash
ssh root@192.168.100.47 'sqlite3 /opt/signal-scheduler/data/scheduler.db "SELECT id, message, group_name, scheduled_at, status, linkedin_status, sent_at FROM posts ORDER BY id DESC LIMIT 20"'
```

### List Signal groups
```bash
ssh root@192.168.100.47 'curl -s http://localhost:8080/v1/groups | python3 -m json.tool'
```

### Test Nostr cross-posting identity
```bash
ssh root@192.168.100.47 'cd /opt/nostr-social && node scripts/nostr.js whoami'
```

### Rebuild web after code changes
```bash
ssh root@192.168.100.47 'cd /opt/signal-scheduler && npm run build && systemctl restart signal-scheduler-web'
```

### Restart scheduler after config changes
```bash
ssh root@192.168.100.47 'systemctl restart signal-scheduler'
```

## Troubleshooting

### Signal authentication broken / account unregistered

**Symptoms:** `/api/groups` returns 500, Docker logs show `WARN MultiAccountManager - Ignoring +17025768110: User is not registered. (NotRegisteredException)`, and `/v1/accounts` returns `[]`.

**Root cause:** The account data in `/opt/signal-data/data/` becomes corrupted or the Signal registration expires. The `accounts.json` file may still list the account but signal-cli considers it unregistered.

**Fix — clear and re-link:**
```bash
ssh root@192.168.100.47

# 1. Backup current data
cp -r /opt/signal-data /opt/signal-data.bak.$(date +%Y%m%d-%H%M%S)

# 2. Clear corrupted account data
rm -rf /opt/signal-data/data/*

# 3. Restart container to reinitialize
docker restart signal-api
sleep 5

# 4. Verify clean state
curl -s http://localhost:8080/v1/accounts  # Should return []
```

Then re-link via QR code:
1. Open `http://192.168.100.47:8080/v1/qrcodelink?device_name=signal-scheduler` in a browser
2. On your phone: Signal → Settings → Linked Devices → + → scan the QR code
3. Wait ~10 seconds, then verify: `curl -s http://localhost:8080/v1/accounts` should return the account
4. Test groups: `curl -s http://localhost:8080/v1/groups/+17025768110 | head -5`

**If QR linking fails repeatedly:** The signal-cli-rest-api Docker image may be outdated. Update it:
```bash
docker pull bbernhard/signal-cli-rest-api:latest
docker stop signal-api && docker rm signal-api
docker run -d --name signal-api --restart unless-stopped \
  -p 8080:8080 -v /opt/signal-data:/home/.local/share/signal-cli \
  -e MODE=normal bbernhard/signal-cli-rest-api:latest
# Then repeat the QR linking steps above
```

### Posts not sending
1. Check Signal API: `curl http://localhost:8080/v1/about`
2. Check account: `curl http://localhost:8080/v1/accounts`
3. Check logs: `journalctl -u signal-scheduler -n 50`
4. Check DB: `sqlite3 /opt/signal-scheduler/data/scheduler.db "SELECT * FROM posts"`

### LinkedIn cross-posting failing
1. Verify ZERNI0_API_KEY is set in .env: `grep ZERNI0 /opt/signal-scheduler/.env`
2. Check scheduler logs for LinkedIn errors: `journalctl -u signal-scheduler -n 100 | grep -i linkedin`
3. Verify account ID `1580176163` is correct in scheduler.ts

### Nostr cross-posting failing
```bash
ssh root@192.168.100.47
cd /opt/nostr-social
echo "Test" | node scripts/nostr.js post -
journalctl -u signal-scheduler -n 100 --no-pager | grep -i nostr
```

### Duplicate posts
- Check for multiple scheduler instances: `systemctl status signal-scheduler`
- Verify timezone alignment between scheduled_at and server time

## API Endpoints (Web UI)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/groups | List Signal groups |
| GET | /api/posts | List all scheduled posts |
| POST | /api/posts | Create a new scheduled post (supports linkedin_status in FormData) |
| PATCH | /api/posts/:id | Update a post (message, group, time, image, linkedin_status) |
| DELETE | /api/posts/:id | Delete a scheduled post |

## Database Schema

```sql
CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message TEXT NOT NULL,
  group_id TEXT NOT NULL,
  group_name TEXT,
  scheduled_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled',
  linkedin_status TEXT DEFAULT 'pending',
  x_status TEXT DEFAULT 'disabled',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP
);

CREATE INDEX idx_posts_scheduled_at ON posts(scheduled_at);
CREATE INDEX idx_posts_status ON posts(status);
```

`linkedin_status`: `'pending'` = will cross-post to LinkedIn, `'disabled'` = skip.
`x_status`: same lifecycle for X/Twitter. Historical rows default to `'disabled'`; new UI posts default to `'pending'`.

## References

- `references/linkedin-integration.md` — Full walkthrough of LinkedIn cross-posting implementation (files changed, deploy sequence, lessons)
- `references/backup-disaster-recovery.md` — Backup/DR audit commands, NAS backup script, restore procedures, and PBS verification notes

## Pitfalls

1. **Always SSH, never read local files** — The Signal Scheduler lives on CT 200 (192.168.100.47). `write_file` and `read_file` tools operate on the local filesystem and will fail for `/opt/signal-scheduler/*` paths. Use `ssh root@192.168.100.47 'cat > /path/to/file' << 'EOF'` for writes, and `ssh root@192.168.100.47 'cat /path/to/file'` for reads.
2. **SSH heredoc can mangle TS/JS escape sequences** — Regex patterns, template literals, and shell-sensitive characters in TypeScript/JavaScript can be corrupted when piped through SSH heredoc. Always `cat` the remote file after writing and before building to verify integrity.
3. **Rebuild AND restart after any code change** — Frontend changes (page.tsx, API routes) need `npm run build` + restart of `signal-scheduler-web`. Backend changes (scheduler.ts) need restart of `signal-scheduler`. Both services may need attention. Hot-reload does not exist.
4. **.env file has hard tabs** — The `.env` on CT 200 uses hard tabs as delimiter, not spaces. Shell heredoc with spaces creates a file that looks identical but breaks `dotenv` parsing. Verify with `cat -A /opt/signal-scheduler/.env` — tabs show as `^I`.
5. **signal-api container must be named exactly "signal-api"** — The scheduler references the Docker container by name. Use `-e MODE=normal` and do not rename the container.
6. **Separate Nostr identities** — The scheduler's Nostr identity (npub156...) on CT 200 is independent of the agent's Nostr identity on clawd. Using the wrong npub in debugging will show no posts. Check with `node scripts/nostr.js whoami` on CT 200.
7. **Edit modal needs its own LinkedIn checkbox** — When adding frontend features like LinkedIn cross-posting, the edit modal renders a separate form. Both the new-post form and the edit form need the checkbox and FormData handling.
8. **Frontend and backend must agree on `linkedin_status`** — page.tsx sends `linkedin_status` in FormData, the API route reads it, and scheduler.ts checks `linkedin_status === 'pending'`. All three layers must be updated together. A mismatch produces silent failures.
9. **ZERNI0_API_KEY is zero-padded** — The env var is `ZERNI0_API_KEY` (with a zero), not `ZERNIO_API_KEY`. Typo produces an auth error that looks like "invalid key" — grep for `ZERNI0` to confirm.
10. **LinkedIn account ID is hardcoded** — `1580176163` is used directly in scheduler.ts. If Zernio changes the account or the user switches accounts, this must be updated manually. No env var exists for it.
11. **Posts with failed LinkedIn still show as "sent"** — The cross-post logic marks a post "sent" if ANY channel succeeds. A post that went to Signal and Nostr but failed LinkedIn will show status "sent" — check `linkedin_status` separately for LinkedIn-specific failures.
12. **Scheduler runs as root** — All paths are absolute, no user context needed. Commands like `systemctl restart signal-scheduler` work without `sudo`.
15. **CT 200 is unprivileged — cannot mount NFS/CIFS from inside** — File-system mounts fail with "Operation not permitted". Use rsync over SSH for backups, or add a bind mount on the Proxmox host.
16. **Always use SQLite `.backup` for live DB copies** — Copying or rsyncing `scheduler.db` while the scheduler service is running can corrupt it or produce a 0-byte file. Use `sqlite3 /opt/signal-scheduler/data/scheduler.db ".backup /tmp/scheduler.db"` and then rsync the backup copy.
17. **Browser extension console errors are noise** — When the user reports "console errors" on the Signal Scheduler, most will be from MetaMask or similar wallet extensions (`contentscript.js`, `ObjectMultiplex`, `app-init-liveness`, `background-liveness`, `MaxListenersExceededWarning`). These are irrelevant. Focus on actual HTTP errors (500 on `/api/groups`, `/api/posts`) and React crashes caused by those errors (e.g., `n.map is not a function` when the API returns an error object instead of an array).