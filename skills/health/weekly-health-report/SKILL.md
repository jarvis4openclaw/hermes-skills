---
name: weekly-health-report
description: Generate a Friday 9am Apple Health week-over-week report from the health-ingest DuckDB, emphasizing Executive Summary and Health Optimization Takeaways.
version: 1.1.0
metadata:
  hermes:
    tags: [health, duckdb, apple-health, weekly-report, longevity, diabetes, fitness]
    trigger_conditions:
      - "weekly health report"
      - "week over week health summary"
      - "Friday health check-in"
      - "Apple Health WoW report"
      - "compare past week to week before"
      - "generate health report"
      - "steps this week vs last week"
      - "health optimization takeaways"
      - "executive summary health"
      - "sleep last week vs this week"
      - "health duckdb query"
---

# Weekly Health Report

Use this skill to generate the user's weekly Apple Health report from `/home/wahid/health-ingest/data/health.duckdb`.

## When to Use

- The Friday 9am cron fires and a week-over-week Apple Health report is due.
- The user asks for a health summary comparing the latest 7 days against the previous 7 days.
- The user asks "how did my steps/sleep/heart rate change this week" and data lives in the health DuckDB.
- Any request that should produce an Executive Summary + Health Optimization Takeaways from the health DB.

## Not For

- Ingesting new Apple Health data into the DuckDB → use the `health-ingest` skill / ingest pipeline.
- Diagnosing why health data is missing from the DB → check the ingest service, not this reporting skill.
- Medical advice or clinical interpretation → this skill reports trends, always with a caveat for uncertainty.
- Non-health reports from other data sources → use the relevant database/analytics skill.

## Purpose

Produce a concise, useful Friday health-optimization report comparing the latest 7-day window to the previous 7-day window for all available Apple Health metrics:

- Exercise Time
- Heart Rate
- Steps
- Sleep
- Oxygen Saturation / Blood Oxygen
- Walking Heart Rate Average
- Walking + Running Distance

The user specifically likes:

1. **Executive Summary**
2. **Health Optimization Takeaways**

Keep those sections prominent every time.

## Data Source

Canonical project root: `/home/wahid/health-ingest/`  
DuckDB: `/home/wahid/health-ingest/data/health.duckdb`  
README: `/home/wahid/health-ingest/README.md`

Table: `apple_health_records`

Important columns:

- `metric_type`
- `observed_at`
- `value_raw`
- `value_num`
- `payload`

File metadata table:

- `ingest_files`

## Privacy Rules

- Health data is sensitive. Do **not** dump raw rows or detailed payloads into the final report.
- Aggregate and summarize only.
- It is okay to include weekly totals, averages, ranges, and notable daily highs/lows.

## Report Windows

Anchor to the latest `observed_at` in the database, not the system date, because data may arrive late.

Default comparison:

- **Current week:** latest 7 calendar days ending on the latest observed day, inclusive.
- **Prior week:** the 7 calendar days immediately before that.

SQL window logic:

```sql
WITH bounds AS (
  SELECT
    date_trunc('day', max(observed_at)) AS latest_day,
    date_trunc('day', max(observed_at)) - INTERVAL 6 DAY AS curr_start,
    date_trunc('day', max(observed_at)) + INTERVAL 1 DAY AS curr_end,
    date_trunc('day', max(observed_at)) - INTERVAL 13 DAY AS prev_start,
    date_trunc('day', max(observed_at)) - INTERVAL 6 DAY AS prev_end
  FROM apple_health_records
)
```

Always state the actual date windows and whether either period is incomplete.

## Metric Interpretation

### Additive metrics

Use weekly totals and daily averages:

- Steps
- Walking + Running Distance
- Exercise Time

For these, compare:

- current total vs prior total
- current average per day vs prior average per day
- best/worst days if useful

### Average metrics

Use sample/daily averages and ranges:

- Heart Rate
- Walking Heart Rate Average
- Oxygen Saturation

For these, compare:

- average value
- min/max
- notable outlier days

### Sleep

The current DB stores sleep as stage-change events (`Core`, `REM`, `Deep`, `Awake`, sometimes `Asleep`) where `value_num` is usually null.

Estimate sleep duration by computing the interval between consecutive sleep stage events, capped to reasonable gaps. Treat this as directional, not clinical-grade. Always caveat if sleep parsing looks odd.

Suggested cap: ignore/cap intervals greater than 12 hours.

Sleep stages considered asleep: `Core`, `Deep`, `REM`, `Asleep`. Awake is separate.

## Suggested Query Pattern

Use the venv Python so DuckDB is available:

```bash
/home/wahid/health-ingest/.venv/bin/python - <<'PY'
import duckdb, csv, sys
con = duckdb.connect('/home/wahid/health-ingest/data/health.duckdb', read_only=True)
# Run aggregate SQL; print compact CSV sections for the agent to summarize.
PY
```

Avoid pandas/numpy because the venv may not include them.

## Recommended Final Report Format

```markdown
I queried the health DuckDB and compared the latest 7-day window against the prior 7-day window.

**Windows compared**
- Current week: ...
- Prior week: ...
- Database rows analyzed: ...
- Data completeness caveat: ...

## Executive Summary

Overall: ...

### The good
- ...

### Watch-outs
- ...

## Metric-by-metric comparison

| Metric | Current week | Prior week | Change / interpretation |
|---|---:|---:|---|
| Steps | ... | ... | ... |

## Daily highlights

- Best activity day: ...
- Lowest movement day: ...
- HR/oxygen/sleep outliers: ...

## Health Optimization Takeaways

1. ...
2. ...
3. ...
```

## Tone

- Clear, supportive, and slightly playful Doctor Strange style.
- Avoid alarmism.
- Admit uncertainty when data is incomplete or sleep parsing is approximate.
- Make takeaways practical and low-barrier.

## Health Priorities for This User

Tie recommendations to the user's goals:

- Diabetes/glycemic control
- Longevity
- Energy
- Shoulder-safe movement
- Injury prevention
- Strength and protein adherence when relevant

High-yield recurring advice if supported by the data:

- 10–15 minute post-meal walks, especially after dinner.
- Gradual step target increases rather than heroic spikes.
- Watch high walking HR days in context: heat, hydration, caffeine, sleep, stress, illness, intentional workout.
- Maintain consistency over intensity.

## Verification Checklist

Before finalizing:

1. Confirm the DB exists.
2. Confirm the latest observed timestamp.
3. Confirm all metric types present.
4. State if the previous week is incomplete.
5. Do not expose raw payloads or row-level data.

## Pitfalls

1. **Anchor windows to the DB's latest `observed_at`, not the system date** — Data arrives late; `date_trunc('day', max(observed_at))` is the only reliable anchor. Using `now()` mislabels incomplete weeks as complete.

2. **Sleep is stored as stage-change events, not durations** — `Core`/`REM`/`Deep`/`Asleep` rows have `value_num` usually null. Estimate duration by interval between consecutive stage events, cap intervals > 12h, and always caveat that it is directional, not clinical-grade.

3. **Don't dump raw rows or payloads** — Health data is sensitive. Aggregate to totals/averages/ranges; never expose row-level `payload` content in the report.

4. **State incomplete periods explicitly** — If either window has missing days, say so and avoid over-interpreting the delta. A half-empty week makes the comparison misleading.

5. **Avoid pandas/numpy in the query venv** — The health-ingest venv may not include them. Use plain `duckdb` + CSV output in a heredoc, then summarize from the CSV.

6. **Sleep parsing looks odd — say so** — If stage gaps or missing `Asleep` rows make the estimate unreliable, caveat rather than reporting a confident number.

7. **The report format is a contract** — Keep Executive Summary and Health Optimization Takeaways prominent; the user specifically wants those sections every time, not buried after a metrics dump.

8. **Missing metrics are normal** — Not every metric type has data every week (e.g., blood oxygen). Report what exists; don't fabricate zeros for absent metric types.

9. **Tie takeaways to the user's stated priorities** — Diabetes/glycemic control, longevity, energy, shoulder-safe movement, injury prevention. Generic fitness advice without those hooks is lower value.

10. **Tone: supportive, not alarmist** — Admit uncertainty on incomplete data, keep practical low-barrier recommendations (post-meal walks, gradual step increases, context-aware HR interpretation).
