---
title: Homelab Headless Browser Backends
name: homelab-browser-backends
author: Jarvis
version: 1.1.0
description: Evaluate, swap, and smoke-test headless browser automation backends for Hermes on Wahid's homelab (LightPanda / Obscura / CDP chromium). Covers the memory-cost decision and the safe-removal verification pattern.
tags: [homelab, browser, automation, hermes, lightpanda, obscura, pinchtab]
metadata:
  hermes:
    trigger_conditions:
      - "which browser backend should I use"
      - "swap headless browser engine"
      - "pinchtab removal or enable"
      - "lightpanda fetch not working"
      - "obscura stealth scraping"
      - "browser memory too high homelab"
      - "hermes browser.engine config"
      - "headless chromium debug profile"
      - "safe removal verification pattern"
      - "web automation engine choice"
      - "browser backend smoke test"
      - "unbroker chromium :9222"
      - "CDP browser for agent tasks"
---

# Homelab Headless Browser Backends

Class skill for choosing and operating the headless browser engine that Hermes (and agent
tasks) use for web automation on this homelab.

## Current state (as of 2026-07-11)
- Hermes browser config sets `browser.engine: lightpanda`. Binary at
  `/home/wahid/.local/bin/lightpanda` (Zig, built-from-scratch engine, NOT Chromium).
- `pinchtab` (a `systemd --user` headless-chromium bridge) was **disabled and stopped** — it
  was the single largest real memory eater (~1.3 GiB / 26 chromium procs) with zero active
  consumers. Reversible: `systemctl --user enable --now pinchtab.service`.
- A separate chromium instance on `:9222` belongs to the Hermes `unbroker` skill's debug
  flow, NOT pinchtab. Don't conflate the two.

## When to Use

- Choosing or swapping the headless browser engine Hermes uses for web automation
- Diagnosing high memory use from browser backends (`pinchtab` was ~1.3 GiB / 26 procs)
- Deciding between LightPanda (default), Obscura (stealth), and CDP chromium (debug)
- Removing or re-enabling a browser-related `systemd --user` service safely
- Smoke-testing a candidate backend before committing to it

## Not For

- **Full browser automation workflows** (fill forms, click, scrape at scale) → use the `agent-browser` skill (or the `browserbase-browse-cli` / `homelab-browser-backends` siblings for specific drivers)
- **Web research / search / crawl** → use the `hound-mcp` MCP server (`mcp_hound_mcp_smart_search`), which is complementary, not a browser engine
- **Debugging the `unbroker` flow itself** → that skill owns its chromium debug profile
- **Server memory troubleshooting** in general → use the `server-health` skill

## Which backend, when

- **LightPanda** — default. Lightweight, CDP-compatible (Puppeteer/Playwright), has
  `fetch`/`serve`/`mcp`/`agent` modes. Good for general fetch/extract and agent tasks. Its
  own JS engine may stumble on very heavy/obfuscated JS pages.
- **Obscura** (Rust, embeds real V8) — choose when you need **stealth / anti-bot scraping**:
  built-in fingerprint randomization, `navigator.webdriver = undefined`, 3,520-domain tracker
  blocking. Apache-2.0. Ships a native Hermes plugin (`hermes-plugin-obscura`) that spawns
  `obscura serve` per session over CDP. NOT installed on this box by default.
- **CDP chromium** — only for `unbroker`/debug flows that explicitly launch a debug profile.

## Verify before swapping
1. Confirm what actually consumes memory: `free -h`, `/proc/pressure/memory`, top RSS
   processes (see `server-health` skill + `references/linux-memory-pressure.md`).
2. Check the Hermes config engine: `grep -n 'engine:' ~/.hermes/config.yaml`.
3. Confirm the candidate backend is present and works: smoke-test with `fetch` on a URL
   (see `references/backends.md`).
4. **Safe removal rule** (the pinchtab pattern): before `systemctl stop/disable` a browser
   service, prove zero active consumers — `ss -tnp` for its ports, no running process
   references it, no config depends on it. If clean, drop it; it's reversible.

## Pitfalls

1. **Stale `agent-browser` pointer** — The `agent-browser` skill (under `openclaw-imports`) still says "Headless browser control via Pinchtab API → use `pinchtab`". That is **stale for this homelab** — pinchtab is removed. Use LightPanda (Hermes engine) or Obscura instead. Do not follow that pointer on this box.
2. **Treating `used` ≈ total as high memory** — buff/cache is reclaimable; `free -h` + `/proc/pressure/memory` tell the real story. See `server-health`.
3. **Trusting vendor benchmark numbers** — LightPanda "~9x faster", Obscura "30 MB/page" are self-reported; verify on this box before capacity planning.
4. **Hound-mcp mistaken for a browser engine** — it's an MCP server for web research (search + fetch + crawl + screenshot) that uses Playwright internally. It complements the browser backends, it doesn't replace them.
5. **Removing a backend without proving zero consumers** — before `systemctl stop/disable` a browser service, check `ss -tnp` for its ports, no running process references it, no config depends on it. If clean, drop it; it's reversible (`systemctl --user enable --now pinchtab.service`).
6. **Conflating the `:9222` chromium with pinchtab** — the `unbroker` skill's debug profile is separate; don't kill or repurpose it when cleaning up browser backends.

## MCP-based web research (hound-mcp)

Since 2026-07-24, this homelab runs **hound-mcp** (v12.4.1 from dondai1234/master-fetch) as
an MCP server for keyless web research. It replaces the Brave/Tavily API-keyed search+extract
stack with a single local process. Tools: `mcp_hound_mcp_smart_fetch`,
`mcp_hound_mcp_smart_search`, `mcp_hound_mcp_smart_crawl`, `mcp_hound_mcp_screenshot`,
`mcp_hound_cache_clear`, `mcp_hound_version`. Full detail in `references/hound-mcp.md`.

## References
- `references/backends.md` — LightPanda vs Obscura comparison + install/smoke-test recipe.
- `references/pinchtab-removal.md` — worked safe-removal example (the memory investigation).
- `references/hound-mcp.md` — hound-mcp web research MCP server reference.
