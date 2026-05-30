---
name: agent-browser
description: Browser automation CLI for AI agents. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, testing web apps, or automating any browser task.
version: 1.0.0
allowed-tools: Bash(agent-browser:*)
metadata:
  hermes:
    tags: [browser-automation, web-scraping, testing, screenshots, forms, navigation, playwright]
    trigger_conditions:
      - "open a website"
      - "fill out a form"
      - "click a button"
      - "take a screenshot"
      - "scrape data from a page"
      - "test this web app"
      - "login to a site"
      - "automate browser actions"
      - "browser automation"
      - "extract data from website"
      - "web scraping"
      - "fill a form online"
      - "programmatic web interaction"
---

# Browser Automation with agent-browser

## When to Use

- Navigating websites and extracting data programmatically
- Filling forms, clicking buttons, and submitting data via browser
- Taking screenshots or PDFs of web pages
- Testing web apps with automated interaction flows
- Logging into sites and maintaining authenticated sessions
- Scraping structured data from pages (products, articles, listings)
- Running parallel browser sessions for multi-site workflows
- Connecting to existing Chrome instances for debugging
- Mobile web testing via iOS Simulator

## Not For

- **Headless browser control via Pinchtab API** → use `pinchtab` instead
- **Configuring MCP servers for tools** → use `native-mcp` instead
- **Static site deployment verification** → use `static-site-deploy-verify` instead
- **Web app exploratory QA / bug finding** → use `dogfood` instead
- **API-only data extraction** → use `web_search_plus` or `web_extract_plus` instead
- **Large-scale web crawling** → use dedicated scraping frameworks (Scrapy, Playwright clusters)

## Core Workflow

Every browser automation follows this pattern:

1. **Navigate**: `agent-browser open <url>`
2. **Snapshot**: `agent-browser snapshot -i` (get element refs like `@e1`, `@e2`)
3. **Interact**: Use refs to click, fill, select
4. **Re-snapshot**: After navigation or DOM changes, get fresh refs

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# Output: @e1 [input type="email"], @e2 [input type="password"], @e3 [button] "Submit"

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i  # Check result
```

## Essential Commands

```bash
# Navigation
agent-browser open <url>              # Navigate (aliases: goto, navigate)
agent-browser close                   # Close browser

# Snapshot
agent-browser snapshot -i             # Interactive elements with refs (recommended)
agent-browser snapshot -i -C          # Include cursor-interactive elements (divs with onclick, cursor:pointer)
agent-browser snapshot -s "#selector" # Scope to CSS selector

# Interaction (use @refs from snapshot)
agent-browser click @e1               # Click element
agent-browser fill @e2 "text"         # Clear and type text
agent-browser type @e2 "text"         # Type without clearing
agent-browser select @e1 "option"     # Select dropdown option
agent-browser check @e1               # Check checkbox
agent-browser press Enter             # Press key
agent-browser scroll down 500         # Scroll page

# Get information
agent-browser get text @e1            # Get element text
agent-browser get url                 # Get current URL
agent-browser get title               # Get page title

# Wait
agent-browser wait @e1                # Wait for element
agent-browser wait --load networkidle # Wait for network idle
agent-browser wait --url "**/page"    # Wait for URL pattern
agent-browser wait 2000               # Wait milliseconds

# Capture
agent-browser screenshot              # Screenshot to temp dir
agent-browser screenshot --full       # Full page screenshot
agent-browser pdf output.pdf          # Save as PDF
```

## Common Patterns

### Form Submission

```bash
agent-browser open https://example.com/signup
agent-browser snapshot -i
agent-browser fill @e1 "Jane Doe"
agent-browser fill @e2 "jane@example.com"
agent-browser select @e3 "California"
agent-browser check @e4
agent-browser click @e5
agent-browser wait --load networkidle
```

### Authentication with State Persistence

```bash
# Login once and save state
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "$USERNAME"
agent-browser fill @e2 "$PASSWORD"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save auth.json

# Reuse in future sessions
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

### Session Persistence

```bash
# Auto-save/restore cookies and localStorage across browser restarts
agent-browser --session-name myapp open https://app.example.com/login
# ... login flow ...
agent-browser close  # State auto-saved to ~/.agent-browser/sessions/

# Next time, state is auto-loaded
agent-browser --session-name myapp open https://app.example.com/dashboard

# Encrypt state at rest
export AGENT_BROWSER_ENCRYPTION_KEY=$(openssl rand -hex 32)
agent-browser --session-name secure open https://app.example.com

# Manage saved states
agent-browser state list
agent-browser state show myapp-default.json
agent-browser state clear myapp
agent-browser state clean --older-than 7
```

### Data Extraction

```bash
agent-browser open https://example.com/products
agent-browser snapshot -i
agent-browser get text @e5           # Get specific element text
agent-browser get text body > page.txt  # Get all page text

# JSON output for parsing
agent-browser snapshot -i --json
agent-browser get text @e1 --json
```

### Parallel Sessions

```bash
agent-browser --session site1 open https://site-a.com
agent-browser --session site2 open https://site-b.com

agent-browser --session site1 snapshot -i
agent-browser --session site2 snapshot -i

agent-browser session list
```

### Connect to Existing Chrome

```bash
# Auto-discover running Chrome with remote debugging enabled
agent-browser --auto-connect open https://example.com
agent-browser --auto-connect snapshot

# Or with explicit CDP port
agent-browser --cdp 9222 snapshot
```

### Visual Browser (Debugging)

```bash
agent-browser --headed open https://example.com
agent-browser highlight @e1          # Highlight element
agent-browser record start demo.webm # Record session
```

### Local Files (PDFs, HTML)

```bash
# Open local files with file:// URLs
agent-browser --allow-file-access open file:///path/to/document.pdf
agent-browser --allow-file-access open file:///path/to/page.html
agent-browser screenshot output.png
```

### iOS Simulator (Mobile Safari)

```bash
# List available iOS simulators
agent-browser device list

# Launch Safari on a specific device
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com

# Same workflow as desktop - snapshot, interact, re-snapshot
agent-browser -p ios snapshot -i
agent-browser -p ios tap @e1          # Tap (alias for click)
agent-browser -p ios fill @e2 "text"
agent-browser -p ios swipe up         # Mobile-specific gesture

# Take screenshot
agent-browser -p ios screenshot mobile.png

# Close session (shuts down simulator)
agent-browser -p ios close
```

**Requirements:** macOS with Xcode, Appium (`npm install -g appium && appium driver install xcuitest`)

**Real devices:** Works with physical iOS devices if pre-configured. Use `--device "<UDID>"` where UDID is from `xcrun xctrace list devices`.

## Ref Lifecycle (Important)

Refs (`@e1`, `@e2`, etc.) are invalidated when the page changes. Always re-snapshot after:

- Clicking links or buttons that navigate
- Form submissions
- Dynamic content loading (dropdowns, modals)

```bash
agent-browser click @e5              # Navigates to new page
agent-browser snapshot -i            # MUST re-snapshot
agent-browser click @e1              # Use new refs
```

## Semantic Locators (Alternative to Refs)

When refs are unavailable or unreliable, use semantic locators:

```bash
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find role button click --name "Submit"
agent-browser find placeholder "Search" type "query"
agent-browser find testid "submit-btn" click
```

## JavaScript Evaluation (eval)

Use `eval` to run JavaScript in the browser context. **Shell quoting can corrupt complex expressions** -- use `--stdin` or `-b` to avoid issues.

```bash
# Simple expressions work with regular quoting
agent-browser eval 'document.title'
agent-browser eval 'document.querySelectorAll("img").length'

# Complex JS: use --stdin with heredoc (RECOMMENDED)
agent-browser eval --stdin <<'EVALEOF'
JSON.stringify(
  Array.from(document.querySelectorAll("img"))
    .filter(i => !i.alt)
    .map(i => ({ src: i.src.split("/").pop(), width: i.width }))
)
EVALEOF

# Alternative: base64 encoding (avoids all shell escaping issues)
agent-browser eval -b "$(echo -n 'Array.from(document.querySelectorAll("a")).map(a => a.href)' | base64)"
```

**Why this matters:** When the shell processes your command, inner double quotes, `!` characters (history expansion), backticks, and `$()` can all corrupt the JavaScript before it reaches agent-browser. The `--stdin` and `-b` flags bypass shell interpretation entirely.

**Rules of thumb:**
- Single-line, no nested quotes -> regular `eval 'expression'` with single quotes is fine
- Nested quotes, arrow functions, template literals, or multiline -> use `eval --stdin <<'EVALEOF'`
- Programmatic/generated scripts -> use `eval -b` with base64

## Browser Engine Selection

Hermes Agent supports multiple browser backends via the `browser.engine` config in `~/.hermes/config.yaml`:

| Engine | Behavior |
|--------|----------|
| `auto` (default) | Uses Chrome via agent-browser |
| `lightpanda` | Lightpanda headless browser + automatic Chrome fallback for unsupported commands |
| `chrome` | Force Chrome |

### Lightpanda Backend

Lightpanda is a Zig-built headless browser without a rendering pipeline — instant startup, ~10x lower memory than Chrome. Ideal for agent workloads that are mostly navigation + DOM scraping.

**Setup:**
```bash
# Install Lightpanda binary (x86_64 Linux example)
mkdir -p ~/.local/bin
curl -fsSL -o ~/.local/bin/lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux
chmod +x ~/.local/bin/lightpanda
# Verify: ~/.local/bin/lightpanda --help
```

**Configure Hermes:**
```yaml
# ~/.hermes/config.yaml
browser:
  engine: lightpanda
```

**What works on Lightpanda:** `open`, `snapshot`, `click`, `type`, `scroll`, `back`, `press`, `eval` — the core agent workflow.

**Auto-fallback to Chrome:** Screenshots, PDF generation, file uploads, multi-tab contexts, clipboard, geolocation emulation, and any command that errors on Lightpanda are transparently retried with Chrome.

**Verify it's working:** Start Hermes and run `/browser` — should show "Lightpanda" with "Automatic Chrome fallback" note.

**Note:** Lightpanda is a nightly build. Re-download when updating Hermes. If `~/.local/bin` is on your PATH, no further config is needed.

## Pitfalls

1. **Stale refs after navigation** — `@e1`, `@e2` refs are invalidated when the page changes. Always call `agent-browser snapshot -i` after clicks that navigate, form submissions, or dynamic content loads.

2. **Shell quoting corrupting JavaScript** — Inner double quotes, `!` characters (history expansion), backticks, and `$()` all corrupt JavaScript before it reaches agent-browser. Use `eval --stdin <<'EVALEOF'` for multiline or `eval -b` with base64 for generated scripts.

3. **Missing `--session-name` for state persistence** — Without `--session-name`, cookies and localStorage are lost when the browser closes. Always use `--session-name myapp` for workflows requiring authentication.

4. **Forgetting `agent-browser wait --load networkidle`** — After clicking submit or navigating, DOM may be ready but network requests (XHR, fetch) are still in flight. Wait for `networkidle` before taking screenshots or extracting data.

5. **Lightpanda screenshot failures** — Lightpanda (the default `browser.engine: lightpanda` in Hermes) cannot render screenshots. Screenshots transparently fall back to Chrome, but this adds ~2s startup per screenshot. For screenshot-heavy workflows, switch to `browser.engine: chrome`.

6. **iOS simulator requirements** — iOS testing requires macOS with Xcode and Appium with XCUITest driver. It will not work on Linux or Windows. Verify with `xcrun xctrace list devices` before attempting.

7. **File access denied for local files** — Opening `file://` URLs requires `--allow-file-access` flag. Without it, local PDFs and HTML files return blank pages or security errors.

8. **Parallel session name collision** — Running multiple `--session` names without cleanup eventually exhausts memory. Call `agent-browser session list` periodically and prune unused sessions.

9. **Semantic locator ambiguity** — `agent-browser find text "Submit" click` matches the first occurrence. If multiple buttons share the same text, it clicks the wrong one. Prefer `@ref` snapshots for unambiguous targeting.

10. **Auto-connect failing on non-standard CDP ports** — `agent-browser --auto-connect` only discovers Chrome on standard remote debugging ports. For Chrome on custom CDP ports, use `--cdp <port>` explicitly.

11. **Encryption key not set for sensitive sessions** — Session state files are stored plaintext in `~/.agent-browser/sessions/`. For sensitive sites, always set `AGENT_BROWSER_ENCRYPTION_KEY` before launching the browser.

12. **Full-page screenshot memory exhaustion** — `agent-browser screenshot --full` on very long pages (>10000px) can exhaust memory. For long pages, use `agent-browser pdf` or take partial screenshots with scroll.

## Deep-Dive Documentation

| Reference | When to Use |
|-----------|-------------|
| [references/commands.md](references/commands.md) | Full command reference with all options |
| [references/snapshot-refs.md](references/snapshot-refs.md) | Ref lifecycle, invalidation rules, troubleshooting |
| [references/session-management.md](references/session-management.md) | Parallel sessions, state persistence, concurrent scraping |
| [references/authentication.md](references/authentication.md) | Login flows, OAuth, 2FA handling, state reuse |
| [references/video-recording.md](references/video-recording.md) | Recording workflows for debugging and documentation |
| [references/proxy-support.md](references/proxy-support.md) | Proxy configuration, geo-testing, rotating proxies |
| [references/lightpanda-backend.md](references/lightpanda-backend.md) | Lightpanda setup, capabilities, fallback behavior |

## Ready-to-Use Templates

| Template | Description |
|----------|-------------|
| [templates/form-automation.sh](templates/form-automation.sh) | Form filling with validation |
| [templates/authenticated-session.sh](templates/authenticated-session.sh) | Login once, reuse state |
| [templates/capture-workflow.sh](templates/capture-workflow.sh) | Content extraction with screenshots |

```bash
./templates/form-automation.sh https://example.com/form
./templates/authenticated-session.sh https://app.example.com/login
./templates/capture-workflow.sh https://example.com ./output
```
