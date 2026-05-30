---
name: parallel-cli
description: Optional vendor skill for Parallel CLI — agent-native web search, extraction, deep research, enrichment, FindAll, and monitoring. Prefer JSON output and non-interactive flows.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Research, Web, Search, Deep-Research, Enrichment, CLI]
    related_skills: [duckduckgo-search, mcporter]
    trigger_conditions:
      - "parallel search"
      - "parallel research"
      - "parallel-cli"
      - "parallel enrich"
      - "parallel findall"
      - "parallel monitor"
      - "deep research parallel"
      - "entity discovery parallel"
      - "parallel web extraction"
      - "parallel enrichment"
      - "use parallel for"
      - "parallel async job"
      - "vendor search parallel"
---

# Parallel CLI

Use `parallel-cli` when the user explicitly wants Parallel, or when a terminal-native workflow would benefit from Parallel's vendor-specific stack for web search, extraction, deep research, enrichment, entity discovery, or monitoring.

This is an optional third-party workflow, not a Hermes core capability.

Important expectations:
- Parallel is a paid service with a free tier, not a fully free local tool.
- It overlaps with Hermes native `web_search` / `web_extract`, so do not prefer it by default for ordinary lookups.
- Prefer this skill when the user mentions Parallel specifically or needs capabilities like Parallel's enrichment, FindAll, or monitor workflows.

`parallel-cli` is designed for agents:
- JSON output via `--json`
- Non-interactive command execution
- Async long-running jobs with `--no-wait`, `status`, and `poll`
- Context chaining with `--previous-interaction-id`
- Search, extract, research, enrichment, entity discovery, and monitoring in one CLI

## When to use it

Prefer this skill when:
- The user explicitly mentions Parallel or `parallel-cli`
- The task needs richer workflows than a simple one-shot search/extract pass
- You need async deep research jobs that can be launched and polled later
- You need structured enrichment, FindAll entity discovery, or monitoring

## Not For

- Quick web searches → use Hermes native `web_search` (faster, no auth needed)
- Simple URL content extraction → use `web_extract` or `web_extract_plus` instead
- Academic paper search → use `arxiv` instead
- GitHub/package search → use `web_search` with `site:` operators instead
- Domain reconnaissance → use `domain-intel` for passive DNS/subdomain enumeration
- General MCP server interaction → use `mcporter` or `native-mcp` instead

Prefer Hermes native `web_search` / `web_extract` for quick one-off lookups when Parallel is not specifically requested.

## Installation

Try the least invasive install path available for the environment.

### Homebrew

```bash
brew install parallel-web/tap/parallel-cli
```

### npm

```bash
npm install -g parallel-web-cli
```

### Python package

```bash
pip install "parallel-web-tools[cli]"
```

### Standalone installer

```bash
curl -fsSL https://parallel.ai/install.sh | bash
```

If you want an isolated Python install, `pipx` can also work:

```bash
pipx install "parallel-web-tools[cli]"
pipx ensurepath
```

## Authentication

Interactive login:

```bash
parallel-cli login
```

Headless / SSH / CI:

```bash
parallel-cli login --device
```

API key environment variable:

```bash
export PARALLEL_API_KEY="***"
```

Verify current auth status:

```bash
parallel-cli auth
```

If auth requires browser interaction, run with `pty=true`.

## Core rule set

1. Always prefer `--json` when you need machine-readable output.
2. Prefer explicit arguments and non-interactive flows.
3. For long-running jobs, use `--no-wait` and then `status` / `poll`.
4. Cite only URLs returned by the CLI output.
5. Save large JSON outputs to a temp file when follow-up questions are likely.
6. Use background processes only for genuinely long-running workflows; otherwise run in foreground.
7. Prefer Hermes native tools unless the user wants Parallel specifically or needs Parallel-only workflows.

## Quick reference

```text
parallel-cli
├── auth
├── login
├── logout
├── search
├── extract / fetch
├── research run|status|poll|processors
├── enrich run|status|poll|plan|suggest|deploy
├── findall run|ingest|status|poll|result|enrich|extend|schema|cancel
└── monitor create|list|get|update|delete|events|event-group|simulate
```

## Common flags and patterns

Commonly useful flags:
- `--json` for structured output
- `--no-wait` for async jobs
- `--previous-interaction-id <id>` for follow-up tasks that reuse earlier context
- `--max-results <n>` for search result count
- `--mode one-shot|agentic` for search behavior
- `--include-domains domain1.com,domain2.com`
- `--exclude-domains domain1.com,domain2.com`
- `--after-date YYYY-MM-DD`

Read from stdin when convenient:

```bash
echo "What is the latest funding for Anthropic?" | parallel-cli search - --json
echo "Research question" | parallel-cli research run - --json
```

## Search

Use for current web lookups with structured results.

```bash
parallel-cli search "What is Anthropic's latest AI model?" --json
parallel-cli search "SEC filings for Apple" --include-domains sec.gov --json
parallel-cli search "bitcoin price" --after-date 2026-01-01 --max-results 10 --json
parallel-cli search "latest browser benchmarks" --mode one-shot --json
parallel-cli search "AI coding agent enterprise reviews" --mode agentic --json
```

Useful constraints:
- `--include-domains` to narrow trusted sources
- `--exclude-domains` to strip noisy domains
- `--after-date` for recency filtering
- `--max-results` when you need broader coverage

If you expect follow-up questions, save output:

```bash
parallel-cli search "latest React 19 changes" --json -o /tmp/react-19-search.json
```

When summarizing results:
- lead with the answer
- include dates, names, and concrete facts
- cite only returned sources
- avoid inventing URLs or source titles

## Extraction

Use to pull clean content or markdown from a URL.

```bash
parallel-cli extract https://example.com --json
parallel-cli extract https://company.com --objective "Find pricing info" --json
parallel-cli extract https://example.com --full-content --json
parallel-cli fetch https://example.com --json
```

Use `--objective` when the page is broad and you only need one slice of information.

## Deep research

Use for deeper multi-step research tasks that may take time.

Common processor tiers:
- `lite` / `base` for faster, cheaper passes
- `core` / `pro` for more thorough synthesis
- `ultra` for the heaviest research jobs

### Synchronous

```bash
parallel-cli research run \
  "Compare the leading AI coding agents by pricing, model support, and enterprise controls" \
  --processor core \
  --json
```

### Async launch + poll

```bash
parallel-cli research run \
  "Compare the leading AI coding agents by pricing, model support, and enterprise controls" \
  --processor ultra \
  --no-wait \
  --json

parallel-cli research status trun_xxx --json
parallel-cli research poll trun_xxx --json
parallel-cli research processors --json
```

### Context chaining / follow-up

```bash
parallel-cli research run "What are the top AI coding agents?" --json
parallel-cli research run \
  "What enterprise controls does the top-ranked one offer?" \
  --previous-interaction-id trun_xxx \
  --json
```

Recommended Hermes workflow:
1. launch with `--no-wait --json`
2. capture the returned run/task ID
3. if the user wants to continue other work, keep moving
4. later call `status` or `poll`
5. summarize the final report with citations from the returned sources

## Enrichment

Use when the user has CSV/JSON/tabular inputs and wants additional columns inferred from web research.

### Suggest columns

```bash
parallel-cli enrich suggest "Find the CEO and annual revenue" --json
```

### Plan a config

```bash
parallel-cli enrich plan -o config.yaml
```

### Inline data

```bash
parallel-cli enrich run \
  --data '[{"company": "Anthropic"}, {"company": "Mistral"}]' \
  --intent "Find headquarters and employee count" \
  --json
```

### Non-interactive file run

```bash
parallel-cli enrich run \
  --source-type csv \
  --source companies.csv \
  --target enriched.csv \
  --source-columns '[{"name": "company", "description": "Company name"}]' \
  --intent "Find the CEO and annual revenue"
```

### YAML config run

```bash
parallel-cli enrich run config.yaml
```

### Status / polling

```bash
parallel-cli enrich status <task_group_id> --json
parallel-cli enrich poll <task_group_id> --json
```

Use explicit JSON arrays for column definitions when operating non-interactively.
Validate the output file before reporting success.

## FindAll

Use for web-scale entity discovery when the user wants a discovered dataset rather than a short answer.

```bash
parallel-cli findall run "Find AI coding agent startups with enterprise offerings" --json
parallel-cli findall run "AI startups in healthcare" -n 25 --json
parallel-cli findall status <run_id> --json
parallel-cli findall poll <run_id> --json
parallel-cli findall result <run_id> --json
parallel-cli findall schema <run_id> --json
```

This is a better fit than ordinary search when the user wants a discovered set of entities that can be reviewed, filtered, or enriched later.

## Monitor

Use for ongoing change detection over time.

```bash
parallel-cli monitor list --json
parallel-cli monitor get <monitor_id> --json
parallel-cli monitor events <monitor_id> --json
parallel-cli monitor delete <monitor_id> --json
```

Creation is usually the sensitive part because cadence and delivery matter:

```bash
parallel-cli monitor create --help
```

Use this when the user wants recurring tracking of a page or source rather than a one-time fetch.

## Recommended Hermes usage patterns

### Fast answer with citations
1. Run `parallel-cli search ... --json`
2. Parse titles, URLs, dates, excerpts
3. Summarize with inline citations from the returned URLs only

### URL investigation
1. Run `parallel-cli extract URL --json`
2. If needed, rerun with `--objective` or `--full-content`
3. Quote or summarize the extracted markdown

### Long research workflow
1. Run `parallel-cli research run ... --no-wait --json`
2. Store the returned ID
3. Continue other work or periodically poll
4. Summarize the final report with citations

### Structured enrichment workflow
1. Inspect the input file and columns
2. Use `enrich suggest` or provide explicit enriched columns
3. Run `enrich run`
4. Poll for completion if needed
5. Validate the output file before reporting success

## Error handling and exit codes

The CLI documents these exit codes:
- `0` success
- `2` bad input
- `3` auth error
- `4` API error
- `5` timeout

If you hit auth errors:
1. check `parallel-cli auth`
2. confirm `PARALLEL_API_KEY` or run `parallel-cli login` / `parallel-cli login --device`
3. verify `parallel-cli` is on `PATH`

## Maintenance

Check current auth / install state:

```bash
parallel-cli auth
parallel-cli --help
```

Update commands:

```bash
parallel-cli update
pip install --upgrade parallel-web-tools
parallel-cli config auto-update-check off
```

## Pitfalls

1. **Always use `--json` for machine-readable output** — Human-formatted output is ambiguous and loses structure. The only exception is when the user explicitly requests human-readable output.

2. **Never cite sources not present in CLI output** — Only URLs, titles, and facts returned by the `parallel-cli` output are valid citations. Fabricating or inferring sources produces untraceable claims.

3. **`login` may require PTY or browser interaction** — In headless/SSH environments, use `parallel-cli login --device` and follow the device-code flow. Direct `login` without `--device` blocks waiting for browser input.

4. **Prefer foreground for short tasks** — Launching every search as a background process creates resource leaks and makes error handling harder. Only use `--no-wait` for genuinely long-running research/enrichment/FindAll jobs.

5. **Save large JSON outputs to `/tmp/*.json`** — Stuffing 500+ line JSON responses into context wastes tokens. Save to a temp file and read back only the fields you need.

6. **Don't silently choose Parallel over Hermes native tools** — `web_search` and `web_extract` are free, always available, and don't require auth. Parallel is a paid vendor service — use it only when the user explicitly asks or needs Parallel-specific workflows.

7. **Account required beyond the free tier** — Most enrichment, deep research with `ultra` processor, and large FindAll runs consume paid credits. Check `parallel-cli auth` to confirm the account state before launching expensive jobs.

8. **Async job IDs expire** — `trun_xxx` and `tgrp_xxx` IDs returned by `--no-wait` jobs have a finite lifetime (typically hours to days). Don't store them in long-lived memory without also storing a timestamp and fallback plan.

9. **`--previous-interaction-id` chains have context limits** — Chaining more than 3-4 follow-up research tasks on the same interaction can degrade quality as the accumulated context window fills. Start fresh interactions for distinct research threads.

10. **Processor tier matters for cost and quality** — `lite`/`base` are fast and cheap but shallow; `ultra` is thorough but expensive and slow. Match the processor to the task: `lite` for fact-checking, `core` for comparisons, `ultra` for multi-source synthesis.

11. **Enrichment column definitions must be explicit** — Vague `--intent` strings like "find info about companies" produce unpredictable results. Define concrete columns with descriptions: `--source-columns '[{"name": "company", "description": "Company legal name"}]' --intent "Find headquarters city and employee count from official sources"`.

12. **Exit code 3 (auth error) means re-authenticate, not retry** — A `403` or exit code `3` won't resolve by waiting. Run `parallel-cli auth` to diagnose, and if the token is expired, run `parallel-cli login --device`.
