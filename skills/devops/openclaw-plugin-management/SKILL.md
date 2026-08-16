---
name: openclaw-plugin-management
description: Manage OpenClaw plugins — install, configure, debug duplicates, and understand discovery/load order. Use when the user asks about plugin errors, duplicate plugins, plugin not loading, or plugin config.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [openclaw, plugin, duplicate, discovery, bundledDiscovery, extensions]
    trigger_conditions:
      - "openclaw plugin error"
      - "duplicate plugin id detected"
      - "openclaw plugin not loading"
      - "plugin not discovered"
      - "bundledDiscovery compat allowlist"
      - "openclaw extensions directory"
      - "plugins.allow plugins.entries"
      - "openclaw plugins list"
      - "plugin registry refresh"
      - "lossless-claw duplicate"
      - "openclaw plugin config"
      - "openclaw plugin install"
---

# OpenClaw Plugin Management

Use when debugging plugin load errors, duplicate plugin warnings, or plugin config issues.

## When to Use

- The user reports "duplicate plugin id detected" or a plugin warning in OpenClaw logs.
- A plugin isn't loading, isn't discovered, or is silently missing from the registry.
- The user asks how OpenClaw discovers plugins or what `bundledDiscovery` means.
- You need to change plugin config (`plugins.allow`, `plugins.entries`, `plugins.slots`).
- You installed a new plugin and it isn't showing up in `openclaw plugins list`.

## Not For

- OpenClaw gateway/config audit at the config-file level → use `openclaw-config-management` instead.
- Installing/updating the OpenClaw CLI or its runtime → use the OpenClaw docs or `openclaw-config-management`.
- Debugging a specific plugin's internal logic (not discovery/loading) → that belongs to the plugin's own docs.
- Hermes (not OpenClaw) plugin management → Hermes skills/plugins live under `~/.hermes`, a different system.

## Plugin Discovery Paths

OpenClaw discovers plugins from multiple sources. Understanding these is key to debugging duplicates:

1. **Bundled plugins** — shipped with OpenClaw at `/home/wahid/.npm-global/lib/node_modules/openclaw/dist/extensions/`
2. **Global npm plugins** — installed in `~/.openclaw/npm/node_modules/@*/` (from `~/.openclaw/npm/package.json` dependencies)
3. **Extensions directory** — `~/.openclaw/extensions/*/` (auto-scanned for `openclaw.plugin.json`)
4. **Explicit paths** — `plugins.load.paths` in config

## Key Config Fields

In `~/.openclaw/openclaw.json` (or `~/.openclaw/config.yml`):

- `plugins.allow` — allowlist of plugin IDs. With `bundledDiscovery: "compat"`, this gates bundled provider plugins but non-bundled plugins in `node_modules` are also auto-discovered if listed here.
- `plugins.entries.<id>` — explicit plugin config (enabled, config object). Creates a **configured** plugin registration.
- `plugins.slots.<slot>` — assigns a plugin to a slot (e.g., `contextEngine: "lossless-claw"`)
- `bundledDiscovery` — `"compat"` (legacy, auto-discovers from npm deps + extensions) or `"allowlist"` (only loads from `plugins.allow`)

## Duplicate Plugin Detection

Error: `plugin <id>: duplicate plugin id detected; global plugin will be overridden by global plugin`

This means OpenClaw found the same plugin ID from two different **global** discovery sources. Common causes:

### Cause 1: In both `plugins.allow` AND `plugins.entries`
With `bundledDiscovery: "compat"`, a plugin listed in `plugins.allow` gets auto-discovered from `node_modules`. If it's also in `plugins.entries`, it gets loaded twice.

**Fix:** Remove from `plugins.entries` if it has no special config (just `enabled: true`). Keep it in `plugins.allow` for auto-discovery.

### Cause 2: In `node_modules` AND `extensions/` directory
The extensions directory (`~/.openclaw/extensions/`) is auto-scanned. If a plugin is installed in BOTH `npm/node_modules/` AND has a copy in `extensions/`, it gets discovered twice.

**Fix:** Move stale backups out of `extensions/`:
```bash
mv ~/.openclaw/extensions/<plugin>.bak.* ~/.openclaw/<plugin>-backup
```

### Cause 3: Listed in `npm/package.json` dependencies AND `plugins.entries`
When a plugin is in `npm/package.json` dependencies, it gets installed to `node_modules` and auto-discovered. Adding it to `plugins.entries` creates a second registration.

**Fix:** Choose one: either manage it via npm deps (auto-discovery) or via `plugins.entries` (explicit), not both.

## Debugging Steps

1. **Check the plugin registry** for all discovered instances:
   ```bash
   cat ~/.openclaw/plugins/installs.json | python3 -c "
   import sys, json
   d = json.load(sys.stdin)
   for p in d.get('plugins', []):
       if '<plugin-id>' in p.get('pluginId', ''):
           print(json.dumps({k: p[k] for k in ['pluginId', 'source', 'rootDir', 'origin', 'enabled']}, indent=2))
   "
   ```

2. **Check config** for the plugin ID:
   ```bash
   grep -n "<plugin-id>" ~/.openclaw/openclaw.json
   ```

3. **Check npm dependencies**:
   ```bash
   grep "<plugin-id>" ~/.openclaw/npm/package.json
   ```

4. **Check extensions directory**:
   ```bash
   ls ~/.openclaw/extensions/*/openclaw.plugin.json 2>/dev/null
   ```

5. **Validate JSON** after edits:
   ```bash
   python3 -c "import json; json.load(open('~/.openclaw/openclaw.json')); print('Valid')"
   ```

## Common Patterns

### Pattern: Plugin works but shows duplicate warning
- Plugin is in `plugins.allow` AND `plugins.entries`
- Remove from `plugins.entries` if no custom config needed
- Keep in `plugins.allow` for auto-discovery

### Pattern: Old/backup extension causing duplicate
- Backup in `~/.openclaw/extensions/` still has `openclaw.plugin.json`
- Move backup out of `extensions/` directory
- Refresh registry: `openclaw plugins registry --refresh`

### Pattern: Plugin not loading at all
- Check `plugins.allow` includes the plugin ID
- Check `plugins.entries.<id>.enabled` is not `false`
- Check `bundledDiscovery` mode — `"allowlist"` requires explicit `plugins.allow` entry
- Run `openclaw plugins list --verbose` to see discovery status

## Real-World Example

See `references/duplicate-global-plugin-fix.md` for a complete walkthrough of fixing the `lossless-claw` duplicate plugin issue (2026-05-15), including the exact error, root cause analysis, and step-by-step fix.

## Pitfalls

1. **Don't put a plugin in both `plugins.allow` and `plugins.entries` with `bundledDiscovery: "compat"`** — The plugin gets auto-discovered from `node_modules` AND explicitly registered, producing "duplicate plugin id detected". Keep it in `plugins.allow` for auto-discovery; remove the `plugins.entries` entry unless it carries custom config.

2. **Don't leave stale extension backups in `~/.openclaw/extensions/`** — The extensions directory is auto-scanned for `openclaw.plugin.json`. A `.bak`/old copy there still registers. Move backups out of the directory.

3. **Don't assume `enabled: false` in the registry prevents discovery** — Disabled plugins are still found, just not loaded. If the duplicate warning persists, the second copy is being discovered elsewhere, not re-enabled.

4. **Always validate JSON after editing `openclaw.json`** — A trailing comma or unescaped character breaks startup. Run `python3 -c "import json; json.load(open('~/.openclaw/openclaw.json'))"` after every edit.

5. **`bundledDiscovery: "allowlist"` changes the rules completely** — In allowlist mode only `plugins.allow` entries load; npm deps and extensions are NOT auto-discovered. If a plugin vanished after switching modes, add it to `plugins.allow`.

6. **`plugins.entries.<id>` with only `enabled: true` is usually redundant** — With `compat` discovery the same plugin is auto-discovered from npm deps. Use `plugins.entries` only when you need to pass a config object or pin a slot.

7. **The registry file is not the source of truth after manual moves** — After moving files in/out of `extensions/`, run `openclaw plugins registry --refresh` (or restart) so `installs.json` reflects the new layout.

8. **Check ALL discovery sources before declaring a plugin missing** — Search `installs.json`, config, `npm/package.json`, and the extensions directory. A plugin can be installed in one source and configured in another; both must agree.

9. **A plugin listed as a npm dependency AND in `plugins.entries` is a duplicate** — Choose one management path: npm deps (auto-discovery) or `plugins.entries` (explicit). Not both.

10. **Verbose listing is the fastest triage** — `openclaw plugins list --verbose` shows discovery status per plugin. Run it before editing config; it pinpoints which source found (or missed) the plugin.
