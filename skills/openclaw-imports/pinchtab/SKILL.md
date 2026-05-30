---
name: pinchtab
description: >
  Control a headless or headed Chrome browser via Pinchtab's HTTP API. Use for web automation,
  scraping, form filling, navigation, and multi-tab workflows. Pinchtab exposes the accessibility
  tree as flat JSON with stable refs — optimized for AI agents (low token cost, fast).
  Use when the task involves: browsing websites, filling forms, clicking buttons, extracting
  page text, taking screenshots, or any browser-based automation. Requires a running Pinchtab
  instance (Go binary).
homepage: https://pinchtab.com
version: 1.0.0
author: Pinchtab
license: MIT
metadata:
  openclaw:
    emoji: "🦀"
    requires:
      bins: ["pinchtab"]
      env:
        - name: BRIDGE_TOKEN
          secret: true
          optional: true
          description: "Bearer auth token for Pinchtab API"
        - name: BRIDGE_PORT
          optional: true
          description: "HTTP port (default: 9867)"
        - name: BRIDGE_HEADLESS
          optional: true
          description: "Run Chrome headless (true/false)"
        - name: BRIDGE_PROFILE
          optional: true
          description: "Chrome profile directory (default: ~/.pinchtab/chrome-profile)"
        - name: BRIDGE_STATE_DIR
          optional: true
          description: "State/session storage directory (default: ~/.pinchtab)"
        - name: BRIDGE_NO_RESTORE
          optional: true
          description: "Skip restoring tabs from previous session (true/false)"
        - name: BRIDGE_STEALTH
          optional: true
          description: "Stealth level: light (default, basic) or full (canvas/WebGL/font spoofing)"
        - name: BRIDGE_BLOCK_IMAGES
          optional: true
          description: "Block image loading for faster, lower-bandwidth browsing (true/false)"
        - name: BRIDGE_BLOCK_MEDIA
          optional: true
          description: "Block all media: images + fonts + CSS + video (true/false)"
        - name: BRIDGE_NO_ANIMATIONS
          optional: true
          description: "Disable CSS animations/transitions globally (true/false)"
        - name: BRIDGE_TIMEZONE
          optional: true
          description: "Force browser timezone (IANA tz, e.g. Europe/Rome)"
        - name: BRIDGE_CHROME_VERSION
          optional: true
          description: "Chrome version string used by fingerprint rotation profiles"
        - name: CHROME_BINARY
          optional: true
          description: "Path to Chrome/Chromium binary (auto-detected if not set)"
        - name: CHROME_FLAGS
          optional: true
          description: "Extra Chrome flags, space-separated"
        - name: BRIDGE_CONFIG
          optional: true
          description: "Path to config JSON file (default: ~/.pinchtab/config.json)"
        - name: BRIDGE_TIMEOUT
          optional: true
          description: "Action timeout in seconds (default: 15)"
        - name: BRIDGE_NAV_TIMEOUT
          optional: true
          description: "Navigation timeout in seconds (default: 30)"
        - name: CDP_URL
          optional: true
          description: "Connect to existing Chrome DevTools instead of launching"
        - name: BRIDGE_NO_DASHBOARD
          optional: true
          description: "Disable dashboard/orchestrator endpoints on instance processes"
        - name: PINCHTAB_AUTO_LAUNCH
          optional: true
          description: "Dashboard mode: auto-launch default profile instance on startup"
        - name: PINCHTAB_DEFAULT_PROFILE
          optional: true
          description: "Dashboard mode: default profile name for auto-launch"
        - name: PINCHTAB_DEFAULT_PORT
          optional: true
          description: "Dashboard mode: default port for auto-launched profile"
        - name: PINCHTAB_HEADED
          optional: true
          description: "Dashboard mode: when set, auto-launched profile runs headed"
        - name: PINCHTAB_DASHBOARD_URL
          optional: true
          description: "Base dashboard URL used by `pinchtab connect` helper"
  hermes:
    tags: [browser, web-automation, scraping, pinchtab, chrome, headless]
    related_skills: [agent-browser]
    trigger_conditions:
      - "use pinchtab"
      - "browse a website"
      - "scrape a webpage"
      - "fill out a form"
      - "click a button on"
      - "take a screenshot of"
      - "extract page text"
      - "automate browser"
      - "navigate to https"
      - "fill in the form at"
      - "headless chrome"
      - "web automation"
      - "pinchtab API"
---

# Pinchtab

Fast, lightweight browser control for AI agents via HTTP + accessibility tree.

## When to Use

Use this skill when:
- Automating browser interactions: form filling, button clicking, navigation
- Scraping web pages that require JavaScript rendering
- Taking screenshots of web pages programmatically
- Extracting page text/content via accessibility tree
- Running multi-tab browser workflows from an agent
- Needing stealth browsing with fingerprint rotation
- Building web automation pipelines that need persistent sessions/cookies

## Not For

- **Simple static page fetching** (no JS needed) → use `web_extract` or `curl`
- **Hermes built-in browser tools** (`browser_navigate`, `browser_click`) → use those first if available
- **Complex browser automation that needs the Chrome DevTools Protocol directly** → use `agent-browser`
- **Visual regression testing** → use Playwright or Puppeteer directly

## Setup

Start Pinchtab in one of these modes:

```bash
# Headless (default) — no UI, pure automation (lowest token cost when using /text and filtered snapshots)
pinchtab &

# Headed — visible Chrome for human + agent workflows
BRIDGE_HEADLESS=false pinchtab &

# Dashboard/orchestrator — profile manager + launcher, no browser in dashboard process
pinchtab dashboard &
```

Default port: `9867`. Override with `BRIDGE_PORT=9868`.
Auth: set `BRIDGE_TOKEN=<secret>` and pass `Authorization: Bearer <secret>`.

Base URL for all examples: `http://localhost:9867`

Token savings come from the API shape (`/text`, `/snapshot?filter=interactive&format=compact`), not from headless vs headed alone.

### Headed mode definition

Headed mode means a real visible Chrome window managed by Pinchtab.

- Human can open profile(s), log in, pass 2FA/captcha, and validate page state
- Agent then calls Pinchtab HTTP APIs against that same running profile instance
- Session state persists in the profile directory, so follow-up runs reuse cookies/storage

In dashboard workflows, the dashboard process itself does not launch Chrome; it launches profile instances that run Chrome (headed or headless).

To resolve a running profile endpoint from dashboard state:

```bash
pinchtab connect <profile-name>
```

Recommended human + agent flow:

```bash
# human
pinchtab dashboard
# setup profile + launch profile instance

# agent
PINCHTAB_BASE_URL="$(pinchtab connect <profile-name>)"
curl "$PINCHTAB_BASE_URL/health"
```

## Core Workflow

The typical agent loop:

1. **Navigate** to a URL
2. **Snapshot** the accessibility tree (get refs)
3. **Act** on refs (click, type, press)
4. **Snapshot** again to see results

Refs (e.g. `e0`, `e5`, `e12`) are cached per tab after each snapshot — no need to re-snapshot before every action unless the page changed significantly.

## API Reference

### Navigate

```bash
curl -X POST http://localhost:9867/navigate \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com"}'

# With options: custom timeout, block images, open in new tab
curl -X POST http://localhost:9867/navigate \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com", "timeout": 60, "blockImages": true, "newTab": true}'
```

### Snapshot (accessibility tree)

```bash
# Full tree
curl http://localhost:9867/snapshot

# Interactive elements only (buttons, links, inputs) — much smaller
curl "http://localhost:9867/snapshot?filter=interactive"

# Limit depth
curl "http://localhost:9867/snapshot?depth=5"

# Smart diff — only changes since last snapshot (massive token savings)
curl "http://localhost:9867/snapshot?diff=true"

# Text format — indented tree, ~40-60% fewer tokens than JSON
curl "http://localhost:9867/snapshot?format=text"

# Compact format — one-line-per-node, 56-64% fewer tokens than JSON (recommended)
curl "http://localhost:9867/snapshot?format=compact"

# YAML format
curl "http://localhost:9867/snapshot?format=yaml"

# Scope to CSS selector (e.g. main content only)
curl "http://localhost:9867/snapshot?selector=main"

# Truncate to ~N tokens
curl "http://localhost:9867/snapshot?maxTokens=2000"

# Combine for maximum efficiency
curl "http://localhost:9867/snapshot?format=compact&selector=main&maxTokens=2000&filter=interactive"

# Disable animations before capture
curl "http://localhost:9867/snapshot?noAnimations=true"

# Write to file
curl "http://localhost:9867/snapshot?output=file&path=/tmp/snapshot.json"
```

Returns flat JSON array of nodes with `ref`, `role`, `name`, `depth`, `value`, `nodeId`.

**Token optimization**: Use `?format=compact` for best token efficiency. Add `?filter=interactive` for action-oriented tasks (~75% fewer nodes). Use `?selector=main` to scope to relevant content. Use `?maxTokens=2000` to cap output. Use `?diff=true` on multi-step workflows to see only changes. Combine all params freely.

### Act on elements

```bash
# Click by ref
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "click", "ref": "e5"}'

# Type into focused element (click first, then type)
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "click", "ref": "e12"}'
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "type", "ref": "e12", "text": "hello world"}'

# Press a key
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "press", "key": "Enter"}'

# Focus an element
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "focus", "ref": "e3"}'

# Fill (set value directly, no keystrokes)
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "fill", "selector": "#email", "text": "user@example.com"}'

# Hover (trigger dropdowns/tooltips)
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "hover", "ref": "e8"}'

# Select dropdown option (by value or visible text)
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "select", "ref": "e10", "value": "option2"}'

# Scroll to element
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "scroll", "ref": "e20"}'

# Scroll by pixels (infinite scroll pages)
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "scroll", "scrollY": 800}'

# Click and wait for navigation (link clicks)
curl -X POST http://localhost:9867/action \
  -H 'Content-Type: application/json' \
  -d '{"kind": "click", "ref": "e5", "waitNav": true}'
```

### Extract text

```bash
# Readability mode (default) — strips nav/footer/ads, keeps article/main content
curl http://localhost:9867/text

# Raw innerText (old behavior)
curl "http://localhost:9867/text?mode=raw"
```

Returns `{url, title, text}`. Cheapest option (~1K tokens for most pages).

### Screenshot

```bash
# Raw JPEG bytes
curl "http://localhost:9867/screenshot?raw=true" -o screenshot.jpg

# With quality setting (default 80)
curl "http://localhost:9867/screenshot?raw=true&quality=50" -o screenshot.jpg
```

### Evaluate JavaScript

```bash
curl -X POST http://localhost:9867/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"expression": "document.title"}'
```

### Tab management

```bash
# List tabs
curl http://localhost:9867/tabs

# Open new tab
curl -X POST http://localhost:9867/tab \
  -H 'Content-Type: application/json' \
  -d '{"action": "new", "url": "https://example.com"}'

# Close tab
curl -X POST http://localhost:9867/tab \
  -H 'Content-Type: application/json' \
  -d '{"action": "close", "tabId": "TARGET_ID"}'
```

Multi-tab: pass `?tabId=TARGET_ID` to snapshot/screenshot/text, or `"tabId"` in POST body.

### Tab locking (multi-agent)

```bash
# Lock a tab (default 30s timeout, max 5min)
curl -X POST http://localhost:9867/tab/lock \
  -H 'Content-Type: application/json' \
  -d '{"tabId": "TARGET_ID", "owner": "agent-1", "timeoutSec": 60}'

# Unlock
curl -X POST http://localhost:9867/tab/unlock \
  -H 'Content-Type: application/json' \
  -d '{"tabId": "TARGET_ID", "owner": "agent-1"}'
```

Locked tabs show `owner` and `lockedUntil` in `/tabs`. Returns 409 on conflict.

### Batch actions

```bash
# Execute multiple actions in sequence
curl -X POST http://localhost:9867/actions \
  -H 'Content-Type: application/json' \
  -d '[{"kind":"click","ref":"e3"},{"kind":"type","ref":"e3","text":"hello"},{"kind":"press","key":"Enter"}]'
```

### Cookies

```bash
# Get cookies for current page
curl http://localhost:9867/cookies

# Set cookies
curl -X POST http://localhost:9867/cookies \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","cookies":[{"name":"session","value":"abc123"}]}'
```

### Stealth

```bash
# Check stealth status and score
curl http://localhost:9867/stealth/status

# Rotate browser fingerprint
curl -X POST http://localhost:9867/fingerprint/rotate \
  -H 'Content-Type: application/json' \
  -d '{"os":"windows"}'
# os: "windows", "mac", or omit for random
```

### Health check

```bash
curl http://localhost:9867/health
```

## Token Cost Guide

| Method | Typical tokens | When to use |
|---|---|---|
| `/text` | ~800 | Reading page content |
| `/snapshot?filter=interactive` | ~3,600 | Finding buttons/links to click |
| `/snapshot?diff=true` | varies | Multi-step workflows (only changes) |
| `/snapshot?format=compact` | ~56-64% less | One-line-per-node, best token efficiency |
| `/snapshot?format=text` | ~40-60% less | Indented tree, cheaper than JSON |
| `/snapshot` | ~10,500 | Full page understanding |
| `/screenshot` | ~2K (vision) | Visual verification |

**Strategy**: Start with `/snapshot?filter=interactive`. Use `?diff=true` on subsequent snapshots in multi-step tasks. Use `/text` when you only need the readable content. Use `?format=text` to cut token costs further. Use full `/snapshot` only for complete page understanding.

## Environment Variables

### Core runtime

| Var | Default | Description |
|---|---|---|
| `BRIDGE_PORT` | `9867` | HTTP port |
| `BRIDGE_HEADLESS` | `true` | Run Chrome headless |
| `BRIDGE_TOKEN` | (none) | Bearer auth token |
| `BRIDGE_PROFILE` | `~/.pinchtab/chrome-profile` | Chrome profile dir |
| `BRIDGE_STATE_DIR` | `~/.pinchtab` | State/session storage |
| `BRIDGE_NO_RESTORE` | `false` | Skip tab restore on startup |
| `BRIDGE_STEALTH` | `light` | Stealth level: `light` or `full` |
| `BRIDGE_BLOCK_IMAGES` | `false` | Block image loading |
| `BRIDGE_BLOCK_MEDIA` | `false` | Block all media (images + fonts + CSS + video) |
| `BRIDGE_NO_ANIMATIONS` | `false` | Disable CSS animations/transitions |
| `BRIDGE_TIMEZONE` | (none) | Force browser timezone (IANA tz) |
| `BRIDGE_CHROME_VERSION` | `144.0.7559.133` | Chrome version string used by fingerprint rotation |
| `CHROME_BINARY` | (auto) | Path to Chrome/Chromium binary |
| `CHROME_FLAGS` | (none) | Extra Chrome flags (space-separated) |
| `BRIDGE_CONFIG` | `~/.pinchtab/config.json` | Path to config JSON file |
| `BRIDGE_TIMEOUT` | `15` | Action timeout (seconds) |
| `BRIDGE_NAV_TIMEOUT` | `30` | Navigation timeout (seconds) |
| `CDP_URL` | (none) | Connect to existing Chrome DevTools |
| `BRIDGE_NO_DASHBOARD` | `false` | Disable dashboard/orchestrator endpoints on instance processes |

### Dashboard mode (`pinchtab dashboard`)

| Var | Default | Description |
|---|---|---|
| `PINCHTAB_AUTO_LAUNCH` | `false` | Auto-launch a default profile at dashboard startup |
| `PINCHTAB_DEFAULT_PROFILE` | `default` | Profile name for auto-launch |
| `PINCHTAB_DEFAULT_PORT` | `9867` | Port for auto-launched profile |
| `PINCHTAB_HEADED` | (unset) | If set, auto-launched profile is headed; unset means headless |
| `PINCHTAB_DASHBOARD_URL` | `http://localhost:$BRIDGE_PORT` | CLI helper base URL for `pinchtab connect` |

## Tips

- **Always pass `tabId` explicitly** when working with multiple tabs — active tab tracking can be unreliable
- Refs are stable between snapshot and actions — no need to re-snapshot before clicking
- After navigation or major page changes, take a new snapshot to get fresh refs
- Use `filter=interactive` by default, fall back to full snapshot when needed
- Pinchtab persists sessions — tabs survive restarts (disable with `BRIDGE_NO_RESTORE=true`)
- Chrome profile is persistent — cookies/logins carry over between runs
- Chrome uses its native User-Agent by default — `BRIDGE_CHROME_VERSION` only affects fingerprint rotation
- Use `BRIDGE_BLOCK_IMAGES=true` or `"blockImages": true` on navigate for read-heavy tasks — reduces bandwidth and memory

## Pitfalls

1. **Pinchtab not running** — All calls fail silently if the Pinchtab process isn't running. Always verify with `curl http://localhost:9867/health` before any automation workflow. Start with `pinchtab &` or `BRIDGE_HEADLESS=false pinchtab &`.

2. **Stale refs after navigation** — After `POST /navigate`, all previous refs (e5, e12, etc.) are invalid. Always take a fresh snapshot after navigation before acting on elements. Refs are only valid within the same page lifecycle.

3. **Active tab ambiguity in multi-tab workflows** — Pinchtab's active tab tracking can be unreliable. Always pass `tabId` explicitly in every request when working with multiple tabs, especially in snapshot and action calls.

4. **Type action requires prior focus** — `{"kind": "type", "ref": "e12"}` only works AFTER clicking/focusing the target element. The `type` action sends keystrokes to the currently focused element, not to the ref directly. Sequence: click → type.

5. **Large snapshots overwhelming context** — Full snapshots can exceed 10K tokens. Default to `?filter=interactive` for action-oriented tasks. Add `?format=compact` for 56-64% token reduction. Use `?maxTokens=2000` as a safety cap. Only use unfiltered snapshots for full-page understanding.

6. **Snapshot diff on first call** — `?diff=true` returns nothing useful on the first snapshot of a page (no baseline to diff against). Always take one normal snapshot first, then use `?diff=true` on subsequent calls.

7. **Text extraction readability mode vs raw** — `/text` (default readability mode) strips navigation, footer, and ads — good for article content. `/text?mode=raw` returns everything including nav/ads. Choose explicitly based on your task; don't rely on the default if you need complete page text.

8. **Chrome profile persistence between runs** — Cookies, logins, and localStorage persist in `~/.pinchtab/chrome-profile` across Pinchtab restarts. This is powerful for maintaining sessions but dangerous: stale auth tokens, corrupted storage, or conflicting session state can cause 401/403 errors. Use `BRIDGE_NO_RESTORE=true` for clean-state automation.

9. **Headless detection by sites** — Even with `BRIDGE_STEALTH=full`, some sites detect headless Chrome via WebDriver flags, `navigator.webdriver`, or bot detection services. For sites with aggressive anti-bot protection, use headed mode (`BRIDGE_HEADLESS=false`) and manually solve CAPTCHAs.

10. **Port conflicts** — Default port 9867 conflicts if another Pinchtab instance or service is already running. Use `BRIDGE_PORT=9868` (or higher) for additional instances. Check with `lsof -i :9867` before starting.

11. **Lock timeouts in multi-agent workflows** — Tab locks default to 30s. If your workflow takes longer, the lock expires and another agent can take the tab, causing race conditions. Use `timeoutSec` explicitly for long-running workflows (up to 300s).

12. **Screenshot quality vs size tradeoff** — Default quality 80 produces 100-500KB JPEGs. Set `quality=30` for thumbnail/preview use (~30KB) or `quality=95` for archival (~1MB). Raw bytes are returned directly; pipe to file carefully.
