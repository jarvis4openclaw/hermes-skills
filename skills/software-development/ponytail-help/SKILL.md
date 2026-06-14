---
name: ponytail-help
description: >
  Quick-reference card for all ponytail modes, skills, and commands.
  One-shot display, not a persistent mode.
version: 1.0.0
metadata:
  hermes:
    trigger_conditions:
      - "/ponytail-help"
      - "ponytail help"
      - "what ponytail commands"
      - "how do I use ponytail"
      - "ponytail reference"
      - "ponytail modes"
      - "ponytail quick reference"
      - "show me ponytail options"
      - "ponytail levels"
      - "ponytail card"
      - "ponytail cheat sheet"
      - "what are the ponytail skills"
      - "how to configure ponytail"
---

# Ponytail Help

Display this reference card when invoked. One-shot, do NOT change mode,
write flag files, or persist anything.

## When to Use

- User types `/ponytail-help` or asks "how do I use ponytail"
- User wants to see all available ponytail modes (lite/full/ultra)
- User needs the quick-reference card of ponytail skills
- User is configuring the default ponytail mode
- User wants to deactivate ponytail or switch modes
- User needs to know how to update the ponytail plugin
- User asks about ponytail levels, skills, or triggers
- User is confused about which ponytail mode to use

## Not For

- **Enforcing ponytail laziness actively** → use `ponytail` instead
- **Reviewing code for over-engineering** → use `ponytail-review` instead
- **Building with ponytail constraints** → use `ponytail` instead (this skill is reference-only)
- **Setting up ponytail auto-activation for a host** → follow the plugin install docs at the GitHub repo
- **Debugging why ponytail isn't applying** → use `ponytail` or check the host's plugin configuration
- **Writing ponytail-compliant code** → use `ponytail` instead

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

## Pitfalls

1. **Mode sticks until session end** — `/ponytail lite` persists for the entire session. If you want a one-shot lazy suggestion without changing the mode, ask "what's the lazier alternative?" instead of switching modes.
2. **Config file path differs by OS** — `~/.config/ponytail/config.json` on Linux/Mac, `%APPDATA%\ponytail\config.json` on Windows. Verify the correct path before editing.
3. **Off state still allows manual activation** — Setting `"defaultMode": "off"` only disables auto-activation at session start. `/ponytail` still activates it manually for that session.
4. **Env var overrides config file silently** — If `PONYTAIL_DEFAULT_MODE` is set, the config file is ignored with no warning. Check for env vars first if the mode isn't what you expect.
5. **Skill is reference-only, not a mode** — Loading `ponytail-help` displays this card and exits. It does NOT activate ponytail mode. If you want actual laziness enforcement, use `/ponytail`.
6. **Does not work without the ponytail plugin installed** — This help card is bundled with the ponytail plugin. If `/ponytail-help` isn't recognized, the plugin isn't installed.
7. **Host-specific plugin commands** — The `/plugin` and `/reload-plugins` commands are Claude Code-specific. Codex, OpenCode, and other hosts use different plugin management. Check the ponytail GitHub repo for host-specific install instructions.
8. **Update flow depends on host** — Auto-update on Claude Code uses the Marketplace. On other hosts, update manually by pulling the plugin repo or reinstalling.
9. **Deactivate commands are literal** — "stop ponytail" and "normal mode" are exact triggers. "disable ponytail" or "turn off ponytail" may not work.
10. **Resolution order is counter-intuitive** — Env var beats config file beats default. If debugging unexpected mode, always check env vars first.

## More

Full docs + examples: https://github.com/DietrichGebert/ponytail
