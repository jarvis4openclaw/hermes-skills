---
name: openclaw-config-management
version: 1.2.0
description: Audit, diagnose, and fix OpenClaw gateway and agent configuration. Covers secrets, models, providers, model whitelist, browser, gateway bind, bootstrap limits, bundledDiscovery, command owner, cron model overrides, and skills dependencies.
category: devops
metadata:
  hermes:
    tags: [openclaw, config, doctor, secrets, gateway, models, providers, model-whitelist, bootstrap, bundledDiscovery, cron]
    trigger_conditions:
      - "openclaw config"
      - "openclaw doctor"
      - "gateway crash"
      - "secrets missing"
      - "model fallback"
      - "model not allowed"
      - "model whitelist"
      - "openclaw audit"
      - "bootstrap limit"
      - "bundledDiscovery"
      - "command owner"
      - "openclaw secrets"
      - "cron model override"
      - "config scan"
      - "config report"
---

# OpenClaw Config Management

Use when auditing, diagnosing, or fixing OpenClaw configuration — config scan, gateway troubleshooting, model/provider issues, secrets, bootstrap limits, and plugin discovery mode.

## Interaction Pattern

**Boss prefers guided sequential fixes.** When presenting config issues, always:
1. List findings ordered by severity (critical → high → medium → low)
2. Present fixes one at a time, from highest priority down
3. Give the exact command/code block to paste — not "you should change X"
4. Wait for confirmation ("done", "next") before presenting the next fix
5. Never apply changes without explicit direction — even safe ones

This comes from the config audit→fix session where Boss said "I will fix them all one by one. You guide me, tell me the best practice and I will make the changes."

## When to Use

- Running `openclaw doctor` or scanning config for issues
- Gateway crash loop or startup failure
- Missing env vars causing secret resolution failures
- Model fallback configuration
- `bundledDiscovery` mode migration
- Command owner setup
- Browser headless configuration
- Bootstrap file size warning triage
- Skills dependency resolution
- Secrets audit and migration

## Not For

- Plugin duplicate errors → use `openclaw-plugin-management`
- WebSocket/401 gateway auth failures → use `mission-control-openclaw-websocket-401-troubleshooting`
- General OpenClaw operations (starting/stopping services)

## Config Locations

| Path | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | Main config (JSON) |
| `~/.openclaw/.env` | Environment variables for secret resolution |
| `~/.openclaw/agents/<id>/agent/models.json` | Per-agent model overrides |
| `~/.openclaw/agents/<id>/agent/auth-profiles.json` | Per-agent auth profiles |
| `~/.config/systemd/user/openclaw-gateway.service` | Systemd service unit |
| `/tmp/openclaw/openclaw-YYYY-MM-DD.log` | Gateway file logs |

## Core Workflow: Config Audit

```bash
# 1. Full doctor scan (read-only, no changes)
openclaw doctor

# 2. Secrets audit (plaintext, unresolved, shadowed)
openclaw secrets audit

# 3. Gateway deep status
openclaw gateway status --deep

# 4. Plugin registry
openclaw plugins list

# 5. Skills readiness
openclaw skills check --agent <id>

# 6. Validate JSON before manual edits
python3 -c "import json; json.load(open('/home/wahid/.openclaw/openclaw.json')); print('Valid')"
```

## Common Issues & Fixes

### Gateway Crash Loop (Missing Env Var)

**Symptoms:** Gateway restarts repeatedly, hits systemd rate limit, stops. Logs show `SecretRefResolutionError: Environment variable "X" is missing or empty`.

**Diagnosis:**
```bash
journalctl --user -u openclaw-gateway.service -n 50 --no-pager | grep -i "secret\|manifest\|error"
openclaw secrets audit | grep REF_UNRESOLVED
```

**Fix:** The `${VAR_NAME}` notation in config resolves from environment. In order of preference:
1. Add the value to `~/.openclaw/.env` (survives restarts, already used by other keys)
2. Set via `systemctl --user set-environment VAR=value` (persistent, but OS-level)

Then reload:
```bash
openclaw secrets reload
systemctl --user restart openclaw-gateway
openclaw gateway status  # verify
```

**Key insight:** A missing env var blocks ALL of startup, not just the provider that uses it. The gateway validates all secret refs before accepting connections. For providers you don't actually use, you can set a placeholder value — the gateway starts, and runtime 401s are handled by model fallbacks.

### Agent Model Fallbacks Clobbered by Bare String

**Symptoms:** Doctor warns `agent.model is a bare string with no fallbacks, clobbers defaults`. Agent has no resilience if primary model fails.

**Root cause:**
```json
// agents.defaults.model — has fallbacks:
"model": {
  "primary": "manifest/auto",
  "fallbacks": ["openrouter/owl-alpha", "..."]
}
// agents.list[0].model — bare string, NO fallbacks:
"model": "openrouter/auto"
```

The per-agent bare string replaces the defaults entirely — fallbacks included.

**Fix:** Change from bare string to object:
```json
"model": {
  "primary": "openrouter/auto",
  "fallbacks": [
    "openrouter/minimax/minimax-m2.5:free",
    "openrouter/owl-alpha"
  ]
}
```

### bundledDiscovery in Legacy "compat" Mode

**Symptoms:** Doctor warns `plugins.allow is restrictive but bundled provider discovery is in legacy compatibility mode`. Bundled providers can leak into runtime despite explicit allowlist.

**Fix:** One command:
```bash
openclaw config set plugins.bundledDiscovery '"allowlist"'
openclaw secrets reload
systemctl --user restart openclaw-gateway
```

After this, only plugins listed in `plugins.allow` are loaded.

### No Command Owner Configured

**Symptoms:** Doctor warns `No command owner is configured`. Nobody can run `/diagnostics`, `/config`, `/export-trajectory`, or approve dangerous actions.

**Fix:** Set your account as owner:
```bash
openclaw config set commands.ownerAllowFrom '["telegram:<your-user-id>"]'
openclaw secrets reload
systemctl --user restart openclaw-gateway
```

**Note:** DM pairing only lets someone talk to the bot — it does NOT grant owner privileges.

### Gateway Bound to LAN (Security Concern)

**Symptoms:** Doctor warns `Gateway bound to lan (0.0.0.0)`. Gateway accessible to entire network.

**Fix (if you have Tailscale or reverse proxy):**
```bash
openclaw config set gateway.bind '"loopback"'
openclaw secrets reload
systemctl --user restart openclaw-gateway
```

**Keep LAN if:** you have no Tailscale/SSH tunnel and need direct LAN access for control UI or API consumers on other machines.

### Browser Headless Mode

**Symptoms:** Doctor warns `No DISPLAY or WAYLAND_DISPLAY, browser.headless is false`. Managed browser profiles can't launch.

**Fix:**
```bash
openclaw config set browser.headless true
openclaw secrets reload
systemctl --user restart openclaw-gateway
```

### Bootstrap File Size Warning

**Symptoms:** Doctor warns `AGENTS.md: <N> chars (<P>% of max/file 12,000)`. When the per-file cap is hit, content is silently truncated — the agent loses whatever is at the bottom.

**Fix — raise the cap:**
```bash
openclaw config set agents.defaults.bootstrapMaxChars 20000
openclaw secrets reload
```

**Note:** AGENTS.md's reported size includes ALL auto-included files (SOUL.md, USER.md, IDENTITY.md, etc.), not just the raw AGENTS.md file. The total bootstrap limit (default 60K) is separate from the per-file limit — check both in the doctor output.

### Skills Missing Dependencies

**Symptoms:** Doctor shows `Missing requirements: <skill> (bins: <binary>)`. The skill can't be used because required CLI tools aren't installed.

**Fix:**
```bash
# Identify the package name (NOT always @openclaw/<name>)
npm search <binary-name>

# Install globally
npm install -g <package-name>

# Verify
which <binary-name>
openclaw skills check --agent <id>
```

**Known packages:** `clawhub` (not `@openclaw/clawhub`), `mcporter` (not `@openclaw/mcporter`).

### Manifest.build API Key Validation

**Symptoms:** Every agent request fails over to fallback models, logs show Manifest 401.

**Quick test:**
```bash
curl -s -H "Authorization: Bearer $MANIFEST_API_KEY" \
  -H "Content-Type: application/json" \
  "https://app.manifest.build/v1/models"
```

If response contains `[🦚 Manifest M005] I don't recognize this key` — the key is expired, rotated, or invalid. Get a fresh key from https://app.manifest.build (keys start with `mnfst_`).

### Model Provider Missing from Whitelist

**Symptoms:** Gateway selects the model (logs show `agent model: manifest/auto`) but immediately rejects it with `model not allowed: manifest/auto`. The provider and model are correctly defined in `models.providers`, and the API key validates fine — yet every request fails.

**Root cause:** `agents.defaults.models` acts as a **runtime model whitelist**. Adding a provider to `models.providers` is only half the job — the model must ALSO appear in `agents.defaults.models` to be callable at runtime.

**Fix — add model to whitelist:**
```json
// In agents.defaults.models, add:
"manifest/auto": {
  "alias": "manifest"
}
```

**Pattern:** Every model used by any agent must exist in BOTH `models.providers.<provider>.models[]` AND `agents.defaults.models`. The provider list defines what's available; the agents list defines what's allowed.

### Cron Job Model Override Stripping (Bulk)

**Symptoms:** Many cron jobs have explicit model overrides (e.g., `zai/glm-5-turbo`, `openrouter/owl-alpha`), some pointing to obsolete models. Jobs should inherit the primary model from `agents.defaults.model`.

**Bulk fix — strip `payload.model` from all jobs:**
```bash
python3 -c "
import json
with open('/home/wahid/.openclaw/cron/jobs.json') as f:
    data = json.load(f)
for j in data['jobs']:
    j.get('payload', {}).pop('model', None)
with open('/home/wahid/.openclaw/cron/jobs.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Stripped model from all jobs')
"
```

Then reload + verify:
```bash
openclaw secrets reload
systemctl --user restart openclaw-gateway
openclaw cron list  # all should show '-' for Model
```

## Secrets Management

### Understanding the System

OpenClaw resolves secrets in order:
1. **Env var references** (`${VAR_NAME}` in config) → reads from `~/.openclaw/.env` and system env
2. **SecretRefs** — advanced encrypted/isolated storage

For most setups, the `.env` file pattern is sufficient and matches OpenClaw's own practice.

### Secrets Audit Output

| Code | Meaning |
|------|---------|
| `PLAINTEXT_FOUND` | Secret is in config file plaintext — migrate to env var |
| `REF_UNRESOLVED` | Env var reference has no value — gateway won't start |
| `LEGACY_RESIDUE` | OAuth credentials in auth-profiles.json — out of scope for static migration |
| `SHADOWED` | Multiple sources define the same secret — resolution order matters |

### Adding a Secret (Proper SecretRef — Avoid `${...}`)

The `${VAR_NAME}` string interpolation format (`"apiKey": "${OPENROUTER_API_KEY}"`) technically works at runtime BUT the audit still flags it as `PLAINTEXT_FOUND`. Use the SecretRef object form for a clean audit:

```json
// Before (plaintext OR ${...} string — audit flags PLAINTEXT_FOUND):
"apiKey": "sk-ant...c123..."
"apiKey": "${OPENROUTER_API_KEY}"

// After (SecretRef object — audit clean):
"apiKey": {"source": "env", "provider": "default", "id": "ANTHROPIC_API_KEY"}
```

The `.env` file must contain the value:
```bash
ANTHROPIC_API_KEY=sk-ant...c123...
```

### Full Secrets Migration Workflow (Plaintext → SecretRef)

```bash
# 1. BACKUP before touching secrets
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak-secrets
cp ~/.openclaw/agents/friday/agent/models.json ~/.openclaw/agents/friday/agent/models.json.bak-secrets
cp ~/.openclaw/agents/main/agent/models.json ~/.openclaw/agents/main/agent/models.json.bak-secrets

# 2. Ensure all values are in .env first
#    (Check what's already there: cat ~/.openclaw/.env)

# 3. Replace each plaintext value in openclaw.json with SecretRef object
#    Pattern: {"source": "env", "provider": "default", "id": "VAR_NAME"}
#    Use targeted patch operations — one per secret

# 4. Validate JSON after each edit
python3 -c "import json; json.load(open('/home/wahid/.openclaw/openclaw.json')); print('Valid')"

# 5. Reload and verify
openclaw secrets reload
systemctl --user restart openclaw-gateway
openclaw secrets audit
```

**⚠️ Agent models.json auto-generation:** Agent-level `models.json` files (under `~/.openclaw/agents/<id>/agent/models.json`) are auto-generated by the gateway. They natively use **bare env var names** (e.g., `"apiKey": "ANTHROPIC_API_KEY"`) — no `${...}` wrapping, no SecretRef objects. This is the format the gateway writes and expects. Do NOT add SecretRef objects to these files — they'll cause `REF_UNRESOLVED` errors. If a provider's `apiKey` is a SecretRef object while all others are bare strings, change it to match: `data['providers']['<name>']['apiKey'] = "VAR_NAME"`. After fixing, run `openclaw secrets reload`.

## Gateway Diagnostics

```bash
# Quick status
openclaw gateway status

# Deep dive (includes config warnings, runtime state, probe results)
openclaw gateway status --deep

# Gateway logs (last 50 lines)
journalctl --user -u openclaw-gateway.service -n 50 --no-pager

# Check for crash loop pattern
journalctl --user -u openclaw-gateway.service --no-pager | grep -c "Gateway failed to start"

# Stability bundles (generated on each crash)
ls ~/.openclaw/logs/stability/
```

## Post-Fix Config Inspection

After resolving all doctor issues, run a deep config inspection to catch hidden problems the doctor misses. See `references/config-inspection.py` for the script (run with `python3`).

Key things it catches:
- **Model naming inconsistency** — provider defines `openrouter/openrouter/auto` but whitelist references `openrouter/auto`
- **Agent-level model overrides** — agent has its own `model.primary` that overrides `agents.defaults.model.primary`
- **Orphan whitelist entries** — model in `agents.defaults.models` but NO matching provider in `models.providers`

## Pitfalls

1. **`openclaw config set` requires double-quoted values** — Single-word values work bare, but strings with special characters or arrays need quoting: `openclaw config set key '"value"'`. For arrays: `openclaw config set key '["item1","item2"]'`.

2. **Restart after config changes** — Most config changes require `openclaw secrets reload && systemctl --user restart openclaw-gateway`. Skipping the restart means stale config in the running gateway.

3. **`secrets configure` wizard is provider-aware** — The interactive wizard only recognizes known providers. For custom or lesser-known providers (e.g., Manifest), it may silently skip them. Use direct `.env` file editing instead.

4. **Don't trust `secrets audit` exit code alone** — Exit code 2 means "unresolved" which is expected during configuration. Check the actual output for your target provider.

5. **`config set` can't modify protected paths** — The gateway rejects config patches that touch provider definitions (models, auth profiles, plugin allowlists defined by plugins). These must be edited directly in `openclaw.json`.

6. **Bootstrap per-file limit is per root file** — When AGENTS.md references other files (SOUL.md, USER.md, etc.), the aggregated content counts against AGENTS.md's limit. Raising `bootstrapMaxChars` is simpler than trimming multiple files.

7. **Manifest key validation is a startup block** — A missing/invalid `MANIFEST_API_KEY` blocks gateway startup entirely, not just the Manifest provider. Set any non-empty value to unblock startup; runtime 401s are handled by model fallbacks.

8. **`config set` on arrays replaces, doesn't merge** — Setting `commands.ownerAllowFrom` or `plugins.allow` replaces the entire array. Include all existing values you want to keep.

9. **Model providers need TWO entries** — Adding a model to `models.providers.<name>.models[]` is not enough. The model must ALSO appear in `agents.defaults.models` to be callable at runtime. Gateway logs will show `model not allowed` if the whitelist entry is missing.

10. **Agent-level model config overrides defaults silently** — Fixing `agents.defaults.model.primary` does NOT cascade if an agent has its own `model` block (object or string). The doctor only inspects defaults — agents with explicit model configs must be checked individually. After changing defaults, inspect all agents in `agents.list[]` to verify they aren't pinning old models.

11. **`openclaw cron list` may not show all jobs** — The CLI list output can truncate or omit jobs. For bulk operations (stripping model overrides, disabling, etc.), always inspect `~/.openclaw/cron/jobs.json` directly. The JSON file is the source of truth.

12. **Agent model fallback chain order matters** — If the primary fails, fallbacks are tried in order. A common anti-pattern: setting `manifest/auto` as primary AND placing it in fallbacks behind `openrouter/auto`. This means OpenRouter runs before Manifest — the primary never gets used unless OpenRouter fails first.

13. **apiKey formats are context-dependent — use the right one per file** — Three formats exist and they're NOT interchangeable:
   - **Main `openclaw.json`:** Use SecretRef objects (`{"source": "env", "provider": "default", "id": "VAR_NAME"}`) for a clean secrets audit.
   - **Agent `models.json`:** Use bare env var names (`"ANTHROPIC_API_KEY"`) — NO `${...}` wrapping, NO SecretRef objects. This is the gateway's native auto-generated format.
   - **`${...}` strings:** Work at runtime via env interpolation but the audit flags them as `PLAINTEXT_FOUND`. Avoid in all files — use SecretRef for main config, bare names for agent files.
   Recovery: if `secrets audit` shows `REF_UNRESOLVED` with "regenerate models.json", check that all providers in agent `models.json` use the same bare-name format. See pitfall #14 for the full recovery flow.

14. **Agent models.json uses bare env var names, NOT SecretRefs** — The gateway auto-generates `~/.openclaw/agents/<id>/agent/models.json` with **bare env var names** as `apiKey` values (e.g., `"apiKey": "ANTHROPIC_API_KEY"`). This is the native format — no `${...}` wrapping, no SecretRef objects. All providers in the same file use this same format. A single provider with a SecretRef object (`{"source": "env", ...}`) causes `REF_UNRESOLVED` because the gateway can't resolve it in this context and won't regenerate the file. Recovery: check ALL providers in the file — if one is a SecretRef object while others are bare strings, change it to match: `data['providers']['<name>']['apiKey'] = "VAR_NAME"`. After fixing, `openclaw secrets reload` and re-audit. Do NOT add SecretRef objects to these files — they'll just break again.

15. **Back up before secrets migration** — Copy `openclaw.json` and both agent `models.json` files before touching secrets. Prefix backups with `-secrets` so they're identifiable: `openclaw.json.bak-secrets`. This lets you revert instantly if a migration breaks secret resolution.

## Safety Rules

1. **Always validate JSON** after manual edits: `python3 -c "import json; json.load(open(...)); print('Valid')"`
2. **Run `openclaw secrets reload`** after any secret/config change
3. **Restart gateway** after most config changes
4. **Don't delete auth profiles or provider blocks** without understanding the dependency chain
5. **Backup config before major changes:** `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak`
