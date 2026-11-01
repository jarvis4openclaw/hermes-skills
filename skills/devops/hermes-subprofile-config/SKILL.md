---
name: hermes-subprofile-config
description: Use when configuring, diffing, or debugging a Hermes sub-profile, whose config does not inherit the default profile.
version: 1.1.0
author: jarvis
license: MIT
metadata:
  hermes:
    tags: [hermes, profiles, config, inheritance]
    related_skills: [hermes-profile-setup, hermes-config-management, hermes-provider-config]
    trigger_conditions:
      - "Hermes sub-profile"
      - "subprofile config"
      - "it works on the default profile"
      - "profile does not inherit config"
      - "profiles config.yaml"
      - "why is this profile missing a setting"
      - "diff profile config"
      - "sub-profile memory provider"
      - "sub-profile toolset"
      - "profile config merge base"
      - "DEFAULT_CONFIG"
      - "hermes profile setup"
      - "which profile is this session using"
---

# Hermes sub-profiles: no config inheritance

## When to Use

- Creating, configuring, or debugging any Hermes sub-profile (`~/.hermes/profiles/<name>/`).
- A behaviour that works on the default profile misbehaves in a sub-profile.
- Checking which context engine, memory provider, provider set, or toolset a sub-profile actually runs.
- Deciding whether a config key must be duplicated into a sub-profile.
- Writing anything (script, cron job, skill) that assumes the default profile's config applies elsewhere.
- Auditing cross-profile drift before running work in a non-default profile.
- Hunting for a credential that exists in one profile but not the one you are running.

## Not For

- **Creating the profile directory and bootstrapping a new profile from scratch** → use `hermes-profile-setup` instead
- **Editing the default profile's `~/.hermes/config.yaml`** → use `hermes-config-management` instead
- **Adding or rewiring provider blocks inside a config** → use `hermes-provider-config` instead
- **CommandCode model pins and pricing** → use `commandcode-provider` instead
- **Restoring a profile after a bad config change** → use `hermes-config-post-audit-recovery` instead
- **Auditing whether profile config leaked into a backup** → use `hermes-backup-audit` instead

## Rule

Proven by measurement (2026-09-16); supersedes earlier assumptions to the contrary.

**The rule:** a sub-profile's config merge base is Hermes's built-in `DEFAULT_CONFIG` overlaid with that profile's **own** `~/.hermes/profiles/<name>/config.yaml`. The default profile's config.yaml is NOT in the chain.

Consequences every time:

- A setting the default profile customized may be **absent or different** in the sub-profile — e.g. `context.engine` falls back to `compressor` while the default runs `hermes-mneme`, `memory.provider` empty vs `mnemosyne`, `platform_toolsets.cli` custom entries absent (silently falling back to the built-in CLI toolset).
- "It works on the default profile" proves nothing for the sub-profile.

## Before any sub-profile work

1. `read_file` the profile's own config.yaml and check the keys the task depends on (context engine, memory provider, providers, toolsets, platform settings).
2. When a sub-profile misbehaves, diff its config against `DEFAULT_CONFIG`, not against the default profile — differences vs the default profile only show what it lacks by design.

Completion criterion: every claim about a sub-profile's model, config, or toolset is backed by a read of that profile's own config.yaml.

## Pitfalls

1. **Extending "it works on default" to a sub-profile** — the default profile's config.yaml is not in the sub-profile's merge chain. Re-verify each depended-on key in the profile's own config.
2. **Diffing against the default profile's config.yaml** — that diff shows only what the sub-profile lacks *by design*. Diff against `DEFAULT_CONFIG` to find real misconfiguration.
3. **Assuming a customized context engine carries over** — `context.engine` falls back to `compressor` in a fresh sub-profile while the default runs `hermes-mneme`. A profile can silently run a different memory architecture.
4. **Assuming the memory provider carries over** — `memory.provider` is empty in a fresh sub-profile vs `mnemosyne` on default; recall will look broken while nothing is actually wrong.
5. **Assuming custom platform toolsets carry over** — `platform_toolsets.cli` custom entries are absent and silently fall back to the built-in CLI toolset, so tools you rely on simply are not exposed.
6. **Assuming credentials carry over** — keys may live only in another profile's `.env`. Scan ALL profiles before declaring a credential missing.
7. **Believing you can switch profiles mid-session** — you cannot; pull the credentials/config across or start a new session under the target profile.
8. **Editing another profile's skills/, plugins/, cron/, or memories/** — each profile owns its own. Do not modify another profile's without explicit instruction.
9. **Assuming cron jobs are shared across profiles** — cron state is per-profile; a job that exists on default does not exist in the sub-profile.
10. **Reading the wrong config path** — `~/.hermes/config.yaml` is the DEFAULT profile only; a sub-profile reads `~/.hermes/profiles/<name>/config.yaml`. Reading the wrong file produces confident nonsense.
11. **Claiming a sub-profile's behavior without reading its config** — the completion criterion requires a read of that profile's own config.yaml for every claim.
12. **Assuming skill/plugin availability matches the default profile** — each profile has its own `skills/` and `plugins/` trees; a skill present on default may simply not exist in the sub-profile.
