---
name: openrouter-model-management
description: Manage OpenRouter model catalog — add free models, remove paid variants when free equivalents exist, update model lists in models.py and model_switch.py. Use when asked to add models, clean up paid/free duplicates, or update the free model tracker.
version: 1.0.0
metadata:
  hermes:
    tags: [openrouter, model-catalog, free-models, model-switch, openrouter-free-models]
---

# OpenRouter Model Management

Manage the OpenRouter model catalog across the Hermes codebase: the static fallback list in `models.py`, the alias resolution logic in `model_switch.py`, and the free model tracker JSON.

## Key Files

| File | Purpose |
|------|---------|
| `hermes_cli/models.py` | `OPENROUTER_MODELS` static fallback list (paid + free), `_PROVIDER_MODELS` per-provider model lists |
| `hermes_cli/model_switch.py` | `resolve_alias()` — resolves short aliases to model IDs, sorts by version |
| `~/.hermes/openrouter-free-models.json` | Free model tracker maintained by cron job |
| `automation-dashboard/my-app/src/app/api/openrouter-free-models/route.ts` | API endpoint serving free models to the dashboard |

## Reference Files

| File | Content |
|------|---------|
| `references/rate-limits.md` | OpenRouter rate limit docs, 429 diagnosis flow, upstream vs account-level distinction, fallback config format |

## Free Model Criteria

A model qualifies for the free tier if:
- **Price**: prompt = 0 AND completion = 0 on OpenRouter
- **Context**: ≥ 200k tokens
- **Tool calling**: supports OpenAI-style `tools`/`tool_choice` parameters
- **Source**: from a frontier lab (DeepSeek, Qwen, Google/Gemma, Nvidia/Nemotron, MiniMax, Z.AI/GLM, Arcee/Trinity, etc.)

## Workflow: Add a New Free Model

### 1. Check the Tracker

The `openrouter-free-model-detector` cron job (daily at 10 AM) auto-discovers free models and writes them to `~/.hermes/openrouter-free-models.json`. Check if the model is already there:

```bash
python3 -c "
import json
with open('/home/wahid/.hermes/openrouter-free-models.json') as f:
    data = json.load(f)
for m in data['models']:
    if '<model-name>' in m['id'].lower():
        print(json.dumps(m, indent=2))
"
```

### 2. Update `OPENROUTER_MODELS` in `models.py`

**Rule: If a free variant exists for a model family, remove the paid variant from the list.**

The free variant uses the `:free` suffix (e.g., `deepseek/deepseek-v4-flash:free`). Some models are natively free without the suffix (e.g., `z-ai/glm-5.1`, `openrouter/owl-alpha`).

Steps:
1. Check if the base model (without `:free`) exists in `OPENROUTER_MODELS` as a paid entry
2. Remove the paid entry
3. Add the free entry with `"free"` description in the free tier section

**Important**: Only modify `OPENROUTER_MODELS` (the OpenRouter aggregator list). Do NOT add `:free` suffixes to native provider lists (`deepseek`, `minimax`, `tencent-tokenhub`, etc.) — those platforms don't use the `:free` convention.

### 3. Update `_PROVIDER_MODELS` if Needed

If a model exists in a provider's static list (e.g., `_PROVIDER_MODELS["nous"]`) and a free variant now exists on OpenRouter, remove the paid entry from the provider list to avoid duplication. The free variant in `OPENROUTER_MODELS` is sufficient.

### 4. Verify `resolve_alias` Sort Logic

The `resolve_alias()` function in `model_switch.py` sorts matching models by version and prefers `:free` variants. The sort key inserts a `0` for free models before the suffix tiebreaker:

```python
def _sort_key(m):
    base_key = _model_sort_key(m, prefix_for_sort)
    is_free = ":free" in m.lower()
    return base_key[:-2] + (0 if is_free else 1,) + base_key[-2:]
```

This ensures that when you type `/model deepseek`, you get `deepseek/deepseek-v4-flash:free` instead of the paid variant.

### 5. Verify

```bash
# Check OPENROUTER_MODELS
python3 -c "
from hermes_cli.models import OPENROUTER_MODELS
for mid, desc in OPENROUTER_MODELS:
    if '<model-name>' in mid.lower():
        print(f'{mid} ({desc})')
"

# Check the free models API endpoint
curl -s http://127.0.0.1:2999/api/openrouter-free-models | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data['models']:
    if '<model-name>' in m['id'].lower():
        print(json.dumps(m, indent=2))
"
```

## Known Free Models (as of 2026-05-20)

| Model | Context | Reasoning | Latency |
|-------|---------|-----------|---------|
| `openrouter/owl-alpha` | 1.05M | ✓ | 3.5s |
| `deepseek/deepseek-v4-flash:free` | 1.05M | ✗ | N/A |
| `qwen/qwen3-coder:free` | 1.05M | ✓ | N/A |
| `nvidia/nemotron-3-super-120b-a12b:free` | 1.0M | ✗ | 2.2s |
| `google/gemma-4-26b-a4b-it:free` | 262k | ✓ | N/A |
| `google/gemma-4-31b-it:free` | 262k | ✓ | 1.3s |
| `arcee-ai/trinity-large-thinking:free` | 262k | ✓ | 0.7s |
| `qwen/qwen3-next-80b-a3b-instruct:free` | 262k | ✓ | N/A |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256k | ✓ | 1.0s |
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256k | ✗ | 0.6s |
| `minimax/minimax-m2.5:free` | 205k | ✗ | 8.8s |
| `z-ai/glm-5.1` | 203k | ✓ | 1.6s |

## Cron Job

The `openrouter-free-model-detector` cron job runs daily at 10 AM. It:
1. Queries the OpenRouter API for all models
2. Filters for free models (prompt=0, completion=0, tools support, ≥200k context)
3. Updates `~/.hermes/openrouter-free-models.json`
4. Reports new/expired models

The Automation Dashboard Free Models page reads from the tracker JSON via its API route.

## Pitfalls

1. **Don't add `:free` to native provider lists** — The `:free` suffix is an OpenRouter convention. Native providers (deepseek, minimax, tencent-tokenhub, etc.) have their own model ID formats.
2. **Don't remove paid models without free equivalents** — Models like `anthropic/claude-opus-4.7`, `openai/gpt-5.5`, `moonshotai/kimi-k2.6` have no free variants and should stay.
3. **Check both `OPENROUTER_MODELS` and `_PROVIDER_MODELS`** — A model might appear in both. Remove from `_PROVIDER_MODELS` if the free variant is in `OPENROUTER_MODELS`.
4. **The tracker JSON is the source of truth for the dashboard** — The Automation Dashboard reads from `~/.hermes/openrouter-free-models.json`, not from `models.py`. Both must be kept in sync.
5. **Test the sort key** — After changes, verify that `resolve_alias` picks the free variant: the sort key inserts `(0,)` for free models before the suffix tiebreaker.

## Rate Limit Debugging

### Two Layers of 429s

OpenRouter has two distinct rate limit layers. Diagnosing 429s requires distinguishing which one you're hitting:

| Layer | Error pattern | Cause | Fix |
|-------|--------------|-------|-----|
| **Account-level** | `Rate limit exceeded: limit_rpd/...` with `X-RateLimit-Limit`/`X-RateLimit-Remaining` headers | Your OpenRouter account hit the per-day/per-minute cap for `:free` models | Wait for reset, or buy $10+ credits to raise `:free` daily limit from 50→1000 |
| **Upstream provider** | `Provider returned error` + `is temporarily rate-limited upstream` | The upstream model provider (MiniMax, Z.AI, etc.) throttled OpenRouter's shared capacity | Retry shortly, add BYOK key, or use a paid variant / different model |

**Account-level `:free` limits (from docs):**
- 20 requests/minute per `:free` model
- 50 requests/day if under $10 purchased; 1000/day if $10+ purchased
- Negative credit balance causes 402 even on free models

**Upstream limits are opaque** — OpenRouter doesn't expose per-model upstream RPM. The `/api/v1/key` endpoint only shows account-level info (`is_free_tier`, credit usage). Upstream capacity is shared across ALL OpenRouter users, so popular free models (owl-alpha, minimax-m2.5:free) frequently 429 during peak hours.

### Diagnosis Procedure

1. Check account status: `curl -s https://openrouter.ai/api/v1/key -H "Authorization: Bearer $KEY" | python3 -m json.tool`
2. Make a test request. If the error says `temporarily rate-limited upstream`, it's upstream — not your account.
3. If `X-RateLimit-Remaining: 0` appears in error metadata, it's account-level.

### Mitigation: Fallback Providers

Configure `fallback_providers` in `~/.hermes/config.yaml` so Hermes auto-retries on a different model when the primary 429s:

```yaml
fallback_providers:
- provider: openrouter
  model: qwen/qwen3-235b-a22b-2507   # cheap MoE, good reasoning + tool calling
- provider: openrouter
  model: mistralai/mistral-small-3.2-24b-instruct  # proven tool calling
```

Key criteria for fallback model selection:
- **Paid model** (not `:free`) — avoids the upstream shared-capacity trap
- **Tool calling support** — must have `tools` + `tool_choice` in `supported_parameters`
- **Low cost** — under $0.10/M input tokens; total spend stays under pennies/day
- **Different upstream provider** — so the same outage doesn't affect both primary and fallback
- **32k+ context** — enough for agent conversations

Verify with: `hermes fallback list`

### Mitigation: BYOK Keys

For heavily used providers, adding your own API key (BYOK) at https://openrouter.ai/settings/integrations gives you a dedicated rate limit pool instead of sharing with all OpenRouter users.

### Cheap Fallback Candidates (verified 2026-05-21)

| Model | Input/M | Output/M | Context | Tool Calling | Notes |
|-------|---------|----------|---------|-------------|-------|
| `qwen/qwen3-235b-a22b-2507` | $0.071 | $0.100 | 262k | ✓ | 235B MoE (22B active), strong reasoning |
| `mistralai/mistral-small-3.2-24b-instruct` | $0.075 | $0.200 | 128k | ✓ | Battle-tested tool calling |
| `google/gemma-3-27b-it` | $0.080 | $0.160 | 131k | ✓ | Google quality, 16k max output |
| `openai/gpt-oss-20b` | $0.030 | $0.140 | 131k | ✓ | Reasoning support, 131k output |
| `nvidia/nemotron-3-nano-30b-a3b` | $0.050 | $0.200 | 262k | ✓ | Reasoning support, 228k max output |

All verified with live tool-call test against OpenRouter API (May 2026).
