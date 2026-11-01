---
name: commandcode-provider
description: Use for CommandCode model pins, pricing lookups, or "model is not supported" errors on the custom:commandcode provider.
version: 1.1.0
author: jarvis
license: MIT
metadata:
  hermes:
    tags: [commandcode, hermes, cron, models, pricing, custom-provider]
    related_skills: [hermes-provider-config, hermes-subprofile-config, cron-model-optimization]
    trigger_conditions:
      - "CommandCode model pin"
      - "model is not supported@this endpoint"
      - "CommandCode pricing"
      - "commandcode provider error"
      - "custom:commandcode"
      - "pin a model on commandcode"
      - "commandcode model list"
      - "CommandCode rates"
      - "commandcode context window"
      - "custom_providers config.yaml"
      - "CommandCode 400"
      - "which models does commandcode offer"
      - "commandcode api key rotation"
---

# CommandCode provider (custom:commandcode)

## When to Use

- Pinning or re-pinning a model on the `commandcode` custom provider — default profile, a sub-profile, or a cron job's `model:` field.
- A model call returns `400 "Model X is not supported@this endpoint"`.
- Looking up CommandCode per-model pricing, context windows, or availability tiers.
- Auditing which model ids the endpoint actually exposes (~90 ids).
- Debugging a cron job that works interactively but fails under its pinned cron model.
- Checking whether the CommandCode API key is a literal or a `${VAR}` reference.

## Not For

- **Adding or rewiring a whole provider block in `~/.hermes/config.yaml`** → use `hermes-provider-config` instead
- **Config that merges differently per profile** → use `hermes-subprofile-config` instead
- **Choosing which model each cron job should run** → use `cron-model-optimization` instead
- **Auditing whether a provider key leaked into the backup repo** → use `hermes-backup-audit` instead
- **Deciding whether a cron alert is a false positive** → use `hermes-cron-false-positive-triage` instead
- **Watching or rotating a non-CommandCode key (e.g. Venice)** → use `venice-key-watchdog` instead
- **Generic provider/toolset import failures not tied to this endpoint** → use `hermes-web-and-mcp-import-failures` instead

## Setup

Custom provider in `~/.hermes/config.yaml` `custom_providers` — endpoint `https://api.commandcode.ai/provider/v1`, key as a `${VAR}` reference, literal API key lives in the file (see memory; rotation unconfirmed).

Invariants — verified facts, not guesses:

- **Model ids carry a provider prefix.** Endpoint ids look like `google/gemini-3.5-flash-lite`, never the bare `gemini-3.5-flash-lite`. A bare pin fails with `400 "Model X is not supported@this endpoint"` (hit by weekly-server-health-check 2026-10-12; fixed by re-pinning with the prefix).
- **There is no pricing API.** `/pricing`, `/costs`, `/usage` on the public API all 404. `/provider/v1/models` returns ~90 ids but no rates.
- **The authoritative price list is scraped, not queried.** It lives inside the Next.js RSC payload of `https://commandcode.ai/docs/resources/pricing-limits`: the `rows` prop of component `$L53` (`ModelPricingTable`), ~52KB of JSON with 94 records — per-model contextWindow, caps, `availability{individual-go|goat|pro|max}`, and `tiers[].rate`.

## Procedure

1. **Pinning a model**: fetch `/provider/v1/models`, copy the id **with its prefix** into the cron/model config, verify with a live probe call (expect 200 + correct tool_call). Never claim a job fixed on config-edit alone.
2. **Needing pricing**: fetch the pricing-limits page, extract the `$L53` / `ModelPricingTable` RSC JSON (~52KB raw), parse `rows`. Record the verification date next to the answer — rates drift.
3. **"Not supported" error**: check for the missing prefix FIRST — before exploring anything else.
4. **Rotating a key**: change the literal in `config.yaml` and the `${VAR}` in the env file together, re-probe, then confirm the value no longer appears verbatim in `hermes dump` output or the backup repo.

Completion criterion: a model pin returning 200 with a correct tool_call on a probe, or a pricing answer carrying rate source + as-of date.

## Pitfalls

1. **Bare model id in the pin** — `gemini-3.5-flash-lite` without the `google/` prefix returns `400 "Model ... is not supported@this endpoint"`. Add the prefix, then re-probe before declaring it fixed.
2. **Assuming a pricing API exists** — `/pricing`, `/costs`, `/usage` all 404 on the public API. Stop probing endpoints and scrape the docs page instead.
3. **Scraping the wrong page shape** — the rates are not in the rendered HTML table; they are in the Next.js RSC payload (`$L53` / `ModelPricingTable`, ~52KB JSON, 94 records). A naive HTML scrape yields nothing.
4. **Quoting a rate without an as-of date** — CommandCode rates drift. Always carry the verification date alongside the number.
5. **Declaring a cron job fixed after a config edit alone** — a config edit is not evidence. Run a live probe (200 + correct tool_call) and say so explicitly.
6. **Treating the key as rotated** — memory records rotation as *unconfirmed*, and `hermes dump` prints the literal verbatim (already committed to the hermes-backups repo). Do not claim rotation without a fresh probe on the new key.
7. **Reading a masked key and concluding it is missing** — `read_file` displays the value as `***`. Read it programmatically before saying the key is absent.
8. **Assuming the default profile's config applies** — sub-profiles do not inherit `~/.hermes/config.yaml`; a pin that works on default may be absent in a sub-profile.
9. **Treating `/models` output as callable** — the endpoint lists ~90 ids but per-model `availability` tiers (individual-go / goat / pro / max) decide what your key can actually call. A listed id can still 4xx.
10. **Editing `config.yaml` without a `.bak` first** — take a `.bak` or timestamped copy before any edit; this file is the single point of failure for every provider.
11. **Probing with the interactive PATH/venv** — cron scripts do not inherit the interactive environment. Reproduce with the pinned interpreter (`/usr/bin/python3`) or the job's own command line.
12. **Confusing the provider API with the CommandCode web app** — the API surface is `api.commandcode.ai/provider/v1`; `/pricing` and `/costs` exist only on the web app, not on the provider API.
