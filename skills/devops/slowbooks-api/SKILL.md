---
name: slowbooks-api
description: "Use when operating the SlowBooks Pro accounting API — reading the books, posting invoices/bills/payments/journal entries, or running P&L/AR/AP reports against books.wahidsaleemi.net."
version: 1.1.0
metadata:
  hermes:
    tags: [slowbooks, bookkeeping, accounting, api, fastapi, rest, invoice, payroll, 192.168.100.50, books.wahidsaleemi.net]
    trigger_conditions:
      - 'slowbooks'
      - 'books.wahidsaleemi.net'
      - 'bookkeeping api'
      - 'post an invoice'
      - 'run a report'
      - 'check the books'
      - '192.168.100.50'
      - 'SlowBooks Pro'
      - 'send an invoice'
      - 'create a customer'
      - 'record a payment'
      - 'profit and loss'
      - 'balance sheet'
      - 'AR aging'
      - 'AP aging'
      - 'schedule C'
      - 'chart of accounts'
      - 'journal entry'
      - 'trial balance'
---

# SlowBooks Pro API — agent operations

## When to Use

- Posting or looking up customers, vendors, items, invoices, bills, estimates, or payments
- Running bookkeeping reports: P&L, balance sheet, AR/AP aging, sales tax, general ledger, Schedule C
- Pulling an analytics snapshot or CSV/PDF export for a period (month/quarter/year/MTD/QTD/YTD)
- Verifying whether a transaction actually landed, or auditing what an agent changed
- Checking role/permission behaviour of the `jarvis` API token (401 vs 403 vs 422 vs 200)
- Exporting data out of SlowBooks as IIF/CSV for downstream analysis
- Searching across entities with the unified `/api/search?q=` endpoint
- Any task that names SlowBooks, `books.wahidsaleemi.net`, `192.168.100.50`, or "the books"

## Not For

- **Changing the SlowBooks application code, schema, or migrations** → use `slowbooks-dev` instead
- **Publishing the site or cutting a release to the internet** → use `static-site-deploy-verify` instead
- **The Caddy vhost / TLS fronting of books.wahidsaleemi.net** → use `caddy-proxy-management` instead
- **The CT 120/CT 107 host itself, VM resources, or Proxmox-level ops** → use `proxmox-host-management` instead
- **Generic REST/OpenAPI exploration of an unknown API** → use `firecrawl` or the app's own `/docs` directly
- **Personal finance tracking outside SlowBooks** → use `notion-idea-entry` or `xlsx` instead
- **Storing or syncing the accounting credentials themselves** → use `bitwarden-cli` or `vault-cli-cron` instead

## What this is

SlowBooks Pro 2026 (github.com/VonHoltenCodes/SlowBooks-Pro-2026) is a free, source-available double-entry bookkeeping app. Wahid runs it as **Server Edition** on **CT 120 (books)**, Ubuntu 26.04, at `192.168.100.50:3001`, fronted by Caddy at `https://books.wahidsaleemi.net`. It is a fresh install (50-account contractor chart seeded, zero balances) unless transactions have since been added.

The app exposes a **338-operation self-documenting REST API** (`/openapi.json`, Swagger at `/docs`). The intended agent surface is an API token, not the browser session.

## Auth

- **Credential:** `SLOWBOOKS_API_KEY` in `/home/wahid/.hermes/.env` (format `sbp_...`, ~47 chars). Do NOT print the value.
- **Mechanism:** `Authorization: Bearer <token>` on every request.
- **Identity:** token label `jarvis`, role `bookkeeper`, stored in `api_tokens` table.
- **No session cookie needed.** Session auth would win if present, but tokens are the agent path.

**RBAC (enforced centrally in `app/main.py`):**

| Role | Read | Write |
|------|------|-------|
| `admin` | everything | everything |
| `bookkeeper` (ours) | everything (GET/HEAD/OPTIONS) | everything EXCEPT admin writes: `/api/users`, `/api/tokens`, `/api/settings`, `/api/backups`, `/api/companies`, `/api/migration` |
| `readonly` | everything except `/api/audit` | nothing |

So with our token: **full read of the books; full write of daily books (customers, vendors, items, invoices, bills, payments, journal entries, payroll runs, estimates, credit memos); NO admin/config/backup/user/token management.** Admin-write paths return `403` (authenticated but forbidden); a bogus token returns `401`. Missing required body/query fields return `422` (schema validation — NOT a permissions issue).

## Base URL & reachability

- External/LAN: `https://books.wahidsaleemi.net` (Caddy, CT 107 = 192.168.100.53) — use this. TLS is a real Let's Encrypt wildcard cert; do NOT `-k` unless testing locally.
- Direct backend: `http://192.168.100.50:3001` (LAN-only; plain HTTP; only when the proxy is down).
- Health: `GET /health` → `200 {"status":"ok","version":"2.15.0"}` (no auth). `/api/system` → `{"version":...,"desktop":false,"server_mode":false}`.

## Quick reference — endpoints that matter

Full operation list: live `/openapi.json` (338 paths) or the repo's `docs/features.md` API reference. A compact endpoint map (path → methods) ships with this skill at `references/endpoint-map.json`. The broad strokes:

- **Snapshot/read:** `/api/accounts` (chart of accounts), `/api/customers`, `/api/vendors`, `/api/items`, `/api/invoices`, `/api/bills`, `/api/estimates`, `/api/payments`, `/api/journal`, `/api/banking/accounts`, `/api/employees`, `/api/audit`
- **Reports (read):** `/api/reports/profit-loss`, `/api/reports/balance-sheet`, `/api/reports/ar-aging`, `/api/reports/ap-aging`, `/api/reports/sales-tax`, `/api/reports/general-ledger`, `/api/reports/account-transactions?account_id=N`, `/api/tax/schedule-c`
- **Analytics:** `/api/analytics/dashboard?period=month|quarter|year|mtd|qtd|ytd` (full snapshot), `/api/analytics/export.csv`, `/api/analytics/export.pdf` — period defaults to month-to-date; explicit `start_date`/`end_date` override
- **Write (bookkeeper-allowed):** `POST /api/customers {name,...}`, `POST /api/invoices`, `POST /api/payments`, `POST /api/bills`, `POST /api/journal`, `POST /api/payroll` + `/api/payroll/{id}/process`, `POST /api/batch-payments`, plus `/void`, `/duplicate`, `/convert`, `/email` sub-actions
- **Admin-only (403 for us):** `/api/users`, `/api/tokens`, `/api/settings`, `/api/backups`, `/api/companies`, `/api/migration`
- **Exports:** `/api/iif/export/*`, `/api/csv/export/*`, `/api/analytics/export.csv` — good for pulling data out for analysis
- **Search:** `/api/search?q=...` unified across entities

## Common curl pattern

```bash
KEY=$(grep -oE '^SLOWBOOKS_API_KEY=.*' /home/wahid/.hermes/.env | cut -d= -f2-)
# Read
curl -s --resolve books.wahidsaleemi.net:443:192.168.100.53 \
  -H "Authorization: Bearer $KEY" \
  'https://books.wahidsaleemi.net/api/accounts'
# Write (JSON body)
curl -s -X POST \
  --resolve books.wahidsaleemi.net:443:192.168.100.53 \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"name":"Acme Corp"}' \
  'https://books.wahidsaleemi.net/api/customers'
```

`--resolve` is needed only when local DNS for the domain is missing; if `books.wahidsaleemi.net` resolves in the environment, plain `https://...` works.

## Verify before you trust

- **401** = bad/missing token. **403** = right token, wrong role for that path. **422** = schema error (missing required field/param) — check the response `detail` for which field. **200** = OK.
- To confirm a token's role/label without an admin route: SSH to CT 120 and query the DB (root SSH works):
  `ssh root@192.168.100.50 "su -s /bin/bash wahid -c 'cd /home/wahid/SlowBooks-Pro-2026 && .venv/bin/python -c \"from app.database import SessionLocal; from app.models.api_tokens import ApiToken; db=SessionLocal(); [print(t.label, t.role, t.is_active, t.last_used_at) for t in db.query(ApiToken).all()]; db.close()\"'"`
- After any write, read the object back (GET list + filter) to confirm it landed and the audit trail recorded it (`/api/audit`).
- Every row write is audit-logged with old/new values (`audit_log` table) — useful as ground truth for what an agent actually changed.

## Pitfalls

1. **Never touch admin paths** — with a bookkeeper token they 403 by design (anti-escalation). If an admin operation is genuinely needed, that requires a UI session as the admin user (or Wahid), not this token.
2. **`/api/tokens` 403s even on GET** — API tokens can never manage users or tokens, even their own. Use the DB query above to inspect tokens.
3. **`/api/dashboard` may 404** — the real dashboard endpoint is `/api/dashboard` in docs but live path can differ (analytics dashboard at `/api/analytics/dashboard` is the reliable one). Check `/openapi.json` when in doubt.
4. **Read-only data is a live accounting system** — a write posts double-entry journal entries automatically. Void (not delete) to reverse; most entities have a `/void` endpoint that writes reversing entries. Prefer `GET .../check-duplicate?name=` before creating customers/vendors (fuzzy dup detection; 409 on similar names unless `?force=true`).
5. **CT 120 has no curl** — use the app's venv Python or the proxy for HTTP checks from the CT; from clawd, curl works fine.
6. **`.env` has an API key but the service `.env` on CT does not** — the agent key lives in `/home/wahid/.hermes/.env` only; don't look for it in the app dir.
7. **Rate limits / auth exempt:** `/api/auth/*`, `/health`, `/pay/*`, `/api/stripe/webhook` are unauthenticated. Everything else needs the bearer token.
8. **Payroll/tax figures are approximations** — verify with a tax professional; the docs say so, and so do we.
9. **Treating a `422` as a permissions problem** — `422` is FastAPI schema validation (missing/invalid body or query field). Read the `detail` array to find the offending field; it says nothing about your role.
10. **Creating a duplicate customer or vendor** — `/api/customers` and `/api/vendors` do fuzzy duplicate detection and return `409`. Call `GET .../check-duplicate?name=` first, and only use `?force=true` after confirming the near-match really is distinct.
11. **Deleting instead of voiding** — this is a real double-entry ledger. There is no safe delete; use the entity's `/void` endpoint so reversing entries are written and the audit trail stays intact.
12. **Assuming the API version is stable** — `GET /health` reports the live version (`2.15.0` at time of writing) and the operation set is self-documenting at `/openapi.json`. When a documented path 404s, re-read `/openapi.json` rather than trusting a stale note.
13. **Rounding/currency assumptions in reports** — report totals are authoritative only for the period and filters you actually passed; a missing or misparsed `start_date`/`end_date` silently changes the answer. Echo the effective period back in your summary.
14. **Leaking the token into logs or chat** — never print the `sbp_...` value, and never paste a `curl` invocation with the literal header into a shared surface. Read it from `.env` into a shell variable at call time.

## Boundaries

- Admin surfaces (`/api/users`, `/api/tokens`, `/api/settings`, `/api/backups`, `/api/companies`, `/api/migration`) are out of scope for this token — escalate to a UI session instead of trying to work around the `403`.
