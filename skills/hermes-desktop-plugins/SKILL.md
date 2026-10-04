---
name: hermes-desktop-plugins
description: Write desktop app plugins that add UI panes and commands.
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [desktop, plugins, ui, extension]
    trigger_conditions:
      - "write a desktop plugin"
      - "add a pane to the hermes desktop app"
      - "add a statusbar item"
      - "add a command-palette command"
      - "register a keybind or route"
      - "ship a theme in a plugin"
      - "plugin shows no panel"
      - "reload desktop plugins"
      - "desktop plugin sdk"
      - "add a python backend to a desktop plugin"
      - "plugin pane placement or dock"
      - "why is my plugin not loading"
      - "desktop plugin hot reload"
    category: productivity
    related_skills: []
---

# Hermes Desktop Plugins Skill

Write plugins for the Hermes desktop app: statusbar items, layout panes,
command-palette commands, keybinds, routes, and themes. A plugin is a single
plain-JavaScript ESM file the app loads at runtime — no build step, no repo
changes. A plugin can also talk to its own Python backend namespace
(`ctx.rest`/`ctx.socket` → `/api/plugins/<id>`); the general Python plugin
system (`~/.hermes/plugins/`) is otherwise documented separately.

Full human reference (every export, area payloads, backend, security):
`website/docs/developer-guide/desktop-plugin-sdk.md`.

## When to Use

- The user asks for a new desktop UI element (a pane, a statusbar widget, a
  dashboard, a command) without modifying the app itself.
- You want to surface data you compute (via gateway RPC) inside the app.
- You need a statusbar chip, a ⌘K command, a keybind, a route/page, or a theme.
- A per-user or per-profile customization that must not touch the app repo.
- The plugin needs its own Python backend namespace (`/api/plugins/<id>`).
- You are debugging why an installed plugin shows no panel (the "three gates").

## Not For

- Changing the app's built-in theme tokens rather than adding a plugin → use `hermes-themes` instead
- Reading or asserting on a running desktop window's DOM/CSS → use `inspecting-hermes-desktop-dom` instead
- Driving the app (menus, typing, clicking) as a user → use `hermes-desktop-app-interaction` instead
- Registering MCP servers or agent tools for the gateway → use `native-mcp` or `mcporter` instead
- Updating a web dashboard's widgets (not a desktop plugin) → use `automation-dashboard-update` instead
- Running a headless browser to test a web UI → use `gui-app-headless-testing` instead

## Prerequisites

- The Hermes desktop app (it loads plugins; the CLI/gateway alone does not).
- Write access to `$HERMES_HOME/desktop-plugins/` (usually
  `~/.hermes/desktop-plugins/`).

## How to Run

1. Create `$HERMES_HOME/desktop-plugins/<name>/plugin.js` from
   `templates/plugin.js` (relative to this skill directory) — that's
   `~/.hermes/...` by default, or `~/.hermes/profiles/<profile>/...` under a
   named profile. Keep `<name>` equal to the plugin `id`.
2. The desktop app watches that directory: the plugin loads within a few
   seconds of the file landing, and every later save hot-reloads it in
   place. No reload step. (Fallback if it doesn't appear: ⌘K →
   **Reload desktop plugins**.)
3. If loading fails the app shows a toast naming the error — fix the file
   and save again.

## Quick Reference

The ONLY import surface is `@hermes/plugin-sdk` (plus `react` /
`react/jsx-runtime`, which resolve to the app's own React — write UI with
`jsx()` calls, not JSX syntax; the file is not compiled).

- `host.state.*` — readonly reactive atoms: `activeSessionId`, `cwd`,
  `gateway`, `model`, `profile`, `viewport`. Read with `.get()` in handlers,
  `useValue(atom)` in components.
- `host.request(method, params)` — gateway JSON-RPC (sessions, config,
  skills, cron — everything the app uses).
- `host.onEvent(type, fn)` — live gateway events (`'*'` for all). Returns a
  disposer.
- `host.notify({ kind, message })`, `host.navigate(path)`, `host.logs(...)`,
  `host.status()`, `haptic('tap')`.
- `ctx.register({ id, area, order?, render?, data? })` — contribute UI.
  Key areas: `'statusBar.right'`/`'statusBar.left'` (chips),
  `'panes'` (layout zones — set `title` and
  `data: { placement, dock?, width?, height? }`; the pane auto-joins a
  matching zone), `PALETTE_AREA` (⌘K commands), `KEYBINDS_AREA` (rebindable
  actions).
- Pane placement: `placement: 'left'|'right'|'bottom'|'main'` is the
  semantic role — the pane stacks (tabs) with existing panes of that role.
  To land on a specific EDGE instead, add `dock: { pane, pos }` — the same
  gesture as dragging onto a pane's drop chip. `pane` is any pane id
  (`workspace` is the main thread; also `sessions`, `terminal`, `files`,
  `review`, `logs`), `pos` is `'top'|'bottom'|'left'|'right'|'center'`.
  E.g. "below the conversation" = `dock: { pane: 'workspace', pos: 'bottom' }`
  — declare a `height` (e.g. `'200px'`) so it doesn't take half the zone.
- Full PAGES: register `area: ROUTES_AREA` with `data: { path: '/my-page' }`
  and a `render` — the page mounts in the workspace (main) pane like any
  built-in view. Make it reachable with a sidebar nav row:
  `ctx.register({ id: 'nav', area: SIDEBAR_NAV_AREA, data: { path: '/my-page', label: 'My Page', codicon: 'project' } })`
  (renders below Artifacts, lights up at the route) — and/or a
  `PALETTE_AREA` command calling `host.navigate('/my-page')`.
- `ctx.storage.get/set/remove` — persistence namespaced to your plugin.
- `ctx.i18n.register({ en, ja, ... })` — ship your OWN locale bundles, scoped
  to your plugin (never edit core `en.ts`). Values are literal strings or
  interpolator functions; nested trees are addressed by dot-path. Read them
  reactively in components with `usePluginI18n(id)` returning `t('key', ...args)`
  (re-renders on a locale switch), or via `ctx.i18n.t` in handlers/stores.
  Resolution follows the app's active locale, then your `en`, then the raw key.
- Data: `useQuery`/`useMutation`/`useQueryClient`/`queryClient` (the app's ONE
  React Query client — cache, dedupe, `refetchInterval`, invalidate like core;
  never hand-roll a poll loop), plus `atom`/`computed` for plugin-local state.
- Backend: if the plugin ships a Python `plugin_api.py` (under
  `~/.hermes/plugins/<id>/dashboard/`, manifest `"api": "plugin_api.py"`), reach
  it with `ctx.rest('/path', { method?, body?, timeoutMs? })` and its live twin
  `ctx.socket('/events', onMessage)` — both scoped to `/api/plugins/<id>` by
  construction (traversal rejected). `ctx.socket` is a **no-op on OAuth
  remotes**, so always keep a polling fallback. The Python backend is imported
  only when the plugin is in `plugins.enabled` in `config.yaml` (separate from
  the in-app enable toggle). For gateway-wide data use `host.request` /
  `host.onEvent` instead.
- `Contribute` (mount-scoped): render `jsx(Contribute, { area, id, children })`
  inside a component so page-owned chrome (e.g. a titlebar control in
  `TITLEBAR_AREAS.center`) leaves when the page unmounts — `ctx.register` is for
  permanent contributions.
- `defaultEnabled: false` on the default export ships an opt-in plugin: it
  inventories in Settings → Plugins, off until the user flips it on.
- Users manage plugins in Settings → Plugins (enable/disable live, reveal
  folder). A disabled plugin stays disabled across restarts — don't fight
  it; the user turned you off.
- UI: the app's design language, importable directly — `Button`, `Input`,
  `Textarea`, `Select*`, `Switch`, `Checkbox`, `SegmentedControl`, `Tabs*`,
  `Dialog*`, `ConfirmDialog`, `DropdownMenu*`, `ContextMenu*`, `Popover*`,
  `Tip`/`Tooltip*`, `Badge`, `Kbd`/`KbdGroup`, `SearchField`, `ScrollArea`,
  `Separator`, `Skeleton`, `GlyphSpinner`, `EmptyState`, `ErrorState`,
  `CopyButton`, `StatusDot`, `LogView`, `Codicon`, `DecodeText`, plus `cn`
  and `icons.*`. Prefer these over hand-rolled elements so the plugin looks
  native; style with theme vars, never hardcoded colors.

## Procedure

1. Pick a short kebab-case `id`; the folder name must match.
2. Start from `templates/plugin.js`; keep the default export shape
   (`{ id, name, register(ctx) }`).
3. For a pane, register `area: 'panes'` with a `placement` hint and a
   `render` returning your component — the app places it into a sensible
   zone automatically; the user can drag it anywhere afterwards.
4. Fetch data with `host.request` and/or subscribe with `host.onEvent`;
   never poll faster than a few seconds.
5. Write the file with your file tools, then ask the user to run
   **Reload desktop plugins** from ⌘K.

## Native plugins (plugins/<id>) vs desktop plugins — three gates

A plugin shipped as an **agent package** (`~/.hermes/plugins/<id>/` with `plugin.yaml`,
`dashboard/plugin_api.py`, `desktop/plugin.js`) only works when all three of these are true. Missing any
one produces a plugin that is "enabled" in Capabilities yet shows **no panel**, or a panel that renders
*"Subscription data unavailable"*:

| Gate | Where | Symptom when unmet | Fix |
|---|---|---|---|
| **Agent half enabled** | `plugins.enabled` in `config.yaml` | rows/JS never load; trust gate blocks the API (`{"detail":"Plugin not found"}`) | `hermes plugins install … --enable`, or add to `plugins.enabled` |
| **Plugin API mounted** | the **dashboard/web server** process | panel loads, `/data` fails (unmounted route → 404, or a 500 the handler wrapped) | **restart the dashboard** — see below |
| **Desktop half delivered** | `$HERMES_HOME/desktop-plugins/<id>/plugin.js` on the **app's own machine** | plugin lists in Capabilities with no panel at all | *Install from Git* in the app with the **Desktop** target checked |

### The API mount happens ONCE, at dashboard startup

`_mount_plugin_api_routes()` (`hermes_cli/web_server_dashboard.py`) is called exactly once from
`web_server.py` module import. There is **no runtime re-mount**: toggling the plugin in Capabilities,
`plugins.manage`, **Rescan**, and `hermes plugins enable/update` all leave the router table untouched.
So a plugin installed while the dashboard is already up gets no API until the dashboard restarts.

Verify by grepping the startup log for the mount line:
`grep "Mounted plugin API routes" ~/logs/hermes-dashboard.log | tail` — an installed-and-enabled plugin
that is absent from that list is not mounted. The dashboard is usually a **system** unit
(`/etc/systemd/system/hermes-dashboard.service`), not a user unit: `sudo systemctl restart hermes-dashboard`.

The installer's advice ("restart the gateway") is **not sufficient** for the panel: the gateway does not
mount plugin APIs at all, and a plugin's `ctx.rest` reaches `/api/plugins/<id>` on the **dashboard**
process the app is connected to. Confirm the app's target before restarting anything:
`ss -tnp | grep <app-ip>` and map the local port to its PID.

### Remote backends cannot deliver a desktop half

Only packages installed on the **same machine as the app** contribute a `desktop/plugin.js`; a remote
host's `plugins/` is not a filesystem the app can read. For a remote backend, install the desktop half
in the app (*Install from Git*, Desktop target) — the source repo's panel file is usually identical
to the one already backing the agent half, so the canonical repo is fine.

## Pitfalls

1. NEVER hardcode colors or backgrounds (`#000`, `black`, `rgb(...)`). Panes
  already sit on the app's editor background — leave the background alone
  and use theme variables for everything else: `var(--ui-text-secondary)`,
  `var(--ui-text-quaternary)`, `var(--ui-stroke-secondary)`,
  `var(--ui-accent)`. For canvas drawing, resolve them once with
  `getComputedStyle(canvas).getPropertyValue('--ui-accent')`.
2. Reference only what you imported — a component you forgot to import
  (e.g. `StatusDot`) is a ReferenceError at render. Double-check every
  identifier in your `jsx()` calls appears in the import line.
3. Canvas panes MUST track their container with a `ResizeObserver` and
  re-size the canvas (width/height attributes, not just CSS) — panes resize
  constantly (sash drags, layout switches); a mount-time-only size leaves
  blank space or blurry scaling.
4. JSX syntax will not parse — the file loads uncompiled. Use
  `jsx('div', { children: ... })` from `react/jsx-runtime`.
5. Do not import anything except `@hermes/plugin-sdk`, `react`, and
  `react/jsx-runtime`; other specifiers fail to resolve.
6. Handlers must read state imperatively (`$atom.get()`), never from render
  closures — rapid events will otherwise see stale values.
7. Keep components small; subscribe (`useValue`) only in the leaf that
  renders the value.
8. **`ctx.socket` is a no-op on OAuth remotes** — always keep a polling fallback; a socket-only plugin silently receives nothing against a remote backend.
9. **The Python backend loads only when the plugin id is in `plugins.enabled`** — separate from the in-app enable toggle, so a plugin "enabled" in Settings can still show no panel until installed with `hermes plugins install … --enable`.
10. **The dashboard mounts plugin API routes ONCE, at startup** — restart the dashboard (usually a system unit: `sudo systemctl restart hermes-dashboard`); restarting the gateway is not enough.
11. **`defaultEnabled: false` ships an opt-in plugin** — it inventories in Settings → Plugins but stays off until the user flips it; do not assume your plugin auto-enables.

## Verification

- The plugin's UI appears after **Reload desktop plugins**.
- No error toast ("Plugin <name> failed to load") appears; if it does, the
  message names the failure — fix and reload.
- For panes: the new zone is visible and draggable like any core pane.
