#!/usr/bin/env python3
"""
OpenRouter Top-Tier Free Model Detector
Checks for new frontier free models (≥200k context, reasoning/tool-calling)
and reports them for Hermes Agent integration. Tracks expirations.
Uses curl for reliable HTTP (avoids Python urllib IPv6 issues).
"""

import json
import os
import subprocess
import sys
from datetime import datetime

MODELS_FILE = os.path.expanduser("~/.hermes/openrouter-free-models.json")
OPENROUTER_API = "https://openrouter.ai/api/v1/models"

# Major labs whose free models we care about
FRONTIER_KEYWORDS = [
    "deepseek", "qwen", "llama", "gemma", "nemotron", "gpt-oss",
    "glm", "minimax", "trinity", "ring", "cobuddy", "laguna",
    "dolphin", "hermes", "lfm", "owl"
]

# Indicators of reasoning/tool-calling capability
REASONING_KEYWORDS = ["reasoning", "thinking", "instruct", "coder", "tool", "omni"]

# Minimum context length for "top tier" (200k)
MIN_CONTEXT = 200_000


def load_known_models() -> dict:
    if os.path.exists(MODELS_FILE):
        with open(MODELS_FILE) as f:
            return json.load(f)
    return {"last_checked": None, "models": [], "expired": []}


def save_known_models(data: dict):
    os.makedirs(os.path.dirname(MODELS_FILE), exist_ok=True)
    with open(MODELS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_openrouter_models() -> list:
    """Fetch models via curl (avoids Python urllib IPv6 hang)."""
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "15", "--max-time", "30",
         "-H", "User-Agent: hermes-agent/1.0", OPENROUTER_API],
        capture_output=True, text=True, timeout=35
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr.strip()}")
    data = json.loads(result.stdout)
    return data.get("data", [])


def is_top_tier_free(model: dict) -> bool:
    pricing = model.get("pricing", {})
    if pricing.get("prompt", "0") != "0" or pricing.get("completion", "0") != "0":
        return False

    mid = model.get("id", "").lower()
    ctx = model.get("context_length", 0)

    if not any(kw in mid for kw in FRONTIER_KEYWORDS):
        return False
    if ctx < MIN_CONTEXT:
        return False

    return True


def main():
    known = load_known_models()
    known_map = {m["id"]: m for m in known.get("models", [])}
    expired_map = {m["id"]: m for m in known.get("expired", [])}

    try:
        all_models = fetch_openrouter_models()
    except Exception as e:
        print(f"ERROR: Failed to fetch OpenRouter models: {e}", file=sys.stderr)
        sys.exit(1)

    # Build current top-tier free list
    top_tier = []
    for m in all_models:
        if is_top_tier_free(m):
            mid = m["id"].lower()
            desc = m.get("description", "").lower()
            has_reasoning = any(kw in mid or kw in desc for kw in REASONING_KEYWORDS)
            top_tier.append({
                "id": m["id"],
                "ctx": m.get("context_length", 0),
                "reasoning": has_reasoning,
            })

    top_tier.sort(key=lambda x: x["ctx"], reverse=True)

    current_ids = {m["id"] for m in top_tier}
    previous_ids = set(known_map.keys())

    # New models: in current but not in previous known
    new_models = [m for m in top_tier if m["id"] not in previous_ids]

    # Expired models: were in known, no longer free/top-tier
    now = datetime.now().astimezone().isoformat()
    expired_models = []
    for eid in previous_ids - current_ids:
        prev = known_map[eid]
        expired_models.append({
            "id": eid,
            "ctx": prev.get("ctx", 0),
            "reasoning": prev.get("reasoning", False),
            "first_seen": prev.get("first_seen", "unknown"),
            "expired_at": now,
        })
    # Merge into expired history (avoid duplicates)
    for em in expired_models:
        expired_map[em["id"]] = em

    # Update known models with first_seen timestamps
    updated_known = []
    for m in top_tier:
        if m["id"] in known_map:
            m["first_seen"] = known_map[m["id"]].get("first_seen", now)
        else:
            m["first_seen"] = now
        updated_known.append(m)

    # Save
    known["last_checked"] = now
    known["models"] = updated_known
    known["expired"] = list(expired_map.values())
    save_known_models(known)

    # Output results
    result = {
        "new_models": new_models,
        "expired_models": expired_models,
        "total_top_tier": len(top_tier),
        "known_count": len(previous_ids),
        "expired_total": len(expired_map),
    }

    if new_models and expired_models:
        print(f"NEW_AND_EXPIRED:{json.dumps(result)}")
    elif new_models:
        print(f"NEW_MODELS:{json.dumps(result)}")
    elif expired_models:
        print(f"EXPIRED_MODELS:{json.dumps(result)}")
    else:
        print(f"NO_CHANGE:{json.dumps(result)}")


if __name__ == "__main__":
    main()
