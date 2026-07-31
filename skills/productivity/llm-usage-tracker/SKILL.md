---
name: llm-usage-tracker
description: Assess feasibility and build tools (system-tray apps, menu-bar apps, dashboards) that show LLM provider usage limits, token counts, and credit balances — e.g. forking a CodexBar-style app to swap providers. Covers provider-API probing, the Cloudflare 1010 pitfall, local-ledger extraction (Hermes/Claude/Codex), read-only HTTP bridges, and OpenRouter/Command Code specifics.
version: 1.0.0
metadata:
  hermes:
    tags: [llm-usage, tray-app, dashboard, providers, feasibility]
    trigger_conditions:
      - "build a usage tracker for an LLM provider"
      - "show token usage / credit balance in a tray app"
      - "fork CodexBar / CodexBar-style app"
      - "does provider X expose a usage API"
      - "how to get OpenRouter credit balance"
      - "read Hermes usage from state.db"
      - "menu-bar app for LLM limits"
      - "probe a provider for usage endpoints"
      - "usage dashboard for Claude/Codex/Command Code"
      - "Cloudflare 1010 error probing a provider"
---

# LLM Usage Tracker — Assess & Build

Class of task: you want a live view of an LLM provider's usage — session/weekly
limit %, token totals, or remaining credits — in a system tray / menu-bar / web
panel. Usually done by forking an existing provider-specific tool (e.g.
CodexBar-Win for Claude/Codex) and swapping the data source.

## When to Use

- User wants a tray/menu-bar/dashboard app showing LLM token usage, limits, or credits.
- Feasibility question: "does provider X expose a usage API?" — before any coding.
- Forking CodexBar or similar and swapping the data source to another provider.
- Reading local usage ledgers (Hermes state.db, Claude Code jsonl, OpenAI Codex rollouts).
- Building the read-only HTTP bridge between a Linux host and a Windows tray consumer.

## Not For

- Building the Hermes AgentBar itself → use `hermes-agentbar` instead.
- Monitoring your own Hermes token spend for cron-model choices → use `llm-usage-tracker`'s ledger only if you need a UI; otherwise `cron-model-optimization` covers job cost control.
- General system tray app development unrelated to LLM usage → use `gui-app-headless-testing` / `pystray-windows-tray-click` for tray mechanics.
- Provider billing/refund issues → that is account support, not an app-building skill.

## Core workflow: recon FIRST, code SECOND

Standing rule for this class: **do not write any code until you have confirmed
exactly how you will get the data.** Feasibility rests entirely on what the
provider actually exposes. A web dashboard showing a meter does NOT mean a JSON
API for that meter exists.

1. List the data the UI needs (session% used, weekly% used, reset countdowns,
   token totals, $ cost, credits remaining).
2. For each data point, find a REAL source, priority order:
   a. Provider REST API (cleanest, multi-device).
   b. Local logs/ledger on the host that runs the agent (no secrets, always on).
   c. Provider CLI `/usage` over PTY (CodexBar does this for Claude).
   d. Browser session cookie -> internal Studio endpoints (brittle; last resort).
3. PROBE the API before promising anything (see references/cloudflare-1010-probe.md).
   - 200 + JSON => endpoint exists, use it.
   - 404 "not a registered API route" / "API endpoint not found" => genuinely absent.
   - 200 but HTML SPA shell => web page, not JSON; needs a session cookie, not the key.
4. Only after sources are confirmed, scaffold. Prefer replacing the upstream
   fetcher class with a provider-specific one and keeping the UI/packaging.

## Pitfall: Cloudflare Error 1010 (read this before probing ANY provider)

Sites behind Cloudflare (commandcode.ai and many others) reject requests with an
empty/non-browser User-Agent using **403 Error 1010 "Access denied based on your
browser's signature."** This is NOT "endpoint not found" and NOT an auth failure.
A naive `urllib.request` with no UA produces this on EVERY route and will make you
wrongly conclude "the API is dead." Always probe WITH a browser User-Agent +
CORS-style headers first; only trust a 404-after-browser-UA as "absent."
See references/cloudflare-1010-probe.md for the exact header set and a reusable script.

## Pitfall: inline SQL containing `&` trips the terminal background-detector

The terminal tool scans the whole command (including heredoc bodies) for an
unquoted shell `&` and **refuses to run it**, treating it as ambiguous
foreground/background. SQL filter strings like
`billing_base_url LIKE '%commandcode.ai%' OR billing_provider LIKE '%commandcode%'`
contain `&` and will falsely trigger this — even inside a
`python3 - <<'PY'` heredoc. Fix: write the SQL + driver code to a `.py` file and run
`python3 file.py`. This also makes the manual cross-check reusable.
(Confirmed the hard way this session — cost a round-trip.)

## Local-ledger fallback (no usage API? read the host)

When the provider has no usage API, the agent host often already logs usage:
- Hermes Agent: `~/.hermes/state.db`, table `session_model_usage`. Filter
  `billing_base_url LIKE '%<provider>%' OR billing_provider LIKE '%<provider>%'`.
  See references/hermes-usage-ledger.md.
- Claude Code: `~/.claude/projects/**/*.jsonl` (assistant msgs carry `message.usage`).
- OpenAI Codex: `~/.codex/sessions/**/rollout-*.jsonl` (last `token_count` payload
  has rate_limits + total_token_usage).

Local ledger gives token counts and cost, but usually NOT the provider's rolling
limit % (computed server-side in credit-value). Be honest in the UI about which
numbers are measured vs reconstructed.

## Read-only HTTP bridge pattern (Windows tray <-> Linux host)

When the consumer is a Windows tray app and the agent runs on a Linux host, the
proven shape is a **read-only loopback HTTP bridge** on the Linux host that the
tray app polls over plain HTTP. Built and self-verified this session
(`HermesAgentBar/host/commandbar_bridge.py`). Key rules:

- Open the DB read-only: `sqlite3.connect("file:%s?mode=ro" % path, uri=True)`.
  SQLite itself then refuses writes — defense in depth beyond "don't call INSERT".
- Set `PRAGMA busy_timeout=50` so a briefly-locked DB waits instead of erroring.
- **Parameterize every window size.** Seconds (`now - N`) are bound params, never
  f-string-interpolated into SQL. The provider filter is a constant literal, never
  derived from request input.
- Bind loopback `127.0.0.1` by default; expose opt-in Bearer auth via env var
  (`HERMES_AGENTBAR_TOKEN`) checked as `Authorization: Bearer <token>` → 401.
- Wrap the query so `sqlite3.OperationalError` (DB locked/busy) returns **HTTP 503**
  JSON, not a 500/crash.
- stdlib `http.server` (ThreadingHTTPServer) is enough — no Flask.
- Don't override `BaseHTTPRequestHandler.log_message` with a `fmt` param name; the
  base uses `format`, so Pyright flags an incompatible override. Use
  `def log_message(self, format, *args)` (or just don't override it).

See references/hermes-usage-bridge.md for the full known-good implementation and a
verification recipe (cross-check the live endpoint against an independent manual
aggregate at the same instant).

## Cross-platform: Windows app reading a Linux host

If the target app runs on Windows but the agent/host runs on Linux, the fetcher
reads the Linux host remotely (SSH/HTTP file-serve of `state.db`, or an SSH PTY to
the provider CLI). Strip Windows-only upstream code (DPAPI cookie decrypt, winpty,
.bat/.ps1) and retarget the tray UI to `pystray` (Linux) or `rumps` (macOS).

## Known provider specifics (in references/)

- references/command-code.md — Command Code (commandcode.ai): Provider API exposes
  ONLY `/models`; NO `/usage` or `/credits`. Live meters exist only in Studio
  (browser cookie) or CC CLI `/usage`. Local ledger via Hermes state.db works today.
- references/openrouter-credits.md — OpenRouter `GET /api/v1/credits` (Bearer key)
  -> `{data:{total_credits, total_usage}}`. Clean, documented, confirmed working.
- references/cloudflare-1010-probe.md — reusable probe script + browser-UA header set.
- references/hermes-usage-ledger.md — ready SQL for the local Hermes usage ledger
  (provider isolation, time-window aggregation, read-only open).
- references/hermes-usage-bridge.md — known-good read-only loopback HTTP bridge
  (state.db -> JSON at GET /api/usage) for a Windows tray consumer, plus the
  verification recipe and pitfalls.

## Pitfalls

1. **Cloudflare 1010 misread as "the API is dead"** — Sites behind Cloudflare (commandcode.ai and many others) return **403 Error 1010** for empty/non-browser User-Agents on EVERY route. A naive `urllib.request` with no UA makes you wrongly conclude the endpoint is gone. Always probe with a browser User-Agent + CORS-style headers first (see references/cloudflare-1010-probe.md); only a 404-after-browser-UA means genuinely absent.

2. **Inline SQL with `&` trips the terminal background-detector** — The terminal tool refuses commands containing an unquoted shell `&` — even inside a `python3 - <<'PY'` heredoc. SQL filters like `billing_base_url LIKE '%commandcode.ai%'` trigger this false positive. Fix: write the SQL + driver code to a `.py` file and run `python3 file.py`; this also makes the cross-check reusable.

3. **200-but-HTML-SPA-shell misread as a JSON API** — A 200 that returns an HTML shell means a web page, not JSON. It needs a browser session cookie, not the API key. Don't build against it.

4. **DB locked/busy crashes the bridge** — Open the DB read-only (`sqlite3.connect("file:%s?mode=ro" % path, uri=True)`) and set `PRAGMA busy_timeout=50`. Wrap queries so `sqlite3.OperationalError` returns HTTP 503 JSON, not a 500/crash.

5. **Interpolating request input into SQL** — Parameterize every window size (`now - N` as bound params) and keep the provider filter a constant literal, never derived from request input. This is the bridge's main security boundary.

6. **Overriding `log_message` with the wrong param name** — The base handler uses `format`; a `fmt` param makes Pyright flag an incompatible override. Use `def log_message(self, format, *args)` or don't override it.

7. **Claiming measured numbers the ledger can't produce** — Local ledgers give token counts and cost but usually NOT the provider's rolling limit % (computed server-side in credit-value). Be honest in the UI about which numbers are measured vs reconstructed — a plausible-looking meter with fake precision is worse than an honest label.

8. **Skipping the probe before scaffolding** — A web dashboard showing a meter does NOT mean a JSON API exists for it. Probe the endpoint (200+JSON vs 404 vs SPA-shell) before promising anything, and only then fork the upstream fetcher class and keep the UI/packaging.
