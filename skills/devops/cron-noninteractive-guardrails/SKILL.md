---
name: cron-noninteractive-guardrails
description: Prevent cron-run failures from non-TTY terminal usage. Use strict non-interactive command patterns, stop after primary check success, and avoid post-check helper commands that trigger ioctl/timeouts.
version: 1.0.0
---

# Cron Non-Interactive Guardrails

## Use when
- Session source is cron/scheduled automation.
- Task is a health check, keepalive, or single-command verification.
- You see recurring errors like `Inappropriate ioctl for device`, `no job control in this shell`, or command timeouts after the main check already succeeded.

## Core rule
If the primary check succeeds and no issue is requested, **stop immediately** and return `[SILENT]` (or the required success format). Do not run extra context/cleanup commands.

## Steps
1. Run exactly the primary command in foreground mode.
2. Parse success/failure from that command only.
3. On success with "report only on issue" instruction: return `[SILENT]` immediately.
4. On failure: report only actionable failure details (exit code + key error line).
5. Never run interactive shell patterns in cron (`bash -i`, job-control assumptions, TTY-dependent tools).

## API Key Access in Cron

**Critical:** Keys in `~/.hermes/.env` may be credential-manager-backed (masked as `***` in display, short length when parsed). They will NOT be available to subprocess API calls (litellm, openai SDK, etc.) even after `source ~/.hermes/.env` — the value exported is the masked stub, not the real key.

**Workarounds:**
- Store a dedicated plaintext service key in `~/.hermes/evolution-creds.env` (not the main `.env`) and `source` that specifically for cron jobs that need API access.
- Or pass the key via the cron job's environment variable configuration in `~/.hermes/cron/jobs.yaml`.
- Diagnose: `python3 -c "open('/home/wahid/.hermes/.env').read()" | grep KEY_NAME` — if len < 20 chars or contains `***`, the key is masked.

## Anti-patterns to avoid
- Running extra CLI helpers after a successful health check.
- Calling tools that expect TTY/job control in cron.
- Extending runtime with non-essential commands that can timeout and create false alarms.
- Running `brv curate` synchronously in cron; it can trigger shell/job-control (`tcsetattr`/ioctl) issues.

## Python urllib IPv6 Hang

**Symptom:** Python scripts using `urllib.request` to call external HTTPS APIs hang indefinitely (30s+ timeout) even though `curl` to the same URL works in <1s.

**Cause:** Python's `urllib` attempts IPv6 first. If the environment has broken IPv6 (no route, silent drop), the connection hangs until timeout. `curl` handles IPv4/IPv6 fallback correctly.

**Fix:** In Python scripts that need HTTP, use `subprocess.run(["curl", ...])` instead of `urllib.request`:

```python
import subprocess, json

def fetch_json(url):
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "15", "--max-time", "30",
         "-H", "User-Agent: hermes-agent/1.0", url],
        capture_output=True, text=True, timeout=35
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr.strip()}")
    return json.loads(result.stdout)
```

This applies to cron scripts, detection scripts, and any Python code making outbound HTTP calls.

## Reference: OpenRouter Free Model Detection

See `references/openrouter-free-model-detection.md` for a complete example of this pattern — a cron-driven external API monitor that tracks new/expired free models with human-in-the-loop notifications.

## Tool-specific guardrail (ByteRover CLI)
- In cron, run `brv curate` with `--detach` (and optionally `--format json`) to queue and exit cleanly.
- Report queued `taskId` as proof of execution instead of waiting on interactive progress output.
- **Binary path**: The brv CLI is at `/home/wahid/.npm-global/bin/brv` (NOT `~/.brv-cli/bin/brv`). Always use the full path in cron.
- **Authentication required**: `brv curate` requires a connected provider. Run `brv login -k <api-key>` (get key at https://app.byterover.dev/settings/keys). Without it, curate fails with "No provider connected".

## Sync Script Deduplication
Any scheduled sync that creates API resources must deduplicate by content key (title+date), not just sync state files. Sync state drifts — always verify against the live API. See `references/sync-script-dedup-pattern.md` for the full pattern and a real Notion→Outlook example.

## Verification next run
- Query sessions for: `"Inappropriate ioctl" OR "no job control" OR "timed out after"`.
- Expect zero new matches in successful health-check runs.
- Confirm successful checks end immediately after the primary command result.
