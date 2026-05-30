# OpenRouter Rate Limits Reference

Source: https://openrouter.ai/docs/api/reference/limits (extracted 2026-05-21)

## Account-Level Rate Limits

### Free Model Variants (IDs ending in `:free`)

- **20 requests per minute** per `:free` model
- **Per-day limits:**
  - Under $10 purchased → **50 `:free` requests/day**
  - $10+ purchased → **1,000 `:free` requests/day**
- These limits are per-account (globally governed — extra API keys don't help)
- Negative credit balance causes 402 even on free models

### Paid Models

No documented per-account RPM/RPD limits. Rate is governed by:
1. Per-model upstream capacity (opaque, varies by provider and demand)
2. Cloudflare DDoS protection (blocks dramatically excessive usage)

### Checking Account Limits

```bash
curl -s https://openrouter.ai/api/v1/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | python3 -m json.tool
```

Response shape:
```json
{
  "data": {
    "label": "key-label",
    "limit": null,              // Credit limit, or null if unlimited
    "limit_reset": null,
    "limit_remaining": null,
    "usage": 3.81,              // All-time credits
    "usage_daily": 0.28,
    "usage_weekly": 2.54,
    "usage_monthly": 2.59,
    "is_free_tier": false,      // false = has purchased $10+ credits
    "rate_limit": {             // DEPRECATED — safe to ignore
      "requests": -1,
      "interval": "10s"
    }
  }
}
```

Key fields:
- `is_free_tier: false` → 1000 `:free` requests/day (vs 50)
- `limit: null` → no credit cap
- `rate_limit` → deprecated, does NOT reflect per-model upstream limits

## Upstream Provider Rate Limits

These are NOT exposed by the `/api/v1/key` endpoint. They are:
- Per-model capacity limits on the upstream provider side
- Shared across ALL OpenRouter users (global pool)
- Variable based on demand and provider capacity
- The most common cause of 429s on popular free/zero-cost models

### Error Patterns

**Upstream 429:**
```json
{
  "error": {
    "message": "Provider returned error",
    "code": 429,
    "metadata": {
      "raw": "minimax/minimax-m2.5:free is temporarily rate-limited upstream. Please retry shortly, or add your own key to accumulate your rate limits: https://openrouter.ai/settings/integrations",
      "provider_name": "OpenInference"
    }
  }
}
```

**Account-level 429:**
```json
{
  "error": {
    "message": "Rate limit exceeded: limit_rpd/google/gemini-2.0-flash-thinking-exp-01-21/...",
    "code": 429,
    "metadata": {
      "headers": {
        "X-RateLimit-Limit": "80",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1741305600000"
      }
    }
  }
}
```

### Diagnosis Flow

1. Hit `/api/v1/key` → check `is_free_tier` and usage
2. Make test request → inspect error body
3. `temporarily rate-limited upstream` → upstream issue (retry or switch model)
4. `X-RateLimit-Remaining: 0` → account-level issue (wait for reset)

### Mitigation Options

1. **Fallback providers** — configure in `fallback_providers` in config.yaml
2. **BYOK keys** — add provider API keys at https://openrouter.ai/settings/integrations for dedicated rate limit pool
3. **Use paid variants** — `minimax/minimax-m2.5` (no `:free`) costs ~$0.15/M tokens but bypasses free-tier upstream contention
4. **Retry with backoff** — upstream limits are often transient

## Hermes Fallback Provider Config

```yaml
# In ~/.hermes/config.yaml
fallback_providers:
- provider: openrouter
  model: qwen/qwen3-235b-a22b-2507
- provider: openrouter
  model: mistralai/mistral-small-3.2-24b-instruct
```

Format: list of `{provider, model, base_url?, api_mode?}` dicts.
Hermes tries each in order when the primary fails (429, 5xx, connection errors).
Verify: `hermes fallback list`
