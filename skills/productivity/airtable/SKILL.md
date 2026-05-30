---
name: airtable
description: Airtable REST API via curl. Records CRUD, filters, upserts.
version: 1.2.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [AIRTABLE_API_KEY]
  commands: [curl]
metadata:
  hermes:
    tags: [Airtable, Productivity, Database, API]
    homepage: https://airtable.com/developers/web/api/introduction
    trigger_conditions:
      - "airtable api"
      - "airtable curl"
      - "query airtable"
      - "create airtable record"
      - "update airtable record"
      - "delete airtable record"
      - "airtable upsert"
      - "airtable filter by formula"
      - "list airtable bases"
      - "airtable schema"
      - "airtable pagination"
      - "airtable base id"
      - "airtable personal access token"
---

# Airtable — Bases, Tables & Records

Work with Airtable's REST API directly via `curl` using the `terminal` tool. No MCP server, no OAuth flow, no Python SDK — just `curl` and a personal access token.

## When to Use

Use this skill when the user needs to interact with Airtable via the REST API:
- Listing bases, tables, or schema metadata for a base
- Querying records with filters, sorting, and field selection
- Creating single or batch records (up to 10 per call)
- Updating records with PATCH (merge) or upsert by merge field
- Deleting individual or batch records
- Paginating through large result sets
- Diagnosing Airtable API errors (403 scope issues, 429 rate limits, invalid field types)
- Setting up or troubleshooting Airtable personal access tokens

## Not For

- Interactive Airtable UI operations → use a browser instead, the REST API is for programmatic access only
- Large-scale data syncs or ETL → use Airtable's Sync integrations or a dedicated ETL tool
- Real-time collaboration features → Airtable's REST API is request-response, not real-time
- Notion database operations → use `notion` skill instead
- Google Sheets operations → use `google-workspace` skill instead
- Building a custom Airtable client/SDK → this skill uses raw `curl`, not a client library
- OAuth-based Airtable integrations → use the Airtable OAuth flow directly, this skill uses PATs only

## Prerequisites

1. Create a **Personal Access Token (PAT)** at https://airtable.com/create/tokens (tokens start with `pat...`).
2. Grant these scopes (minimum):
   - `data.records:read` — read rows
   - `data.records:write` — create / update / delete rows
   - `schema.bases:read` — list bases and tables
3. **Important:** in the same token UI, add each base you want to access to the token's **Access** list. PATs are scoped per-base — a valid token on the wrong base returns `403`.
4. Store the token in `~/.hermes/.env` (or via `hermes setup`):
   ```
   AIRTABLE_API_KEY=pat_your_token_here
   ```

> Note: legacy `key...` API keys were deprecated Feb 2024. Only PATs and OAuth tokens work now.

## API Basics

- **Endpoint:** `https://api.airtable.com/v0`
- **Auth header:** `Authorization: Bearer $AIRTABLE_API_KEY`
- **All requests** use JSON (`Content-Type: application/json` for any POST/PATCH/PUT body).
- **Object IDs:** bases `app...`, tables `tbl...`, records `rec...`, fields `fld...`. IDs never change; names can. Prefer IDs in automations.
- **Rate limit:** 5 requests/sec/base. `429` → back off. Burst on a single base will be throttled.

Base curl pattern:
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=5" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

`-s` suppresses curl's progress bar — keep it set for every call so the tool output stays clean for Hermes. Pipe through `python3 -m json.tool` (always present) or `jq` (if installed) for readable JSON.

## Field Types (request body shapes)

| Field type | Write shape |
|---|---|
| Single line text | `"Name": "hello"` |
| Long text | `"Notes": "multi\nline"` |
| Number | `"Score": 42` |
| Checkbox | `"Done": true` |
| Single select | `"Status": "Todo"` (name must already exist unless `typecast: true`) |
| Multi-select | `"Tags": ["urgent", "bug"]` |
| Date | `"Due": "2026-04-01"` |
| DateTime (UTC) | `"At": "2026-04-01T14:30:00.000Z"` |
| URL / Email / Phone | `"Link": "https://…"` |
| Attachment | `"Files": [{"url": "https://…"}]` (Airtable fetches + rehosts) |
| Linked record | `"Owner": ["recXXXXXXXXXXXXXX"]` (array of record IDs) |
| User | `"AssignedTo": {"id": "usrXXXXXXXXXXXXXX"}` |

Pass `"typecast": true` at the top level of a create/update body to let Airtable auto-coerce values (e.g. create a new select option on the fly, convert `"42"` → `42`).

## Common Queries

### List bases the token can see
```bash
curl -s "https://api.airtable.com/v0/meta/bases" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### List tables + schema for a base
```bash
curl -s "https://api.airtable.com/v0/meta/bases/$BASE_ID/tables" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Use this BEFORE mutating — confirms exact field names and IDs, surfaces `options.choices` for select fields, and shows primary-field names.

### List records (first 10)
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?maxRecords=10" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Get a single record
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Filter records (filterByFormula)
Airtable formulas must be URL-encoded. Let Python stdlib do it — never hand-encode:
```bash
FORMULA="{Status}='Todo'"
ENC=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$FORMULA")
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?filterByFormula=$ENC&maxRecords=20" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

Useful formula patterns:
- Exact match: `{Email}='user@example.com'`
- Contains: `FIND('bug', LOWER({Title}))`
- Multiple conditions: `AND({Status}='Todo', {Priority}='High')`
- Or: `OR({Owner}='alice', {Owner}='bob')`
- Not empty: `NOT({Assignee}='')`
- Date comparison: `IS_AFTER({Due}, TODAY())`

### Sort + select specific fields
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?sort%5B0%5D%5Bfield%5D=Priority&sort%5B0%5D%5Bdirection%5D=asc&fields%5B%5D=Name&fields%5B%5D=Status" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Square brackets in query params MUST be URL-encoded (`%5B` / `%5D`).

### Use a named view
```bash
curl -s "https://api.airtable.com/v0/$BASE_ID/$TABLE?view=Grid%20view&maxRecords=50" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```
Views apply their saved filter + sort server-side.

## Common Mutations

### Create a record
```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Name":"New task","Status":"Todo","Priority":"High"}}' | python3 -m json.tool
```

### Create up to 10 records in one call
```bash
curl -s -X POST "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "typecast": true,
    "records": [
      {"fields": {"Name": "Task A", "Status": "Todo"}},
      {"fields": {"Name": "Task B", "Status": "In progress"}}
    ]
  }' | python3 -m json.tool
```
Batch endpoints are capped at **10 records per request**. For larger inserts, loop in batches of 10 with a short sleep to respect 5 req/sec/base.

### Update a record (PATCH — merges, preserves unchanged fields)
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"Status":"Done"}}' | python3 -m json.tool
```

### Upsert by a merge field (no ID needed)
```bash
curl -s -X PATCH "https://api.airtable.com/v0/$BASE_ID/$TABLE" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "performUpsert": {"fieldsToMergeOn": ["Email"]},
    "records": [
      {"fields": {"Email": "user@example.com", "Status": "Active"}}
    ]
  }' | python3 -m json.tool
```
`performUpsert` creates records whose merge-field values are new, patches records whose merge-field values already exist. Great for idempotent syncs.

### Delete a record
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE/$RECORD_ID" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

### Delete up to 10 records in one call
```bash
curl -s -X DELETE "https://api.airtable.com/v0/$BASE_ID/$TABLE?records%5B%5D=rec1&records%5B%5D=rec2" \
  -H "Authorization: Bearer $AIRTABLE_API_KEY" | python3 -m json.tool
```

## Pagination

List endpoints return at most **100 records per page**. If the response includes `"offset": "..."`, pass it back on the next call. Loop until the field is absent:

```bash
OFFSET=""
while :; do
  URL="https://api.airtable.com/v0/$BASE_ID/$TABLE?pageSize=100"
  [ -n "$OFFSET" ] && URL="$URL&offset=$OFFSET"
  RESP=$(curl -s "$URL" -H "Authorization: Bearer $AIRTABLE_API_KEY")
  echo "$RESP" | python3 -c 'import json,sys; d=json.load(sys.stdin); [print(r["id"], r["fields"].get("Name","")) for r in d["records"]]'
  OFFSET=$(echo "$RESP" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("offset",""))')
  [ -z "$OFFSET" ] && break
done
```

## Typical Hermes Workflow

1. **Confirm auth.** `curl -s -o /dev/null -w "%{http_code}\n" https://api.airtable.com/v0/meta/bases -H "Authorization: Bearer $AIRTABLE_API_KEY"` — expect `200`.
2. **Find the base.** List bases (step above) OR ask the user for the `app...` ID directly if the token lacks `schema.bases:read`.
3. **Inspect the schema.** `GET /v0/meta/bases/$BASE_ID/tables` — cache the exact field names and primary-field name locally in the session before mutating anything.
4. **Read before you write.** For "update X where Y", `filterByFormula` first to resolve the `rec...` ID, then `PATCH /v0/$BASE_ID/$TABLE/$RECORD_ID`. Never guess record IDs.
5. **Batch writes.** Combine related creates into one 10-record POST to stay under the 5 req/sec budget.
6. **Destructive ops.** Deletions can't be undone via API. If the user says "delete all Xs", echo back the filter + record count and confirm before firing.

## Pitfalls

1. **`filterByFormula` MUST be URL-encoded** — Field names with spaces or non-ASCII also need encoding (`{My Field}` → `%7BMy%20Field%7D`). Use Python stdlib (`urllib.parse.quote`) — never hand-escape. Incorrect encoding silently returns empty results instead of errors.

2. **Empty fields are omitted from API responses** — A missing `"Assignee"` key doesn't mean the field doesn't exist — it means this record's value is empty. Check the schema (`GET /v0/meta/bases/$BASE_ID/tables`) before concluding a field is missing from the base.

3. **PATCH vs PUT** — `PATCH` merges supplied fields into the record (preserves unchanged fields). `PUT` replaces the record entirely and clears any field you didn't include. Default to `PATCH` unless you need a full replacement.

4. **Single-select options must exist** — Writing `"Status": "Shipping"` when `Shipping` isn't in the field's option list errors with `INVALID_MULTIPLE_CHOICE_OPTIONS` unless you pass `"typecast": true` (which auto-creates the option). Check schema options before writing to select fields.

5. **Per-base token scoping** — A `403` on one base while another works means the token's Access list doesn't include that base — not a scope or auth issue. Send the user to https://airtable.com/create/tokens to grant it. The error code is `INVALID_PERMISSIONS`.

6. **Rate limits are per base, not per token** — 5 req/sec on `baseA` and 5 req/sec on `baseB` is fine; 6 req/sec on `baseA` alone will throttle. Monitor the `Retry-After` header on `429` responses. For batch operations, add `sleep 0.3` between calls.

7. **Use `python3 -m json.tool` for pretty-printing, not `jq`** — `python3 -m json.tool` is always present on any Python installation. Only reach for `jq` when you need complex filtering or projection that would be painful in Python.

8. **Pagination is per-page, not global** — Airtable's 100-record cap is a hard limit per page; there is no way to bump it. Loop with `offset` until the field is absent from the response. Pages are independent — sorting within a page doesn't guarantee global sort order.

9. **Read the `errors` array on non-2xx responses** — Airtable returns structured error codes like `AUTHENTICATION_REQUIRED`, `INVALID_PERMISSIONS`, `MODEL_ID_NOT_FOUND`, `INVALID_MULTIPLE_CHOICE_OPTIONS` that tell you exactly what's wrong. Always parse the error body before guessing.

10. **Batch endpoints cap at 10 records** — Creating or deleting more than 10 records requires multiple API calls. Loop in batches of 10 with a short sleep to respect the 5 req/sec/base limit. The error for exceeding 10 is `INVALID_REQUEST_UNKNOWN`.

11. **URL-encode square brackets in query params** — `sort[0][field]` must be encoded as `sort%5B0%5D%5Bfield%5D`. Most `curl` implementations don't auto-encode brackets. Use Python or a pre-encoded URL string. Unencoded brackets may work with some shells but fail silently with others.

12. **PATs require base-level access grants** — Creating a PAT with the right scopes isn't enough. In the token management UI, you must explicitly add each base you want the token to access. A valid token on the wrong base returns `403` with `INVALID_PERMISSIONS`, not `AUTHENTICATION_REQUIRED`.

## Important Notes for Hermes

- **Always use the `terminal` tool with `curl`.** Do NOT use `web_extract` (it can't send auth headers) or `browser_navigate` (needs UI auth and is slow).
- **`AIRTABLE_API_KEY` flows from `~/.hermes/.env` into the subprocess automatically** when this skill is loaded — no need to re-export it before each `curl` call.
- **Escape curly braces in formulas carefully.** In a heredoc body, `{Status}` is literal. In a shell argument, `{Status}` is safe outside `{...}` brace-expansion context — but pass dynamic strings through `python3 urllib.parse.quote` before splicing into a URL.
- **Pretty-print with `python3 -m json.tool`** (always present) rather than `jq` (optional). Only reach for `jq` when you need filtering/projection.
- **Pagination is per-page, not global.** Airtable's 100-record cap is a hard limit; there is no way to bump it. Loop with `offset` until the field is absent.
- **Read the `errors` array** on non-2xx responses — Airtable returns structured error codes like `AUTHENTICATION_REQUIRED`, `INVALID_PERMISSIONS`, `MODEL_ID_NOT_FOUND`, `INVALID_MULTIPLE_CHOICE_OPTIONS` that tell you exactly what's wrong.
