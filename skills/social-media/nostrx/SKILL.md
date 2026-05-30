---
name: nostrx
description: >
  Nostr-to-X/Twitter cross-poster. Monitors one or more Nostr npubs and syncs new text posts to Twitter/X via the Twitter API v2.
  Use when: (1) user reports posts not appearing on X, (2) X posts are truncated or missing content, (3) user wants to change which Nostr pubkeys are monitored, (4) nostrX service needs restart/update/debug.
triggers:
  - "nostrX"
  - "nostr to twitter"
  - "nostr to x"
  - "cross post to x"
  - "posts not appearing on twitter"
  - "x posts truncated"
---

# nostrX — Nostr → X/Twitter Sync

## Overview

`nostrx.py` is a Python sync tool running on **CT 202** (`192.168.100.54`). It monitors specified Nostr npubs and cross-posts new text posts to X/Twitter using the Twitter API v2 (via tweepy).

**Location:** `/root/nostrX/nostrx.py`
**State file:** `/root/nostrX/sync_state.json`
**Service:** Not a systemd service — runs as a cron-triggered script
**Python venv:** `/root/nostrX/venv`

## Architecture

```
Nostr relays (wss://relay.damus.io, wss://nos.lol, etc.)
       ↓
  nostrx.py (Python, nostr_sdk)
       ↓
  Twitter API v2 (tweepy)
       ↓
  X/Twitter (@wahiddotmy)
```

- Uses **Twitter API credentials** (not bird CLI cookies) — API key/secret + access token/secret stored in `.env`
- State is tracked in `sync_state.json` to avoid duplicate posts
- Only syncs **top-level posts** (Kind 1, no 'e' or 'reply' tags)
- Skips posts with media URLs in content (extracts image URLs, uploads separately)
- 1-second delay between posts to avoid rate limiting

## Common Tasks

### Run manually
```bash
ssh root@192.168.100.54 "cd /root/nostrX && source venv/bin/activate && python nostrx.py"
```

### View recent logs
```bash
ssh root@192.168.100.54 "tail -50 /root/nostrX/nostrx.log"
```

### Check state
```bash
ssh root@192.168.100.54 "cat /root/nostrX/sync_state.json"
```

### Change monitored npubs
Edit `.env` on CT 202:
```bash
ssh root@192.168.100.54 "nano /root/nostrX/.env"
# Find: NOSTR_NPUBS=<comma-separated npubs>
# Example: NOSTR_NPUBS=npub1xxx...,npub1yyy...
```

### Restart/reload after config change
Since it's cron-triggered, just wait for the next cron run — or kill the running instance and restart manually:
```bash
ssh root@192.168.100.54 "pkill -f nostrx.py; cd /root/nostrX && source venv/bin/activate && python nostrx.py &"
```

## Threading Behavior

Long posts (> 280 chars) are automatically posted as a proper Twitter thread:

- Posts **≤ 280 chars**: single tweet with `https://njump.me/{event_id}` appended at the end
- Posts **> 280 chars**: split into a thread via `in_reply_to_tweet_id`, each tweet ≤ 275 chars, final tweet ends with the Nostr link
- Media (images/videos) attach to the **first tweet only** (Twitter threading rule)
- Nostr link format: `https://njump.me/{event_id}`
- 1-second delay between thread tweets

Implemented via `post_thread()` method using Tweepy 4.16+ `create_tweet(in_reply_to_tweet_id=...)`.

## Investigation Notes

### Finding nostrX (debugging path)
1. signal-scheduler on CT 200 only sends to Signal + Nostr — **zero X code there**
2. The `bird` CLI (@steipete/bird) found in the environment is for **reading** likes/bookmarks, not posting
3. `/home/wahid/clawd/scripts/health-check.sh` references `nostrX (Proxmox CT 202: 192.168.100.54)` — key clue
4. nostrX is independent of signal-scheduler — it monitors Nostr pubkeys directly via relay, not the scheduler DB
5. **Search pattern used:** `find / -maxdepth 8 ... | xargs grep -l 'bird tweet'` across all CTs until /root/nostrX/nostrx.py was found
6. The actual bug location: `post_thread()` call in `run()` — old code had `if len(clean_text) > 280: clean_text = clean_text[:277] + "..."`

### CT access
- **Host:** `192.168.100.54`
- **User:** `root`
- **Auth:** SSH key — try `ssh root@192.168.100.54` (key auth configured)
- **Test:** `ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@192.168.100.54 "hostname"`

## References

- `references/nostrx-py.md` — full source of nostrx.py with threading implementation (updated 2026-05-20)

## Related Services

| Service | CT | Port | Purpose |
|---------|-----|------|---------|
| signal-scheduler | 200 (192.168.100.47) | 3000 | Signal + Nostr scheduling |
| nostrX | 202 (192.168.100.54) | — | Nostr → X sync |
| nostr.js CLI | CT 200 + local | — | Direct Nostr posting CLI |

nostrX is the cross-post layer that reads from Nostr (not the scheduler DB) and posts to X. signal-scheduler handles Signal + Nostr posting only.