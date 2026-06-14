---
name: signal-scheduler
description: Manage the Signal Scheduler — a web-based scheduler (Next.js 16) that posts messages to Signal groups and auto cross-posts to Nostr with opt-in LinkedIn cross-posting via Zernio API. Runs on Proxmox CT 200 at 192.168.100.47. Covers the web UI, background scheduler, signal-cli-rest-api Docker container, dual Nostr identity architecture, Blossom image uploads, LinkedIn integration, systemd services, and troubleshooting. Use when asked to inspect, fix, schedule posts, or configure anything on the Signal Scheduler.
version: 1.0.0
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

## How Cross-Posting Works

Every Signal post is cross-posted. Signal and Nostr are always tried; LinkedIn is opt-in via checkbox:

1. Post is due (scheduled_at <= now)
2. `sendToSignal()` fires via signal-cli-rest-api
3. `sendToNostr()` fires via `/opt/nostr-social/scripts/nostr.js`
4. If `linkedin_status === 'pending'`, `postToLinkedIn()` fires via Zernio API
5. If ANY succeed → post marked as "sent"
6. Only if ALL fail → post marked as "failed"

### LinkedIn Cross-Posting

LinkedIn integration uses Zernio's unified social API. It is opt-in — users must check the "Cross-post to LinkedIn" checkbox when scheduling a post.

- Endpoint: `POST https://api.zernio.com/linkedin/post`
- Auth: `Bearer <ZERNI0_API_KEY>` from .env
- Account ID: hardcoded `1580176163` in scheduler.ts
- Image support: images uploaded to Blossom first, then passed as `image_url`
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

### Signal authentication broken
Usually means signal-cli can't reach Signal servers. Update Docker image:
```bash
ssh root@192.168.100.47
docker pull bbernhard/signal-cli-rest-api:latest
docker stop signal-api && docker rm signal-api
docker run -d --name signal-api --restart unless-stopped \
  -p 8080:8080 -v /opt/signal-data:/home/.local/share/signal-cli \
  -e MODE=normal bbernhard/signal-cli-rest-api:latest
# Then re-link: curl to /v1/qrcodelink, scan QR from phone
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
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP
);

CREATE INDEX idx_posts_scheduled_at ON posts(scheduled_at);
CREATE INDEX idx_posts_status ON posts(status);
```

`linkedin_status`: `'pending'` = will cross-post to LinkedIn, `'disabled'` = skip LinkedIn.

## References

- `references/linkedin-integration.md` — Full walkthrough of LinkedIn cross-posting implementation (files changed, deploy sequence, lessons)

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