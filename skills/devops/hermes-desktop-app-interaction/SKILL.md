---
name: hermes-desktop-app-interaction
description: Use the desktop app preview pane to open browser URLs.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, desktop, preview, browser, pane, tui]
    category: devops
    trigger_conditions:
      - "open X in a browser"
      - "preview this page"
      - "open cnn.com"
      - "show me localhost:3000"
      - "what does this page say"
      - "what's on screen in the app"
      - "read the preview pane"
      - "open the embedded terminal"
      - "switch panes in hermes desktop"
      - "read the terminal pane"
      - "where is the skill in that post"
      - "open the in-app browser"
      - "focus the files pane"
---

# Hermes Desktop App Interaction

Drive the Hermes desktop app's visible surfaces: the in-app browser (preview
pane), the embedded terminal, and the pane switcher. These are the `desktop_ui`
plugin tools: `open_preview`, `read_preview`, `read_terminal`, `focus_pane`,
`close_terminal`, `read_window_below`.

## When to Use

- The user asks to "open X in a browser", "preview X", "open cnn.com", "show me localhost:3000".
- The user asks what's on screen in the in-app browser: "what does this page say?", "the X post I just loaded", "where is the skill in that post".
- The user wants to see the embedded terminal or switch panes.

## Not For

- Launching an external browser on a headless/gateway shell with no desktop app attached → use `agent-browser` or `homelab-browser-backends` instead.
- Full browser automation (form filling, multi-tab scraping, downloads) → use `agent-browser` instead.
- Diagnosing X11/Wayland/display configuration → there is a dedicated computer-use path; this skill assumes the desktop app pane.
- Reading web content from a normal terminal session without the desktop app → use `web_extract` instead.
- Managing which panes exist (adding/removing panes) → that is desktop-app configuration, not this skill's scope.

## Key lesson (user correction, 2026-08)

In the Hermes desktop app, **"open X in a browser" means the in-app preview
pane (`open_preview`)** — NOT launching an external browser (xdg-open,
chromium, firefox). Agent shells typically have no DISPLAY/WAYLAND, and a
headless Chromium on :9222 is invisible to the user. Do NOT spend turns
diagnosing display state, X11 sockets, or browser availability. Load the
desktop_ui tools and call `open_preview` directly.

## Steps

1. If `open_preview`/`read_preview` are not already in the schema, find them:
   `tool_search(query="open preview pane browser")` then `tool_describe`.
2. Open the target: `open_preview(url=...)` — accepts `https://` URLs, bare
   domains (e.g. `www.cnn.com`), localhost dev-server URLs, or file paths
   (HTML renders live; other files show contents). Optional `label`.
3. Verify/read the page: `read_preview()` returns
   `{kind, url, title, text, start, end, total_chars}` — page through long
   pages with `start`/`count` (character offsets).

## Reading what's already in the in-app browser

- When the user references a page they "just loaded" (X post, article, docs),
  call `read_preview()` with no args FIRST — it returns the rendered visible
  text of the active tab. Treat that text as the primary source before
  web-searching.
- For links found in that text, resolve short links before judging them:
  `curl -sIL -o /dev/null -w '%{url_effective}\n' <short-url>`.
  If the resolved URL is an `/optin/` or email-capture page, the "free
  download" is a lead magnet — report that and let the user decide; don't
  fetch it for them.
- If the user asks where a skill from a post lives, check the local skills
  tree first (search_files in `~/.hermes`), then resolve the post's link;
  "not installed locally + no public repo + gated link" is a complete answer.

## Other pane tools

- `focus_pane` — reveal/focus a pane: chat, files, terminal, review, sessions.
- `read_terminal` — read the embedded terminal pane's visible screen + scrollback.
- `close_terminal`, `read_window_below` — housekeeping/inspection.

## Pitfalls

1. **"Open in a browser" means the preview pane, not an external browser** — The user is in the desktop app; they want the pane beside the chat. Launching xdg-open/chromium or diagnosing DISPLAY/WAYLAND wastes turns and shows nothing. Call `open_preview` directly.

2. **The preview pane opens for the current window only** — If the user expects the pane to persist across windows, it won't. Re-open it in the active window rather than assuming a stale pane is visible.

3. **A previous external browser launch does NOT satisfy "open in a browser"** — Having launched a browser earlier in the session (or having one running on :9222) does not count. The user means the pane beside the chat.

4. **Don't diagnose DISPLAY/WAYLAND/X11 when the user is clearly in the desktop app** — The pane is the visible surface by definition; display debugging is irrelevant noise and burns turns.

5. **`read_preview()` with no args is the fastest source for "what's on screen"** — The active tab's rendered visible text is primary evidence. Web-searching for a page the user just loaded in the pane duplicates work and can drift from what they actually see.

6. **Resolve short links before judging them** — `curl -sIL` to get `url_effective`. An `/optin/` or email-capture page means the "free download" is a lead magnet — report that and let the user decide; don't fetch it for them.

7. **Check the local skills tree before chasing a post's link** — For "where is the skill in that post", `search_files` in `~/.hermes` first. "Not installed locally + no public repo + gated link" is a complete answer; don't keep digging.

8. **`focus_pane` targets existing panes only** — It reveals/focuses chat, files, terminal, review, sessions. It cannot create a pane that doesn't exist; pair with the desktop-app pane management if a pane is missing.

9. **`open_preview` accepts localhost dev-server URLs and file paths** — HTML files render live; other files show contents. A bare domain like `www.cnn.com` works without a scheme.

10. **The pane may be on a different profile's session** — Desktop app panes are per-profile. If the page isn't there, check which profile/session owns the visible pane before assuming the tool failed.
