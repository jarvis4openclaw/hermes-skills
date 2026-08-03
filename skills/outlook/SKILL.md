---
name: outlook
description: Read, search, and manage Outlook emails and calendar via Microsoft Graph API. Use when the user asks about emails, inbox, Outlook, Microsoft mail, calendar events, or scheduling.
version: 1.6.0
author: jotamed
metadata:
  hermes:
    tags: [outlook, email, calendar, microsoft, graph-api, oauth]
    trigger_conditions:
      - "check my email"
      - "read my inbox"
      - "outlook emails"
      - "Microsoft mail"
      - "calendar events"
      - "schedule a meeting"
      - "add to Family Room calendar"
      - "add to Birthdays calendar"
      - "what's on my calendar today"
      - "TeamSnap events"
      - "morning brief"
      - "send an email"
      - "reply to that email"
      - "unread emails"
      - "Hotmail / live.com mail"
---

# Outlook Skill

Access Outlook/Hotmail email and calendar via Microsoft Graph API using OAuth2.

## When to Use

- The user asks about emails, inbox, unread mail, or a specific sender's messages
- The user asks about calendar events, today's schedule, or wants an event created
- Any calendar operation — **Outlook is Wahid's exclusive calendar platform** (never Google Calendar)
- Processing email-to-calendar workflows (e.g. TeamSnap practice events)
- The user references a named calendar (Family Room, Birthdays, Personal)

## Not For

- **Google Calendar / Gmail operations** — Wahid does not use them for calendar; do not set up Google Calendar or route calendar ops to google-workspace. → use \`google-workspace\` for Gmail *only if the user explicitly asks for Gmail*, never for calendar.
- **Notion calendar databases** — named calendars (Family Room etc.) are Outlook, not Notion → use \`notion\` only for genuinely Notion-hosted data.
- **Generic IMAP/SMTP mail tooling** (himalaya, agentmail) when the user has an Outlook account with this skill configured — use this skill's scripts first.
- **Teams meeting summaries** — that's the \`teams-meeting-pipeline\` skill, not Outlook.

## Quick Setup (Automated)

```bash
# Requires: Azure CLI, jq
./scripts/outlook-setup.sh
```

The setup script will:
1. Log you into Azure (device code flow)
2. Create an App Registration automatically
3. Configure API permissions (Mail.ReadWrite, Mail.Send, Calendars.ReadWrite)
4. Guide you through authorization
5. Save credentials to `~/.outlook-mcp/`

## Manual Setup

See `references/setup.md` for step-by-step manual configuration via Azure Portal.

## Usage

### Token Management
```bash
./scripts/outlook-token.sh refresh  # Refresh expired token
./scripts/outlook-token.sh test     # Test connection
./scripts/outlook-token.sh get      # Print access token
```

### Reading Emails
```bash
./scripts/outlook-mail.sh inbox [count]           # List latest emails (default: 10)
./scripts/outlook-mail.sh unread [count]          # List unread emails
./scripts/outlook-mail.sh focused [count]         # Focused/important inbox
./scripts/outlook-mail.sh other [count]           # Other/low-priority inbox
./scripts/outlook-mail.sh search "query" [count]  # Search emails
./scripts/outlook-mail.sh from <email> [count]    # List emails from sender
./scripts/outlook-mail.sh read <id>               # Read email content
./scripts/outlook-mail.sh thread <id>             # View conversation thread
./scripts/outlook-mail.sh attachments <id>        # List email attachments
./scripts/outlook-mail.sh download <id> <name> [path]  # Download attachment
```

### Managing Emails
```bash
./scripts/outlook-mail.sh mark-read <id>          # Mark as read
./scripts/outlook-mail.sh mark-unread <id>        # Mark as unread
./scripts/outlook-mail.sh flag <id>               # Flag as important
./scripts/outlook-mail.sh unflag <id>             # Remove flag
./scripts/outlook-mail.sh delete <id>             # Move to trash
./scripts/outlook-mail.sh archive <id>            # Move to archive
./scripts/outlook-mail.sh move <id> <folder>      # Move to folder
```

### Categories (like Gmail labels)
```bash
./scripts/outlook-mail.sh categories              # List available categories
./scripts/outlook-mail.sh categorize <id> <name>  # Add category to email
./scripts/outlook-mail.sh uncategorize <id>       # Remove categories
```

### Sending Emails
```bash
./scripts/outlook-mail.sh send <to> <subj> <body> # Send new email
./scripts/outlook-mail.sh reply <id> "body"       # Reply to email
./scripts/outlook-mail.sh forward <id> <to> [msg] # Forward email
```

### Drafts
```bash
./scripts/outlook-mail.sh draft <to> <subj> <body>  # Create draft (not sent)
./scripts/outlook-mail.sh drafts [count]             # List drafts
./scripts/outlook-mail.sh send-draft <id>            # Send a draft
```

### Folders & Stats
```bash
./scripts/outlook-mail.sh folders                 # List mail folders
./scripts/outlook-mail.sh create-folder <name> [parent]  # Create folder
./scripts/outlook-mail.sh delete-folder <name>    # Delete folder
./scripts/outlook-mail.sh stats                   # Inbox statistics
```

### Bulk Operations
```bash
./scripts/outlook-mail.sh bulk-read <id1> <id2>...   # Mark multiple as read
./scripts/outlook-mail.sh bulk-delete <id1> <id2>... # Delete multiple
```

## Calendar

**Preferred: Python script** (avoids shell interpolation issues, supports `--body`):
```bash
python3 scripts/outlook-calendar.py calendars
python3 scripts/outlook-calendar.py events [calendar_id] [count]
python3 scripts/outlook-calendar.py create <subj> <start> <end> [location] [calendar_id] [--body TEXT]
python3 scripts/outlook-calendar.py delete <event_id>
```

**Alternative: Shell script** (fragile `$()` mangling — see Pitfalls):
```bash
./scripts/outlook-calendar.sh calendars
./scripts/outlook-calendar.sh create <subj> <start> <end> [location] [calendar_id]
./scripts/outlook-calendar.sh today
./scripts/outlook-calendar.sh week
./scripts/outlook-calendar.sh events [count]
./scripts/outlook-calendar.sh delete <event_id>
```

### Creating Events

```bash
# Default calendar (no calendar_id):
python3 scripts/outlook-calendar.py create "Meeting" "2026-06-30T10:00" "2026-06-30T11:00" "Conference Room"

# Family Room (fast path — cached ID, skip listing):
python3 scripts/outlook-calendar.py create "Ball Stars - Practice" "2026-06-30T17:30" "2026-06-30T18:15" "Scott Elementary School" "AQMkADAwATM3ZmYAZS04ZWYwLWRkADY5LTAwAi0wMAoARgAAAwItU7aLnqJEndgJZGhaWxQHADZTx7K111xGqfCgdGBzjC8AAAIBBgAAADZTx7K111xGqfCgdGBzjC8AAAI8CAAAAA==" --body "Basketball courts behind school\n\nFrom Kevin Chen (TeamSnap)"
```

**Cached calendar IDs** (for this user — see `references/boss-calendars.md`):

| Calendar | Full ID |
|----------|---------|
| Calendar (default) | `AQMkADAwATM3ZmYAZS04ZWYwLWRkADY5LTAwAi0wMAoARgAAAwItU7aLnqJEndgJZGhaWxQHADZTx7K111xGqfCgdGBzjC8AAAIBBgAAADZTx7K111xGqfCgdGBzjC8AAAI8BQAAAA==` |
| Family Room | `AQMkADAwATM3ZmYAZS04ZWYwLWRkADY5LTAwAi0wMAoARgAAAwItU7aLnqJEndgJZGhaWxQHADZTx7K111xGqfCgdGBzjC8AAAIBBgAAADZTx7K111xGqfCgdGBzjC8AAAI8CAAAAA==` |
| Birthdays | `AQMkADAwATM3ZmYAZS04ZWYwLWRkADY5LTAwAi0wMAoARgAAAwItU7aLnqJEndgJZGhaWxQHADZTx7K111xGqfCgdGBzjC8AAAIBBgAAADZTx7K111xGqfCgdGBzjC8AAAI8CQAAAA==` |

**Event body**: The Python `create` supports `--body TEXT`. The shell script does not. Timezone is `America/Chicago` (CDT/CST auto-switching via "Central Standard Time").

### Viewing Events
```bash
python3 scripts/outlook-calendar.py events [calendar_id] [count]
```

### Managing Events
```bash
python3 scripts/outlook-calendar.py delete "EVENT_ID"
```

Date format: `YYYY-MM-DDTHH:MM` (e.g., `2026-06-30T17:30`)

### Example Output

```bash
$ python3 scripts/outlook-calendar.py create "Lunch with client" "2026-01-26T13:00" "2026-01-26T14:00" "Restaurant"

{
  "status": "event created",
  "subject": "Lunch with client",
  "start": "2026-01-26T13:00:00.0000000",
  "end": "2026-01-26T14:00:00.0000000",
  "id": "AAMkAGQ5NzE4YjQ3..."
}
```

## Token Refresh

Access tokens expire after ~1 hour. Refresh with:

```bash
./scripts/outlook-token.sh refresh
```

## Files

- `~/.outlook-mcp/config.json` - Client ID and secret
- `~/.outlook-mcp/credentials.json` - OAuth tokens (access + refresh)

## Permissions

- `Mail.ReadWrite` - Read and modify emails
- `Mail.Send` - Send emails
- `Calendars.ReadWrite` - Read and modify calendar events
- `offline_access` - Refresh tokens (stay logged in)
- `User.Read` - Basic profile info

## Notes

- **Email IDs**: The `id` field shows the last 20 characters of the full message ID. Use this ID with commands like `read`, `mark-read`, `delete`, etc.
- **Numbered results**: Emails are numbered (n: 1, 2, 3...) for easy reference in conversation.
- **Text extraction**: HTML email bodies are automatically converted to plain text.
- **Token expiry**: Access tokens expire after ~1 hour. Run `outlook-token.sh refresh` when you see auth errors.
- **Recent emails**: Commands like `read`, `mark-read`, etc. search the 100 most recent emails for the ID.
- **Multi-account**: Use `--account <name>` to target secondary profiles. The setup script reuses the same Azure app registration for additional accounts — only the OAuth authorization step repeats. See `references/boss-calendars.md` for this user's specific calendar architecture.

## Pitfalls

1. **NEVER default to Google Calendar** — Wahid uses Outlook exclusively for all calendar management. Do NOT attempt to set up Google Calendar access, use the google-workspace skill for calendar operations, or suggest Google Calendar as an alternative. If a calendar operation is needed, this Outlook skill is the only tool to use.
2. **Calendar routing by event type** — Wahid has multiple calendars. Route events correctly:
- **Family Room** calendar: All kid/family events (TeamSnap events, sports, school activities, birthdays, family gatherings)
- **Personal** calendar: Individual adult events (work meetings, appointments, solo activities)
- When in doubt, default to Family Room for anything involving children or family activities
3. **Email-to-calendar workflow** — When processing calendar events from emails (especially TeamSnap):
1. Read the email body to extract event details (title, date, time, location, court/field number)
2. Format the title descriptively: "{Event Type} - {Location} ({Team/Organization})"
3. Add details to the --body parameter: "Court #5 · Zayn's practice (Ball Stars - Summer 2026)"
4. Use the correct calendar ID based on event type (see routing above)
4. **Stale skill path breaks silent token refresh** — The Outlook skill moved from `~/.hermes/skills/openclaw-imports/outlook/` to `~/.hermes/skills/outlook/`. Any script that calls `outlook-token.sh` (or `outlook-calendar.py`) via the old `openclaw-imports` path fails silently — and when `>/dev/null 2>&1` swallows the error, an expired token produces false **"0 events" / "no events" reports** instead of an error. Symptoms: morning brief says "free day" but the calendar actually has events. Always grep for `openclaw-imports/outlook` when diagnosing Outlook script failures. Also ensure `refresh_token()` is actually *called* in the main flow (it was defined-but-never-invoked in morning-brief.sh), or the retry logic never runs.
5. **Shell escaping with `$()` and OAuth tokens** — The terminal tool strips `$()` subshell substitution from commands. This breaks `outlook-calendar.sh` if regenerated via `write_file`/`patch` — bash commands like `ACCESS_TOKEN=*** -r '.access_token' ...)` get mangled. The shell script has been hardened but `$()` remains at risk during file edits.
6. **`outlook-calendar.py` hangs on consecutive `create` calls** — The Python script works for a single event creation but hangs/times out (20+ seconds, never returns) when creating multiple events in succession. The first call succeeds; subsequent calls stall indefinitely. **Workaround**: Use `curl` directly to the Microsoft Graph API for bulk event creation — it's fast (~1s per event) and reliable:
7. **Rebuilding shell scripts with `$()`** — If you must edit the shell script and `$()` gets mangled, use `cat > file << 'EOF'` via terminal (the heredoc syntax with quoted delimiter preserves `$()`). Do NOT use `write_file` or `patch` — they will mangle the substitution syntax.
8. **Working directory** — Always `cd` to the skill directory before running scripts, since they use relative paths to call each other.
9. **Named calendars are Outlook, not Notion** — When a user references a named calendar (e.g., "add to Family Room", "check Birthdays"), load this skill and use the cached calendar IDs FIRST. All of Wahid's named calendars (Family Room, Birthdays, Personal) are Outlook calendars — not Notion databases. Searching Notion wastes time and returns irrelevant results. The `references/boss-calendars.md` reference documents the full calendar architecture.
10. **Preferred workaround** — Use `python3 scripts/outlook-calendar.py` instead of the shell script for calendar operations. It avoids all shell parsing issues and supports `--body TEXT` for event descriptions.
11. **Multi-account token drift** — Each `--account` variant stores its own refresh token. Stale tokens produce cryptic `jq` null errors on calendar/mail commands (the scripts try to parse Graph API error JSON as regular output). Diagnostic path: always run `outlook-token.sh --account <name> test` first. If it fails, re-setup that account with `outlook-setup.sh --account <name>`.
12. **Empty `today` output** — The `today` command uses `calendarView` which returns `null` when zero events exist. This is not an auth failure. Verify with `events 5` to confirm connectivity — that endpoint always returns results if upcoming events exist.

## Troubleshooting

**"Token expired"** → Run `outlook-token.sh refresh`

**"Invalid grant"** → Token invalid, re-run setup: `outlook-setup.sh`

**"Insufficient privileges"** → Check app permissions in Azure Portal → API Permissions

**"Message not found"** → The email may be older than 100 messages. Use search to find it first.

**"Folder not found"** → Use exact folder name. Run `folders` to see available folders.

**Multi-account token drift** → Each `--account` variant stores its own refresh token. Stale tokens produce cryptic `jq` null errors on calendar/mail commands (the scripts try to parse Graph API error JSON as regular output). Diagnostic path: always run `outlook-token.sh --account <name> test` first. If it fails, re-setup that account with `outlook-setup.sh --account <name>`.

**Empty `today` output** → The `today` command uses `calendarView` which returns `null` when zero events exist. This is not an auth failure. Verify with `events 5` to confirm connectivity — that endpoint always returns results if upcoming events exist.

## Supported Accounts

- Personal Microsoft accounts (outlook.com, hotmail.com, live.com)
- Work/School accounts (Microsoft 365) - may require admin consent
- Multi-account: use `--account <name>` flag. Each account stores config in `~/.outlook-mcp-<name>/`.

## Morning Brief

A daily summary script is available at `scripts/morning-brief.sh`. It fetches today's events from Personal and Family Room calendars, checks Cal.com for new bookings, and formats a clean summary.
It is scheduled via cron to run at 8:30 AM daily (`daily-morning-brief` job).

## References

- `references/setup.md` — Manual Azure Portal setup
- `references/calendars.md` — Wahid's calendar IDs and integration architecture
- `references/skill-comparison-membranedev.md` — Comparison with membranedev's microsoft-outlook skill; documents known gaps (Contacts, Tasks, Groups, Rooms not covered)

## Changelog

### v1.5.1
- Reinforced: "NEVER default to Google Calendar" pitfall — user corrected assumption that Google Calendar was available. Outlook is the exclusive calendar platform.
- Fixed: Clarified that all calendar operations must use this skill, never google-workspace or other calendar tools

### v1.5.0
- Added: Mail commands documented in script but missing from SKILL.md
  - `focused`, `other` (inbox views)
  - `thread <id>` (conversation view)
  - `download <id> <name> [path]` (attachment download)
  - `categories`, `categorize`, `uncategorize` (label management)
  - `forward <id> <to> [msg]`
  - `draft`, `drafts`, `send-draft` (draft management)
  - `create-folder`, `delete-folder` (folder management)
  - `bulk-read`, `bulk-delete` (bulk operations)
- Fixed: SKILL.md now matches actual script capabilities

### v1.4.0
- Added: Python calendar script (`outlook-calendar.py`) as preferred tool — avoids shell `$()` mangling, supports `--body TEXT` for event descriptions
- Added: `delete` command to Python script
- Added: Cached calendar IDs inline in SKILL.md (fast path — skip listing API call)
- Fixed: Shell script `$()` syntax rebuilt via `cat heredoc` (terminal avoids mangling that write_file/patch cannot)
- Improved: Pitfalls section now recommends Python script as primary for calendar ops
- Improved: SKILL.md reorganized — Python script first, shell script as fallback

### v1.3.0
- Added: **Calendar support** (`outlook-calendar.sh`)
  - View events (today, week, upcoming)
  - Create/quick-create events
  - Update event details (subject, location, time)
  - Delete events
  - Check availability (free/busy)
  - List calendars
- Added: `Calendars.ReadWrite` permission

### v1.2.0
- Added: `mark-unread` - Mark emails as unread
- Added: `flag/unflag` - Flag/unflag emails as important
- Added: `delete` - Move emails to trash
- Added: `archive` - Archive emails
- Added: `move` - Move emails to any folder
- Added: `from` - Filter emails by sender
- Added: `attachments` - List email attachments
- Added: `reply` - Reply to emails
- Improved: `send` - Better error handling and status output
- Improved: `move` - Case-insensitive folder names, shows available folders on error

### v1.1.0
- Fixed: Email IDs now use unique suffixes (last 20 chars)
- Added: Numbered results (n: 1, 2, 3...)
- Improved: HTML bodies converted to plain text
- Added: `to` field in read output

### v1.0.0
- Initial release
