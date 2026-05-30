#!/usr/bin/env python3
"""Post-fix config inspection — catches issues the doctor misses.

Run after resolving all doctor findings to check for:
  - Model naming inconsistency (provider vs whitelist)
  - Agent-level model overrides that override defaults
  - Orphan whitelist entries (no matching provider)
  - Unused provider models (not in whitelist)
  - Cron job model overrides still present
"""

import json, os

CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
CRON = os.path.expanduser("~/.openclaw/cron/jobs.json")

with open(CONFIG) as f:
    c = json.load(f)

print("=" * 60)
print("CONFIG INSPECTION")
print("=" * 60)

# --- Model Whitelist vs Provider Models ---
whitelist = set(c.get("agents", {}).get("defaults", {}).get("models", {}).keys())
provider_models = set()
for name, p in c.get("models", {}).get("providers", {}).items():
    for m in p.get("models", []):
        provider_models.add(f"{name}/{m['id']}")

orphan = provider_models - whitelist
unused = whitelist - provider_models

print(f"\nWhitelisted: {len(whitelist)}  |  Provider-defined: {len(provider_models)}")
if orphan:
    print(f"⚠️  Provider models NOT whitelisted (can't be used): {orphan}")
if unused:
    print(f"⚠️  Whitelisted models with NO provider: {unused}")
if not orphan and not unused:
    print("✓ Whitelist and providers match")

# --- Primary Model Validation ---
primary = c.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "")
fallbacks = c.get("agents", {}).get("defaults", {}).get("model", {}).get("fallbacks", [])

print(f"\nPrimary: {primary}")
if primary not in whitelist:
    print(f"🔴 PRIMARY NOT IN WHITELIST: {primary}")
else:
    print("✓ Primary in whitelist")

print(f"Fallbacks: {fallbacks}")
missing_fb = [f for f in fallbacks if f not in whitelist]
if missing_fb:
    print(f"🔴 Fallbacks NOT in whitelist: {missing_fb}")
else:
    print("✓ All fallbacks in whitelist")

# --- Agent-Level Model Overrides ---
print(f"\nAgent configs:")
for agent in c.get("agents", {}).get("list", []):
    name = agent.get("id", "?")
    model = agent.get("model", {})
    if isinstance(model, str):
        print(f"  {name}: model={model}  ⚠️  BARE STRING — no fallbacks")
    elif isinstance(model, dict):
        ap = model.get("primary", "?")
        af = model.get("fallbacks", [])
        differs = ap != primary or af != fallbacks
        flag = " ⚠️  DIFFERS FROM DEFAULTS" if differs else ""
        print(f"  {name}: primary={ap}  fallbacks={af}{flag}")

# --- Cron Model Overrides ---
if os.path.exists(CRON):
    with open(CRON) as f:
        cron_data = json.load(f)
    jobs = cron_data.get("jobs", [])
    overrides = [(j["id"][:8], j.get("name", "?"), j.get("payload", {}).get("model", ""))
                 for j in jobs if j.get("payload", {}).get("model")]
    if overrides:
        print(f"\n⚠️  Cron jobs with model overrides ({len(overrides)}):")
        for jid, name, model in overrides:
            print(f"  {jid}: {name} → {model}")
    else:
        print(f"\n✓ No cron model overrides ({len(jobs)} jobs)")

print()
