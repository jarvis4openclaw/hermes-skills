---
name: agent-wikis
description: Use agentwikis.com as a live, non-stale knowledge source for AI-agent / dev tooling docs (Hermes, Claude Code, Codex, MCP, Docker, Tailscale, Shopify, etc). Fetch-on-demand via raw Markdown URLs — never store a copy offline. Load this when the user references agentwikis.com, asks for fresh docs on a covered tool, or wants source-of-truth material newer than the agent's training.
version: 1.1.0
metadata:
  hermes:
    trigger_conditions:
      - "agentwikis.com"
      - "fresh docs on a covered tool"
      - "source-of-truth material newer than training"
      - "hermes wiki llms.txt"
      - "mcp wiki building a server"
      - "authorization in MCP wiki"
      - "version-specific hermes behavior"
      - "what does the agentwikis manifest contain"
      - "fetch agentwiki raw markdown page"
      - "agentwikis shopify docs"
      - "agentwikis claude-code or codex"
      - "transport-decision mcp syntheses"
      - "distill agentwiki conclusion into skill"
---

# Agent Wikis (agentwikis.com) — Live Fetch-on-Demand

`agentwikis.com` is a hub of curated, structured knowledge bases ("Agent Wikis") compiled from messy sources. Each wiki is curated Markdown with frontmatter carrying `updated:` and `sources:` metadata. Three delivery modes exist: raw Markdown, human HTML, and a read-only MCP server.

## When to Use

- The user references agentwikis.com or a specific wiki page
- Need fresh, dated docs on a covered tool (Hermes, MCP, Claude Code, Codex, Docker, Tailscale, Shopify)
- Need version-specific Hermes behavior (e.g. "approval system in v0.18")
- Answering a question where the agent's training data is likely stale

## Not For

- **Repeatedly-used facts** (hit weekly) → distill the conclusion into a skill instead of re-pulling the wiki
- **Content that must be stored/archived** → the wiki's terms expect on-demand fetch; never commit fetched pages to notes
- **Non-covered tools** → check the manifest first; if the wiki isn't there, use `web_search` / `web_extract` on the official docs instead
- **Interactive or transactional tasks** (auth flows, API writes) → use the tool's own docs / MCP servers

## Core rule: NEVER STORE A COPY

The content goes stale. Do NOT `write_file`, `curl > file`, or commit any fetched page to disk/notes/wiki. Pull into your context only, answer, discard. If a conclusion is worth keeping, cache the *distilled conclusion* as a skill — not the source page.

## URLs

- **Manifest (discovery):** `https://agentwikis.com/llms.txt` — top-level list of all wikis with scopes + "Current as of" dates.
- **Per-wiki manifest:** `https://agentwikis.com/wiki/<wiki>/llms.txt` — full page list for one wiki (use this when the top manifest is truncated, as it often is).
- **Raw page (content):** `https://agentwikis.com/raw/<wiki>/wiki/<section>/<page>.md`
  - Example: `https://agentwikis.com/raw/mcp/wiki/concepts/what-is-mcp.md` (verified live, dated 2026-07-07)
- **Human HTML (not needed by agent):** `https://agentwikis.com/wiki/<wiki>/<path>`

## How to use

1. To find what exists: `curl -sS -L https://agentwikis.com/llms.txt` (or per-wiki `/wiki/<wiki>/llms.txt`).
2. To read a page: `curl -sS -L https://agentwikis.com/raw/<wiki>/wiki/<section>/<page>.md`
3. Read the page's frontmatter `updated:` field to judge freshness before trusting it.
4. Answer from the fetched content. Do not persist the page.

## Wikis of interest to this user (verified present 2026-07)

- **hermes** — Hermes Agent usage/config/skills/providers. Most exhaustive wiki (644-skill map, version digests). Use when a question is version-specific (e.g. "approval system in v0.18").
- **mcp** — Model Context Protocol: architecture, transports, building servers/clients, authorization, SDKs. High operational value (user runs MCP integration tasks). Pages: `concepts/building-a-server.md`, `syntheses/transport-decision.md`, `concepts/authorization.md`.
- **gbrain** — Garry Tan's OpenClaw/Hermes agent brain: schema packs, skillpacks, retrieval, minions. Reference only — pull when designing memory/retrieval architecture, not proactively.
- **shopify** — Shopify developer platform (Admin/Storefront GraphQL, apps, Functions, Hydrogen). Contingent on Crave Net being Shopify-based; dead weight until then.
- Also available: claude-code, codex, llama.cpp, huggingface, grok-build, anchor, postgresql, redis, bullpen, polymarket, tailscale, docker.

## Pitfalls

1. **MCP server endpoint is NOT at `/mcp`** — returns 404. The manifest says content is "served to MCP clients via the read-only MCP server" but does NOT publish the endpoint URL. Do not guess it; use the raw-URL fetch path instead. Re-check if the user later reports a working MCP URL.
2. **Top-level `/llms.txt` is often truncated** — the manifest is ~137K chars and display truncates at ~50K. For a complete page list of a wiki, fetch `/wiki/<wiki>/llms.txt` directly.
3. **Schemeless URLs trigger the security scanner** — always pass `https://` explicitly in curl.
4. **Paid `XL edition (Pro)` pages exist** — some wikis offer extra pages at `/pro`; not needed for normal use. Don't chase them unless the user explicitly pays.
5. **Copying the page into context anyway** — the biggest anti-pattern is storing the fetched page in notes or a wiki. Keep it in context only; if a conclusion is worth keeping, distill it into a skill.
6. **Forgetting to check the `updated:` frontmatter** — a page can be months old even on a live site. Always read the `updated:` field before trusting the content for version-sensitive answers.

## Cost note

Each fetch = one network round-trip + a few thousand tokens. For facts hit weekly (e.g. MCP transport rules), prefer a skill with the *conclusion* baked in over re-pulling. Strategy: source-of-truth pages stay live-fetched; distilled conclusions get cached as skills.
