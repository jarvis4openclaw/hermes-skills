---
name: hermes-provider-config
description: Manage LLM provider configuration for Hermes Agent, including setting primary providers, managing API keys, updating plugins, and optimizing memory providers.
version: 1.1.0
metadata:
  hermes:
    trigger_conditions:
      - "change LLM provider in Hermes"
      - "set primary provider"
      - "provider not showing in /model picker"
      - "add a custom provider (Manifest, CommandCode, Ollama)"
      - "providers vs custom_providers format"
      - "API key not working for a provider"
      - "update Hermes plugins"
      - "optimize Mnemosyne memory provider"
      - "configure env_passthrough / environment variables for Hermes"
      - "canonical vs custom provider confusion"
      - "restart Hermes after config change"
---

# Hermes Provider Configuration

Manage LLM provider configuration for Hermes Agent, including setting primary providers, managing API keys, updating plugins, and optimizing memory providers.

## When to Use This Skill

- Changing LLM provider configuration in Hermes
- Distinguishing between similarly named providers (e.g., Manifest vs CommandCode)
- Promoting a custom provider to primary provider status
- Diagnosing why a provider doesn't appear in the `/model` picker (see `references/picker-diagnostics.md`)
- Updating Hermes plugins
- Optimizing Hermes memory provider (Mnemosyne) settings
- Configuring environment variables for Hermes

## Not For

- **Setting up a brand-new Hermes profile / first-time install** → use `hermes-profile-setup` instead.
- **Tuning which model each cron job uses** → use `cron-model-optimization` instead (provider config only matters when a job needs a non-default provider).
- **Backing up / sanitizing the config file** → use `hermes-config-backup` instead.
- **Recovering settings after a Hermes update wiped them** → use `hermes-config-post-audit-recovery` instead.
- **General Hermes config edits (UI, toolsets, gateway platforms)** → use `hermes-config-management` instead — this skill is provider-scoped only.

## Provider Configuration Hierarchy

Hermes config.yaml has three provider-related sections:

1. **`providers:`** - First-class providers referenceable by `model.provider` (MUST be dict format)
2. **`custom_providers:`** - Provider definitions not directly referenceable as primary (list format)
3. **`fallback_providers:`** - Provider failover chain for when primary fails

To use a custom provider as primary:
- Add it to the `providers:` section as a **dict** (not a list) — see the `providers:` Format pitfall below
- ALSO add it to `custom_providers:` as a **list** — both code paths are live and feed different picker surfaces
- Set `model.provider` to the provider name
- Set `model.base_url` to the provider's base URL
- Set `model.default` to the desired model (or "auto" if provider supports it)
- Ensure required API keys are available via environment variables

## Common Provider Patterns

### CommandCode
```yaml
# In providers: (dict format — REQUIRED for picker visibility)
providers:
  commandcode:
    name: commandcode
    base_url: https://api.commandcode.ai/provider/v1
    api_key: ${COMMANDCODE_API_KEY}
    models:
      - name: deepseek/deepseek-v4-flash
        model: deepseek/deepseek-v4-flash

# ALSO in custom_providers: (list format — REQUIRED for compat path visibility)
custom_providers:
  - name: commandcode
    base_url: https://api.commandcode.ai/provider/v1
    api_key: ${COMMANDCODE_API_KEY}
    models:
      - deepseek/deepseek-v4-flash
      - moonshotai/Kimi-K3
      # ... full model list
```

### Manifest
```yaml
# In providers: (dict format)
providers:
  manifest:
    name: manifest
    base_url: https://app.manifest.build/v1
    api_key: ${MANIFEST_API_KEY}
    models:
      - name: auto
        model: auto

# ALSO in custom_providers: (list format)
custom_providers:
  - name: manifest
    base_url: https://app.manifest.build/v1
    api_key: ${MANIFEST_API_KEY}
    models:
      - auto
```

### OpenRouter (typically automatic)
OpenRouter is a canonical built-in provider — do NOT define it in `providers:` or `custom_providers:`. Just add `OPENROUTER_API_KEY` to `~/.hermes/.env` and it appears in the picker with its full curated catalog automatically.

### Ollama
```yaml
# In providers: (dict format)
providers:
  ollama:
    name: ollama
    base_url: http://127.0.0.1:11434/v1
    api_key: not-needed
    models:
      - name: llama3.2:3b
        model: Llama 3.2 3B

# ALSO in custom_providers: (list format)
custom_providers:
  - name: ollama
    base_url: http://127.0.0.1:11434/v1
    models:
      - llama3.2:3b
```

## Plugin Management

### Updating Plugins
```bash
# Navigate to plugin directory
cd ~/.hermes/plugins/<plugin-name>

# Fetch latest tags
git fetch --tags

# Check current version
git describe --tags

# Pull updates
git pull

# Verify new version
git describe --tags
```

### Key Plugins to Keep Updated
- **web-search-plus**: Brings research provider quorum, enhanced result provenance
- **hermes-lcm**: Adds SQLite WAL retry, tool output externalization, token-capped fresh tail
- **mnemosyne-dashboard**: Adds MEMORIA table browser, runtime diagnostics tab

### Enabling/Disabling Plugins
```bash
# Disable conflicting plugins
hermes plugins disable <plugin-name>

# Enable plugins (may require --allow-tool-override for tool override permissions)
hermes plugins enable <plugin-name> [--allow-tool-override]
```

## Memory Provider (Mnemosyne) Optimization

### Known Issue: Mnemosyne Plugin Non-Functional
As of 2026-07-27, the Mnemosyne plugin at `~/.hermes/plugins/mnemosyne` is a broken symlink to a non-existent venv package. No `mnemosyne_remember` tool is registered. The `memory.provider: mnemosyne` config setting points to a non-functional backend. **Workaround**: Use the legacy `MEMORY.md` flat-file memory (via the `memory` tool) until the Mnemosyne installation is repaired.

### Environment Variables
Add to `env_passthrough` in config.yaml:
- `MNEMOSYNE_LLM_ENABLED`
- `MNEMOSYNE_RECALL_DIAGNOSTICS`

Set in current session:
```bash
export MNEMOSYNE_LLM_ENABLED=1
export MNEMOSYNE_RECALL_DIAGNOSTICS=1
```

### Regular Maintenance
```bash
# Consolidate memories (run periodically)
mnemosyne_sleep(all_sessions=true)

# Diagnose and repair vector storage
mnemosyne diagnose --repair-vec_working
```

### Monitoring
Watch for:
- Working memory vector status (should show vectors after LLM processing)
- Hygiene noise percentage (aim to keep below 50%)
- Orphan gids count (indicates metadata cleanup opportunities)
- Session consolidation statistics

## Step-by-Step Procedures

### Configuring a New Primary Provider
1. **Backup current config**:
   ```bash
   cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d-%H%M%S)
   ```

2. **Determine provider details**:
   - Identify desired primary provider (e.g., CommandCode)
   - Obtain required API key
   - Verify base URL and model naming conventions

3. **Update providers section**:
   - Add provider to `providers:` if not present
   - Configure `base_url`, `api_key`, and `models` appropriately

4. **Update model section**:
   ```yaml
   model:
     provider: <provider-name>
     base_url: <provider-base-url>
     default: <default-model-or-auto>
     # ... other settings
   ```

5. **Verify environment variables**:
   - Ensure API key available in environment
   - Add to `env_passthrough` if needed for subprocess access

6. **Restart Hermes**:
   - Restart the Hermes agent for changes to take effect

7. **Verify functionality**:
   - Check `hermes model info` shows correct provider
   - Test with a simple query
   - Confirm model responses are working

### Updating Key Plugins
1. **web-search-plus**:
   ```bash
   cd ~/.hermes/plugins/web-search-plus
   git fetch --tags
   git pull
   # Review CHANGELOG.md for v3.x changes
   ```

2. **hermes-lcm**:
   ```bash
   cd ~/.hermes/plugins/hermes-lcm
   git fetch --tags
   git pull
   # Review CHANGELOG.md for v0.20.0 changes
   ```

3. **mnemosyne-dashboard**:
   ```bash
   cd ~/.hermes/plugins/mnemosyne-dashboard
   git fetch --tags
   git pull
   # Review CHANGELOG.md for v0.14.0 changes
   ```

### Optimizing Mnemosyne Memory
1. **Enable advanced features**:
   - Edit `~/.hermes/config.yaml`
   - Add to `env_passthrough`:
     ```yaml
     env_passthrough:
       - MNEMOSYNE_LLM_ENABLED
       - MNEMOSYNE_RECALL_DIAGNOSTICS
     ```
   - Apply to current session:
     ```bash
     export MNEMOSYNE_LLM_ENABLED=1
     export MNEMOSYNE_RECALL_DIAGNOSTICS=1
     ```

2. **Run consolidation**:
   ```bash
   mnemosyne_sleep(all_sessions=true)
   ```

3. **Run diagnostics and repair**:
   ```bash
   mnemosyne diagnose --repair-vec_working
   ```

4. **Review results**:
   - Check working memory vector status
   - Review hygiene statistics
   - Verify orphan reduction

## Pitfalls

1. **Provider confusion** — Mixing up similarly named providers (e.g., Manifest vs CommandCode) silently routes requests to the wrong endpoint. Always verify `base_url` and provider purpose before editing: Manifest is `https://app.manifest.build/v1` (model routing service), CommandCode is `https://api.commandcode.ai/provider/v1` (direct model access).
2. **Incorrect provider placement** — Adding a provider only to `custom_providers:` instead of `providers:` makes it unavailable as primary (`model.provider` setting is ignored). Ensure the provider appears in `providers:` as a dict with proper configuration.
3. **Canonical vs custom provider confusion** — Defining canonical providers (openrouter, anthropic, etc.) in `providers:` or `custom_providers:` is redundant and can conflict; canonical providers already have built-in auth flows and model catalogs. Only define custom endpoint providers in those sections — canonical ones need only an API key in `.env`. Rule of thumb: if it's in `CANONICAL_PROVIDERS` (see `hermes_cli/models.py`), don't add it to either section.
4. **`providers:` as a list instead of a dict** — The model picker calls `providers_dict_to_custom_providers(config.get("providers"))`, which checks `isinstance(providers_dict, dict)` and returns `[]` for lists — a list-format `providers:` section is invisible to the picker. Mitigation: if the provider is ALSO in `custom_providers:` (list, which IS read), the picker sees it via `get_compatible_custom_providers()` — but only because of the duplicate. Best practice: define custom endpoint providers in BOTH places (dict in `providers:`, list in `custom_providers:`) and keep name/base_url/api_key/model list in sync.
5. **Stale config after changes** — Config is snapshotted at process startup; the running gateway/desktop process holds the old config until restarted. After edits, restart (`/restart` in gateway sessions, or relaunch the desktop app), then verify with the diagnostic script.
6. **Missing environment variables** — API keys not added to `env_passthrough` are unavailable to subprocesses (cron jobs, subagents), causing auth errors in background processes. Add required variables to `env_passthrough` in config.yaml.
7. **Forgetting to restart** — Configuration or plugin changes don't take effect until Hermes restarts; old behavior persists after updates. Always restart after config or plugin changes.
8. **Blind plugin updates** — Updating plugins without checking for breaking changes risks configuration incompatibilities and lost functionality. Always review the CHANGELOG before updating.
9. **Tool override permissions** — Enabling plugins like `rtk-rewrite` without proper permissions fails to override built-in tools. Use `--allow-tool-override` when enabling such plugins.
10. **Neglecting memory maintenance** — Infrequent consolidation degrades performance (slow responses, high memory usage). Run `mnemosyne_sleep` regularly (weekly recommended).
11. **Ignoring hygiene warnings** — High noise ratios or secret flags indicate problems (performance degradation, potential credential exposure). Investigate and address root causes when warnings appear.
12. **Non-functional Mnemosyne plugin symlink** — As of 2026-07-27, the Mnemosyne plugin at `~/.hermes/plugins/mnemosyne` was a broken symlink to a non-existent venv package; `memory.provider: mnemosyne` pointed at a non-functional backend. If `mnemosyne_remember` is not registered, verify the symlink target exists before blaming provider config — the workaround is the legacy `MEMORY.md` flat-file memory until installation is repaired.

## Verification Steps

### After Provider Changes
1. **Check active provider**:
   ```bash
   hermes model info
   # Should show correct provider in output
   ```

2. **Validate plugin status**:
   ```bash
   hermes plugins list
   # Confirm expected plugins are enabled/disabled
   ```

3. **Confirm memory settings**:
   - Check `mnemosyne_dashboard_status` output
   - Look for `MNEMOSYNE_LLM_ENABLED` and `MNEMOSYNE_RECALL_DIAGNOSTICS` as "set"

4. **Test end-to-end functionality**:
   ```bash
   # Simple test query
   echo "test" | hermes
   # Should return successful response
   ```

### After Plugin Updates
1. **Verify versions**:
   ```bash
   hermes plugins list --plain --no-bundled
   # Check versions match expected updates
   ```

2. **Check for errors**:
   - Review Hermes logs for plugin loading issues
   - Verify no missing dependency errors

3. **Test relevant functionality**:
   - For web-search-plus: Test web search and extraction
   - For hermes-lcm: Test context management
   - For mnemosyne-dashboard: Verify dashboard loads and shows new tabs

### After Mnemosyne Optimization
1. **Confirm environment variables**:
   - Check `mnemosyne_diagnose` output shows variables as "set"
   - Verify `MNEMOSYNE_LLM_ENABLED` and `MNEMOSYNE_RECALL_DIAGNOSTICS` are active

2. **Validate consolidation results**:
   - Review `mnemosyne_sleep` output for:
     - Number of sessions processed
     - Items consolidated
     - Summaries created

3. **Check vector status**:
   - After LLM usage, verify `memories diagnose` shows:
     - Working memory has vectors (not "no_vectors")
     - Episodic memory vector count increased appropriately

4. **Monitor performance**:
   - Observe improved recall relevance
   - Check for reduced latency in memory-intensive operations