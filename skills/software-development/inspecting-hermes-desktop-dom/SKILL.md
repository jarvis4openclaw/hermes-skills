---
name: inspecting-hermes-desktop-dom
description: "Read the live Hermes desktop DOM/CSS over CDP."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [desktop, electron, cdp, dom, ui-verification, self-inspection]
    related_skills: [node-inspect-debugger, systematic-debugging, dogfood]
    trigger_conditions:
      - "read the live desktop DOM"
      - "inspect the running app over CDP"
      - "which CSS rule is winning"
      - "why is this element still styled like that"
      - "get computed style of an element in the app"
      - "attach to the electron renderer"
      - "chrome devtools protocol port 9222"
      - "debug the hermes desktop ui"
      - "verify a ui change took effect"
      - "read renderer console errors"
      - "launch an isolated desktop instance"
      - "cdp port is closed"
---

# Inspecting the live Hermes desktop DOM

## Overview

When you are developing `apps/desktop` and the user is running that same app
(`hgui` / `npm run dev`), you can read the **live rendered DOM** of the window
they are looking at — computed styles, geometry, which CSS rule actually won,
console output — instead of inferring it from `.tsx` and being wrong.

Dev-server runs open a Chrome DevTools Protocol port on `127.0.0.1:9222`
automatically. The renderer is a Chromium page, so everything DevTools can read,
a script can read.

**This does not replace looking at it.** CDP answers *factual* questions ("what
is the computed padding", "did this element render", "which selector matches").
It cannot tell you whether the result looks good. Colour balance, spacing feel,
and "is this ugly" still need the user's eyes or a screenshot. Answer facts with
CDP; hand aesthetics to the user.

## When to Use

- Verifying a UI change actually took effect in the running app
- "Why is this element still X?" — find the winning rule before editing anything
- Locating a stable selector for a component you're about to change
- Checking a design token's computed value on a real node
- Reading renderer console errors the user mentions but can't copy out
- Confirming which CSS rule won before "fixing" call sites one by one
- Asserting first-paint facts: font face, computed colour, background ancestor
- Confirming a plugin's pane actually rendered inside the app

## Not For

- Operating the app as a user (menus, typing, clicking) → use `hermes-desktop-app-interaction` instead
- Adding or extending UI via a plugin → use `hermes-desktop-plugins` instead
- Judging whether a UI looks good (aesthetics) → use `frontend-taste` for visual review instead
- Asserting a web app's UI in a headless browser (not this Electron app) → use `gui-app-headless-testing` instead
- Debugging a Hermes TUI command → use `debugging-hermes-tui-commands` instead
- Debugging errors in agent-generated source code → use `debug-generated-code-errors` instead
- Comparing browser backends for a scraping/automation task → use `homelab-browser-backends` instead

## The port

Open on `127.0.0.1:9222` for any dev-server run. Closed in exactly two cases
(`apps/desktop/electron/dev-cdp.ts`):

- **packaged builds** — always, and no environment value overrides it;
- **no `HERMES_DESKTOP_DEV_SERVER`** — an unpackaged `electron .` against
  `dist/` is how the packaged app gets smoke tested, so it behaves like one.

`HERMES_DESKTOP_CDP_PORT` moves the port (`=9333`) or disables it (`=off`).

Check before doing anything else:

```bash
curl -s --max-time 3 http://127.0.0.1:${HERMES_DESKTOP_CDP_PORT:-9222}/json/version
```

Empty → no port. Do not guess another port silently.

**Never relaunch the user's app to get a port.** That destroys their session and
their state. Launch your own isolated instance instead (below).

## Reading the DOM

`apps/desktop/scripts/eval.mjs` is the one-liner:

```bash
cd apps/desktop
node scripts/eval.mjs "document.querySelectorAll('[data-slot]').length"
```

For multi-step work use the shared client — it has target discovery and
promise-aware eval:

```js
import { CDP, SELECTORS } from './scripts/perf/lib/cdp.mjs'

const cdp = await CDP.connect({ port: 9222, match: '5174' })
const out = await cdp.eval(`JSON.stringify({
  radius: getComputedStyle(document.documentElement).getPropertyValue('--radius-scalar').trim(),
  composer: !!document.querySelector('[data-slot="composer-rich-input"]')
})`)
cdp.close()
```

`SELECTORS` in `scripts/perf/lib/cdp.mjs` holds the stable `data-slot` hooks
(composer, thread viewport, assistant message, turn pair, profile rail). Prefer
them over inventing a `querySelector` — they are updated as a unit when
components move.

## The question this is best at: which rule won?

Editing every call site because a style "isn't applying" is the classic waste.
Read the real node first:

```js
const el = document.querySelector('[data-slot="aui_assistant-message-root"] a')
JSON.stringify({
  ownClasses: el.className,
  weight: getComputedStyle(el).fontWeight,
  parents: (() => {
    const out = []
    let n = el
    while ((n = n.parentElement) && out.length < 6) out.push(n.className)
    return out
  })()
})
```

If the node carries no class of its own, the value is **inherited** — sweeping
call sites will not fix it, and you need the ancestor rule. A plugin stylesheet
(e.g. `@tailwindcss/typography`'s `prose a { font-weight: 500 }`) routinely beats
a utility class; override on the shared class, not at each usage.

## Your own isolated instance

When there is no port, or you must not disturb the user's window:

```bash
cd apps/desktop
HERMES_HOME=$HOME/.hermes/cache/scratch/cdp-probe-home \
HERMES_DESKTOP_DEV_SERVER=http://127.0.0.1:5174 \
HERMES_DESKTOP_CDP_PORT=9333 \
  npx electron . --user-data-dir=$HOME/.hermes/cache/scratch/cdp-probe-userdata
```

The separate `--user-data-dir` dodges Electron's single-instance lock, so it
cannot collide with a running `hgui`; the separate `HERMES_HOME` keeps it away
from real sessions. Pick a port other than 9222 for the same reason. Run it in
the background and kill it when done.

`npm run perf:serve` does the same with a temp `HERMES_HOME` baked in, if you
also want the perf harness.

## Pitfalls

1. **Never kill the user's dev server or app to "free" anything.** A mid-serve
  kill nukes Chromium's socket pool, and the resulting `ERR_NETWORK_CHANGED`
  gets blamed on whatever you just changed.
2. **A throwaway `HERMES_HOME` has no backend.** The app logs `ECONNREFUSED` for
  `hermes:api` and may exit on its own. The renderer still mounts and the DOM is
  readable — read promptly, and don't mistake a self-exited probe for a broken
  port. Chromium logs `DevTools listening on ws://127.0.0.1:<port>/…` when it
  binds; that line is the proof the port opened.
3. **Poll, don't probe once.** A just-launched app needs a second or two before
  the port answers.
4. **Never dump the whole DOM.** The desktop renders hundreds of nodes and
  `outerHTML` will bury your context. Project down to a small JSON object inside
  the evaluated expression.
5. **Pass `match` to `CDP.connect`.** Without it you may attach to the pet
  overlay, quick-entry window, or a devtools target instead of the main window.
6. **`cdp.eval` returns the value; raw `Runtime.evaluate` double-nests it**
  (`.result.result.value`). Use the wrapper.
7. **`import.meta.env.DEV` is `true` under `vite dev`** in this repo. The note in
  `apps/desktop/scripts/profile-typing-lag.md` claiming otherwise is stale.
8. **Never relaunch the user's app to get a port** — that destroys their session and state; launch an isolated instance (`HERMES_HOME` + `--user-data-dir` + a different CDP port) instead.
9. **A packaged build always has CDP closed** — no environment value overrides it; only a dev-server run (`HERMES_DESKTOP_DEV_SERVER`) opens the port.
10. **Don't silently guess another port.** An empty `/json/version` means there is no port — say so rather than trying 9223, 9333, …
11. **`--user-data-dir` is what dodges Electron's single-instance lock** — without it your probe instance cannot start while `hgui` runs.
