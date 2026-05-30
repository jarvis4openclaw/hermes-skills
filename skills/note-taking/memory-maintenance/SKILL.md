---
name: memory-maintenance
version: 1.0.0
description: Nightly review and cleanup of memory files — enforce MEMORY.md/TOOLS.md separation, promote lessons, prune stale context, and log results in daily notes.
category: note-taking
metadata:
  hermes:
    tags: [memory, maintenance, cleanup, nightly, cron]
    trigger_conditions:
      - "clean up memory"
      - "run memory maintenance"
      - "review memory files"
      - "prune old memories"
      - "enforce MEMORY.md separation"
      - "promote lessons from daily notes"
      - "check memory hygiene"
      - "nightly memory cleanup"
      - "fix memory drift"
      - "move operational data to TOOLS.md"
      - "stale context"
      - "memory audit"
      - "organize memory files"
---

# Memory Maintenance

Nightly cron job that reviews and cleans up the memory system under `~/.hermes/memories/`. Runs autonomously — no user interaction expected.

## When to Use

- Running the nightly memory cleanup cron job
- Enforcing the MEMORY.md / TOOLS.md separation boundary after drift is detected
- Promoting durable lessons from daily notes to lessons.md
- Pruning stale or completed-task entries from MEMORY.md
- Auditing TOOLS.md for dead service references or outdated URLs
- Checking USER.md for accuracy drift without editing it
- Generating the daily `YYYY-MM-DD.md` maintenance log
- Verifying operational references are current after infrastructure changes

## Not For

- Creating or editing notes in the Obsidian vault → use `obsidian` instead
- Saving new durable facts from a conversation → use the `memory` tool directly
- Editing USER.md (the user's profile) → only edit when user explicitly directs
- Routine note-taking or knowledge capture → use `obsidian` for structured notes
- General file cleanup or disk space management → use `terminal` directly
- Searching past session transcripts for context → use `session_search` instead
- Modifying the memory system's schema or file locations → this skill assumes the standard layout

## Core Rules

- **MEMORY.md** = personal context ONLY (Boss preferences, trust signals, setup state). No IPs, SSH, config paths, service details.
- **TOOLS.md** = operational references ONLY (URLs, IPs, SSH info, config paths, service details, API quirks, workarounds).
- **USER.md** = read-only reference. Don't edit unless user explicitly directs.
- **lessons.md** = durable patterns derived from failures/recoveries. Promote from daily notes when a non-trivial lesson emerges.
- **Daily notes** = `YYYY-MM-DD.md` — log what changed under `## Memory Maintenance`.

## Workflow

### 1. Locate Files

All under `/home/wahid/.hermes/memories/`:
- `MEMORY.md`, `TOOLS.md`, `USER.md`
- `openclaw_archive/memory/lessons.md` (only lessons source)
- Recent daily notes: `20YY-MM-DD.md` (last 3-4 days)

### 2. Review MEMORY.md

Scan every entry. For each line/section, ask: *"Is this personal context or operational reference?"*

**Keep** (personal context):
- Boss preferences, trust signals, execution style
- "Boss set up X" notes (personal action, not config)
- Pointers to TOOLS.md (routing metadata)

**Move to TOOLS.md** (operational):
- SSH addresses, IPs, hostnames
- Config file paths, daemon locations
- Port numbers, service URLs
- iptables rules, networking workarounds
- WireGuard keys, API tokens, credentials
- Skill references that map to services

**Remove** (outdated):
- Completed task records (e.g., "Mnemosyne setup requested 2026-05-17")
- Historical one-off notes superseded by TOOLS.md entries
- Stale status updates ("currently working on X")

### 3. Review TOOLS.md

- Check each section for accuracy against known current state
- Add new sections for operational content moved from MEMORY.md
- Bump `*Last updated:*` date at the bottom
- Keep a running count of total sections

### 4. Review lessons.md

- Read recent daily notes (last 3-4 days) for failure/recovery patterns
- If a non-trivial lesson emerged (debugging breakthrough, architecture insight, recurring pitfall with fix), promote to lessons.md
- Skip: routine maintenance logs, "all clear" reports, heartbeat checks
- Existing lessons stay unless proven wrong or environment has changed

### 5. Check for Outdated Context

- Anything in MEMORY.md that's no longer true? Remove it.
- TOOLS.md references to dead services, old URLs, or retired hosts? Update or flag.
- USER.md still accurate? Note any drift.

### 6. Write Daily Notes

Create `2026-MM-DD.md` (or whichever today's date is) with this structure:

```markdown
# YYYY-MM-DD

## Memory Maintenance

### MEMORY.md Review
- [What was moved/removed/kept, with rationale]
- **Result:** N clean entries, listing what remains

### TOOLS.md Review
- [New sections added, dates bumped, section count]
- Now N sections total — all current and accurate

### lessons.md Review
- [Promotions or "no new lessons"]
- Existing N lessons listed

### Outdated Context Check
- MEMORY.md: [status]
- TOOLS.md: [status]
- USER.md: [status]

---

*Memory maintenance completed: YYYY-MM-DD — [summary of changes]*
```

## Pitfalls

1. **Don't touch USER.md** — Even a typo fix counts as an edit. USER.md is the user's profile — only modify it when the user explicitly gives you a directive to do so. Recovery: if you accidentally edited it, revert from git history or restore the backup.

2. **Canonical lessons.md lives in the archive** — The active memories directory (`~/.hermes/memories/`) does NOT contain a lessons.md. The canonical file is at `openclaw_archive/memory/lessons.md`. Creating a new one in the active directory creates a fork that will never be maintained. Recovery: if you created one, delete it and use the archive path.

3. **Operational drift is sneaky and cumulative** — A note that starts as personal context ("Boss set up Start Tunnel at 20.51.120.252") accumulates IPs, ports, and config paths over subsequent edits. Re-check entries that look clean at first glance — read the full line, not just the first sentence. Recovery: search for IP address patterns (`\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`) inside MEMORY.md to catch drift.

4. **Routine days are valid outcomes** — "No changes needed" is a legitimate report. Don't force edits or invent cleanup just to have output. Forcing changes on a clean system creates noise. Recovery: if you did this, note it in the daily log and revert bogus changes.

5. **Removing stale entries can orphan references** — If TOOLS.md references a MEMORY.md entry that you're about to remove, verify no cross-references will break. TOOLS.md sections often say "See MEMORY.md line X" — removing that line creates a dead pointer. Recovery: update the TOOLS.md reference or remove it too.

6. **Sensitive data stays in TOOLS.md** — Don't strip API keys, tokens, or credentials that are actively in use. The goal is organization (move operational data TO TOOLS.md), not redaction. Removing an active credential breaks whatever automation depends on it. Recovery: if you removed a credential, restore it from the previous version immediately.

7. **Daily note date format is strict** — Use `YYYY-MM-DD.md` exactly. Off-by-one dates (wrong day) or slashes (`2026/05/29.md`) break the convention that other tools rely on. Recovery: rename the file to the correct date format.

8. **Don't promote noise to lessons.md** — Routine "all clear" reports, heartbeat checks, and trivial one-liner fixes are not lessons. A lesson requires: (a) a failure or near-miss occurred, (b) a root cause was identified, and (c) the fix is durable and reusable. Promoting noise dilutes the lessons signal. Recovery: if you promoted noise, revert the lessons.md change.

9. **File writes require verification** — After every mutation (patch, write_file, remove), re-read the file to confirm the edit landed correctly. Hermes tools can truncate or misapply on large files. Recovery: if verification shows a mismatch, re-apply the edit.

10. **TOOLS.md section count can drift silently** — When adding sections, increment the count. When removing, decrement it. A stale count causes confusion in future maintenance runs. Recovery: recount sections manually and update.

11. **Don't conflate session logs with daily notes** — Session transcripts are searchable via `session_search`. Daily notes should summarize maintenance actions, not duplicate every conversation. Recovery: trim the daily note to maintenance-only content.

12. **Outdated context is worse than no context** — A TOOLS.md entry pointing to a retired host or dead service causes agents to waste time probing endpoints that don't exist. If a service is confirmed dead, remove its TOOLS.md entry entirely rather than flagging it "maybe outdated." Recovery: if you're unsure whether a service is dead, test it from the terminal before removing.

13. **`patch` truncation risk on `§`-delimited files** — MEMORY.md uses `§` as entry separators. When using `patch` (mode='replace') to remove an entry, the `old_string` MUST include the surrounding `§` boundary and sufficient unique text from the entry itself. A short `old_string` (e.g., just the separator and one sentence) can match `patch`'s fuzzy matching across `§` boundaries and silently truncate adjacent entries. **If a patch goes wrong on MEMORY.md, do NOT attempt a second patch to clean up** — the second patch's `old_string` is likely to match across the already-damaged boundary and cause further truncation. Recovery: read the file to assess damage, then use `write_file` with the full intended content. Before any MEMORY.md patch, read the entry's full text first so you have the verbatim content to restore if needed.

## Tool Notes

- Use `patch` (mode='replace') for targeted line removals and section insertions — never terminal sed/awk.
- **When patching MEMORY.md (or any `§`-delimited file), ensure `old_string` spans the full entry text including the `§` separator.** Short matches risk truncation. Prefer `write_file` for multi-entry changes.
- Use `write_file` for creating the daily notes file and for restoring damaged files.
- Use `read_file` for inspecting files; don't cat/head/tail in terminal.
- Verify after every mutation — re-read the file to confirm the edit landed correctly.
