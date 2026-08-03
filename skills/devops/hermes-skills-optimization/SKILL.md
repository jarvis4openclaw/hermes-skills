---
name: hermes-skills-optimization
description: Audit and optimize Hermes profile skill trees — enumerate enabled skills, extract sub-skills from bundles, recommend disables by category, validate changes.
version: 1.2.0
tags: [hermes, skills, optimization, profiles, token-cost]
metadata:
  hermes:
    trigger_conditions:
      - "User asks to audit, review, or optimize skills for a profile"
      - "User asks which skills are enabled for a specific profile"
      - "User wants to reduce per-turn context overhead by disabling skills"
      - "User mentions \"skills.disabled\", \"skill headers\", or \"token cost\""
      - "Extract a sub-skill from a bundle like openclaw-imports"
      - "Which skills should I disable"
      - "Skill tree is too large"
      - "Reduce token usage from skills"
---

# Hermes Skills Optimization

Systematic workflow for auditing and optimizing skill trees across Hermes profiles to reduce per-turn context overhead and token costs.

## When to Use

- Profile has 100+ enabled skills and needs trimming
- User wants to reduce token costs for a specific profile
- Bundles like `openclaw-imports` need extraction to top-level
- Cross-profile skill inheritance needs clarification
- A skill appears "missing" but may live in another profile or the shared pool

## Not For

- **Authoring or editing a single skill's content** → use \`hermes-agent-skill-authoring\` or \`writing-great-skills\` instead.
- **Running GEPA self-evolution cycles over the skill tree** → use \`hermes-self-evolution-gepa\` instead (this skill is the manual audit path, not the automated optimizer).
- **Installing third-party skills safely** → use \`agent-skills-cli\` instead.
- **Setting up a new Hermes profile from scratch** → use \`hermes-profile-setup\` instead.
- **Diagnosing why a specific skill misbehaves at runtime** → use \`hermes-prompt-diagnosis\` instead.

## Core workflow

### 1. Enumerate enabled skills for the target profile

```python
# Ground truth: global + hermes-agent + profile-local, minus global disabled
roots = [
    f'{HOME}/skills',
    f'{HOME}/hermes-agent/skills', 
    f'{HOME}/profiles/{profile}/skills',
]

# Flatten all skill IDs (individual, not bundles)
# Walk each root, yield path-qualified IDs like 'devops/proxmox', 'creative/ascii-art'
# Subtract global disabled set
```

**Output**: List of individual skill/sub-skill IDs, grouped by parent category.

### 2. Build disable recommendations by category

Group skills by domain relevance to the profile's purpose:

- **devops/homelab** — infrastructure, routers, servers
- **mlops** — ML training, inference, models
- **creative** — design, art, music novelty
- **apple/*** — macOS-only (skip if server is Linux)
- **gaming** — game servers, mods
- **research/academic** — arxiv, papers, wikis (keep market-research ones)
- **productivity/SaaS** — airtable, linear, teams, etc.
- **sub-agent coding** — claude-code, codex, opencode
- **email redundancy** — himalaya, agentmail-operations
- **media/social novelty** — spotify, songsee, heartmula, nostrx
- **homelab devices** — proxmox, robo-rock, sonoscli, startos

**For each profile**, tailor the "keep" list to its purpose:
- `automation-dashboard` → keep devops, homelab devices
- `income` → keep social-media, research (market), productivity (notion), pepper-*
- `health` → keep health/*, devops/health-ingest, media (transcription), research (llm-wiki)

### 3. Present recommendations to user

Format:
```
### KEEP (relevant to {profile purpose})
- list of skills to keep

### DISABLE — {count} individual skills (grouped)
**category (count):** skill1, skill2, ...
```

Ask user which to keep as exceptions before applying.

### 4. Apply disables to profile-local config

```python
cfg = yaml.safe_load(open(profile_cfg))
cfg['skills'] = {'disabled': sorted(final_disable_list)}
yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
```

**Why profile-local?** Prevents cross-profile contamination. Global disabled affects all profiles.

### 5. Validate and report

- Verify disabled count matches expected
- Confirm kept exceptions are NOT in disabled
- Report: `Enabled before: X -> after: Y (Z% reduction)`

## Pitfalls

1. **`hermes skills disable [name]` doesn't exist** — must edit `config.yaml` directly. Recovery: patch the YAML `skills.disabled` block and validate with a YAML parse.
2. **`find` over the skill tree must exclude vendored dirs** — a bare
  `find ~/.hermes/skills/ -name SKILL.md` also matches SKILL.md files inside
  `nostr-social/scripts/node_modules/` and any npm package that ships one. They
  pollute every skill-tree scan (enumerate, 4-gap audits, GEPA candidate
  selection) with false candidates. Always walk with
  `find . -name SKILL.md -not -path "*/node_modules/*" -not -path "*/.git/*"`.
  Observed in GEPA cycle 32 (2026-08-01): `nostr-social/scripts/node_modules/cocod`
  showed up as a plausible 4-gap candidate until excluded.
3. **Spark `recipe-*` / `persona-*` skills are third-party personas — exclude from 4-gap/optimization scans** — `recipe-unsubscribe-audit`, `persona-project-manager`, and ~30 siblings always top the word-count scan (they lack trigger_conditions / When to Use / Not For / Pitfalls), but they are Spark email personas with `metadata.requires: [use-spark]` and `accessLevel: triage` frontmatter. Evolving them adds no reuse value and risks mangling Spark-required frontmatter. Skip them in candidate selection (same category as `node_modules` vendored skills). Observed in GEPA cycle 33 (2026-08-02) where they dominated the top of the 4-gap list.
4. **Sub-skill names match in disabled list** — `himalaya` disables `email/himalaya`, not just top-level `himalaya`. Recovery: use the path-qualified ID from the enumeration step, not the bare name.
5. **Profile inheritance** — profiles without `skills.disabled` inherit global list; adding profile-level block overrides. Recovery: check the target profile's config before assuming global state applies.
6. **Bundle extraction**: when moving sub-skills from `openclaw-imports/` to top-level:
  1. `cp -rp` sub-dir to `~/.hermes/skills/`
  2. Ensure SKILL.md has `name:` line in frontmatter
  3. `rm -rf` the source sub-dir from bundle
  4. Add to profile `skills.disabled` if you want to disable the bundle version
  Recovery if a sub-skill "doesn't load" after extraction: the `name:` frontmatter line is missing — add it and restart the session.
7. **Orphaned disabled entries** — skills in `config.yaml` disabled list but no directory exists — clean these up or they're no-ops. Recovery: diff the disabled list against `find` results and prune.
8. **`hermes skills list` may not reflect file moves** until next session start — validate via YAML parse instead. Recovery: verify the live tree with `find`, not the CLI cache.
9. **A "missing" skill is often in another profile or the shared pool** — before declaring a skill absent, search `~/.hermes/profiles/<name>/skills/` and `~/.agents/skills/` (symlinked into default). Recovery: `find /home/wahid/.hermes/skills /home/wahid/.agents/skills /home/wahid/.hermes/profiles -name SKILL.md -path "*<skill>*"`; enable via a symlink rather than a copy.
10. **Name collisions after symlinking** — `skill_view` refuses with "Ambiguous skill name". Recovery: namespace the new link (e.g. `code-review-matt`), never delete the user's existing skill to make room.

## Extraction from bundles

When extracting sub-skills from a bundle like `openclaw-imports`:

```bash
# For each kept skill
for s in agent-browser calcom-api outlook ...; do
  cp -rp ~/.hermes/skills/openclaw-imports/$s ~/.hermes/skills/
  rm -rf ~/.hermes/skills/openclaw-imports/$s
done
```

Then validate each has `name:` in SKILL.md:
```python
if not any(re.match(r'^name: ', l) for l in lines):
    lines = ['name: '+name] + lines
```

## Enabling skills across profiles via symlink

Sometimes a skill (or whole third-party pack like `mattpocock/skills`) is installed in one profile but you want it available in the *active* profile too. The cheap, reversible way is a symlink — not a copy.

**Skill install locations (ground truth via `find`, never trust the session "available skills" list alone):**
- `~/.hermes/skills/` — active profile's own tree (top-level + categorized)
- `~/.agents/skills/` — shared pool symlinked into `default` (e.g. `grill-me -> ../../.agents/skills/grill-me`)
- `~/.hermes/profiles/<name>/skills/` — other profiles' private trees (e.g. `income`)

A skill that appears in the session's available-skills list may actually live in a *different* profile or the shared pool, not in `default`. Always locate the real source dir before assuming "it's missing."

**Discovery:**
```bash
# Where does skill X physically live?
find /home/wahid/.hermes/skills /home/wahid/.agents/skills /home/wahid/.hermes/profiles -name SKILL.md \
  -path "*<skill-name>*" 2>/dev/null
```

**Enable (symlink into active profile):**
```bash
SRC=/home/wahid/.hermes/profiles/income/skills/mattpocock/skills/skills/engineering/<skill>
DST=/home/wahid/.hermes/skills/<skill>
[ -e "$DST" ] && echo "already present: $(readlink -f "$DST")" || ln -s "$SRC" "$DST"
```

**Verify the runtime actually resolves it** (this is the real test, not just `ls`):
```
skill_view(name="<skill>")
```

**Revoke:** `rm ~/.hermes/skills/<skill>` — removes only the link, leaves the source untouched.

## Name-collision handling (IMPORTANT)

If a same-named skill already exists in the active tree, `skill_view` refuses with:
`Ambiguous skill name 'X': 2 skills match... Refusing to guess`.
Example hit this session: homegrown `software-development/code-review` vs a newly-linked `code-review`.

**Fix:** namespace the new link (don't rename the source). `ln -s <src> ~/.hermes/skills/code-review-matt`. Both coexist; runtime resolves each unambiguously. Never delete the user's existing skill to make room — namespace instead.

## Validation checklist

After applying disables:
- [ ] Profile config has `skills.disabled` block with correct count
- [ ] Kept exceptions confirmed NOT in disabled list
- [ ] Enabled count reduced as expected
- [ ] No orphaned entries (disabled skills with no directory)
- [ ] Profile-local changes (not global) to avoid cross-profile effects

## Reference files

- `scripts/enumerate_enabled.py` — Python script to walk skill trees and enumerate enabled skills for a profile
- `references/profile-purpose-mapping.md` — Recommended keep/disable patterns for common profile types (automation, income, health, etc.)
