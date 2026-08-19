---
name: shell-timezone-date
description: Convert local date to UTC in shell without the date -u trap.
version: 1.1.0
author: hermes-curator
metadata:
  hermes:
    tags: [shell, bash, date, timezone, utc, epoch, cron]
    trigger_conditions:
      - "compute a UTC query window from a local date"
      - "convert local midnight to UTC for an API"
      - "date -u is giving the wrong offset"
      - "calendar query returns yesterday's or drops today's events"
      - "timezone skew in a cron script"
      - "UTC window for Graph calendarView"
      - "startDateTime endDateTime UTC range"
      - "Central midnight to UTC"
      - "DST boundary date arithmetic"
      - "TZ= date -d conversion wrong"
      - "epoch arithmetic for date windows"
      - "morning brief shows wrong events"
      - "Cal.com filter startswith today broken"
---

# Shell Timezone / Date Conversion

## When to use
Any bash script that needs a **timezone-correct UTC instant** derived from a local
calendar date — most commonly to build a query window for an API that takes UTC
(e.g. Microsoft Graph `calendarView`, Cal.com bookings, any `startDateTime`/`endDateTime`
range). Also when debugging a 1-hour-to-5-hour offset mystery in scheduled output.

## Not For
- **Formatting a single timestamp for display** — if you just need `date +%Y-%m-%d` with
  the host's local time, plain `date` suffices → no skill needed.
- **UTC-only server-side code** (Node/Python services that never touch local TZ) — timezone
  libraries in the language runtime are a better fit → use the language's own `Intl`/`zoneinfo`.
- **Cross-platform scheduling math** (cron in containers with a different TZ than the host) —
  you need `TZ=` + `CRON_TZ` semantics, not epoch conversion → see `cron-model-optimization`.
- **Date parsing inside Python/Node scripts** — use `zoneinfo`/`Intl` instead of shelling out
  to `date` → no shell skill needed.

## The trap (why naive code is wrong)
```bash
# WRONG — reproduces a UTC-midnight bug under CDT/CST
START=$(TZ="America/Chicago" date -u -d "2026-08-18 00:00:00" +%Y-%m-%dT%H:%M:%SZ)
# -> 2026-08-18T00:00:00Z   (NOT Central midnight; this IS the bug)
```
`date -u` forces UTC **output** AND treats the **zoneless input string as UTC**, silently
ignoring `TZ=`. So `TZ=… date -u -d "zoneless string"` does NOT convert local→UTC; it
just formats the already-UTC string. Symptoms: a window meant to be "today in Central"
becomes "UTC midnight" = Central 19:00 *yesterday*, leaking prior-day late events and
dropping today's late events.

`TZ=… date -d "string" +%s` (NO `-u`) IS correct for parsing: it honors `TZ` when
converting the local string to an epoch integer.

## Correct pattern: epoch arithmetic
```bash
TZ="America/Chicago"
TODAY=$(date +%Y-%m-%d)
EPOCH_START=$(TZ="$TZ" date -d "${TODAY} 00:00:00" +%s)   # local midnight -> epoch (TZ honored)
EPOCH_END=$((EPOCH_START + 86400))                          # exactly one day
UTC_START=$(date -u -d "@${EPOCH_START}" +%Y-%m-%dT%H:%M:%SZ)  # -> 2026-08-18T05:00:00Z (CDT)
UTC_END=$(date -u -d "@${EPOCH_END}" +%Y-%m-%dT%H:%M:%SZ)        # -> 2026-08-19T05:00:00Z
```
`date -u -d "@<epoch>"` converts epoch→UTC reliably. Always verify the inverse:
```bash
TZ="$TZ" date -d "@${EPOCH_START}" +%Y-%m-%dT%H:%M:%S%Z   # 2026-08-18T00:00:00CDT
```

## Cal.com / string-time filtering
Never match by date prefix (`startswith($today)`) when the API stores UTC — that inherits
the same skew. Compare against the UTC window bounds:
```jq
map(select(.startTime >= $start and .startTime <= $end))
```
with `$start="${UTC_START%Z}.000Z"`, `$end="${UTC_END%Z}.999Z"`.

## Verification recipe + mock test
See `references/timezone-window-fix.md` for a full reproduction (the wrong vs right
`date` calls, and a 4-event Cal.com mock that proves yesterday/tomorrow are excluded and
a late "today" event — previously dropped — is now included).

## Pitfalls
1. **`date -u` + zoneless input = parsing-as-UTC trap** — `TZ=… date -u -d "zoneless string"` formats the string as UTC *and* parses it as UTC, silently ignoring `TZ=`. The output looks correct but is shifted by the whole offset. Recovery: pivot through epoch integers (`TZ="$TZ" date -d "…" +%s`, then `date -u -d "@epoch"`).
2. **`+1 day` string math breaks at DST boundaries** — `date -d "… +1 day"` can land at 23:00 or 01:00 across a DST switch. Recovery: use `+86400` seconds on the epoch integer — the only DST-proof day increment.
3. **Displayed times are NOT the bug** — Outlook/Graph event *times* come from `Prefer: outlook.timezone=…` and are correct; only the *selection window* was wrong. Recovery: fix the `calendarView` window, don't touch the display formatter.
4. **Host TZ differs from user TZ** — cron and containers often run UTC while the user lives in CDT/CST. Never trust the host `date` default; always set `TZ=` explicitly and compute UTC bounds from local midnight.
5. **`startswith($today)` filtering on UTC-stored data inherits the skew** — matching `2026-08-18` against UTC timestamps drops today's late events and leaks yesterday's. Recovery: compare against the UTC window bounds (`>= $start and <= $end`), never a date prefix.
6. **Forgotten `Z` suffix in API windows** — passing `2026-08-18T05:00:00` (no `Z`) to Graph/Cal.com can be re-interpreted as local time. Recovery: build bounds as `"${UTC_START%Z}.000Z"` / `"${UTC_END%Z}.999Z"`.
7. **Epoch arithmetic without verifying the inverse** — a wrong `TZ` variable silently produces a wrong window with no error. Recovery: always verify with `TZ="$TZ" date -d "@${EPOCH_START}" +%Y-%m-%dT%H:%M:%S%Z` — it must print the intended local midnight with the right offset abbreviation.
