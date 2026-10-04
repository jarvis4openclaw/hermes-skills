---
name: hermes-web-and-mcp-import-failures
description: "Use when Hermes web_search or MCP calls fail."
version: "1.1.0"
author: jarvis
license: MIT
metadata:
  hermes:
    tags: [hermes, web-search, mcp, python, diagnostics]
    related_skills: [hermes-config-management, hermes-provider-config, hermes-memory-provider-management]
    trigger_conditions:
      - "web_search provider not found"
      - "no registered web search provider has that name"
      - "brave provider has no key"
      - "BRAVE_API_KEY not working"
      - "mcp call failed module not found"
      - "firecrawl mcp error"
      - "site-packages shadowing"
      - "python 3.11 vs 3.14 package conflict"
      - "web search backend not running"
      - "mcp tool works in shell but not in chat"
      - "hermes update broke a tool"
      - "rpds jsonschema import error"
---

# Hermes web search + MCP import failures

## When to Use

- `web_search` returns `no registered web search provider has that name`.
- A source is set in `web.search_backend` but never actually runs.
- An MCP tool (`mcp__firecrawl__*`, etc.) fails with `MCP call failed: ModuleNotFoundError: ...`.
- A tool works from a fresh shell but not from a long-running gateway/chat process.
- `BRAVE_API_KEY` is set but the bundled Brave provider still reports no key.
- `web-search-plus` providers never show up in core `web_search`.
- An MCP tool HTTP-200s but fails client-side with a `ModuleNotFoundError`.
- You need to prove which `site-packages` tree a live gateway process imports from.

## Not For

- General Hermes config editing or provider setup → use `hermes-config-management` instead
- Choosing or swapping LLM providers/models → use `hermes-provider-config` instead
- Memory provider (mnemosyne) setup → use `hermes-memory-provider-management` instead
- Adding or authoring an MCP server from scratch → use `native-mcp` instead
- Installing or porting third-party MCP servers → use `mcporter` instead
- Scraping one specific page rather than fixing tool plumbing → use `firecrawl` instead
- Keyless web search without configuring a provider → use `exa-web-search-free` or `duckduckgo-search` instead

Two independent-looking symptoms that account for most "search/MCP is broken" reports on this host. Diagnose from evidence, never from the error text alone.

## Symptom A — `no registered web search provider has that name`

`tools/web_tools.py:_get_backend()` returns a configured `web.search_backend` **as-is, with no availability probe and no fallback** — deliberate, so a broken selection shows the vendor's real error. A typo therefore looks like a dead provider.

Check the real registered name before believing the config:

```bash
grep -rn "NAME = " ~/.hermes/hermes-agent/plugins/web/*/provider.py
grep -i "registered web provider" ~/.hermes/logs/agent.log | tail
```

The bundled Brave provider is named **`brave-free`** (`plugins/web/brave_free/provider.py`), never `brave`. Provider names are hyphenated and are NOT the vendor name.

Also check the provider's own env var — it is often not the obvious one:

```bash
grep -n "KEY_ENV\|provider_env(" ~/.hermes/hermes-agent/plugins/web/<vendor>/provider.py
```

`brave-free` wants `BRAVE_SEARCH_API_KEY`; `BRAVE_API_KEY` is a different name and is simply ignored.

Do not blame the `web-search-plus` plugin: it registers providers only in its own registry for its own `web_search_plus` / `web_extract_plus` tools. It never calls the core `register_web_search_provider` hook, so core `web_search` cannot see its providers. Its log line `capability_check plugin=web-search-plus capability=tools.override decision=deny` confirms it is not allowed to override core tools.

Fix (config edits must go through the CLI — the file editors refuse to touch Hermes config):

```bash
cp -p ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.webfix-$(date +%Y%m%d-%H%M%S)
cp -p ~/.hermes/.env ~/.hermes/.env.bak.webfix-$(date +%Y%m%d-%H%M%S)
hermes config set web.search_backend brave-free
```

Then add the provider's expected key name to `~/.hermes/.env` (copy the value without printing it), keeping mode 600.

Entry points read `os.environ` then `~/.hermes/.env` via `hermes_cli.config.get_env_value`, so a `.env` edit is enough; no shell export needed.

## Symptom B — MCP tool fails `ModuleNotFoundError: No module named '<pkg>.<submodule>'`

Almost always **cross-Python-version `site-packages` shadowing**, not a broken MCP server and not a missing dependency.

The backend runs the bundled Python 3.14 toolchain with deps from
`~/.hermes/installs/<id>/environments/<hash>/venv/lib/python3.14/site-packages`.
A legacy 3.11 tree still exists at `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages`. If a process has the 3.11 tree first, the package directory resolves from 3.11, its `__init__.py` runs `from .<pkg> import *`, and the `*.cpython-311*.so` cannot load under 3.14 → the submodule looks missing.

Confirm which tree a live process actually imports from:

```bash
P=$(pgrep -f 'hermes_cli/main.py gateway run' | head -1)
grep -o "[^ ]*site-packages" /proc/$P/maps | sort -u
```

Two site-packages entries — one `python3.11`, one `python3.14` — proves it.

Reproduce the exact error by ordering:

```bash
PY=~/.hermes/tools/python-3.14.7*/bin/python3
$PY -c "import sys;sys.path.insert(0,'<3.11 site-packages>');import rpds"   # -> ModuleNotFoundError: No module named 'rpds.rpds'
$PY -c "import sys;sys.path.insert(0,'<3.14 site-packages>');import rpds"   # -> OK
```

Fresh processes boot clean: `pm/environments.py:activate_dependencies` strips every `site-packages` entry from `sys.path` and adds only the selected one. So this only affects processes that booted around an interrupted dependency publication — which is also why it never reproduces in a new shell.

Why Firecrawl is the usual canary: `mcp`'s `ClientSession.call_tool` imports `jsonschema` (→ `rpds`) to validate server `structuredContent` against the tool's `outputSchema`. Tools declaring an `outputSchema` therefore need `rpds` on every call, and the failure happens *after* a successful HTTP 200 response. `tools/mcp_tool_handlers.py:_dispatch` wraps it into `MCP call failed: ...`.

Remedy — finish the publication, then restart so processes boot clean:

```bash
hermes update          # or: hermes pm install   (clears 'venv: out of sync with uv.lock')
systemctl --user restart hermes-gateway.service
```

Then reopen the desktop app / start a fresh chat. Restarting the gateway kills the running session, so hand these commands to the user rather than running them.

## Verification (always do this)

Prove the fix with real calls, in a clean process:

```bash
# search backend resolves and returns live results
<3.14 venv>/bin/python -c "<resolve provider, call search, print success + result count>"
```

Then exercise the actual tool (`web_search`, `mcp__firecrawl__firecrawl_search`) and report the observed result.

## Pitfalls

1. The file patch/write tools **refuse to edit `~/.hermes/config.yaml`** by design. Use `hermes config set`.
2. `web.backend` is the shared/legacy backend; `search_backend` / `extract_backend` name only their own capability and never reroute the other.
3. `web.search_api_key` / `extraction_api_key` in config are not what core providers read — providers use `provider_env()` on their own `KEY_ENV`. Leave these keys alone rather than "fixing" a typo that has no effect.
4. Never conclude an MCP server is broken from a client-side Python traceback. Check the HTTP status in `~/.hermes/logs/agent.log` (`httpx2: HTTP Request: POST ... 200 OK`) first.
5. Don't restart the user's gateway unilaterally; it terminates the active session.
6. **Provider names are hyphenated and are NOT the vendor name** — the bundled Brave provider is `brave-free`, never `brave`.
7. **`BRAVE_API_KEY` is simply ignored** — `brave-free` reads `BRAVE_SEARCH_API_KEY` via its own `KEY_ENV`; check with `grep -n "KEY_ENV" plugins/web/<vendor>/provider.py`.
8. **`web-search-plus` never registers into core** — its providers live only in its own registry for `web_search_plus`/`web_extract_plus`; core `web_search` cannot see them.
9. **3.11/3.14 `site-packages` shadowing only bites already-booted processes** — fresh processes strip every `site-packages` entry and re-add one, so restart after `hermes update` to boot clean.
10. **The "module missing" error happens AFTER an HTTP 200** — `mcp` validates `structuredContent` and imports `jsonschema`→`rpds`; the HTTP call succeeded, the failure is client-side.
11. **A `.env` edit suffices — no shell export needed** — entry points read `os.environ` then `~/.hermes/.env` via `hermes_cli.config.get_env_value`; keep the file mode 600.
