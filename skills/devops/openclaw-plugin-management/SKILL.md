---
name: openclaw-plugin-management
description: Manage OpenClaw plugins — install, configure, debug duplicates, and understand discovery/load order. Use when the user asks about plugin errors, duplicate plugins, plugin not loading, or plugin config.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [openclaw, plugin, duplicate, discovery, bundledDiscovery, extensions]
---

# OpenClaw Plugin Management

Use when debugging plugin load errors, duplicate plugin warnings, or plugin config issues.

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
- Don't put a plugin in both `plugins.allow` and `plugins.entries` with `bundledDiscovery: "compat"`
- Don't leave stale extension backups in `~/.openclaw/extensions/` — they get auto-scanned
- Don't assume `enabled: false` in the registry prevents discovery — it still gets found, just not loaded
- Always validate JSON after editing `openclaw.json` — a trailing comma breaks startup
