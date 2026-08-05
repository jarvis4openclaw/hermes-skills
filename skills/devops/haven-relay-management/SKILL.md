---
name: haven-relay-management
description: Manage the HAVEN Nostr relay on CT 203 at relay.wahid.my. Use when the Nostr relay is down, slow, or needs config changes, when checking relay health/status, or when working with Nostr relay infrastructure.
version: 1.1.0
tags: [nostr, haven, relay, blossom, proxmox, homelab]
metadata:
  hermes:
    tags: [nostr, haven, relay, blossom, proxmox, homelab]
    trigger_conditions:
      - "Nostr relay is down / unreachable"
      - "relay.wahid.my status"
      - "HAVEN relay restart"
      - "Nostr relay configuration"
      - "Blossom media upload"
      - "relay filters blocked"
      - "whitelist / blacklist npub"
      - "relay backups"
      - "Nostr relay migration"
      - "CT 203 nostr-relay"
      - "relay WebSocket test"
---

# HAVEN Nostr Relay Management

Manage the self-hosted HAVEN Nostr relay at `wss://relay.wahid.my` running on Proxmox CT 203.

## When to Use

- Diagnosing a down/slow/unreachable Nostr relay (WebSocket connect failures, NIP-11 not responding).
- Restarting or reconfiguring the HAVEN service, or editing `/opt/haven/.env`.
- Checking relay health publicly (NIP-11, WebSocket handshake) or verifying DNS/routing.
- Managing Blossom media, whitelist/blacklist files, or relay backups to Backblaze B2.
- Migrating the relay between hosts (e.g., Fly.io → CT 203, as done 2026-08-03).

## Not For

- General Nostr protocol questions or building Nostr apps → use `nostr-social` / `Nostr` skill instead.
- Deploying a NEW relay from scratch (CT provisioning, image choice) → use `nostr-relay-hosting` instead.
- Caddy/reverse-proxy troubleshooting (the relay is just one site block there) → use `caddy-proxy-management` instead.
- Proxmox CT lifecycle (creating/deleting CT 203) → use `proxmox-ssh-lifecycle` / `proxmox` instead.
- Blossom server setup on other hosts → this skill covers the built-in Blossom on CT 203 only.

## Architecture

- **CT 203** `nostr-relay` — Debian 12, 1GB RAM, 2 cores, IP `192.168.100.51`
- **HAVEN binary** at `/opt/haven/haven` (v1.2.2)
- **systemd service** `haven` (enabled, MemoryMax 900M), listens on port 3355
- **Config:** `/opt/haven/.env` + `relays_import.json`, `relays_blastr.json`, `whitelisted_npubs.json`, `blacklisted_npubs.json` (must all exist, use `[]` if empty — HAVEN fails to start if files missing)
- **Blossom media** built-in at `/opt/haven/app/data/blossom/` (uploads require Nostr auth)
- **Public route:** `relay.wahid.my` → Cloudflare DNS (A record → `64.25.11.235`, proxied=false) → Caddy CT 107 (`192.168.100.53`) → `reverse_proxy 192.168.100.51:3355`
- **Backups:** Backblaze B2 bucket `haven-wahid` (S3-compatible, us-west-004), daily JSONL backups
- **Owner npub:** `npub1l5khqwq3hyw2q9698zj4ujvuxapmldjmtlrnvmq472553wmhg5wq9y8emr`
- **Config source repo:** private GitHub `wahidmy/haven` (raw URLs with token)

## Common Operations

### Check status / logs
```bash
ssh root@192.168.100.23 'pct exec 203 -- systemctl status haven --no-pager'
ssh root@192.168.100.23 'pct exec 203 -- journalctl -u haven -n 50'
```

### Restart
```bash
ssh root@192.168.100.23 'pct exec 203 -- systemctl restart haven'
```

### Verify publicly
```bash
curl -s -H "Accept: application/nostr+json" https://relay.wahid.my/   # NIP-11
# WebSocket: expect HTTP 101 + EOSE
python3 /tmp/haven-env/ws_public_test.py  # (or websocat)
```

### Health check sequence (down relay)

When the relay appears down, run these in order — each isolates a different layer:

```bash
# 1. DNS — does relay.wahid.my resolve to the WAN IP?
dig +short relay.wahid.my   # expect 64.25.11.235 (Cloudflare A record, proxied=false)

# 2. Service — is haven running on CT 203?
ssh root@192.168.100.23 'pct exec 203 -- systemctl is-active haven'

# 3. Local port — is 3355 listening inside the CT?
ssh root@192.168.100.23 'pct exec 203 -- ss -ltnp | grep 3355'

# 4. Public NIP-11 — does the outside world see it?
curl -s -m 10 -H "Accept: application/nostr+json" https://relay.wahid.my/

# 5. WebSocket handshake
curl -s -m 10 -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  https://relay.wahid.my/ | head -5   # expect HTTP/1.1 101
```

A failure at step 1 means DNS; step 2–3 means CT/service; step 4–5 with everything local healthy means Caddy or the router/Cloudflare path.

## Pitfalls

1. **HAVEN fails to start if referenced files are missing** — `whitelisted_npubs.json`/`blacklisted_npubs.json` must exist even if empty (`[]`). Error: `Failed to read file: open whitelisted_npubs.json: no such file or directory`.
2. **Startup takes 40-60s** — HAVEN tests import relays and builds Web of Trust before binding port 3355. Don't panic if `ss` shows nothing right after restart.
3. **Empty filters are blocked** — outbox/inbox relays have `ALLOW_EMPTY_FILTERS=false`, so `["REQ","x",{}]` returns `["CLOSED","x","blocked: can't handle empty filters"]`. Use a real filter like `{"kinds":[1],"limit":1}`.
4. **Caddy admin is off** — `admin off` in Caddyfile means `caddy reload` fails (connection refused on :2019). Edit the bind-mounted `/opt/caddyui/Caddyfile` then `docker restart caddy` on CT 107.
5. **DNS must be direct A record** — relay.wahid.my needs `proxied=false` (Cloudflare proxy breaks long-lived WebSockets).
6. **Caddy on CT 107 uses Azure DNS module** for `*.wahidsaleemi.net`; `relay.wahid.my` uses standard HTTP-01/TLS-ALPN (Cloudflare zone) — do NOT add it under the Azure wildcard block.
7. **SSH into CTs via PVE host** — `ssh root@192.168.100.23 'pct exec <id> -- ...'`; CTs don't have direct SSH keys, go through PVE.
8. **Nested quoting breaks pct exec** — for files with apostrophes/quotes, write locally then `pct push` (e.g. `pct push 203 /tmp/file /opt/haven/.env`).

## Fly.io Migration History

- Previously hosted on Fly.io as app `haven-wahidmy` (`1380xl0.haven-wahidmy.fly.dev`, 66.241.124.122) — charged for "Additional RAM" 2GB + shared CPU
- Migrated 2026-08-03 to CT 203. DNS record id `79c6d7b181cdd66b16b486f26a189c9c` in zone `9f14d36bc1f3e3dbb73f154609ac81b0`
- Decommission: `fly apps destroy haven-wahidmy` (in Fly dashboard or CLI after auth)
