---
name: ponytail-help
description: >
  Quick-reference card for all ponytail modes, skills, and commands.
  One-shot display, not a persistent mode. Trigger: /ponytail-help,
  "ponytail help", "what ponytail commands", "how do I use ponytail".
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Ponytail, Reference, Commands, Minimalism]
    trigger_conditions:
      - "/ponytail-help"
      - "ponytail help"
      - "what ponytail commands"
      - "how do I use ponytail"
      - "ponytail reference card"
      - "show ponytail modes"
---

# Ponytail Help

Display this reference card when invoked. One-shot, do NOT change mode,
write flag files, or persist anything.

## When to Use

Use when you need a quick reference card for ponytail modes, commands, and companion skills:
- Looking up ponytail levels (Lite, Full, Ultra) and their triggers
- Checking companion skill commands (`/ponytail`, `/ponytail-review`, `/ponytail-gain`)
- Configuring default ponytail modes via environment variables or config files
- Learning how to update ponytail or reset normal mode

## Not For

- **Writing or reviewing code** — this skill is a static reference card only; use `/ponytail` or `ponytail-review` for actual work.
- **Persisting session state** — ponytail-help is explicitly one-shot and must not modify flag files or change active session state.
- **Debugging ponytail installation errors** — use standard troubleshooting workflows instead of the reference card.

## Levels

| Level | Trigger | What change |
|-------|---------|-------------|
| **Lite** | `/ponytail lite` | Build what's asked, name the lazier alternative in one line. |
| **Full** | `/ponytail` | The ladder enforced: YAGNI → stdlib → native → one line → minimum. Default. |
| **Ultra** | `/ponytail ultra` | YAGNI extremist. Deletion before addition. Challenges requirements before building. |

Level sticks until changed or session end.

## Skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| **ponytail** | `/ponytail` | Lazy mode itself. Simplest solution that works. |
| **ponytail-review** | `/ponytail-review` | Over-engineering review: `L42: yagni: factory, one product. Inline.` |
| **ponytail-gain** | `/ponytail-gain` | Measured-impact scoreboard: less code, less cost, more speed. |
| **ponytail-help** | `/ponytail-help` | This card. |

Codex uses `@ponytail`, `@ponytail-review`, and `@ponytail-help`; Claude Code
and OpenCode use the slash-command forms above (OpenCode ships `/ponytail` and
`/ponytail-review`).

## Deactivate

Say "stop ponytail" or "normal mode". Resume anytime with `/ponytail`.
`/ponytail off` also works.

## Configure Default Mode

Default mode = `full`, auto-active every session. Change it:

**Environment variable** (highest priority):
```bash
export PONYTAIL_DEFAULT_MODE=ultra
```

**Config file** (`~/.config/ponytail/config.json`, Windows: `%APPDATA%\ponytail\config.json`):
```json
{ "defaultMode": "lite" }
```

Set `"off"` to disable auto-activation on session start, activate manually
with `/ponytail` when wanted.

Resolution: env var > config file > `full`.

## Update

Enable auto-update once: open `/plugin`, go to Marketplaces, pick ponytail, Enable auto-update. Claude Code then pulls new versions at startup (run `/reload-plugins` when it prompts). Manual refresh: `/plugin marketplace update ponytail` then `/reload-plugins`.

If `/plugin` is not recognized, your Claude Code is out of date. Update it (`npm install -g @anthropic-ai/claude-code@latest`, or `brew upgrade claude-code`) and restart. Other hosts use their own update flow.

## More

Full docs + examples: https://github.com/DietrichGebert/ponytail

## Pitfalls

1. **Persisting state from a one-shot help command** — Accidentally modifying active session state or writing flag files when invoked. Recovery: keep `ponytail-help` strictly one-shot and read-only.
2. **Confusing Lite, Full, and Ultra behavior** — Expecting Full mode behavior while in Ultra mode (deleting requirements before building). Recovery: check current level trigger (`/ponytail lite`, `/ponytail`, or `/ponytail ultra`).
3. **Failing to reset normal mode properly** — Stating "stop ponytail" or "normal mode" but failing to clear the active level. Recovery: explicitly deactivate using the documented deactivation commands.
4. **Incorrect config file path** — Placing `config.json` in the wrong directory (`~/.hermes/` instead of `~/.config/ponytail/`). Recovery: place the config file at `~/.config/ponytail/config.json`.
5. **Ignoring environment variable priority** — Wondering why `config.json` settings are overridden by environment variables. Recovery: remember that `PONYTAIL_DEFAULT_MODE` takes precedence over config files.
