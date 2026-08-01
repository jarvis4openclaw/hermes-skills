---
name: notion-cli
description: Notion CLI for creating and managing pages, databases, and blocks.
version: 1.1.0
homepage: https://github.com/litencatt/notion-cli
metadata:
  openclaw:
    emoji: "📓"
    requires:
      env: ["NOTION_TOKEN"]
    primaryEnv: "NOTION_TOKEN"
  hermes:
    tags: [notion, cli, databases, pages, blocks]
    trigger_conditions:
      - "create a Notion page or database entry"
      - "query a Notion database"
      - "update Notion page properties"
      - "search Notion pages"
      - "manage Notion blocks"
      - "notion-cli"
      - "Notion API"
      - "retrieve a Notion page"
      - "Notion database filter"
      - "add idea to Notion"
      - "update Notion status"
      - "get Notion page content"
---

# notion

Use *notion-cli* to create/read/update pages, data sources (databases), and blocks.

## When to Use

- Creating, reading, updating, or deleting Notion pages and database entries.
- Querying a Notion database with property filters (Status, Select, Date, etc.).
- Searching Notion for pages by title.
- Retrieving page content/blocks or updating page properties programmatically.
- Automating idea capture or status workflows that write into Notion.

## Not For

- **Managing Notion *calendar* databases with date-aware scheduling logic** → use `notion-calendar` instead
- **Searching a local Notion archive export (offline, not via the API)** → use `notcrawl-search` instead
- **High-level creative ideation workflows that happen to store output in Notion** → use `notion-idea-entry` / `income-stream-setup` for the idea-capture pattern
- **General Notion API exploration when you need to inspect a workspace's structure first** → use `notion-api-exploration` instead

## Setup

- Install notion-cli: `npm install -g @iansinnott/notion-cli`
- Create an integration at https://notion.so/my-integrations
- Copy the API key (starts with *ntn_* or *secret_*)
- Store it:
  - `mkdir -p ~/.config/notion`
  - `echo "ntn_your_key_here" > ~/.config/notion/api_key`
- Share target pages/databases with your integration (click "..." → "Connect to" → your integration name)

## Usage

All commands require the *NOTION_TOKEN* environment variable to be set:

```bash
export NOTION_TOKEN=$(cat ~/.config/notion/api_key)
```

## Common Operations

- **Search for pages and data sources:**

  `notion-cli search --query "page title"`

- **Get page:**

  `notion-cli page retrieve <PAGE_ID>`

- **Get page content (blocks):**

  `notion-cli page retrieve <PAGE_ID> -r`

- **Create page in a database:**

  ```bash
  curl -X POST https://api.notion.com/v1/pages \
    -H "Authorization: Bearer $NOTION_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Notion-Version: 2025-09-03" \
    --data '{
      "parent": { "database_id": "YOUR_DATABASE_ID" },
      "properties": {
        "Name": {
          "title": [
            {
              "text": {
                "content": "Nouvelle idée"
              }
            }
          ]
        }
      }
    }'
  ```

- **Query a database:**

  `notion-cli db query <DB_ID> -a '{"property":"Status","status":{"equals":"Active"}}'`

- **Update page properties:**

  ```bash
  curl -X PATCH https://api.notion.com/v1/pages/PAGE_ID \
    -H "Authorization: Bearer $NOTION_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Notion-Version: 2025-09-03" \
    --data '{
      "properties": {
        "Name": {
          "title": [
            {
              "text": {
                "content": "Nouveau titre"
              }
            }
          ]
        },
        "Status": {
          "status": {
            "name": "In progress"
          }
        },
        "Priority": {
          "select": {
            "name": "High"
          }
        },
        "Due date": {
          "date": {
            "start": "2026-02-10"
          }
        },
        "Description": {
          "rich_text": [
            {
              "text": {
                "content": "Description mise à jour"
              }
            }
          ]
        }
      }
    }'
  ```

- **Get database info:**

  `notion-cli db retrieve <DB_ID>`

## Property Types

Common property formats for database items:

- **Title:** `{"title": [{"text": {"content": "..."}}]}`
- **Rich text:** `{"rich_text": [{"text": {"content": "..."}}]}`
- **Status:** `{"status": {"name": "Option"}}`
- **Select:** `{"select": {"name": "Option"}}`
- **Multi-select:** `{"multi_select": [{"name": "A"}, {"name": "B"}]}`
- **Date:** `{"date": {"start": "2024-01-15", "end": "2024-01-16"}}`
- **Checkbox:** `{"checkbox": true}`
- **Number:** `{"number": 42}`
- **URL:** `{"url": "https://..."}`
- **Email:** `{"email": "a@b.com"}`

## Examples

- **Search for pages:**

  `notion-cli search --query "AIStories"`

- **Query database with filter:**

  ```bash
  notion-cli db query 2faf172c094981d3bbcbe0f115457cda \
    -a '{
      "property": "Status",
      "status": { "equals": "Backlog" }
    }'
  ```

- **Retrieve page content:**

  `notion-cli page retrieve 2fdf172c-0949-80dd-b83b-c1df0410d91b -r`

- **Update page status:**

  ```bash
  curl -X PATCH https://api.notion.com/v1/pages/2fdf172c-0949-80dd-b83b-c1df0410d91b \
    -H "Authorization: Bearer $NOTION_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Notion-Version: 2025-09-03" \
    --data '{
      "properties": {
        "Status": {
          "status": {
            "name": "In progress"
          }
        }
      }
    }'
  ```

## Key Features

- *Interactive mode:* For complex queries, run `notion-cli db query <DB_ID>` without arguments to enter interactive mode
- *Multiple output formats:* table (default), csv, json, yaml
- *Raw JSON:* Use `--raw` flag for complete API responses
- *Filter syntax:* Use `-a` flag for complex filters with AND/OR conditions

## Notes

- Page/database IDs are UUIDs (with or without dashes)
- The CLI handles authentication automatically via *NOTION_TOKEN*
- Rate limits are managed by the CLI
- Use `notion-cli help` for complete command reference

## Pitfalls

1. **Forgetting to share the page/database with the integration** — Every Notion page/database you touch must be explicitly connected to your integration (… → "Connect to" → integration name). The CLI works fine but returns "Could not find page" / 404 on unshared resources. Recovery: share the resource in the Notion UI, then retry.
2. **Using an unset `NOTION_TOKEN`** — All commands require the env var; running without it produces auth errors that look like token problems. Recovery: `export NOTION_TOKEN=$(cat ~/.config/notion/api_key)` first.
3. **Hardcoding page/database IDs with dashes vs without** — Notion accepts both UUID forms, but copying an ID with the wrong format (or the URL path truncated mid-UUID) yields 404. Recovery: use `notion-cli search --query "<title>"` to resolve real IDs.
4. **Wrong Notion-Version header on raw API calls** — The REST examples pin `Notion-Version: 2025-09-03`; an outdated header breaks property schemas (status/select changes). Recovery: keep the version header in sync with the workspace, or prefer the CLI which manages it.
5. **`metadata` key collision with the OpenClaw metadata format** — The original frontmatter used a single-line `metadata: {...}` JSON blob. If you add `metadata.hermes` in YAML, keep the OpenClaw keys intact (as done in this skill). Recovery: validate frontmatter parses as YAML after edits.
6. **Using `***` literal placeholders in curl examples** — The examples show `Authorization: Bearer ***`; pasting that verbatim sends a bogus token. Recovery: substitute the real token via `$(cat ~/.config/notion/api_key)`.
7. **Interactive mode hanging in cron/headless runs** — `notion-cli db query <DB_ID>` without args enters interactive mode and blocks. Recovery: always pass the `-a` filter or `--raw` flag in non-interactive contexts.

## References

- GitHub Notion-CLI: https://github.com/litencatt/notion-cli
- Notion API Documentation: https://developers.notion.com
