---
name: firecrawl
description: Scrape, search, and parse the web with the Firecrawl CLI (keyless free tier, 1,000 credits/month), including JS-heavy pages, local document parsing (PDF/DOCX/XLSX/HTML), and remote MCP endpoints. Use when asked to scrape a URL, search the web, extract markdown from a page, parse a local document, or interact with dynamic sites.
version: 1.1.0
category: devops
tags: [firecrawl, scraping, web-search, markdown, mcp, parse, crawl]
metadata:
  hermes:
    trigger_conditions:
      - "scrape this URL"
      - "scrape a website"
      - "extract text from a page"
      - "web search"
      - "search the web"
      - "parse this PDF"
      - "parse a document"
      - "firecrawl"
      - "convert webpage to markdown"
      - "get clean content from"
      - "search with firecrawl"
      - "parse local document"
      - "interact with a dynamic page"
---

# Firecrawl

Firecrawl provides search, scraping, page interaction, document parsing, and research tools for web data extraction.

## When to Use

- User asks to scrape a single URL to clean markdown (including JS-heavy SPAs)
- User asks to search the web and get markdown/content extraction of results
- User needs to parse a local document (PDF, DOCX, XLSX, HTML) into markdown
- User needs to interact with dynamic pages (click, fill forms, paginate, navigate)
- User asks for a research summary from scientific paper index or GitHub search
- User wants a remote MCP endpoint for Firecrawl (`https://mcp.firecrawl.dev/v2/mcp`)

## Not For

- **Deep multi-page crawls of a whole site** → use `mcp__hound__mcp_smart_crawl` (via the hound MCP) or the authenticated Firecrawl `crawl` endpoint — the keyless tier does not include `crawl`/`map`/`monitor`
- **Free AI web search via Exa MCP** → use `exa-web-search-free` instead
- **Searching a local Notion archive** → use `notcrawl-search` instead
- **One-off URL fetch without scraping semantics** → the hound MCP `mcp_smart_fetch` is lighter and keyless
- **Authenticated bulk crawling with API key** → set `FIRECRAWL_API_KEY` and use the API endpoints directly (out of scope here)

## Keyless Tier (No API Key Required)
## Keyless Tier (No API Key Required)

Firecrawl offers a free keyless tier (1,000 credits/month) for official clients (CLI, MCP, SDK).
Endpoints available keyless:
- `search` — live web search with markdown/content extraction
- `scrape` — scrape single URLs to clean markdown (including JS-heavy pages)
- `interact` — click, fill forms, paginate, and navigate dynamic sites
- `parse` — parse local documents (PDF, DOCX, XLSX, HTML) into markdown
- `research` — scientific paper index and GitHub search

*Note: `crawl`, `map`, `monitor`, and bulk operations require an authenticated account (`FIRECRAWL_API_KEY`).*

---

## Quick Start (CLI)

Run directly via `npx` without storing long-term credentials:

### 1. Scrape a URL
```bash
npx -y firecrawl-cli@latest scrape "https://example.com"
# Save to file:
npx -y firecrawl-cli@latest scrape "https://example.com" -o output.md
```

### 2. Search the Web
```bash
npx -y firecrawl-cli@latest search "query keywords"
```

### 3. Parse a Local Document
```bash
npx -y firecrawl-cli@latest parse ./document.pdf -o ./output.md
# With AI summary:
npx -y firecrawl-cli@latest parse ./document.pdf -S
```

### 4. Interact with Dynamic Pages
```bash
npx -y firecrawl-cli@latest interact "https://example.com" --actions '[{"type": "click", "selector": "#btn"}]'
```

---

## Remote MCP Integration

To use Firecrawl as a remote MCP endpoint:
- **Transport URL:** `https://mcp.firecrawl.dev/v2/mcp`
- Works with standard MCP client configurations without authentication headers for keyless tier.

---

## API Usage (Direct HTTP)

- **Base URL:** `https://api.firecrawl.dev/v2`
- **Authenticated Header (Optional / If key available):** `Authorization: Bearer fc-...`

### Scrape Endpoint (`POST /scrape`)
```bash
curl -s -X POST "https://api.firecrawl.dev/v2/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Search Endpoint (`POST /search`)
```bash
curl -s -X POST "https://api.firecrawl.dev/v2/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "site:example.com documentation"}'
```

---

## Pitfalls

1. **Keyless tier excludes `crawl`, `map`, and `monitor`** — these endpoints return 401/403 without `FIRECRAWL_API_KEY`. Use `search`/`scrape`/`interact`/`parse`/`research` instead, or fall back to hound's `mcp_smart_crawl` for whole-site walks. Check the error body before assuming a network fault.
2. **`npx -y firecrawl-cli@latest` re-downloads on cache miss** — first invocation can take 30s+; don't treat a slow first call as a hang. Prefer `-o output.md` to persist results and avoid re-scraping.
3. **JS-heavy pages need `scrape` (or `interact`), not `search`** — `search` returns snippets; a SPA's rendered content only appears via the scraper's headless browser. If a scrape returns minimal markdown, try `interact` with a click action first.
4. **`parse` expects a local file path, not a URL** — `parse ./document.pdf`, not `parse https://...`. For remote documents, `scrape` the URL first.
5. **The keyless tier is rate-limited (1,000 credits/month)** — batch operations can exhaust it quickly. Check the response headers/body for credit usage; when near the cap, prefer `mcp_smart_fetch` for single URLs and reserve Firecrawl for JS-heavy or document parsing.
6. **API base is v2** — `https://api.firecrawl.dev/v2`. If you copy v1 examples from the docs, endpoints 404. Verify the version in the URL before debugging auth.
7. **MCP transport URL is not the API base** — `https://mcp.firecrawl.dev/v2/mcp` is for MCP clients; direct HTTP calls go to `https://api.firecrawl.dev/v2`. Mixing them up yields confusing connection errors.
8. **Don't store the CLI key in shell history** — the keyless tier needs no key; if you add `FIRECRAWL_API_KEY` for authenticated calls, pass it via env in the command, not inline in the URL or `-H` (pitfall: shell history + process listing).
