---
name: notion-api-exploration
description: "Explore and query Notion workspaces via ntn CLI or HTTP API. Use when discovering page structure, finding databases, reading properties, or when Notion data shows unexpected 'Untitled' values. Covers title property key discovery, child database enumeration, and integration sharing requirements."
version: 1.1.0
author: pepper
tags:
  - notion
  - api
  - exploration
  - databases
  - properties
metadata:
  hermes:
    tags: [notion, api, exploration, databases, properties]
    trigger_conditions:
      - "explore Notion workspace"
      - "Notion pages show Untitled"
      - "find Notion databases"
      - "Notion child database"
      - "Notion 404 integration access"
      - "query Notion data source"
      - "ntn api search"
      - "Notion title property key"
      - "Notion API version 2025-09-03"
      - "connect integration to Notion page"
      - "Notion property type reference"
      - "notion-idea-entry pepper income"
      - "Untitled values in Notion"
---

# Notion API Exploration

Discover and query Notion workspace structure via `ntn` CLI or HTTP API.

## When to Use

- Exploring a Notion workspace to understand page/database structure
- Finding all pages, databases, or child databases
- Querying database properties and records
- Debugging "Untitled" or missing property values
- Setting up integration access to shared pages

## Not For

- **Creating/updating pages or databases** → use `notion` or `notion-cli` (write operations).
- **Local archived Notion search** → use `notcrawl-search` (SQLite + FTS5).
- **Logging new ideas into the Pepper income bucket** → use `notion-idea-entry` (purpose-built).
- **Full workspace automation / webhooks** → use the `notion` skill's broader API reference.

## Critical Pitfall: Title Property Key Varies

**Symptom:** All pages show as "Untitled" even though they have titles.

**Root cause:** Notion databases can name their title property anything — "Name", "Title", "Task", "Project", etc. The property **type** is always `"title"`, but the **key** varies per database.

**Wrong:**
```bash
ntn api v1/pages/{id} | jq '.properties.title.title[0].text.content'
```

**Right:**
```bash
# First, discover the property keys and types
ntn api v1/pages/{id} | jq '.properties | to_entries[] | {key, type: .value.type}'

# Then use the actual key (e.g., "Name")
ntn api v1/pages/{id} | jq '.properties.Name.title[0].text.content'
```

**Fix pattern:**
1. Fetch any page from the database
2. Inspect `.properties | keys` to see all property names
3. Find which property has `"type": "title"`
4. Use that property's key for all subsequent queries

## Discovering Workspace Structure

### List all pages and databases
```bash
ntn api v1/search query="" page_size:=100 | jq '.results[] | {
  object: .object,
  id: .id,
  title: (.properties | to_entries[] | select(.value.type == "title") | .value.title[0].text.content // "Untitled")
}'
```

### Find child databases in a page
```bash
ntn api v1/blocks/{page_id}/children | jq '.results[] | select(.type == "child_database") | {id, title: .child_database.title}'
```

### Query a database (data source)
```bash
# Use database_id for creating pages, data_source_id for querying
ntn api v1/data_sources/{data_source_id}/query -X POST | jq '.results[] | {id, name: .properties.Name.title[0].text.content}'
```

## Integration Sharing Requirements

**Symptom:** `404 Not Found` when querying a database that exists.

**Root cause:** The integration hasn't been granted access to that page/database.

**Fix:** In Notion UI:
1. Open the page/database
2. Click `...` menu
3. Select **Connect to** → choose your integration name

Without this step, the API returns 404 even though the resource exists.

## Property Type Reference

Common property types and their access patterns:
- **Title:** `.properties.{key}.title[0].text.content`
- **Rich text:** `.properties.{key}.rich_text[0].text.content`
- **Select:** `.properties.{key}.select.name`
- **Multi-select:** `.properties.{key}.multi_select[].name`
- **Date:** `.properties.{key}.date.start`
- **Checkbox:** `.properties.{key}.checkbox`
- **Number:** `.properties.{key}.number`
- **URL:** `.properties.{key}.url`
- **Relation:** `.properties.{key}.relation[].id`

## API Version Notes

- Use `Notion-Version: 2022-06-28` for HTTP API (ntn handles this automatically)
- Databases became "data sources" in API version 2025-09-03
- Use `database_id` when creating pages: `parent: {"database_id": "..."}`
- Use `data_source_id` when querying: `POST /v1/data_sources/{id}/query`
- Search returns databases as `"object": "data_source"` with `data_source_id` field

## ntn CLI vs HTTP API

| Task | ntn CLI | HTTP API |
|------|---------|----------|
| Search | `ntn api v1/search query=""` | `curl -X POST /v1/search` |
| Read page | `ntn api v1/pages/{id}` | `curl /v1/pages/{id}` |
| Query DB | `ntn api v1/data_sources/{id}/query -X POST` | `curl -X POST /v1/data_sources/{id}/query` |
| Create page | `ntn api v1/pages parent[database_id]={id} properties[Name][title][0][text][content]="Title"` | `curl -X POST /v1/pages` |

**ntn syntax notes:**
- `key=value` — string fields
- `key[nested]=value` — nested object fields
- `key:=value` — typed assignment (booleans, numbers, null, arrays)
- Use `page_size:=100` not `page_size=100` for numeric parameters

## Environment Setup

For `ntn` CLI:
```bash
export NOTION_API_TOKEN=$NOTION_API_KEY
export NOTION_KEYRING=0  # don't try OS keychain in headless/cron
```

For HTTP API:
```bash
curl -H "Authorization: Bearer $NOTION_API_KEY" \
     -H "Notion-Version: 2022-06-28" \
     ...
```

## Related Skills

- `notion` — full Notion API reference with ntn CLI and HTTP patterns
- `notion-cli` — Notion CLI for creating and managing pages, databases, and blocks
- `notcrawl-search` — local Notion archive search via SQLite + FTS5

## Pitfalls

1. **Title property key varies per database (the "Untitled" trap)** — Notion databases can name their title property anything ("Name", "Title", "Task"...). The type is always `"title"` but the KEY varies. Always discover keys first: `ntn api v1/pages/{id} | jq '.properties | to_entries[] | {key, type: .value.type}'`, then use the actual key. See the Critical Pitfall section above.
2. **404 on an existing database = integration not shared** — the resource exists but the integration hasn't been granted access. In Notion UI: `...` → **Connect to** → your integration. Without this, the API returns 404 even though the resource exists.
3. **`data_source_id` vs `database_id` confusion (API 2025-09-03)** — databases became "data sources": use `database_id` when CREATING pages (`parent: {"database_id": ...}`), but `data_source_id` when QUERYING (`POST /v1/data_sources/{id}/query`). Mixing them 404s or returns wrong results.
4. **ntn numeric params need `:=` not `=`** — `page_size:=100` is a typed assignment; `page_size=100` is a string and gets rejected/ignored. Same for booleans (`include_archived:=true`).
5. **Search returns databases as `object: "data_source"`** — a naive jq filter for `"database"` objects silently misses them. Filter on both object types.
6. **`NOTION_KEYRING=0` required in headless/cron** — without it, ntn tries the OS keychain and hangs in a non-TTY context. Export `NOTION_API_TOKEN=$NOTION_API_KEY` and `NOTION_KEYRING=0` before running.
7. **`Notion-Version` header matters** — use `2022-06-28` for the HTTP API (ntn handles it automatically). A missing/outdated version header changes response shapes (e.g. the data_source rename).
8. **Child database enumeration needs `child_database` filter** — `v1/blocks/{page_id}/children` returns ALL block types; filter `.results[] | select(.type == "child_database")` or you'll wade through paragraphs.
9. **Masked `Authorization: Bearer ***` in docs is a display artifact** — always read the real token from env/credential store; never paste the masked value into a curl call.
10. **Property type determines access path** — title uses `.title[0].text.content`, rich_text `.rich_text[0].text.content`, select `.select.name`, multi_select `[].name`, date `.date.start`, relation `[].id`. Using the wrong path returns `null` without an error.