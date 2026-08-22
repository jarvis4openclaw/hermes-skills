---
name: notcrawl-search
description: "Search and query local Notion archive via notcrawl (SQLite + FTS5)"
version: 1.1.0
author: jarvis
tags: [notion, notcrawl, search, sqlite, local-archive]
metadata:
  hermes:
    tags: [notion, notcrawl, search, sqlite, local-archive]
    trigger_conditions:
      - "search my Notion"
      - "find in Notion archive"
      - "notcrawl search"
      - "query Notion sqlite"
      - "Notion page title search"
      - "Notion comments search"
      - "notcrawl export markdown"
      - "Notion archive sync"
      - "notcrawl not working"
      - "FTS5 query Notion"
---

# notcrawl-search

Search your local Notion workspace mirrored by notcrawl. Uses the SQLite archive and FTS5 full-text search.

## When to Use

- The user asks to search their Notion knowledge base (pages, blocks, comments).
- A request needs content that likely lives in the Notion archive and should be checked locally before hitting the API.
- The user asks for a structured query (by date, database, title pattern) against the mirror.
- The user wants an up-to-date local copy of Notion (`notcrawl sync api` + `export-md`).
- The user reports `notcrawl` misbehaving (PATH, config token, or headless issues).

## Not For

- Writing/editing pages in Notion → notcrawl here is a read/search mirror; use the Notion API or app for writes.
- Searching other knowledge bases (Obsidian, Confluence, local files) → different tools per source.
- The initial one-time Notion archive setup/backfill → see the notcrawl docs / setup skill for the first mirror.
- Replacing full-text search across the whole filesystem → that's `rg`/agent search, not this archive.

## Setup

Requires notcrawl installed and configured:

```bash
notcrawl --version  # verify install
```

Config at `~/.notcrawl/config.toml` must have API sync enabled with `NOTION_API_KEY`.

## Commands

| Task | Command |
|------|---------|
| Full-text search pages | `notcrawl search "query"` |
| Search with JSON output | `notcrawl search "query" --json` |
| Search comments | `notcrawl search "query" --comments` |
| SQL query on archive | `notcrawl sql "SELECT * FROM pages WHERE title LIKE '%foo%'"` |
| Archive report | `notcrawl report` |
| Export fresh markdown | `notcrawl export-md --all` |
| Sync latest changes | `notcrawl sync api` |

## Search Tips

- FTS5 syntax: `"exact phrase"`, `term1 term2` (AND), `term1 OR term2`
- Results show: type, ID, title, snippet
- Use `notcrawl sql` for complex queries across pages, blocks, databases

## Pitfalls

1. **`notcrawl` not in PATH** — If installed to `~/.local/bin`, that directory may not be in the cron or session PATH. Recovery: export PATH explicitly before calling notcrawl commands:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   notcrawl --version
   ```
2. **Config token env mismatch** — The default `notcrawl init` writes `token_env = 'NOTION_TOKEN'`. If your env var is `NOTION_API_KEY`, change the config or set `NOTION_TOKEN=$NOTION_API_KEY`. Recovery: `grep token_env ~/.notcrawl/config.toml` and align it with the actual env var.

3. **Desktop mode on Linux headless** — notcrawl defaults to desktop + API. Disable desktop in config if on Linux without Notion Desktop app: `enabled = false` under `[notion.desktop]`. Recovery: after the change, re-run `notcrawl sync api` and confirm it no longer waits on a desktop socket.

4. **Stale mirror gives confidently wrong answers** — The SQLite archive only reflects the last successful sync. Recovery: check `notcrawl report` for the last sync time before answering; run `notcrawl sync api` first if the user expects current data.

5. **FTS5 syntax surprises** — `notcrawl search` uses FTS5: `"exact phrase"`, implicit AND for space-separated terms, `OR` for alternatives. Recovery: quote phrases, avoid bare `-` negation quirks, and fall back to `notcrawl sql` for complex predicates.

6. **`notcrawl sql` output width** — Wide rows (payload/JSON columns) can flood the transcript. Recovery: select only needed columns (`SELECT title, url FROM pages WHERE ...`) and limit rows with `LIMIT 20`.

## Integration with Hermes

When asked to search your Notion knowledge:
1. Try `notcrawl search` first — fast, covers all content
2. Use `notcrawl sql` for structured queries (by date, database, etc.)
3. Read markdown files at `~/.notcrawl/pages/default/` for full page content

## Daily Sync

Cron job runs `notcrawl sync api && notcrawl export-md --all` daily at 6am via Hermes cron.
