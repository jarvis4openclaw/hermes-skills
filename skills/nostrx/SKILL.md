---
name: nostrx
description: >
  nostrX: Nostr-to-Twitter/X cross-poster. Monitors Nostr posts from configured npubs
  and posts them to X as a thread (if > 280 chars) with the Nostr link appended.
  Use when: user asks about nostrX status, X cross-posting fails, or wants to monitor
  the Nostr→X sync. The service runs on Proxmox CT 202 (192.168.100.54), not locally.
version: 1.1.0
tags: nostr, twitter, x, cross-post, sync, social
metadata:
  hermes:
    tags: [nostr, twitter, x, cross-post, sync, social]
    trigger_conditions:
      - "nostrX"
      - "nostr cross-poster"
      - "Nostr to X sync"
      - "Nostr cross-posting failed"
      - "check nostrx status"
      - "force Nostr→X sync"
      - "nostrx is not posting"
      - "tweets not appearing from nostr"
      - "debug nostr cross-poster"
      - "nostrx log"
      - "reset nostrx sync state"
      - "nostrx Proxmox CT"
---

# nostrX — Nostr to X Cross-Poster

## What It Is

nostrX watches your Nostr posts and automatically syncs them to X (@wahiddotmy). It's a Python script running on **CT 202** (`192.168.100.54`), triggered every 10 minutes via cron.

**Two monitored npubs:**
- `npub1l5khqwq3hyw2q9698zj4ujvuxapmldjmtlrnvmq472553wmhg5wq9y8emr` (Jarvis/agent)
- `npub156spnmrgn4av0y6qkw3mjhlar0jpwe3ytmmu0guuxx66qsy5g8xqhzkzcm` (wahiddotmy)

## When to Use

- nostrX stopped cross-posting and posts aren't appearing on X
- Need to check sync state or recent nostrX run logs
- Force a manual Nostr→X sync outside the cron schedule
- Debug why specific Nostr posts were skipped (replies, dedup)
- Verify threading behavior for long Nostr posts (280+ chars)
- Reset sync state after clock drift or state corruption
- Check which Proxmox CT is running the nostrX service

## Not For

- Posting directly to Nostr from Hermes → use `nostr` nostr-cli
- Posting directly to X/Twitter → use `xitter` or `xurl` 
- General social media scheduling → use `signal-scheduler`
- Modifying the nostrX Python script itself → SSH + manual editing on CT 202
- Nostr relay management or key generation → use `nostr` nostr-cli
- Monitoring X/Twitter mentions or DMs → use `xurl` or `xitter`

## Files & Locations

| File | Purpose |
|------|---------|
| `/root/nostrX/nostrx.py` | Main sync script |
| `/root/nostrX/nostrx.py.bak.*` | Timestamped backups |
| `/root/nostrX/nostrx.log` | Run log (output of each cron run) |
| `/root/nostrX/sync_state.json` | Last synced timestamp + event IDs |
| `/root/nostrX/.env` | API credentials + npub config |
| `/root/venv/bin/python` | Python with tweepy + nostr_sdk |

## Quick Commands

```bash
# Check if nostrX is running / recent logs
ssh root@192.168.100.54 "tail -30 /root/nostrX/nostrx.log"

# Check sync state
ssh root@192.168.100.54 "cat /root/nostrX/sync_state.json | python3 -m json.tool"

# Force a manual sync run
ssh root@192.168.100.54 "source /root/venv/bin/activate && python /root/nostrX/nostrx.py"

# Restart the cron (after editing script — cron auto-runs but this forces next run sooner)
ssh root@192.168.100.54 "systemctl restart cron"  # CT is LXC, no systemd service for nostrX

# Verify threading code is live
ssh root@192.168.100.54 "grep -A5 'def post_thread' /root/nostrX/nostrx.py"
```

## How Threading Works

**Posts ≤ 280 chars:** Single tweet — text + space + `https://njump.me/{event_id}`

**Posts > 280 chars:** Thread posted as a series of replies:
1. First tweet: first ~275 chars of content (+ media if any)
2. Middle tweets: next ~275 chars each (marked ` (1/n)`, ` (2/n)` …)
3. Final tweet: remaining content + `https://njump.me/{event_id}`

**Media:** Images/videos are stripped from the Nostr text and uploaded natively to Twitter. Media is attached to the **first tweet only** (Twitter threading rule).

**Deduplication:** Tracks `synced_event_ids` in `sync_state.json` — won't re-post.

**Skipped content:**
- Replies (any post with `e` or `reply` tags)
- Posts with no content

## Relays

Configured relays (`.env`):
- `wss://relay.wahid.my` (custom, primary)
- `wss://relay.damus.io`
- `wss://nos.lol`
- `wss://relay.nostr.band`

## Pitfalls

1. **"No new posts found" every run but posts exist on Nostr** — `sync_state.json` has a stale `last_synced_timestamp`. Recovery: reset the timestamp back 24h: `ssh root@192.168.100.54 "python3 -c 'import json,time; s=json.load(open(\"/root/nostrX/sync_state.json\")); s[\"last_synced_timestamp\"]=int(time.time())-86400; json.dump(s,open(\"/root/nostrX/sync_state.json\",\"w\"),indent=2)'"`

2. **Posts not appearing on X with no error in log** — Twitter API rate limit hit (500 posts/month, 10 posts/day on free tier). Tweepy throws 403 which the script catches silently. Recovery: check `grep "403\|429\|Rate limit" /root/nostrX/nostrx.log`; wait for rate window reset.

3. **Replies/directed posts not cross-posting** — By design, nostrX skips any post with `e` or `reply` tags. Recovery: not a bug — replies are excluded. Direct-post (root note) to trigger cross-posting.

4. **Media upload failing with "Failed to download media"** — Network timeout downloading from Blossom CDN or relay. The post goes out text-only. Recovery: check network from CT 202 (`ping relay.wahid.my`); re-post after CDN recovers.

5. **Twitter API credentials expired or invalid** — X API v2 tokens rotate or get revoked. Script fails silently with auth error. Recovery: `ssh root@192.168.100.54 "grep -i 'auth\|token\|401\|403' /root/nostrX/nostrx.log"`; regenerate tokens in X Developer Portal; update `.env`.

6. **CT 202 unreachable via SSH** — Proxmox CT 202 might be stopped or networking broken. Recovery: check Proxmox web UI first; `ping 192.168.100.54`; if down, start the CT from Proxmox.

7. **sync_state.json corruption from concurrent runs** — If two nostrX processes run simultaneously (cron overlap), state file gets corrupted. Recovery: `ssh root@192.168.100.54 "rm /root/nostrX/sync_state.json"`; next run reconstructs from scratch.

8. **Nostr relays unreachable, leading to empty fetch** — When primary relay (`relay.wahid.my`) is down, nostrX may fall back to public relays that don't have the relevant posts. Recovery: check relay status; verify relay list in `.env` is current.

9. **Threading fails for posts near 280-char boundary** — The split logic uses hard ~275 character chunks; emoji or Unicode chars may cause mis-splits. Recovery: keep Nostr posts under 260 chars for clean threading, or above 280 to trigger thread but below 275 per chunk.

10. **Cron isn't triggering but manual run works** — CT 202's cron daemon may be stopped or the crontab entry may be malformed. Recovery: `ssh root@192.168.100.54 "systemctl status cron"` and `crontab -l` to verify the `*/10` entry exists.

## Configuration

Edit `.env` to change monitored npubs or relays:
```bash
ssh root@192.168.100.54 "nano /root/nostrX/.env"
```

Then restart sync state (or just wait for next cron cycle):
```bash
ssh root@192.168.100.54 "cat /root/nostrX/.env"
```

## Cron Schedule

```
*/10 * * * * /root/venv/bin/python /root/nostrX/nostrx.py >> /root/nostrX/nostrx.log 2>&1
```

Every 10 minutes. Edit `/etc/crontab` on CT 202 to change.