---
name: hermes-plugin-debug
description: "Debug Hermes plugins where the desktop app and backend disagree — actions that don't persist, unmounted REST routes, stale plugin state, or 'plugin command not found'."
version: 1.1.0
metadata:
  hermes:
    tags: [hermes, plugins, debugging, desktop, backend, rest, state]
    trigger_conditions:
      - "plugin action doesn't persist"
      - "plugin changes revert after refresh"
      - "plugin command not found"
      - "desktop and backend out of sync"
      - "plugin state stale"
      - "hermes plugin debug"
      - "done button doesn't stick"
      - "snooze doesn't persist"
      - "plugin REST routes not mounted"
      - "plugin installed but not showing"
      - "dashboard restart plugin"
      - "plugin not working after install"
      - "hermes plugin troubleshooting"
---

# Hermes Plugin Debugging

Specialized debugging for Hermes plugins where the desktop app and backend appear to be out of sync.

## When to Use

- Plugin actions (Done/Snooze/Archive/etc.) look like they work but revert on the next refresh
- Plugin data shown in the UI is stale, inconsistent, or contradicts the backend's own state
- The UI reports "plugin command not found" or falls back to a CLI that isn't installed
- The desktop app and the backend dashboard are pointed at different Hermes installs or versions
- A plugin was just installed or updated and its REST routes never appeared in the dashboard logs
- You need to prove where a plugin persists state before blaming the plugin's own logic
- A plugin works from the CLI but not from the desktop UI (or vice versa)
- You are about to file a bug and need evidence separating plugin bug from environment drift

## Not For

- **Building a new native Hermes plugin** → use `hermes-plugin-authoring` instead
- **Writing or packaging a desktop-app plugin** → use `hermes-desktop-plugins` instead
- **A genuine application bug with a stack trace and no plugin/desktop split** → use `diagnosing-bugs` instead
- **Inspecting the desktop app's renderer/DOM state directly** → use `inspecting-hermes-desktop-dom` instead
- **Hermes config or provider settings drifted from defaults** → use `hermes-provider-config` instead
- **Plugin/web/MCP import failures during install** → use `hermes-web-and-mcp-import-failures` instead
- **The dashboard or another service is simply down** → use `server-health` instead

## Debugging Procedure

### 1. Verify Plugin State Persistence

Check where the plugin stores its state:

```bash
# Check if state directory and file exist
ls -la ~/.local/state/<plugin-name>/  # XDG_STATE_HOME aware

# If exists, examine contents
cat ~/.local/state/<plugin-name>/state.json
```

**Key insight**: If state.json doesn't exist anywhere, plugin actions are not persisting state.

### 2. Verify Plugin REST Routes Are Mounted

Check if the plugin's backend API routes are properly mounted:

```bash
# Look for mount confirmation in dashboard logs (look for recent timestamps)
grep -i "Mounted plugin API routes" ~/.hermes/logs/hermes-dashboard.log

# Check for plugin-specific API calls in auth logs
grep "api/plugins/<plugin-name>" ~/.hermes/logs/dashboard-auth.log | tail -10
```

**Key insight**: No mount logs + auth hits to plugin endpoints = routes not mounted.
This commonly occurs when the dashboard was started before the plugin was installed/restarted.

### 3. Diagnose Desktop/Backend Communication Split

Determine if desktop and backend are talking to different systems:

#### On the Desktop Machine:
```bash
# Find Hermes Desktop connection configuration
find ~/.config -maxdepth 2 -iname '*hermes*' -name 'connections.json' 2>/dev/null

# Check which Hermes binary is being used
which hermes
readlink -f $(which hermes)

# Test if plugin CLI is available
hermes <plugin-name> --help 2>&1
```

#### On the Backend Machine (if accessible):
```bash
# Check if plugin is installed in backend's plugin directory
ls -la ~/.hermes/plugins/<plugin-name>/

# Verify dashboard process environment (find PID from ps aux)
tr '\0' '\n' < /proc/<dashboard-pid>/environ | grep HERMES
```

### 4. Identify Common Failure Patterns

#### Pattern A: Listing Works, Actions Fail
- **Symptoms**: Data loads correctly, but Done/Snooze/etc. actions don't persist
- **Cause**: Desktop reads from mounted REST API, but actions fall back to local CLI (missing/broken)
- **Check**: `hermes <plugin-name> --help` fails on desktop, but data loads via UI

#### Pattern B: Actions Appear to Work But Don't Persist
- **Symptoms**: Item vanishes when marked Done, but reappears after refresh
- **Cause**: Optimistic UI update without verified persistence; state reverts on next refresh
- **Check**: No state.json updates when performing actions via UI

#### Pattern C: CLI Command Not Found Errors
- **Symptoms**: Explicit "plugin command not found" errors in UI or logs
- **Cause**: Desktop falls back to CLI but local Hermes lacks the plugin command
- **Check**: `hermes <plugin-name> --help` returns "not a hermes command" or similar

### 5. Resolution Path

#### If Plugin REST Routes Aren't Mounted on Backend:
1. Restart the Hermes dashboard service to pick up new plugins:
   ```bash
   # Depending on your setup:
   systemctl --user restart hermes-dashboard  # or
   pkill -f hermes-dashboard && hermes dashboard &
   ```
2. Verify mount logs appear after restart:
   ```bash
   grep -i "Mounted plugin API routes" ~/.hermes/logs/hermes-dashboard.log
   ```
3. Confirm desktop can now reach plugin endpoints:
   ```bash
   # Check auth logs for successful 200 responses (not 401)
   grep "api/plugins/<plugin-name>/" ~/.hermes/logs/dashboard-auth.log | grep -v 401
   ```

#### If Desktop Is Using Wrong/Broken Hermes Binary:
1. Ensure desktop and backend use matching Hermes versions:
   ```bash
   # On both machines:
   hermes --version
   ```
2. Fix desktop Hermes installation or PATH:
   ```bash
   # Reinstall or fix the hermes command in PATH
   which hermes  # should point to correct version
   ```
3. Verify plugin is installed on desktop if using local fallback:
   ```bash
   hermes plugins list | grep <plugin-name>
   ```

### 6. Verification After Fix

After applying fixes, verify:

1. State persistence works:
   ```bash
   # Perform action via UI
   # Check state.json updates
   stat ~/.local/state/<plugin-name>/state.json  # should show newer timestamp
   ```

2. Plugin REST routes are mounted and responding:
   ```bash
   # Check for successful API calls in logs
   grep "api/plugins/<plugin-name>/" ~/.hermes/logs/dashboard-auth.log | grep " 200 "
   ```

3. Desktop and backend are in sync:
   ```bash
   # Data shown in UI matches state.json
   # Actions persist across refreshes
   ```

## Prevention

To avoid these issues in the future:

1. **Install plugins before starting dashboard**: Ensures routes mount on startup
2. **Keep desktop and backend Hermes versions matched**: Prevents CLI fallback mismatches
3. **Monitor plugin state location**: Know where to look for persistence issues
4. **Check logs early**: Mount errors and auth failures appear in dashboard logs

## Pitfalls

1. **State file may not exist at all** — a missing `~/.local/state/<plugin>/state.json` is itself the diagnosis: nothing is persisting. Do not conclude "persistence is fine" because there is no error. Create the directory/file expectation explicitly and re-test the action.
2. **`XDG_STATE_HOME` relocates the state dir** — if the env var is set, `~/.local/state` is the wrong path. Check `echo $XDG_STATE_HOME` on the machine actually running the plugin before declaring state absent.
3. **Timezone/report-time scans produce `Invalid Date`** — timestamp arithmetic can fail on numeric ID-derived or UTC-shifted times. Pass fixed, valid timestamps to date filters in any verification script; if a filter silently matches nothing, suspect the timestamp, not the plugin.
4. **Desktop may not read the shared config dir** — the backend reads `~/.hermes/...`; the desktop app may resolve a different home, container, or bundle. Always confirm you are looking at the *same* filesystem the failing process uses.
5. **No mount log ≠ routes absent** — dashboard logs rotate and are capped. Confirm with a fresh restart plus a request to `api/plugins/<plugin>/`, not by grepping an old log tail.
6. **Restarting the dashboard is disruptive** — a restart drops in-flight requests across every plugin, not just the broken one. Announce it, then verify mounts for all plugins, not only the target.
7. **A `401` on a plugin endpoint is not the same as an unmounted route** — `401` means the route exists and auth rejected you; only `404`/missing mount logs indicate a routing problem. Check `dashboard-auth.log` for `200` vs `401` before changing any config.
8. **`hermes <plugin> --help` failing on desktop is expected when the desktop uses REST** — the CLI is only a fallback. A failing CLI is evidence for Pattern A, not necessarily a broken install; check whether the UI path is supposed to be REST-only.
9. **Version skew between desktop and backend produces confusing CLI fallback** — compare `hermes --version` on both sides before debugging plugin logic. A mismatched pair is a common root cause of "works on backend, dead on desktop".
10. **Optimistic UI hides failures** — an item disappearing when marked Done proves nothing; the UI may delete it locally and resurrect it on refresh. Only `state.json` mtime and a read-back from the backend count as evidence.
11. **Do not edit a plugin's bundled files while debugging** — patching vendored plugin code invalidates upgrades and hides the real cause. Debug against logs and state files, and fix upstream or in your own plugin source.
12. **Claiming a fix without a read-back** — "restarted the dashboard" is not a fix. The fix is proven only when the action persists across an explicit refresh *and* the state change is visible in the backend's own store.

## Related Skills

- `hermes-plugin-authoring`: For writing native Hermes plugins
- `hermes-desktop-plugins`: For writing desktop app plugins
- `diagnosing-bugs`: General bug debugging methodology
- `inspecting-hermes-desktop-dom`: For renderer-level desktop inspection
- `hermes-provider-config`: For config/provider drift rather than plugin state
