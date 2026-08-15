---
name: browserbase-browse-cli
description: "Browserbase browse CLI: cloud browser automation with anti-bot bypass. Use when unbroker skill references Browserbase or when you need stealth browser automation."
version: 1.1.0
tags: [browser, automation, browserbase, anti-bot, cloud-browser]
related_skills: [unbroker, agent-browser]
metadata:
  hermes:
    tags: [browser, automation, browserbase, anti-bot, cloud-browser]
    trigger_conditions:
      - "browserbase browse"
      - "cloud browser automation"
      - "anti-bot bypass"
      - "cloudflare turnstile bypass"
      - "hcaptcha checkbox"
      - "residential ip browser"
      - "unbroker browserbase"
      - "stealth browser"
      - "opt-out form automation"
      - "browse cloud sessions"
      - "browse cli ref format"
      - "browse snapshot"
      - "browse fill click"
---

# Browserbase browse CLI

The `browse` CLI is Browserbase's command-line tool for driving cloud browser sessions. It provides anti-bot bypass (Cloudflare Turnstile, hCaptcha checkbox) via residential IP + real browser fingerprint, which the Hermes `browser_*` tools cannot do.

## When to Use

- **Unbroker skill** references Browserbase for Phase 1 scanning and Phase 2 opt-out forms
- **Anti-bot sites** that block Hermes `browser_*` tools (Cloudflare, DataDome)
- **Residential IP required** for sites that fingerprint datacenter IPs
- **Soft CAPTCHA clearing** (Turnstile, hCaptcha checkbox) — the CLI passes these as normal operation

## Not For

- **General headless browser automation on ordinary sites** → `agent-browser` (local, free, no API key)
- **Interacting with a running browser's live DOM/CDP** → `agent-browser` or the Hermes `browser_*` tools
- **Screenshot/visual-check workflows on normal pages** → `agent-browser`
- **Sites with hard interactive image challenges** (visual puzzles, DataDome sliders) — Browserbase Free cannot solve these either; escalate to the operator's residential browser per `unbroker`

## Installation

```bash
npm install -g @browserbase/browse
export PATH="$HOME/.npm-global/bin:$PATH"
```

Verify: `browse --version` (should output `browse/X.Y.Z`)

## Session Management

### Create a Cloud Session

```bash
export BROWSERBASE_API_KEY=$(grep '^BROWSERBASE_API_KEY=' ~/.hermes/.env | cut -d= -f2-)
browse cloud sessions create
```

Returns JSON with `id`, `status`, `connectUrl`, `seleniumRemoteUrl`. The session runs for ~5 minutes (configurable).

### List Active Sessions

```bash
browse cloud sessions list
```

### Stop a Session

```bash
browse stop
```

Always stop sessions when done to avoid billing overages.

## Core Commands

### Open a URL

```bash
browse open "https://example.com" --timeout 30
```

Returns JSON with `url`, `title`, `pages[]`. The `--timeout` flag waits for page load (milliseconds).

### Snapshot (Read Page State)

```bash
browse snapshot
```

Returns an accessibility tree with **refs in `[NN-N]` format** (e.g., `[12-14]`, `[11-530]`). This is different from Hermes `browser_snapshot` which uses `@eN` format.

**Example output:**
```json
{
  "tree": "[12-1] RootWebArea: Page Title\n  [12-3] scrollable, html\n    [12-14] textbox: First Name *\n    [12-16] textbox: Last Name *\n    [12-238] button: Submit"
}
```

### Click an Element

```bash
browse click "@12-238"
```

**Note:** Despite the snapshot showing `[12-238]`, the click command uses `@12-238` (with `@` prefix, no brackets). This is the same ref format as Hermes `browser_click`.

### Fill an Input

```bash
browse fill "@12-14" "Wahid"
```

Clears the field and types the value. Returns `{"filled": true, "pressedEnter": false}`.

### Type Text

```bash
browse type "@12-14" "Wahid"
```

Appends text without clearing. Use `fill` to clear first.

### Press a Key

```bash
browse press "Enter"
browse press "Tab"
```

### Get Page Content

```bash
browse get text
browse get url
browse get title
```

### Wait for Element

```bash
browse wait --selector "@12-238" --timeout 5000
```

### Screenshot

```bash
browse screenshot --output /tmp/page.png
```

## Ref Format Differences

| Tool | Snapshot Format | Click/Fill Format |
|---|---|---|
| Hermes `browser_snapshot` | `@e14`, `@e238` | `@e14`, `@e238` |
| Browserbase `browse snapshot` | `[12-14]`, `[12-238]` | `@12-14`, `@12-238` |

**Key insight:** The snapshot shows `[NN-N]` but commands use `@NN-N`. The `@` prefix is consistent; only the snapshot display differs.

## Common Patterns

### Fill and Submit a Form

```bash
# Open the form
browse open "https://example.com/optout" --timeout 30

# Snapshot to read refs
browse snapshot

# Fill fields (refs from snapshot)
browse fill "@12-14" "Wahid"
browse fill "@12-16" "Saleemi"
browse fill "@12-17" "email@example.com"

# Click submit
browse click "@12-238"

# Wait for confirmation
browse wait --selector "@12-300" --timeout 10000

# Snapshot to verify
browse snapshot
```

### Handle Soft CAPTCHA (hCaptcha Checkbox)

```bash
# Snapshot to find the checkbox
browse snapshot

# Click the hCaptcha checkbox (usually in an iframe)
browse click "@11-530"

# Wait for it to clear (Browserbase auto-solves soft CAPTCHAs)
sleep 3

# Snapshot to verify it cleared
browse snapshot
```

**Gotcha:** If the hCaptcha escalates to a visual image challenge ("Find everything that fits in hand luggage"), Browserbase Free cannot solve it. Record `blocked` and move on — only the paid CAPTCHA-solving tier handles interactive challenges.

### Navigate Between Pages

```bash
browse open "https://example.com/page1"
# ... do work ...
browse open "https://example.com/page2"
# ... do work ...
browse stop
```

## Anti-Bot Bypass

Browserbase passes **soft/managed CAPTCHAs** as normal operation:
- Cloudflare Turnstile (checkbox)
- hCaptcha checkbox ("I am human")
- reCAPTCHA v2 checkbox

It does **NOT** bypass:
- Hard interactive image challenges (visual puzzles)
- Behavioral scoring that flags the session
- DataDome slide-to-verify sliders
- Sites that require login with session-bound cookies

When Browserbase fails, record `blocked` and escalate to the operator's residential browser (see `unbroker` skill → "Operator-browser path").

## Billing

Browserbase charges per session minute. Always `browse stop` when done. Check usage:

```bash
browse cloud sessions list --json | python3 -c "import sys,json; [print(f\"{s['id']}: {s['status']}\") for s in json.load(sys.stdin)]"
```

## Pitfalls

1. **`browse: command not found`** — npm global bin not on PATH. Add `export PATH="$HOME/.npm-global/bin:$PATH"` (or the npm prefix dir) to your shell profile, then verify `browse --version`.
2. **`waitForMainLoadState(load) timed out`** — the page didn't load within the timeout. Increase `--timeout` (milliseconds) or check if the site is down.
3. **Snapshot shows empty tree** — the page may be blocked by anti-bot. Try: increase `--timeout` on `browse open`; check if the site requires login; record `blocked` and escalate.
4. **Ref not found on click** — refs change after navigation. Always `browse snapshot` after a page load to get fresh refs.
5. **Session billing overage** — sessions run ~5 minutes and are billed per minute. Always `browse stop` when done; list active sessions with `browse cloud sessions list`.
6. **API key not exported** — the CLI reads `BROWSERBASE_API_KEY` from the environment. If you use the `~/.hermes/.env` copy, `export BROWSERBASE_API_KEY=$(grep '^BROWSERBASE_API_KEY=' ~/.hermes/.env | cut -d= -f2-)` before creating a session.
7. **Free tier hits visual challenge** — if hCaptcha escalates to a visual image challenge ("find everything that fits in hand luggage"), Browserbase Free cannot solve it. Record `blocked` and move on; only the paid CAPTCHA-solving tier handles interactive challenges.

## Integration with Unbroker

The `unbroker` skill uses Browserbase for:
- **Phase 1 scanning:** Stealth browser passes blocked sites (Cloudflare, DataDome)
- **Phase 2 opt-out:** Drives web forms that Hermes `browser_*` tools cannot reach

When `unbroker` says "use the cloud/stealth browser backend", it means this CLI. The `BROWSERBASE_API_KEY` env var is already in `~/.hermes/.env` — no setup needed beyond `npm install -g @browserbase/browse`.
