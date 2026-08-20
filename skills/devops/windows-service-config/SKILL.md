---
name: windows-service-config
description: Manage Windows services running as SYSTEM vs user context — config paths, debugging, gotchas. Use when troubleshooting Windows services that don't see config changes, or when setting up services that run under SYSTEM account.
version: 1.1.0
metadata:
  hermes:
    trigger_conditions:
      - "windows service not picking up config"
      - "service running as SYSTEM"
      - "which config file is the service reading"
      - "edited config but nothing changed"
      - "backrest config not visible"
      - "systemprofile AppData config"
      - "task scheduler run whether user logged on"
      - "run as administrator not system context"
      - "windows service profile path"
      - "config.json systemprofile location"
      - "service reading wrong config"
      - "scheduled task SYSTEM profile"
---

# Windows Service Config Management

## When to Use

- Windows service not picking up config changes
- Setting up a service to run as SYSTEM
- Confusion about which config file a service is reading
- "I edited the config but nothing changed"
- Debugging a scheduled task that runs whether the user is logged on or not
- Backrest (or similar) config not showing up in the UI despite correct-looking edits

## Not For

- **Linux services / systemd units** → different profile model entirely; use the platform-native guidance
- **Windows apps that run interactively** (not services/tasks) → they read the normal user profile; this skill is about the SYSTEM-vs-user split
- **Active Directory / Group Policy config management** → out of scope
- **Writing Windows services from scratch** (code-level) → that's a development task, not a config-management one

## Key Concept: SYSTEM vs User Context

Windows services running as SYSTEM use a **separate user profile** from any logged-in user, even Administrators.

### Config Paths

| Context | %APPDATA% Location |
|---------|-------------------|
| **SYSTEM service** (via Task Scheduler, Windows Service) | `C:\Windows\System32\config\systemprofile\AppData\Roaming\` |
| **Interactive user** (even "Run as Administrator") | `C:\Users\<username>\AppData\Roaming\` |

These are **completely separate**. A service running as SYSTEM will never read from `C:\Users\...` unless explicitly configured.

## Debugging: "Config Changes Not Visible"

When a Windows service doesn't see your config edits:

1. **Find all possible config locations:**
   ```powershell
   Get-ChildItem -Recurse -Filter config.json -Path "$env:APPDATA","$env:LOCALAPPDATA","C:\Windows\System32\config\systemprofile\AppData" -ErrorAction SilentlyContinue | Select-Object FullName,LastWriteTime
   ```

2. **Check timestamps** — the most recently modified config is likely the one being read

3. **Verify execution context:**
   - If launched via Task Scheduler with "Run whether user is logged on or not" → SYSTEM context
   - If launched via "Run as Administrator" from Start Menu → user context (even if elevated)

4. **Kill all instances** before testing:
   ```powershell
   Get-Process *servicename* | Stop-Process -Force
   ```

5. **Relaunch via the same method** you want to debug (scheduled task vs interactive)

## Example: Backrest on Windows

**Scenario:** Backrest installed as Administrator, config edited at `C:\Users\wahid\AppData\Roaming\backrest\config.json`, but changes don't appear in UI.

**Root cause:** Backrest was launched via Task Scheduler running as SYSTEM, which reads from `C:\Windows\System32\config\systemprofile\AppData\Roaming\backrest\config.json` instead.

**Fix:** Edit the SYSTEM-profile config, or change the scheduled task to run as the user instead of SYSTEM.

## Pitfalls

1. **"Run as Administrator" ≠ SYSTEM context** — this is the #1 confusion. Interactive elevation still uses your user profile (`C:\Users\<user>\AppData\Roaming\`), not `systemprofile`.
2. **Task Scheduler "Run whether user is logged on or not"** — runs as SYSTEM by default; the service reads `systemprofile` paths.
3. **Windows Services (services.msc)** — run as SYSTEM unless configured otherwise.
4. **Editing the wrong config wastes time** — always verify which profile the process is using first (`Get-ChildItem -Recurse -Filter config.json` across both profile roots, compare `LastWriteTime`).
5. **SYSTEM-profile paths require Admin** — you can't edit `C:\Windows\System32\config\systemprofile\...` from an unelevated editor; use an elevated one.
6. **Stale running instance** — after editing, kill all instances (`Get-Process *servicename* | Stop-Process -Force`) before relaunching, or the old config stays in memory.
7. **Scheduled task config doesn't live in `%APPDATA%`** — Task Scheduler stores task definitions in the registry/XML; only the *service's own config files* follow the profile split. Don't hunt for `config.json` in the wrong layer.

## Verification

After editing config for a SYSTEM service:
1. Stop the service/task
2. Edit the correct config file (use elevated editor)
3. Start via the same method (scheduled task, service restart)
4. Check UI/logs to confirm changes took effect
