---
name: nostrx
description: >
  nostrX: Nostr-to-Twitter/X cross-poster. Monitors Nostr posts from configured npubs
  and posts them to X as a thread (if > 280 chars) with the Nostr link appended.
  Use when: user asks about nostrX status, X cross-posting fails, or wants to monitor
  the Nostr→X sync. The service runs on Proxmox CT 202 (192.168.100.54), not locally.
tags: nostr, twitter, x, cross-post, sync, social
---

# nostrX — Nostr to X Cross-Poster

## What It Is

nostrX watches your Nostr posts and automatically syncs them to X (@wahiddotmy). It's a Python script running on **CT 202** (`192.168.100.54`), triggered every 10 minutes via cron.

**Two monitored npubs:**
- `npub1l5khqwq3hyw2q9698zj4ujvuxapmldjmtlrnvmq472553wmhg5wq9y8emr` (Jarvis/agent)
- `npub156spnmrgn4av0y6qkw3mjhlar0jpwe3ytmmu0guuxx66qsy5g8xqhzkzcm` (wahiddotmy)

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

## Troubleshooting

### "No new posts found" every run
- Check `sync_state.json` — `last_synced_timestamp` may be too old or stuck
- Force a fresh sync by resetting the timestamp:
  ```bash
  ssh root@192.168.100.54 "python3 -c 'import json; s=json.load(open(\"/root/nostrX/sync_state.json\")); s[\"last_synced_timestamp\"]=int(__import__(\"time\").time())-86400; json.dump(s,open(\"/root/nostrX/sync_state.json\",\"w\"),indent=2)'"
  ```

### Posts not appearing on X
- Check log for errors: `tail /root/nostrX/nostrx.log`
- Verify Twitter credentials are still valid (monthly rate limit: 500 posts)
- Check if post was filtered as a reply

### Media upload failing
- Usually a network timeout downloading from Blossom/CDN
- Script logs `❌ Failed to download media` — post goes out text-only

### Script runs but tweets fail
- Twitter API v2 free tier: 500 posts/month, 10 posts/day
- If rate limited, tweepy throws a 403 — script skips that post and retries next cycle

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