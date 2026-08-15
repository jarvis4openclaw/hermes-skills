---
name: hermes-prompt-diagnosis
description: "Diagnose and reduce Hermes agent system prompt token usage. Use when the user asks why token usage is high, why input tokens are large, or how to reduce the per-call prompt budget. Covers the `hermes prompt-size` tool, context-file auto-loading pitfalls, and config-driven fixes."
version: 1.1.0
tags: [hermes, prompt, tokens, optimization, diagnosis, config]
metadata:
  hermes:
    tags: [hermes, prompt, tokens, optimization, diagnosis, config]
    trigger_conditions:
      - "why is token usage so high"
      - "input tokens 50k per call"
      - "reduce system prompt size"
      - "expensive models for simple tasks"
      - "hermes prompt-size"
      - "skip_context_files"
      - "prompt budget too large"
      - "token usage diagnosis"
      - "system prompt too big"
      - "agent log shows large in token count"
      - "context file auto-loading"
      - "reduce per-call prompt"
      - "memory bloat tokens"
---

# Hermes Prompt Diagnosis

## When to Use

Load this skill when the user asks any of:
- "Why is my token usage so high?"
- "Why are my input tokens 50K+ per call?"
- "How do I reduce the system prompt size?"
- "Why is my agent using expensive models for simple tasks?"

Also load when you see agent logs showing large `in=` token counts per API call.

## Not For

- **Creating/editing profiles** → `hermes-profile-setup`
- **Choosing models/providers or API keys** → `hermes-provider-config`
- **Optimizing cron job model selection** → `cron-model-optimization`
- **Memory provider migration (Mnemosyne)** → `hermes-memory-provider-management`
- **General config editing/auditing** → `hermes-config-management`

## Quick Diagnosis

The built-in tool:
```bash
hermes prompt-size
```

Or programmatically:
```bash
cd ~/.hermes/hermes-agent && venv/bin/python3 -c "
from hermes_cli.prompt_size import compute_prompt_breakdown, render_breakdown
print(render_breakdown(compute_prompt_breakdown('cli')))
"
```

This prints a breakdown of the three tiers (stable, context, volatile), the skills index size, memory/user profile, and tool schemas.

## The Three Tiers

| Tier | Contents | Typical Size |
|------|----------|-------------|
| **stable** | SOUL.md, skills index, tool guidance, platform hints | ~25K chars |
| **context** | AGENTS.md/CLAUDE.md/.cursorrules from cwd | 0–20K chars |
| **volatile** | MEMORY.md, USER.md, timestamp | ~3K chars |

**Tool schemas** add ~85K bytes (~21K tokens) for ~58 tools — this is separate from the system prompt but sent on every call.

## The #1 Token Killer: Context-File Auto-Loading

The agent loads AGENTS.md, CLAUDE.md, or .cursorrules from the current working directory. The gateway daemon runs from `~/.hermes/hermes-agent/`, which contains a **57KB AGENTS.md** (the hermes-agent development guide). This gets truncated to 20K chars and injected into every call — adding ~4,600 tokens.

**Detect it:** If the context tier in `hermes prompt-size` is >1KB, auto-loading is active.

**Fix:** Add to `~/.hermes/config.yaml`:
```yaml
agent:
  skip_context_files: true
```

Or via CLI:
```bash
hermes config set agent.skip_context_files true
```

Then restart the gateway:
```bash
hermes gateway run --replace
```

**Alternative:** Set an explicit workspace cwd that doesn't contain AGENTS.md:
```yaml
terminal:
  cwd: /home/wahid
```

## Reference Files

- `references/token-breakdown-session-2026-06-06.md` — Full token breakdown from a real diagnostic session, including `hermes prompt-size` output and agent log excerpts.

## Reading Agent Logs for Token Usage

```bash
grep "agent.conversation_loop" ~/.hermes/logs/agent.log | tail -20
```

Key fields:
- `in=` — input tokens (system prompt + conversation history)
- `out=` — output tokens
- `total=` — combined
- `cache=` — cache hit tokens (shows `cache_ratio` in newer versions)

Watch for `in=` values growing with each turn. If turn 1 starts at 30K+ input tokens, the system prompt is the culprit.

## Manifest.Build Routing Note

When `model: auto` and `provider: custom` with `base_url: https://app.manifest.build/v1`, manifest.build's tier-based auto-router classifies the prompt and selects a model. It typically routes to Nemotron 3 Ultra for complex prompts but can fall through to cheaper models (e.g., Liquid LFM-2.5 1.2B) for trivial ones. This means the same session can hit different models with different per-token costs depending on prompt complexity.

## Pitfalls

1. **`hermes prompt-size` Doesn't Reflect `skip_context_files` From Config** — the `prompt_size` tool constructs a bare `AIAgent` without reading `agent.skip_context_files` from config. It will always show the context tier as if auto-loading is enabled, even when the running agent actually skips it. This is a known gap — use the manual check below to verify the real size.
2. **`python-dotenv` Missing From Install Venv** — the `prompt_size` tool (and other `hermes_cli` modules) import `dotenv`. If the venv doesn't have `python-dotenv` installed, you get `ModuleNotFoundError: No module named 'dotenv'`. Fix: `venv/bin/pip install python-dotenv`.
3. **Config Changes Don't Apply Mid-Session** — `skip_context_files` (and most config changes) are read at session start. The running CLI session won't pick up the change until you start a new `hermes chat`. The gateway needs `hermes gateway run --replace`. New sessions (including gateway-spawned ones) will use the updated config.
4. **Context tier >1KB means auto-loading is active** — AGENTS.md/CLAUDE.md/.cursorrules from cwd get truncated to 20K chars and injected into every call (~4,600 tokens). Detect via `hermes prompt-size`, fix with `agent.skip_context_files: true`, then restart the gateway.
5. **Cron jobs also load AGENTS.md** — cron sessions run from the same hermes-agent directory, so they ALSO load AGENTS.md unless `skip_context_files` is set. This compounds cron cost issues — see `cron-model-optimization` for the full picture.
6. **Tool schemas cost ~21K tokens per call** — ~58 tools × ~1.5KB each is separate from the system prompt but sent on every call. Disable unused toolsets in config to reduce it.
7. **Memory bloat silently grows the volatile tier** — `~/.hermes/memories/MEMORY.md` entries accumulate and are joined by `§`; each entry adds tokens to every call. If Mnemosyne is active, migrate flat-file content via `mnemosyne_remember` and clear the legacy files (see `hermes-memory-provider-management`) — retrieval-based injection only adds relevant context, saving ~800+ tokens per turn.
8. **Skills index scales with skill count** — 58 skills ≈ 16K chars of index. `hermes curator` prunes unused skills if the index grows.
9. **Inferring cost from `in=` alone is misleading** — manifest.build's auto-router (or any cost-based router) may route the same session to different models with different per-token prices. A large `in=` on a cheap model can cost less than a small `in=` on a frontier model. Check which model actually served the call before optimizing.

**To verify the actual prompt size after applying `skip_context_files`**, run a manual check:

```bash
cd ~/.hermes/hermes-agent && venv/bin/python3 -c "
from run_agent import AIAgent
from hermes_cli.config import load_config
from agent.system_prompt import build_system_prompt_parts, build_system_prompt

cfg = load_config()
model = cfg.get('model', {}).get('default', '')
skip = cfg.get('agent', {}).get('skip_context_files', False)

agent = AIAgent(
    model=model, api_key='inspect-only',
    base_url='https://openrouter.ai/api/v1',
    quiet_mode=True, save_trajectories=False,
    platform='cli', skip_context_files=skip,
)
parts = build_system_prompt_parts(agent)
print(f'Stable: {len(parts[\"stable\"]):,} chars')
print(f'Context: {len(parts[\"context\"]):,} chars')
print(f'Volatile: {len(parts[\"volatile\"]):,} chars')
print(f'Total: {len(build_system_prompt(agent)):,} chars')
"
```

### `python-dotenv` Missing From Install Venv

The `prompt_size` tool (and other `hermes_cli` modules) import `dotenv`. If the venv doesn't have `python-dotenv` installed, you'll get:

```
ModuleNotFoundError: No module named 'dotenv'
```

Fix: `venv/bin/pip install python-dotenv`

### Config Changes Don't Apply Mid-Session

`skip_context_files` (and most config changes) are read at session start. The running CLI session won't pick up the change until you start a new `hermes chat`. The gateway needs `hermes gateway run --replace`. New sessions (including gateway-spawned ones) will use the updated config.

## Other Optimization Levers

- **Memory bloat:** `~/.hermes/memories/MEMORY.md` entries accumulate. Each entry is joined by `§`. Run `hermes memory` to review and trim. Better fix if Mnemosyne is active: migrate to Mnemosyne via `mnemosyne_remember`, then clear the flat files — retrieval-based injection only adds relevant context, saving ~800+ tokens per turn (see `hermes-memory-provider-management`).
- **Skills index:** 58 skills → ~16K chars. If unused skills pile up, the index grows. `hermes curator` handles pruning.
- **Tool reduction:** Each tool schema adds ~1.5KB. Disable unused toolsets in config.
- **Model pinning for cron:** See `cron-model-optimization` skill for routing simple cron jobs to local Ollama.
- **Cron jobs are also affected:** Cron jobs run from the same hermes-agent directory, so they ALSO load AGENTS.md unless `skip_context_files` is set. This compounds cron cost issues — see `cron-model-optimization` for the full picture.