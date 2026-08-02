---
name: pystray-windows-tray-click
description: Make a pystray system-tray icon respond to left-click on Windows, and avoid the Menu(default=...) runtime crash. Use when building/wiring a pystray tray app where left-click does nothing, or you hit "Menu.__init__() got an unexpected keyword argument 'default'".
version: 1.1.0
metadata:
  hermes:
    tags: [pystray, tray, windows, gui, left-click]
    trigger_conditions:
      - "pystray left-click does nothing on Windows"
      - "Menu.__init__() got an unexpected keyword argument 'default'"
      - "Wire a system-tray icon click handler"
      - "pystray on_activate not firing"
      - "Build a Windows tray app"
      - "pystray MenuItem default attribute"
      - "Customtkinter popup always on top"
      - "Debug pystray headless (no display)"
---

# pystray Windows left-click activation

## The rule (Windows backend)
A left single-click on a pystray `Icon` (Windows) sends `WM_LBUTTONUP` →
`Icon.__call__()` → `Menu.__call__()`, which **only invokes the menu item
whose `default` attribute is truthy**. There is no separate `on_activate`
dispatch on Windows — setting `icon.on_activate = cb` alone does nothing
unless a `default` item also exists. (macOS/AppKit is the backend that uses
`on_activate`.)

## Correct wiring
```python
from pystray import MenuItem as Item, Menu
show_item = Item("Show", self._on_show, default=True)   # default on the ITEM
menu = Menu(show_item,
            Item("Refresh now", self._on_refresh),
            Item("Open config", self._on_open_config),
            Item("Quit", self._on_quit))
icon = pystray.Icon("name", image, "tooltip", menu)
# Do NOT rely on icon.on_activate for Windows left-click.
```
Left-click now calls `self._on_show`.

## Common crash (and why it slips past Linux checks)
```python
menu = Menu(Item("Show", cb), default=show_item)   # WRONG
# TypeError: Menu.__init__() got an unexpected keyword argument 'default'
```
`default` is a **`MenuItem`** kwarg:
`MenuItem.__init__(self, text, action, checked=None, radio=False, default=False, visible=True, enabled=True)`
It is NOT accepted by `Menu.__init__(self, *items)`.

## Verification gotchas
- `python -m py_compile` and syntax-only checks do **NOT** validate keyword
  arguments. Invalid kwargs only fail at runtime on the target OS. Always test
  pystray GUI code on Windows (or actually import the backend) before shipping —
  Linux `py_compile` happily accepts a bad `Menu(default=...)`.
- Importing pystray on a headless Linux box fails (`Xlib.error.DisplayNameError`
  / no display backend). To confirm behavior, **read the source** instead of
  importing:
  - `pystray/_win32.py` → `_on_notify`: `if lparam == win32.WM_LBUTTONUP: self()`
  - `pystray/_base.py` → `Icon.__call__` calls `self._menu(self)`;
    `Menu.__call__` returns `next(item for item in self.items if item.default)(icon)`;
    `MenuItem.__init__` signature (above).

## Symptoms → cause
- **Left-click does nothing, no error** → menu has no `default` item. Add
  `default=True` to the target `MenuItem`.
- **`TypeError: Menu.__init__() got an unexpected keyword argument 'default'`**
  → you passed `default=` to `Menu(...)` instead of to `Item(...)`.
- **`on_activate` set but no effect** → Windows ignores `on_activate` without a
  `default` item; use `Item(..., default=True)`.

## Bonus: always-on-top + stay-open popup (customtkinter)
- A borderless `CTkToplevel` with `overrideredirect(True)` should set
  `self.attributes("-topmost", True)` in `__init__` to float above other windows.
- To keep it open for glancing (don't auto-close on focus loss), do NOT bind
  `<FocusOut>` to a close handler. Provide dismissal via a Close button and/or
  a left-click toggle instead.

## When to Use
- Wiring a pystray tray icon where left-click should open/show something on Windows.
- Hit `Menu.__init__() got an unexpected keyword argument 'default'` at runtime.
- `icon.on_activate` is set but clicks do nothing.
- Building a Windows tray app (HermesAgentBar, dashboard widgets, etc.) with pystray + customtkinter.
- Verifying pystray behavior on a headless Linux box by reading source instead of importing.

## Not For
- **General pystray icon setup (icons, tooltips, menus) without click-wiring problems** → the pystray docs cover that; this skill is specifically about left-click activation and the `Menu(default=...)` crash.
- **Building the full GUI app** (customtkinter layout, styling) → use `gui-app-headless-testing` for headless-testable GUI patterns.
- **Windows service/startup configuration** → use `windows-service-config`.
- **Tray apps that never need left-click** → no `default` item needed; skip the pattern.

## Pitfalls
1. **Passing `default=` to `Menu(...)` instead of `MenuItem(...)`** — `TypeError: Menu.__init__() got an unexpected keyword argument 'default'`. Put `default=True` on the ITEM: `Item("Show", cb, default=True)`.
2. **Relying on `icon.on_activate` on Windows** — The Windows backend dispatches `WM_LBUTTONUP` through the menu's `default` item, not `on_activate`. Without a `default` item, left-click silently does nothing.
3. **Validating with `py_compile` on Linux** — Syntax checks do NOT catch invalid kwargs; they only fail at runtime on Windows. Test on Windows or read the pystray source (`pystray/_win32.py`, `pystray/_base.py`).
4. **Importing pystray on headless Linux** — Fails with `Xlib.error.DisplayNameError`. Read the source files instead of importing to confirm behavior.
5. **Multiple `default` items** — `Menu.__call__` returns `next(item for item in self.items if item.default)` — with more than one default, behavior is nondeterministic. Keep exactly one `default=True`.
6. **Borderless popup disappearing behind other windows** — `CTkToplevel` + `overrideredirect(True)` needs `self.attributes("-topmost", True)` in `__init__` or it will not float above other windows.
7. **Auto-closing popup on focus loss** — Binding `<FocusOut>` to a close handler makes the popup vanish while the user is reading it. Use a Close button or click-toggle instead.
8. **Assuming macOS behavior applies on Windows** — `on_activate` is the AppKit path; it is NOT the Windows path. Code that works on macOS may do nothing on Windows.
