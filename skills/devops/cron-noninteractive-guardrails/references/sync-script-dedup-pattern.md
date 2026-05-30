# Sync Script Deduplication Pattern

## Pattern
Any sync script that creates resources via an API (calendar events, database records, etc.) **must** implement deduplication by content key (e.g., title + date), not just rely on sync state files.

## Why
Sync state files (`synced.json`, checkpoint files) can get out of sync with reality — manual deletions, partial failures, or script changes can cause drift. The only reliable source of truth is the live API.

## Real-World Example: Notion → Outlook Calendar Sync
- **Script:** `~/notion-calendar/sync-script.sh` (runs daily at 8 AM via system crontab)
- **Bug:** No deduplication logic. Each run created new events even if identical ones already existed.
- **Result:** 8x duplicate "Bitcoin Cert [Notion]" events on the same day, 5x duplicates of other events.
- **Root cause:** Script only tracked what it had synced, never checked whether events already existed in Outlook.

## Defensive Pattern (apply to all sync scripts)

### Step 0: Pre-sync cleanup pass
Before creating anything, query the target API for existing resources matching your source identifiers. Delete duplicates.

### Step 1: Runtime deduplication
Before each creation call:
1. Query the target API (`calendarView`, `list`, etc.)
2. Build a lookup of existing resources by content key (title + date, or equivalent)
3. Skip creation if a match already exists

### Step 2: Safe CLI argument passing
Pass title/start as CLI args to Python dedup scripts instead of shell interpolation — safer for special characters.

### Step 3: Cleanup on exit
Use `trap` to clean up temp files on exit.

## Gotchas
- **Unreliable ID matching:** `outlook-calendar.sh delete` uses last-20-char ID matching against `$API/calendar/events?$top=50`, which is unreliable when multiple events share similar ID suffixes. Use direct Graph API DELETE calls with full IDs instead.
- **Sync state files are not ground truth:** Always verify against the actual API before deciding "no changes needed."

## Applicability
This pattern applies to any sync script that:
- Creates resources via an API (calendar events, database records, files, etc.)
- Runs on a schedule (cron, systemd timer, etc.)
- Could run multiple times with the same source data
