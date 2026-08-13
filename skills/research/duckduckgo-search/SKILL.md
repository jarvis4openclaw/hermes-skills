---
name: duckduckgo-search
description: Free web search via DuckDuckGo — text, news, images, videos. No API key needed. Prefer the `ddgs` CLI when installed; use the Python DDGS library only after verifying that `ddgs` is available in the current runtime.
version: 1.4.0
author: gamedevCloudy
license: MIT
metadata:
  hermes:
    tags: [search, duckduckgo, web-search, free, fallback]
    related_skills: [arxiv]
    fallback_for_toolsets: [web]
    trigger_conditions:
      - "web search with no API key"
      - "search the web for free"
      - "DuckDuckGo search"
      - "search without Firecrawl or API key"
      - "ddgs CLI search"
      - "news search free"
      - "image search free"
      - "video search free"
      - "web_search unavailable fallback"
      - "search results JSON parse"
      - "DDGS python library"
      - "search then extract page content"
      - "DuckDuckGo rate limited empty results"
---

# DuckDuckGo Search

Free web search using DuckDuckGo. **No API key required.**

## When to Use

- `web_search` is unavailable, rate-limited, or unsuitable (for example when `FIRECRAWL_API_KEY` is not set)
- User explicitly asks for DuckDuckGo results or wants a no-API-key search path
- Quick text/news/image/video lookups where a snippet list is enough (no full page content needed)
- Building a fallback search chain: built-in `web_search` → DuckDuckGo → direct extraction
- Programmatic search inside `execute_code`/Python after verifying `ddgs` is installed in that runtime

## Not For

- Full page content extraction → use `web_extract`, browser tools, or `curl` after the search
- Deep, configurable site-scoped search (Firecrawl-style) → use `web_search` with site: operators when available
- Academic paper lookups → use `arxiv` skill (has paper-specific metadata)
- Searches needing an API key, premium ranking, or guaranteed uptime → a keyed provider is more reliable
- Browsing/interacting with result pages → browser skills, not a search API

Preferred when `web_search` is unavailable or unsuitable (for example when `FIRECRAWL_API_KEY` is not set). Can also be used as a standalone search path when DuckDuckGo results are specifically desired.

## Detection Flow

Check what is actually available before choosing an approach:

```bash
# Check CLI availability
command -v ddgs >/dev/null && echo "DDGS_CLI=installed" || echo "DDGS_CLI=missing"
```

Decision tree:
1. If `ddgs` CLI is installed, prefer `terminal` + `ddgs`
2. If `ddgs` CLI is missing, do not assume `execute_code` can import `ddgs`
3. If the user wants DuckDuckGo specifically, install `ddgs` first in the relevant environment
4. Otherwise fall back to built-in web/browser tools

Important runtime note:
- Terminal and `execute_code` are separate runtimes
- A successful shell install does not guarantee `execute_code` can import `ddgs`
- Never assume third-party Python packages are preinstalled inside `execute_code`

## Installation

Install `ddgs` only when DuckDuckGo search is specifically needed and the runtime does not already provide it.

```bash
# Python package + CLI entrypoint
pip install ddgs

# Verify CLI
ddgs --help
```

If a workflow depends on Python imports, verify that same runtime can import `ddgs` before using `from ddgs import DDGS`.

## Method 1: CLI Search (Preferred)

Use the `ddgs` command via `terminal` when it exists. This is the preferred path because it avoids assuming the `execute_code` sandbox has the `ddgs` Python package installed.

```bash
# Text search
ddgs text -k "python async programming" -m 5

# News search
ddgs news -k "artificial intelligence" -m 5

# Image search
ddgs images -k "landscape photography" -m 10

# Video search
ddgs videos -k "python tutorial" -m 5

# With region filter
ddgs text -k "best restaurants" -m 5 -r us-en

# Recent results only (d=day, w=week, m=month, y=year)
ddgs text -k "latest AI news" -m 5 -t w

# JSON output for parsing
ddgs text -k "fastapi tutorial" -m 5 -o json
```

### CLI Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-k` | Keywords (query) — **required** | `-k "search terms"` |
| `-m` | Max results | `-m 5` |
| `-r` | Region | `-r us-en` |
| `-t` | Time limit | `-t w` (week) |
| `-s` | Safe search | `-s off` |
| `-o` | Output format | `-o json` |

## Method 2: Python API (Only After Verification)

Use the `DDGS` class in `execute_code` or another Python runtime only after verifying that `ddgs` is installed there. Do not assume `execute_code` includes third-party packages by default.

Safe wording:
- "Use `execute_code` with `ddgs` after installing or verifying the package if needed"

Avoid saying:
- "`execute_code` includes `ddgs`"
- "DuckDuckGo search works by default in `execute_code`"

**Important:** `max_results` must always be passed as a **keyword argument** — positional usage raises an error on all methods.

### Text Search

Best for: general research, companies, documentation.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.text("python async programming", max_results=5):
        print(r["title"])
        print(r["href"])
        print(r.get("body", "")[:200])
        print()
```

Returns: `title`, `href`, `body`

### News Search

Best for: current events, breaking news, latest updates.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.news("AI regulation 2026", max_results=5):
        print(r["date"], "-", r["title"])
        print(r.get("source", ""), "|", r["url"])
        print(r.get("body", "")[:200])
        print()
```

Returns: `date`, `title`, `body`, `url`, `image`, `source`

### Image Search

Best for: visual references, product images, diagrams.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.images("semiconductor chip", max_results=5):
        print(r["title"])
        print(r["image"])
        print(r.get("thumbnail", ""))
        print(r.get("source", ""))
        print()
```

Returns: `title`, `image`, `thumbnail`, `url`, `height`, `width`, `source`

### Video Search

Best for: tutorials, demos, explainers.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.videos("FastAPI tutorial", max_results=5):
        print(r["title"])
        print(r.get("content", ""))
        print(r.get("duration", ""))
        print(r.get("provider", ""))
        print(r.get("published", ""))
        print()
```

Returns: `title`, `content`, `description`, `duration`, `provider`, `published`, `statistics`, `uploader`

### Quick Reference

| Method | Use When | Key Fields |
|--------|----------|------------|
| `text()` | General research, companies | title, href, body |
| `news()` | Current events, updates | date, title, source, body, url |
| `images()` | Visuals, diagrams | title, image, thumbnail, url |
| `videos()` | Tutorials, demos | title, content, duration, provider |

## Workflow: Search then Extract

DuckDuckGo returns titles, URLs, and snippets — not full page content. To get full page content, search first and then extract the most relevant URL with `web_extract`, browser tools, or curl.

CLI example:

```bash
ddgs text -k "fastapi deployment guide" -m 3 -o json
```

Python example, only after verifying `ddgs` is installed in that runtime:

```python
from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("fastapi deployment guide", max_results=3))
    for r in results:
        print(r["title"], "->", r["href"])
```

Then extract the best URL with `web_extract` or another content-retrieval tool.

## Limitations

- **Rate limiting**: DuckDuckGo may throttle after many rapid requests. Add a short delay between searches if needed.
- **No content extraction**: `ddgs` returns snippets, not full page content. Use `web_extract`, browser tools, or curl for the full article/page.
- **Results quality**: Generally good but less configurable than Firecrawl's search.
- **Availability**: DuckDuckGo may block requests from some cloud IPs. If searches return empty, try different keywords or wait a few seconds.
- **Field variability**: Return fields may vary between results or `ddgs` versions. Use `.get()` for optional fields to avoid `KeyError`.
- **Separate runtimes**: A successful `ddgs` install in terminal does not automatically mean `execute_code` can import it.

## Troubleshooting

| Problem | Likely Cause | What To Do |
|---------|--------------|------------|
| `ddgs: command not found` | CLI not installed in the shell environment | Install `ddgs`, or use built-in web/browser tools instead |
| `ModuleNotFoundError: No module named 'ddgs'` | Python runtime does not have the package installed | Do not use Python DDGS there until that runtime is prepared |
| Search returns nothing | Temporary rate limiting or poor query | Wait a few seconds, retry, or adjust the query |
| CLI works but `execute_code` import fails | Terminal and `execute_code` are different runtimes | Keep using CLI, or separately prepare the Python runtime |

## Pitfalls

1. **`max_results` is keyword-only** — `ddgs.text("query", 5)` raises an error. Use `ddgs.text("query", max_results=5)`.
2. **Do not assume the CLI exists** — Check `command -v ddgs` before using it; if missing, install `pip install ddgs` or use built-in web/browser tools.
3. **Do not assume `execute_code` can import `ddgs`** — `from ddgs import DDGS` may fail with `ModuleNotFoundError` unless that runtime was prepared separately. Verify import in the same runtime you will execute in.
4. **Package name changed** — The package is `ddgs` (previously `duckduckgo-search`). Install with `pip install ddgs`; old docs referencing `duckduckgo-search` will mislead.
5. **Don't confuse `-k` and `-m`** (CLI) — `-k` is for keywords, `-m` is for max results count. Mixing them returns wrong-size or empty result sets.
6. **Empty results from rate limiting** — If `ddgs` returns nothing, it is likely throttled (DuckDuckGo blocks rapid or cloud-IP bursts). Wait a few seconds and retry, or vary the query; a short `sleep` between batched searches avoids the block.
7. **Field variability across results/versions** — Return fields differ between result types and `ddgs` versions. Use `.get()` for optional fields to avoid `KeyError`; do not hardcode a field you have not seen.
8. **Result snippets are not page content** — A search returns titles/URLs/snippets only. Do not quote from a snippet as if it were the full article; run `web_extract`/`curl` on the best URL first.
9. **`-o json` needed for programmatic parse** — Without `-o json`, CLI output is human-formatted and fragile to parse. For pipelines, request JSON and parse with `jq` or Python.
10. **Region/time filters silently narrow results** — `-r us-en` or `-t w` can return near-empty sets for niche queries. If results look thin, drop the filters before concluding the topic has no coverage.

## Validated With

Validated examples against `ddgs==9.11.2` semantics. Skill guidance now treats CLI availability and Python import availability as separate concerns so the documented workflow matches actual runtime behavior.
