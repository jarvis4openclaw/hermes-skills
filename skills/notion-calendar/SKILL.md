---
name: Notion Calendar
slug: notion-calendar
version: 1.1.0
homepage: https://clawic.com/skills/notion-calendar
description: Manage Notion calendar databases with date-aware search, page creation, rescheduling, and safe workflows for planning views.
changelog: "Initial release with date-aware Notion workflows, CLI fallback guidance, and safe create and reschedule patterns. v1.1.0: added trigger_conditions, Not For disambiguation, and numbered pitfalls."
metadata:
  clawdbot: {emoji: "N", requires: {env: ["NOTION_API_KEY"], config: ["~/notion-calendar/"]}, primaryEnv: "NOTION_API_KEY", os: ["linux", "darwin", "win32"], configPaths: ["~/notion-calendar/"]}
  hermes:
    trigger_conditions:
      - "manage Notion calendar database"
      - "create page in Notion calendar"
      - "reschedule Notion page"
      - "notion data source id"
      - "query notion database by date window"
      - "content calendar Notion"
      - "editorial plan Notion database"
      - "launch schedule Notion"
      - "notion status update page"
      - "safe Notion write verify read-back"
---

## Setup

On first use, read `setup.md` to establish token access, workspace scope, and safe write defaults.

## When to Use

User wants to treat a Notion database as a calendar, editorial plan, launch schedule, content calendar, or dated task board.
Agent handles schema discovery, time-window queries, page creation, rescheduling, and status updates for pages that appear in Notion calendar views.

## Not For

- Native Notion Calendar app settings / account preferences → configure those in the Notion app directly
- Google Calendar sync/management → use the `outlook` skill's calendar architecture or `google-workspace` skill
- General Notion page/workspace CRUD outside calendar databases → use the `notion` skill
- Recurring event series semantics → this skill models recurrence explicitly (template or batch pages); not a calendar-server replacement
- Multi-step scheduling workflows (availability, invitations) → use `schedule` skill

## Requirements

- `NOTION_API_KEY` for official API access.
- A Notion integration shared with the target database.
- Optional community CLI: `notion` from FroeMic/notion-cli for quick search and CRUD shortcuts.

## Architecture

Memory lives in `~/notion-calendar/`. See `memory-template.md` for structure.

```text
~/notion-calendar/
|-- memory.md        # Status, timezone defaults, and workspace context
|-- calendars.md     # Database and data source IDs plus property mappings
|-- templates.md     # Reusable page payload patterns
`-- safety-log.md    # Ambiguous matches, destructive confirmations, and rollbacks
```

## Quick Reference

| Topic | File |
|-------|------|
| Setup and first-run behavior | `setup.md` |
| Memory structure | `memory-template.md` |
| Calendar source mapping | `calendars.md` |
| Reusable payload templates | `templates.md` |
| Optional CLI patterns | `cli-patterns.md` |
| Calendar database schema guidance | `calendar-schema.md` |
| Query, create, and reschedule flows | `query-playbook.md` |
| Common failures and fixes | `troubleshooting.md` |

## Core Rules

### 1. Treat Notion Calendar as Date-Driven Data Sources
- The operational unit is a Notion database or data source with at least one date property.
- Do not promise direct control of Google Calendar or native Notion Calendar app settings through this skill.

### 2. Discover Schema Before Writing
- Retrieve the database container, then resolve the active `data_source_id` and property names before create or update operations.
- Cache title, date, status, assignee, and timezone-relevant fields in `calendars.md` after user approval.

### 3. Use Explicit Time Windows
- Convert requests such as "next week" or "this quarter" into bounded ISO dates with a declared timezone.
- Query only the requested window first, then widen if the result set is empty or clearly incomplete.

### 4. Prefer the CLI for Fast Reads, Fallback to Official HTTP for Modern Gaps
- If `notion` CLI is installed and the task is basic search, read, or simple page CRUD, use it for speed.
- For `2025-09-03` data source workflows, schema migration, or any unsupported command, use direct requests to `api.notion.com`.

### 5. Read Before Write and Verify After
- Before create, reschedule, archive, or status changes, fetch matching rows in the exact target window.
- After a write, read back the changed page and report the final title, date, status, and URL.

### 6. Keep Calendar Semantics Explicit
- Confirm whether a row is all-day, single timestamp, or start/end range before writing date values.
- Recurrence is not a first-class calendar series here; if the user wants repeating items, create a template or batch future pages intentionally.

### 7. Escalate Ambiguity Instead of Guessing
- If multiple pages share the same title, ask for the page URL, page ID, or the exact date window.
- Never archive or move rows on a low-confidence title match.

## Pitfalls

1. **Assuming every database ID is enough on its own** — newer Notion versions may require `data_source_id`. Resolve the active `data_source_id` before any query/write; a bare database ID silently hits the wrong container or 404s.
2. **Writing to the first property named "Date" without schema review** — the wrong calendar column gets updated. Fetch the schema, identify the exact date property, and cache it in `calendars.md` after approval.
3. **Treating Notion rows as true recurring events** — repeat behavior must be modeled (template or batch pages), not assumed. A recurring "series" in Notion is still discrete rows.
4. **Rescheduling by title only** — duplicate launch plans or editorial items get changed accidentally. Match on URL/page ID or the exact date window, and confirm before writing.
5. **Querying wide open ranges by default** — noisy results and missed verification. Bound the window (e.g. `next week` → explicit ISO dates with a declared timezone) and widen only when empty.
6. **Skipping the read-back verification** — a write "succeeds" but the row may land with the wrong date/status. Always read back the changed page and report final title, date, status, and URL.
7. **Ambiguous title matches** — multiple pages share a title; archiving or moving on a low-confidence match is destructive. Ask for the page URL/ID or the exact window instead.
8. **All-day vs timestamp confusion** — writing a bare date where a datetime is expected (or vice-versa) shifts events by a day or creates phantom times. Confirm all-day/single/range semantics before writing date values.
9. **CLI lag on modern API shapes** — the optional `notion` CLI may not support `2025-09-03` data-source workflows. Fall back to direct `api.notion.com` requests rather than forcing the CLI.
10. **Recurrence template drift** — when creating recurring pages from a template, verify each generated page's dates; a template with a relative-date formula can produce shifted dates across the batch.

## External Endpoints

| Endpoint | Data Sent | Purpose |
|----------|-----------|---------|
| `https://api.notion.com/v1/search` | Search text, filters, pagination cursor | Find candidate databases, data sources, or pages |
| `https://api.notion.com/v1/databases/*` | Database ID | Retrieve container metadata and child data sources |
| `https://api.notion.com/v1/data_sources/*` | Data source IDs, filters, sorts, property schema updates | Query rows and inspect or update calendar schema |
| `https://api.notion.com/v1/pages/*` | Page properties and content updates | Create pages, reschedule items, update status |

No other data is sent externally.

## Security & Privacy

**Data that leaves your machine:**
- Search text, page properties, dates, and page content sent to Notion through `api.notion.com`.

**Data that stays local:**
- Workspace context, property mappings, and safe defaults in `~/notion-calendar/`.

**This skill does NOT:**
- Store API keys in skill memory files.
- Access undeclared third-party calendar APIs.
- Claim a write succeeded without a read-back check.
- Modify files outside `~/notion-calendar/` for this workflow.

## Scope

This skill ONLY:
- Works with Notion databases, data sources, and pages used as calendar items.
- Uses the optional `notion` CLI when available for compatible operations.
- Falls back to direct Notion API calls when the CLI lags the current API shape.

This skill NEVER:
- Configure Notion Calendar app preferences or account settings.
- Synchronize Google Calendar accounts on the user's behalf.
- Hide destructive changes behind implicit matches.

## Trust

By using this skill, calendar-related workspace data is sent to Notion.
Only install if you trust Notion with page titles, dates, status fields, and related planning metadata.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `api` - general REST API request patterns and debugging.
- `dates` - precise date math, ranges, and timezone interpretation.
- `pkm` - broader knowledge and workspace organization patterns.
- `productivity` - execution systems around tasks and schedules.
- `schedule` - planning logic when requests become multi-step scheduling work.
- **Boss's calendar architecture**: See `outlook` skill → `references/boss-calendars.md` for the full four-calendar integration design, including the Notion→Outlook sync pipeline where Notion items get prefixed `[Notion]` and written to the Outlook Personal calendar.

## Feedback

- If useful: `clawhub star notion-calendar`
- Stay updated: `clawhub sync`
