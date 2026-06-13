---
name: exa-web-search-free
description: Free AI search via Exa MCP. Web search for news/info, code search for docs/examples from GitHub/StackOverflow, company research for business intel. No API key needed.
version: 1.1.0
metadata:
  hermes:
    tags: [exa, web-search, free, neural-search, code-search, company-research]
    trigger_conditions:
      - "exa search"
      - "search with exa"
      - "free web search"
      - "exa web search"
      - "exa code search"
      - "get code context exa"
      - "company research exa"
      - "search without API key"
      - "exa MCP"
      - "exa-free"
      - "mcporter exa"
      - "neural search"
      - "use exa"
---

# Exa Web Search (Free)

## When to Use

- Searching the web for current info, news, or facts without an API key
- Finding code examples or documentation from GitHub or Stack Overflow
- Researching companies for business intelligence or competitive analysis
- Need neural/semantic search (understands meaning, not just keywords)
- Quick fact-checking without setting up a search API account
- When `web_search` results are insufficient and you need alternative coverage
- Searching for professional profiles or people (with the full toolset enabled)

## Not For

- Broad web search with many results → use `web_search` or `web_search_plus`
- Extracting full page content from URLs → use `web_extract` or `web_extract_plus`
- Domain reconnaissance or subdomain enumeration → use `domain-intel`
- Searching within local files or notes → use `search_files` or `lightrag`
- Session-specific recall (what was just said) → use `session_search`
- Academic paper discovery → use `huggingface-hub` or `web_search_plus` with arxiv filter

Neural search for web, code, and company research. No API key required.

## Setup

Verify mcporter is configured:
```bash
mcporter list exa
```

If not listed:
```bash
mcporter config add exa https://mcp.exa.ai/mcp
```

## Core Tools

### web_search_exa
Search web for current info, news, or facts.

```bash
mcporter call 'exa.web_search_exa(query: "latest AI news 2026", numResults: 5)'
```

**Parameters:**
- `query` - Search query
- `numResults` (optional, default: 8)
- `type` (optional) - `"auto"`, `"fast"`, or `"deep"`

### get_code_context_exa
Find code examples and docs from GitHub, Stack Overflow.

```bash
mcporter call 'exa.get_code_context_exa(query: "React hooks examples", tokensNum: 3000)'
```

**Parameters:**
- `query` - Code/API search query
- `tokensNum` (optional, default: 5000) - Range: 1000-50000

### company_research_exa
Research companies for business info and news.

```bash
mcporter call 'exa.company_research_exa(companyName: "Anthropic", numResults: 3)'
```

**Parameters:**
- `companyName` - Company name
- `numResults` (optional, default: 5)

## Advanced Tools (Optional)

Six additional tools available by updating config URL:
- `web_search_advanced_exa` - Domain/date filters
- `deep_search_exa` - Query expansion
- `crawling_exa` - Full page extraction
- `people_search_exa` - Professional profiles
- `deep_researcher_start/check` - AI research agent

**Enable all tools:**
```bash
mcporter config add exa-full "https://mcp.exa.ai/mcp?tools=web_search_exa,web_search_advanced_exa,get_code_context_exa,deep_search_exa,crawling_exa,company_research_exa,people_search_exa,deep_researcher_start,deep_researcher_check"

# Then use:
mcporter call 'exa-full.deep_search_exa(query: "AI safety research")'
```

## Pitfalls

1. **mcporter not installed or exa server not configured** — The most common failure: `mcporter list exa` returns nothing. Recovery: `mcporter config add exa https://mcp.exa.ai/mcp`, then verify with `mcporter list exa --schema`.

2. **mcporter call fails with "server not found"** — The server name doesn't match what's in `mcporter list`. Recovery: run `mcporter list` to see exact server names; use the exact name (case-sensitive).

3. **web_search_exa returns few or no results with `type: "fast"`** — Fast mode trades thoroughness for speed; some queries need deeper search. Recovery: use `type: "deep"` for comprehensive results; increase `numResults`.

4. **get_code_context_exa tokensNum too low, missing important snippets** — Default 5000 tokens may return fragments without full context. Recovery: increase `tokensNum` to 10000–20000 for complex code queries; reduce to 1000–2000 for focused lookups.

5. **company_research_exa returns unrelated companies with ambiguous names** — Neural search may match similar-sounding companies. Recovery: add location or industry context (e.g., `"Anthropic AI company"`); use `numResults: 3` for targeted results.

6. **mcporter daemon conflicts with existing MCP servers** — The daemon binds ports that may conflict. Recovery: `mcporter daemon stop` if conflicts occur; run ad-hoc commands instead with `--http-url` or `--stdio`.

7. **Advanced tools not available (deep_search, crawling, people_search)** — Only the basic 3 tools are available with the default exa config URL. Recovery: re-add with the full `?tools=` URL string (see Advanced Tools section) to enable all 9 tools.

8. **JSON output (`--output json`) contains escaped quotes that break parsing** — mcporter's JSON output may contain nested escaped strings. Recovery: pipe through `python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin),indent=2))"` for clean output.

9. **OAuth auth flow hangs without pty** — `mcporter auth` opens a browser for OAuth which requires interactive terminal. Recovery: use `terminal(command="mcporter auth <server>", pty=true)` for interactive flows.

10. **Mixed content when query language is non-English** — Exa's neural search optimizes for English; Chinese/Japanese/Korean queries may return fewer relevant results. Recovery: include an English translation alongside the non-English query for better coverage.

## Resources

- [GitHub](https://github.com/exa-labs/exa-mcp-server)
- [npm](https://www.npmjs.com/package/exa-mcp-server)
- [Docs](https://exa.ai/docs)
