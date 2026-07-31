---
name: hermes-agentbar
description: Build, debug, and extend Hermes AgentBar — a Windows tray app showing Command Code token usage, OpenRouter credits, and budget forecasts. Use when working on the HermesAgentBar codebase, debugging pystray tray icon behavior, integrating with Command Code internal APIs, or adding new fetchers and UI panels.
version: 1.0.0
metadata:
  hermes:
    tags: [hermes-agentbar, tray-app, pystray, command-code, openrouter]
    trigger_conditions:
      - "work on the HermesAgentBar codebase"
      - "AgentBar tray app"
      - "debug pystray tray icon behavior"
      - "Command Code token usage display"
      - "OpenRouter credits in a tray"
      - "add a fetcher or UI panel to AgentBar"
      - "Command Code internal billing API"
      - "tray icon left-click does nothing"
      - "HermesAgentBar config keys"
      - "run AgentBar without a console window"
---

# Hermes AgentBar

Windows system-tray app that displays real-time Hermes/Command Code token usage and OpenRouter credit balance. Built with Python 3.10+, pystray, customtkinter, Pillow, and requests.

## When to Use

- Working on the HermesAgentBar codebase (hermes_agentbar.py, fetchers.py, ui_panel.py, config.py, host bridge).
- Debugging pystray behavior on Windows (left-click activation, menu defaults, console windows).
- Integrating a new data source/fetcher or UI panel into AgentBar.
- Refreshing Command Code session cookies or the Linux-side bridge config.

## Not For

- Building a brand-new usage tracker from scratch for a different provider → use `llm-usage-tracker` instead.
- Generic pystray tray-icon mechanics on Windows → use `pystray-windows-tray-click` instead.
- Building system-tray apps on Linux/macOS → use `gui-app-headless-testing` (pystray/rumps) instead.
- Reading LLM usage ledgers or provider usage APIs in general → use `llm-usage-tracker` instead.

## Architecture

```
hermes_agentbar.py   — entry point, tray icon, refresh loop, pystray wiring
fetchers.py          — three fetchers: CC tokens (bridge), OpenRouter credits, CC budget (billing API)
ui_panel.py          — CTkToplevel popup with Command Code + OpenRouter tabs
config.py            — JSON config at %APPDATA%/HermesAgentBar/config.json
host/commandbar_bridge.py — Linux-side HTTP bridge serving state.db token data
```

### Data flow

1. `do_refresh()` (runs every N minutes + on manual Refresh) reloads config, calls all fetchers in parallel.
2. Command Code token data comes from the Linux bridge (`host/commandbar_bridge.py` → `GET /api/usage`).
3. OpenRouter credit data comes from `https://openrouter.ai/api/v1/credits`.
4. Command Code budget data comes from `https://api.commandcode.ai/internal/billing/credits` (requires session cookies).
5. Last-good data is stored; errors keep the previous payload. Popup is rebuilt on each refresh.

## Pitfalls

1. **pystray left-click does nothing on Windows** — Right-click menu works but left single-click is dead.

See also: **`pystray-windows-tray-click`** skill for full source analysis and the debug technique.

**Symptom:** Tray icon right-click menu works, but left single-click does nothing.
**Root cause:** On Windows, `WM_LBUTTONUP` → `Icon.__call__()` → `Menu.__call__()` → **only the menu item flagged `default=True` is invoked.** There is no separate `on_activate` path on Windows (that's macOS/AppKit only).

**Fix:**
```python
# WRONG — default is a MenuItem kwarg, NOT a Menu kwarg:
menu = Menu(Item("Show", self._on_show), default=Item("Show", self._on_show))
# TypeError: Menu.__init__() got an unexpected keyword argument 'default'

# CORRECT — default=True ON the Item itself:
menu = Menu(Item("Show", self._on_show, default=True), ...)
```
Verified against pystray source: `_win32.py` line 200 → `self()` → `_base.py` line 108 → `self._menu(self)` → `Menu.__call__` line 630 → `next(menuitem for menuitem in self.items if menuitem.default)`.

Do NOT use `icon.on_activate = ...` for Windows left-click — it won't fire.

2. **py_compile passes but the app crashes at runtime on Windows** — `py_compile` catches syntax errors but NOT invalid kwargs. `Menu(default=...)` passed `py_compile` on Linux but crashed at runtime on Windows. Always verify pystray code on the actual platform or read the library source when fighting tray behavior.

3. **Using the API key against `/internal/*` endpoints** — The Command Code internal endpoints (usage, billing/credits) are NOT authenticated by `COMMANDCODE_API_KEY`. They require browser session cookies from a logged-in commandcode.ai session (`__Secure-commandcode_prod_.session_token`, `__Secure-commandcode_prod_.session_data`, plus Stripe cookies). Extract via F12 → Network → Copy as cURL → paste the full `-b` value into `cc_session_cookie`. Tokens expire after ~7 days — expect to refresh them; the session is NOT IP-pinned so the same cookies work from the Linux host.

4. **Left-click handlers that rely on `on_activate`** — On Windows there is no `on_activate` path; only the `default=True` menu item fires on left-click. Porting macOS-style `icon.on_activate = ...` code to Windows silently does nothing.

5. **Running AgentBar with a console window you can't get rid of** — `python hermes_agentbar.py` from a `.bat` keeps a console open (fine for debugging). For auto-start use `pythonw hermes_agentbar.py` (no console, prompt returns immediately) and drop a shortcut to `pythonw`/the built `.exe` into `shell:startup`.

6. **Treating OpenRouter credits as tokens** — `GET /api/v1/credits` returns `data.total_credits` and `data.total_usage` which are already USD (1 credit = $1). No conversion needed. Rendering `$` is a UI decision (`_fmt_usd(n)` → `f"${n:,.2f}"`).

7. **Session cookie expiry silently kills the budget tab** — The `cc_session_cookie` expires after ~7 days; after that the billing fetcher fails while the token-usage (bridge) and OpenRouter tabs keep working. The last-good payload hides the failure, so check the fetcher error path, not just the visible values.

## UI patterns

### Collapsible section (token usage)
The token usage section (cards + model list + daily chart) is collapsed by default. Toggle state lives in `self._cc_token_open` (bool). The toggle button calls `_toggle_token_section(parent)`:
- `pack(fill="x", after=self._cc_token_btn)` to show, `pack_forget()` to hide
- Button label toggles between `▸  Token Usage` and `▾  Token Usage`
- All token children are parented into `self._cc_token_frame` so a single `pack_forget()` hides everything

### Color palette (ui_panel.py)
```
ACCENT     = "#2DD4BF"   # teal — CC tab, header dot, cmd tab button
GREEN      = "#34D399"   # budget status bars, countdown labels
PURPLE     = "#8B5CF6"   # daily trend heading + bar peaks
PURPLE_DK  = "#5B4A8A"   # daily trend dim bars
LIME       = "#BCE241"   # OpenRouter USD badge, tab highlight, green dot
LIME_BG    = "#2A3514"   # lime pill background
ACCENT_DK  = "#1F8C80"   # (legacy — no longer used in daily chart, replaced by purple)
BG         = "#0E1525"   # deep slate shell
SURFACE    = "#16203A"   # card surface
TRACK      = "#23304D"   # progress bar track
```

Colors are assigned by section: **Budget Status → green**, **Daily tokens → purple**, **OpenRouter → lime**. The old teal-only palette (amber forecast bars, teal daily bars) was replaced in the 2026-07-17 UI refresh.

### Running without locking the console
Use `pythonw hermes_agentbar.py` — `pythonw.exe` starts Python without a console window, returns the prompt immediately. The `.bat` file keeps a console open (useful for debugging). For auto-start, drop a shortcut to `pythonw.exe hermes_agentbar.py` or the built `.exe` into `shell:startup`.

### OpenRouter credits are dollars

`GET /api/v1/credits` returns `data.total_credits` and `data.total_usage` — these are already USD values (1 credit = $1). No conversion needed. Rendering `$` is a UI decision: `_fmt_usd(n)` → `f"${n:,.2f}"`.

## Config keys

| Key | Type | Description |
|---|---|---|
| `bridge_url` | str | Linux bridge URL (default: `http://127.0.0.1:8766`) |
| `bridge_token` | str | Bearer token for bridge auth |
| `openrouter_key` | str | OpenRouter API key |
| `weekly_token_budget` | int | CC token budget for the % bar |
| `cc_session_cookie` | str | Full Cookie header from browser (with `__Secure-` cookies) |
| `cc_5h_budget` | float | 5-hour USD cap (default 45) |
| `cc_weekly_budget` | float | Weekly USD cap (default 90) |
| `refresh_minutes` | int | Auto-refresh interval (default 5) |

## Files

- `references/commandcode-internal-api.md` — billing endpoint schema and auth details
- `references/pystray-windows-activation.md` — investigation notes on pystray left-click behavior
