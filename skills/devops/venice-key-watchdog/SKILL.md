---
name: venice-key-watchdog
description: >-
  Watch @AskVenice for free DIEM keys and test expired ones.
version: 1.1.0
tags: [venice, diem, kimi-k3, api-keys, watchdog, x-twitter]
metadata:
  hermes:
    tags: [venice, diem, kimi-k3, api-keys, watchdog, x-twitter]
    trigger_conditions:
      - "venice key watchdog"
      - "watch AskVenice for DIEM keys"
      - "free DIEM inference key"
      - "VENICE_INFERENCE_KEY"
      - "test expired venice key"
      - "midnight UTC key reset"
      - "kimi-k3 free key"
      - "AskVenice tweet new key"
      - "check if venice key works"
      - "diem budget reset"
---

# Venice Key Watchdog

Use when the user wants to monitor @AskVenice on X for free DIEM inference API key drops, test known expired keys for daily reset (midnight UTC), and catch live keys before the free daily budget is drained.

## When to Use

- The user wants to monitor @AskVenice on X for newly dropped free DIEM inference keys.
- A known `VENICE_INFERENCE_KEY_*` has expired and the user wants it re-tested around the midnight UTC reset.
- A live-key alert fired and the user needs to know which models the key supports and where to wire it in.
- The user asks why the Venice free budget is drained or how DIEM daily resets work.

## Not For

- Using Venice as a normal paid API provider → that's standard provider config, not a key-watchdog task.
- Monitoring other API-key sources (OpenRouter free keys, HuggingFace tokens, etc.) → different feeds and formats; the xurl-based scanner is Venice-specific.
- Diagnosing Venice API latency or model errors once a key is working → check provider status and model docs instead.
- Buying or managing paid Venice credits → this skill tracks the free DIEM economy only.

## How It Works

Venice's DIEM (Decentralized Inference Economy Model) grants free daily API inference budget. When a public key is shared in a tweet (especially one with $1,000/day budget), it gets consumed quickly. This watchdog:

1. **Tests the known expired key** every 30 minutes — DIEM budgets reset at **midnight UTC** so a formerly expired key may come back to life
2. **Searches @AskVenice feed** for new `VENICE_INFERENCE_KEY_*` patterns and tests any new keys immediately
3. Runs as a **no-agent watchdog cron** — stays silent when nothing to report, alerts immediately on any live key find

## Setup

### Cron Job

The job was created with:
```
cronjob( action='create', name='Venice Key Watchdog', schedule='*/30 * * * *', script='venice-key-monitor.sh', no_agent=True )
```

The script lives at `~/.hermes/scripts/venice-key-monitor.sh`.

### Manual Test

```bash
bash ~/.hermes/scripts/venice-key-monitor.sh
```

## DIEM Reset Schedule

| Detail | Value |
|--------|-------|
| Reset Time | **Midnight UTC** (00:00 UTC) |
| Check Interval | Every 30 minutes |
| Known Key | `VENICE_INFERENCE_KEY_fIoSZrFtFJbhKeDwUDJODkI6HWuqplHpRZpi-CqOV1` |
| Model | `kimi-k3` (2.8T MoE, frontier-level on Venice) |

## What to Do If a Key Is Found Live

The watchdog will print the full key and test output. You can then:

1. Test what models the key supports:
   ```bash
   curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
     -d '{"model":"kimi-k3","messages":[{"role":"user","content":"hi"}]}' \
     https://api.venice.ai/api/v1/chat/completions
   ```
2. Save it to your `.env` or use it directly in Hermes as a custom provider
3. Try other Venice-hosted models: `dolphin-2.9.4`, `llama-3.3-70b`, etc.
4. Add the key as a Venice provider in Hermes config

## Pitfalls

1. **X API rate limits** — The script uses xurl to search @AskVenice. If the X API is rate-limited, the script won't find new keys until the limit resets. Recovery: check `xurl` errors in the job log, wait for the window, or reduce poll frequency to hourly.

2. **False positives** — Any text matching `VENICE_INFERENCE_KEY_*` in @AskVenice posts triggers a test. The script deduplicates by hashing tested keys, but a quoted/retweeted old key still burns a test call. Recovery: confirm the tweet is a fresh drop before acting on the alert.

3. **Key rotation** — Venice may rotate keys or change their prefix. If monitoring stops catching new keys, check whether the format changed. Recovery: re-grep the feed for the new pattern and update the regex in `venice-key-monitor.sh`.

4. **DIEM vs. USD billing** — The key gives DIEM-based access. If the DIEM budget is $1,000/day, hitting that means waiting for the UTC reset — the key is not broken, just budget-drained. Recovery: don't discard the key; keep it in the rotation for the next reset.

5. **Midnight UTC drift** — "Midnight UTC" may have a slight delay. The 30-minute polling accounts for this. Recovery: if a key consistently comes alive at 00:05–00:15 UTC, the delay is normal; don't tighten the poll interval below 30 min.

6. **`curl` with the Bearer token in a `-H` flag mangles in shell** — If the key contains `$` or special chars, inline shell escaping can corrupt the request. Recovery: prefer a Python `requests` call or pass the header via a config file, and verify the key bytes with `echo "$KEY" | wc -c` before testing.
