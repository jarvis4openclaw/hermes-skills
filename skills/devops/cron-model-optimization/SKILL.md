---
name: cron-model-optimization
description: Optimize model selection for Hermes cron jobs — use local Ollama models for simple tasks, pin per-job model/provider overrides, and avoid expensive manifest.build auto-routing for bash-script-style cron jobs. Use when the user asks about cron job model routing, cron cost reduction, or why a cron job is using an expensive model.
version: 1.4.0
metadata:
  hermes:
    tags: [cron, model-routing, ollama, cost-optimization, manifest-build]
    trigger_conditions:
      - "cron job uses expensive model"
      - "why is my cron using deepseek"
      - "cron model routing"
      - "pin cron job model"
      - "reduce cron cost"
      - "cron job failed model not found"
      - "cron drift guard skipped job"
      - "convert cron to no_agent"
      - "cron timeout tts"
      - "model deprecated in cron script"
---

# Cron Model Optimization

Prevent Hermes cron jobs from burning expensive API credits on trivial tasks. The first question is always: **does this job need an agent at all?** If it's a pure bash script, use `no_agent` mode. If it needs light reasoning, pin to local Ollama. Avoid manifest.build's tiered auto-routing entirely.

## When to Use

- A cron job is consuming expensive API credits on trivial tasks (manifest.build auto-routing to DeepSeek-v4-Pro for a 5-line bash check)
- A cron job failed with "Skipped to prevent unintended spend: global inference config drifted" — the provider-drift guard fired
- A cron job errors with "model not found" / "Request timed out" / `"<model>" does not support thinking` / "Response truncated due to output length limit"
- Migrating cron jobs to cheaper models (`qwen2.5:7b` → `llama3.2:3b` → `google/gemini-2.5-flash`), including model references embedded inside `no_agent` scripts
- Converting pure-script cron jobs to `no_agent` mode for zero LLM cost
- A script-embedded TTS call gets silently killed by the cron scheduler's timeout

## Not For

- **Debugging gateway/messaging platform issues** → use `hermes-gateway-platforms`
- **Non-cron agent model routing in interactive sessions** → see `hermes-provider-config` / `openrouter-model-management`
- **Generic cron failures unrelated to models** (auth, missing files, delivery) → see `cron-noninteractive-guardrails`
- **Building or modifying the cron scheduler itself** → Hermes core development; see `hermes-core-architecture`
- **TTS engine selection or voice cloning** → see `f5-tts-setup` / `kittentts-server` / `voice-cloning-workflow`

## Decision Flow

**Always ask no_agent first — it's the ultimate optimization. ZERO tokens, ZERO model routing.**

```
1. Read the PROMPT. Does the agent do work the script doesn't?
   ├─ Prompt is just "run X, report output"  → no_agent: true  (script handles everything)
   │  └─ See references/no-agent-conversion-guide.md for criteria and examples
   └─ Prompt has conditional logic, notifications, file decisions → Keep agent

2. If agent is needed, pin to cheapest viable model:
   ├─ Simple reasoning (bash output → [SILENT]/report) → `llama3.2:3b` (ollama, 128K) or `google/gemini-2.5-flash` (openrouter, 1M)
   └─ Complex reasoning (web search, multi-step, large context) → `google/gemini-2.5-flash` (openrouter, 1M)

**⚠️ Context window constraint:** Hermes enforces a 64K minimum for agent-mode cron jobs. All Ollama Qwen2.5 models (0.5B–72B) have only 32K context in Ollama and will be rejected. Use `llama3.2:3b` (128K, 2.0 GB) for light agent tasks instead, or pin a cloud model like `google/gemini-2.5-flash`.
```

**Key test:** Read the cron output logs. If the agent's response is just parroting the script output, it's a no_agent candidate. If the agent is making decisions (formatting notifications, choosing between actions, interpreting thresholds), keep it.

## Problem

When a cron job has no explicit `model` or `provider` set (`"model": null, "provider": null` in `jobs.json`), the scheduler falls back to the global `model.default` from `config.yaml`. If that default is `"auto"` with a manifest.build custom provider, manifest's smart tier routing classifies the task and can assign it to the "Complex" tier — routing to expensive models like DeepSeek-v4-Pro for what is essentially a 5-line bash health check.

## Provider-Drift Safety Guard

**When the global inference config changes** (e.g., `provider: openrouter` → `provider: custom`), Hermes now **intentionally skips** any unpinned cron job to prevent unintended spend. The error is explicit:

```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted
since this job was created (provider 'openrouter' -> 'custom'), and this job is
unpinned. No inference call was made.
```

**Mechanism:** Each cron job stores `provider_snapshot` and `model_snapshot` at creation time. The scheduler compares current config against these snapshots. If they differ and the job is unpinned (`model: null, provider: null`), it skips.

**Fix — pin the job AND clear snapshots (both are required):**
```python
import json, shutil, datetime
p = '/home/wahid/.hermes/profiles/<name>/cron/jobs.json'
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
shutil.copy2(p, f'{p}.bak.{ts}')
data = json.load(open(p))
for job in data['jobs']:
    if job['id'] == '<job-id>':        # NOTE: profile cron uses "id", not "job_id"
        job['model'] = 'deepseek/deepseek-v4-pro'
        job['provider'] = 'custom'
        job['provider_snapshot'] = None   # CRITICAL: clear these or
        job['model_snapshot'] = None       # drift guard re-fires next run
json.dump(data, open(p, 'w'), indent=2)
```

**Profile cron storage paths:**
- Default profile: `~/.hermes/cron/jobs.json` — jobs use key `"job_id"`
- Named profiles: `~/.hermes/profiles/<name>/cron/jobs.json` — jobs use key `"id"`
- The `cronjob` agent tool operates on the **default** profile's cron storage. Profile cron jobs must be edited directly via `jobs.json`.

## How Model Resolution Works for Cron Jobs

Priority order (in `cron/scheduler.py`):

1. **Per-job override** — `job.get("model")` from `jobs.json`
2. **Environment variable** — `HERMES_MODEL` env var
3. **Config default** — `model.default` from `config.yaml`
The provider is resolved similarly via `resolve_runtime_provider()` with `job.get("provider")` taking priority.
The provider is resolved similarly via `resolve_runtime_provider()` with `job.get("provider")` taking priority.

## Solution: Pin Model/Provider Per Job

**In-session (preferred):** Use the `cronjob` agent tool directly — it accepts `model` as a dict:

```
cronjob(action='update', job_id='<job-id>', model={"model": "qwen2.5:7b", "provider": "ollama"})
cronjob(action='update', job_id='<job-id>', model={"model": "llama3.2:3b", "provider": "ollama"})

This is the simplest path when doing cron maintenance during a conversation. No Python imports needed.

**From terminal (fallback):** Edit `/home/wahid/.hermes/cron/jobs.json` directly — set `"model"` and `"provider"` for each job. The scheduler reads these fields at execution time.

From Python API (legacy):
```bash
cd ~/.hermes/hermes-agent && python3 -c "
import json
from tools.cronjob_tools import cronjob
result = cronjob(action='update', job_id='<job-id>', model='llama3.2:3b', provider='ollama')
print(json.dumps(json.loads(result), indent=2))
"
```

## Solution: Convert to no_agent (Zero LLM Cost)

For pure script execution (bash health checks, curl pings, process monitors), convert the job to `no_agent` mode. The scheduler runs the script directly and delivers its stdout verbatim — no agent loop, no tokens, no model needed.

**Requirements:**
- Script must be placed in `~/.hermes/scripts/` (NOT a symlink — `validate_within_dir` rejects symlinks)
- Copy the script or use an absolute path inside the scripts dir

**Conversion steps:**

```bash
# 1. Copy the script to ~/.hermes/scripts/
cp /path/to/script.sh ~/.hermes/scripts/script-name.sh

# 2. Update the job to no_agent mode
cd ~/.hermes/hermes-agent && python3 -c "
import json
from tools.cronjob_tools import cronjob
result = cronjob(
    action='update',
    job_id='<job-id>',
    no_agent=True,
    script='script-name.sh',
    prompt=''   # prompt is ignored in no_agent mode
)
print(json.dumps(json.loads(result), indent=2))
"
```

**no_agent delivery semantics:**
- Non-empty stdout → delivered verbatim as the message
- Empty stdout → SILENT (nothing sent, watchdog pattern)
- Non-zero exit / timeout → error alert sent

**no_agent vs. agent mode comparison:**

| Aspect | Agent mode | no_agent mode |
|--------|-----------|---------------|
| LLM invoked | Yes | No |
| Token cost | Per run | Zero |
| Script location | Anywhere (agent runs it) | Must be in ~/.hermes/scripts/ |
| Delivery | Agent decides what to say | Script stdout verbatim |
| Best for | Tasks needing reasoning | Watchdogs, health checks, data collection |

## Which Jobs Should Use Local Models

**Local Ollama models with ≥64K context (e.g. `llama3.2:3b` at 128K) are viable for:** Light agent-mode cron tasks with simple reasoning — read a file, run a check, format a report. The Qwen2.5 family (all sizes) uses 32K context in Ollama and cannot run as agent-mode cron models; they're only usable via `no_agent` scripts that call them through the terminal.

**Use `google/gemini-2.5-flash` on openrouter for:** All other agent-mode cron jobs — 1M context, very low cost.

**For no_agent script-only tasks:** No model needed — set `no_agent: true`.

**Keep on API models:**
- Jobs requiring web search, complex reasoning, or multi-step tool orchestration
- Jobs that need large context windows (>8K tokens)
- Self-evolution or skill optimization pipelines

## Checking Available Ollama Models

```bash
ollama list
```

**ALWAYS verify the model is actually pulled before pinning a cron job to it.** A pinned model that doesn't exist locally will cause a `RuntimeError: Request timed out` — the Ollama server hangs waiting for a model it can't find.

Available models (verify with `ollama list` each session — they can change):
- `llama3.2:3b` (~2.0 GB) — **✅ Default local model**. 128K context. Meets Hermes' 64K minimum. Use for light agent-mode cron jobs.
- (Historical) `qwen2.5:7b` and `qwen2.5:3b-instruct` — both removed from Ollama as of July 2026. Had 32K context, below the 64K minimum for cron agents. Any script still referencing them will fail with `"model '<name>' not found"`.

## Detecting Stale Model References in no_agent and Script-Only Jobs

Script-based cron jobs (`script:` field set, or `no_agent: true`) can **embed model references inside the script itself** — hardcoded in bash variables, curl payloads, or Python strings. These are invisible to the cron scheduler and won't appear in the job's `model` field in `jobs.json`.

### Audit Pattern: Find Stale Script-Embedded Models

```bash
# Find ALL scripts referenced by cron jobs
grep -A5 '"script":' ~/.hermes/cron/jobs.json | grep '"script":' | awk -F'"' '{print $4}'

# Search those scripts for hardcoded model references
for s in $(grep -A5 '"script":' ~/.hermes/cron/jobs.json | grep '"script":' | awk -F'"' '{print $4}'); do
  if grep -n -i 'model.*:' ~/.hermes/scripts/"$s" 2>/dev/null; then
    echo "→ $s has model references"
  fi
done
```

### What to look for inside scripts

- `ollama run <model>` calls
- `"model": "..."` in jq/curl JSON payloads
- `LLM_MODEL=...` or `MODEL=...` environment variables
- Python `model = "..."` strings inside CLI calls to Ollama or API endpoints
- TTS service model names (e.g. Chatterbox voice selection — not a model, but can go stale too)

**Key insight:** The cron job's `model` field and the script's internal model references are **two separate concerns**. When migrating models across cron jobs, check BOTH the job config AND the script body.

### Chronicle of stale-model script failures

| Date | Script | Cause | Fix |
|------|--------|-------|-----|
| 2026-07-28 | `morning-brief-voice.sh` | Ollama `qwen2.5:7b` was removed from local instance; script used it in `curl` payload to `ollama/api/generate` | Replaced with `llama3.2:3b` (128K, already installed) |
| 2026-07-29 | `daily-morning-brief-voice` | **Composite failure** (two independent causes): (1) script was unpinned → model drift guard blocked agent infererence; (2) script itself exited with code 5 due to earlier DNS/network outage, but user saw only the drift-guard error. Neither cause alone fully explains the failure state. | Pinned job to `deepseek/deepseek-v4-flash` on `custom:commandcode`; script-embedded model (`llama3.2:3b`) was already correct from the Jul 28 fix |
| 2026-07-30 | `morning-brief-voice.sh` | **F5-TTS CPU generation exceeded cron timeout.** Cron default timeout is 3600s. F5-TTS with TTS_TIMEOUT=7200 generates ~40 min for a 30s briefing — script was killed at 3600s by the cron scheduler, not the TTS server. Script had been changed from Chatterbox Turbo (fast, ~2-3 min) to F5-TTS (slow, ~40 min) without adjusting the cron timeout. See pitfall #16. | Reverted TTS engine to Chatterbox Turbo. Script uses `{text:..., voice:"mariah", response_format:"opus"}` format to `http://192.168.100.49:8080/v1/audio/speech`. |

### Batch-Audit Workflow (covers both job config and scripts)

```
1. cronjob action='list' — identify ALL jobs, filter by provider/model
2. Separate agent-mode jobs (need model pin) from script-only jobs (may need script audit)
3. For script-only jobs: check cron output logs for "model not found" or Ollama errors
4. Search script bodies for hardcoded model strings
5. Verify each model name actually exists via `ollama list`
```

**Tier guidance:**
| Task Class | Model | Rationale |
|---|---|---|
| Simple agent (read files, report, [SILENT]) | `llama3.2:3b` (ollama) or `google/gemini-2.5-flash` (openrouter) | Local: 128K context, lightweight (2.0 GB). Cloud: 1M context, very low cost. |
| Medium agent (multi-step, web search) | `google/gemini-2.5-flash` (openrouter) | 1M context, low cost |
| Heavy agent (self-evolution, DSPy, GEPA) | `google/gemini-2.5-flash` (openrouter) | Required >=64K context |
| Pure script (no reasoning) | `no_agent: true` | Zero LLM cost, zero model dependency |

## Batch Model Migration Across Cron Jobs

When replacing a local model across all cron jobs (e.g., `qwen2.5:7b` → `llama3.2:3b`), follow this procedure:

1. **Pull the new model first:** `ollama pull <new-model>` — verify with `ollama list`
2. **Identify affected jobs** via `cronjob action='list'` — filter for `provider: ollama` or the old model name
3. **Update agent-mode jobs** (those with `no_agent: false` or no `script` field) using `cronjob(action='update', job_id='...', model={"model": "<new-model>", "provider": "ollama"})` — model selection matters here
4. **Update no_agent jobs** using the same call — the model field is unused by the scheduler but keeping it consistent prevents confusion
5. **Update config files** — see pitfall #13 for the regex-safe approach to distinguish local model names from cloud API paths
6. **Verify:** `cronjob action='list'` and confirm no jobs remain on the old model

**Important:** Do not skip `no_agent` jobs — their model field is dead weight but leaving it pointing to a removed model is misleading for anyone reading the job list.
## Pitfalls

1. **Don't use `--model auto`** — that's the default that triggers manifest.build tier routing. Always pin a specific model.
2. **Ollama must be running** — the cron scheduler will fail if Ollama isn't reachable. Check `ollama list` before configuring.
3. **Verify the model exists before pinning** — `ollama list` to confirm the model is pulled. Pinning to a model not present locally (e.g., `qwen3:8b` after it was removed) causes `RuntimeError: Request timed out` — Ollama hangs waiting for a model it can't find. Always run `ollama list` before updating cron jobs.
4. **`hermes cron edit` CLI does NOT support `--model`/`--provider` flags** — but the `cronjob` agent tool (available in-session) does. Use `cronjob(action='update', job_id='...', model={"model": "llama3.2:3b", "provider": "ollama"})` from within a conversation. For terminal/scripted batch updates, edit `jobs.json` directly or use the Python API.
5. **`no_agent` mode is the ultimate optimization** — for pure script execution, use `no_agent: true`. Zero LLM cost, zero tokens, zero model routing. Always ask: "does this job need an agent?"
6. **Scripts for no_agent must be real files in `~/.hermes/scripts/`** — symlinks are rejected by `validate_within_dir()`. Copy the script, don't symlink.
7. **Clearing model/provider on a no_agent job is not possible via the update API** — the scheduler ignores model/provider when `no_agent` is true, so leftover values are harmless. Don't try to null them out.
8. **Context-file auto-loading ALSO affects cron** — the gateway/agent runs from `~/.hermes/hermes-agent/`, which contains AGENTS.md. If `skip_context_files` is not set, every cron run loads ~18K chars of hermes-agent development guide into the system prompt (~4,600 extra tokens). Set `agent.skip_context_files: true` in config.yaml to eliminate this. See `hermes-prompt-diagnosis` skill for full diagnosis workflow.
9. **no_agent script failures look like model failures** — when `last_status: 'error'` on a `no_agent` job, check the output log. Script failures (missing `.env` files, timeouts, non-zero exit) produce different errors than model routing failures (401, timeout on LLM call). Don't assume every `error` status is a model problem.
10. **`deliver: local` with script failures is silent to the user** — if a no_agent job has `deliver: local`, script failures write to the output dir but don't notify the user. The user only discovers the failure when they check or when other jobs cascade. Prefer `deliver: origin` for critical jobs.
11. **`no_agent` delivers raw stdout verbatim** — if the script outputs HTML tables, the raw HTML lands in chat unformatted. Prefer a plain-text wrapper layer.
12. **64K minimum context window** — Hermes rejects cron agent models below 64K context.
13. **`agent.reasoning_effort: medium/high` crashes Ollama fallback** — When the primary provider fails and the fallback chain reaches an Ollama model (e.g. `llama3.2:3b`), the `reasoning_effort` setting in config.yaml is inherited by the fallback call. Ollama models do not support thinking/reasoning parameters and return HTTP 400. Fixes (prefer order):
    - **Surgical (A — preferred, user-validated):** Set `agent.reasoning_overrides` mapping the offending model to `"none"`: `hermes config set agent.reasoning_overrides '{"llama3.2:3b": "none"}'`. Keeps global reasoning_effort for deepseek/other API models while disabling it only for small local models. User explicitly chose this option over the alternatives.
    - **Blunt (B):** Lower `agent.reasoning_effort` to `low` or `none`.
    - **Structural (C):** Restructure fallback_providers ordering so Ollama never follows API providers.
- **Verification:** Run a cron job that hits the fallback (e.g. `cronjob(action='run', job_id='nightly-memory-maintenance')`). The error `"llama3.2:3b" does not support thinking` should disappear. The job may still fail on output truncation (pitfall #14) — that's a separate fix.
14. **Agent-mode cron output truncation with small local models** — When an agent-mode cron job uses `llama3.2:3b` (or any small model), the model's verbose response can exceed the output buffer limit, producing `RuntimeError: Response truncated due to output length limit`. **Fix: craft the prompt to enforce extreme conciseness.** Include instructions like "Be EXTREMELY concise (3 lines max)" and "If nothing needs changing, respond with exactly [SILENT]". This is a prompt hygiene problem, not a model quality problem.
15. **Config-wide model migration: distinguish local vs cloud model names** — When replacing a local Ollama model across all config files and profiles, config.yaml contains both local Ollama model names (`qwen2.5:7b`) and cloud API paths (`openrouter/qwen/qwen2.5-7b-instruct`). Use regex anchored on YAML context to only match bare model names. Always backup and validate YAML afterwards.
16. **Script-embedded TTS timeouts exceed cron scheduler's timeout** — The cron scheduler enforces a hard timeout (default 3600s for this user). A no_agent or agent-mode script that calls a slow TTS endpoint (e.g. F5-TTS on CPU: ~40 min per briefing) with an internal curl timeout longer than the cron timeout will be **killed by the scheduler** before the TTS finishes, even though the curl's own `--max-time` is set higher. The script appears to hang silently — the scheduler kills it, and the cron error log shows "killed after 3600s" without a helpful TTS error. **Fix options:**
    - **Swap TTS engine** — Use a fast endpoint (Chatterbox Turbo at 8080: ~2-3 min) instead of a slow one (F5-TTS at 7860: ~40 min). This is the simplest fix.
    - **Raise cron timeout** — The cron job's `max_runtime_seconds` field in `jobs.json` can be raised to 7200s (for F5-TTS), but this is wasteful since the scheduler holds the slot.
    - **Async generation** — Have the script spawn a background TTS job, return immediately with [SILENT], and have the background job deliver the result when done. Requires a delivery mechanism independent of the cron session.
    - **Verify script's internal timeout vs cron timeout** — When changing TTS engines in a script, always check BOTH the curl `--max-time` AND the cron scheduler's `max_runtime_seconds`. The smaller value wins and silently kills. The script's `TTS_TIMEOUT` is irrelevant if the cron timeout is shorter.

## Env-Sourced no_Agent Scripts (Shell Wrapper Pattern)

Some no_agent scripts need environment variables stored in `~/.hermes/.env` (e.g. `OPENROUTER_API_KEY` for API calls, `MANIFEST_API_KEY` for Manifest builds). The cron scheduler does NOT source `.env` before running the script — it only sets the script's stdout as the message body. If the script needs `.env` vars, it will fail with "KEY not set" errors.

### Solution: Shell Wrapper in `~/.hermes/scripts/`

Create a `.sh` wrapper that sources `.env` and then executes the real script:

```bash
#!/usr/bin/env bash
set -e
if [ -f "$HOME/.hermes/.env" ]; then
    set -a
    source "$HOME/.hermes/.env"
    set +a
fi
exec python3 "$HOME/.hermes/scripts/my-script.py"
```

Then create the cron job with `script='my-wrapper.sh'` pointing to the wrapper, not the Python script directly.

### Pitfalls
- **`deliver: local` is silent on errors.** If a no_agent script with `deliver: local` fails (missing `.env`, timeout, non-zero exit), the error is saved to the output directory but NOT delivered to any channel. The user only discovers the failure by checking `cronjob action='list'`. For critical scripts, deliver to a gateway platform.
- **Shell wrapper path resolution:** The cron scheduler resolves script paths relative to `~/.hermes/scripts/`. Both the wrapper and the Python script must live there — no symlinks, no absolute paths.
- **`set -a` / `set +a`** is important: `-a` marks all defined/following variables for export so `python3` inherits them, `+a` restores. Without `set -a`, sourced variables stay as shell variables and don't propagate to the subprocess.
- **Order matters:** source `.env` BEFORE calling any tools that need those vars. If the Python script itself imports libraries that check env on import (like `yaml` doesn't but `requests` auth helpers might), ensure the env is sourced before the Python process starts.

## Model-Deprecation Checker Cron Job (no_agent Pattern + Env Sourcing)

A concrete application of the env-sourced no_agent pattern: a nightly job that checks all OpenRouter model references in `config.yaml` against the live API and auto-replaces deprecated models.

### Architecture

```
~/.hermes/scripts/
  ├── check-models.sh        # Shell wrapper (sources .env, calls Python)
  └── check-models.py        # Actual logic
```

### Python Script Pattern

The script should:
1. Fetch `https://openrouter.ai/api/v1/models` with `Authorization: Bearer $OPENROUTER_API_KEY`
2. Load config.yaml and scan: auxiliary sections, fallback_providers, MOA presets, smart_model_routing, x_search
3. For each model not in the available set, call `find_replacement()` using replacement tier lists
4. Backup config.yaml before writing, replace deprecated models, write, re-parse to verify
5. Report results (count of changes, or "no changes needed")

### Replacement Tiers (define in order of preference)

Separate vision, text, reasoning, and tiny/decomposition models so a deprecated vision model isn't
replaced with a text-only model. Match capability class.

```python
TIER_FREE_VISION = [
    "nvidia/nemotron-nano-12b-v2-vl:free",
]
TIER_FREE_TEXT = [
    "nvidia/nemotron-nano-9b-v2:free",
    "poolside/laguna-xs-2.1:free",
    "poolside/laguna-s-2.1:free",
    "poolside/laguna-m.1:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]
TIER_FREE_DECOMP = [
    "meta-llama/llama-3.2-1b-instruct",
    "cohere/north-mini-code:free",
]
TIER_FREE_REASON = [
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
]
```

### Deployed Scripts

The model-deprecation checker is deployed at:
- `~/.hermes/scripts/check-models.py` — Python logic
- `~/.hermes/scripts/check-models.sh` — Shell wrapper sourcing `.env`

Cron job: `model-deprecation-checker` (job_id `d2f0d8e08efa`), runs daily at 1AM Chicago with `no_agent: true`.

### Cron Job Creation

```bash
# cronjob(action='create',
#   name='model-deprecation-checker',
#   schedule='0 1 * * *',
#   no_agent=True,
#   script='check-models.sh')
```

## Related Skills

- **cron-noninteractive-guardrails** — Prevent cron-run failures from non-TTY terminal usage. Complementary: this skill handles model routing; that skill handles execution hygiene.
- **health-ingest** — Demonstrates the no_agent pattern for a weekly data ingestion pipeline AND for GitHub repository management (push via no_agent cron when shell is blocked).

## Reference Files

- `references/no-agent-conversion-guide.md` — Decision criteria, examples, and verification steps for converting jobs to `no_agent` mode
- `references/xlikes-keepalive-case-study.md` — Detailed case study of converting the first job to Ollama
- `references/subagent-terminal-fabrication.md` — Anti-hallucination rationale: no_agent cron is the only reliable way to get real shell output without a user present
- `references/ghost-model-timeout-pattern.md` — Why pinning to an unpulled model causes silent timeouts instead of clear errors
- `references/config-yaml-api-key-trap.md` — Why naive `re.search` on `api_key:` grabs the wrong provider's key, how `${VAR}` references are literal strings, and the env-var-first fix pattern (real incident: X-Likes categorization 401)