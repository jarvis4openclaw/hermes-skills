# Fix: "duplicate plugin id detected; global plugin will be overridden by global plugin"

## Error
```
plugins.entries.lossless-claw: plugin lossless-claw: duplicate plugin id detected;
global plugin will be overridden by global plugin
(/home/wahid/.openclaw/npm/node_modules/@martian-engineering/lossless-claw/dist/index.js)
```

## Root Cause (this session, 2026-05-15)

Two global discoveries of the same plugin:

1. **npm auto-discovery**: `lossless-claw` was in `~/.openclaw/npm/package.json` dependencies → installed at `~/.openclaw/npm/node_modules/@martian-engineering/lossless-claw/` → auto-discovered via `bundledDiscovery: "compat"` + `plugins.allow` list.

2. **Extensions directory scan**: A stale backup at `~/.openclaw/extensions/lossless-claw.bak.20260513/` also had `openclaw.plugin.json` → auto-scanned and discovered as a second global plugin.

Additionally, `lossless-claw` was in `plugins.entries` (with just `enabled: true`, no custom config), which compounded the issue.

## Fix Applied

1. Moved backup out of extensions directory:
   ```bash
   mv ~/.openclaw/extensions/lossless-claw.bak.20260513 \
      ~/.openclaw/lossless-claw-extension-backup-20260513
   ```

2. Removed `lossless-claw` from `plugins.entries` (it had no custom config, just `enabled: true`):
   ```json
   // BEFORE
   "entries": {
     "anthropic": { "enabled": true },
     "lossless-claw": { "enabled": true }  // REMOVE this
   }
   
   // AFTER
   "entries": {
     "anthropic": { "enabled": true }
   }
   ```

3. Kept `lossless-claw` in `plugins.allow` for auto-discovery from npm.

4. Validated JSON after edit (trailing comma removal was also needed).

## Verification

After restart, check:
```bash
openclaw plugins list --verbose | grep lossless-claw
```
Should show exactly one entry, no duplicate warning in logs.
