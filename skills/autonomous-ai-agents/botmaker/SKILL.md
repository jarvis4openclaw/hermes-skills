---
name: botmaker
description: "Create or re-spec a specialist Hermes bot profile: interview, signed SOUL draft, scaffold with pinned brain and file-level skill links, certify in the child's Bot Chat, then write the vault note."
version: 0.3.0
author: techjanitor
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, bots, profiles, soul]
    category: autonomous-ai-agents
    related_skills: [hermes-agent, hermes-profile-setup, hermes-agent-skill-authoring, kanban-worker]
    trigger_conditions:
      - "create a bot"
      - "make a new specialist bot"
      - "new bot profile"
      - "hermes profile create"
      - "draft a SOUL"
      - "SOUL rewrite"
      - "certify the bot"
      - "bot roster"
      - "vault bot note"
      - "share a skill with another profile"
      - "profile skill symlink"
      - "the bot's DM acked and vanished"
      - "pin the bot's model / brain"
      - "no-alias preflight"
---

# Botmaker

Design, scaffold, certify, and document specialist Hermes bots. Load this skill on every in-scope question. You draft; the child earns. Seeding files is not a bot.

Details: `references/soul-craft.md` (SOUL + human gate), `references/process.md` (mechanics), `references/vault.md` (vault conventions). Shared-skill linker: `scripts/link_skill_tree.py`. Drift tripwire: `scripts/drift_check.py`. Brain selection: `scripts/cc_model_pick.py` (rank a provider catalog by score-per-dollar for a lane — handles the WAF User-Agent trap and promo strikethroughs), `scripts/cc_promo_check.py` (watch a promo price; exit 0 cheap / 1 lapsed / 2 check-failed).

## When to Use

- Your human wants a new specialist bot, or a SOUL drafted for one — in chat, or as a task card assigned to `botmaker` (if your fleet dispatches work by kanban). A card carrying a human-signed SOUL spec satisfies the human gate.
- An existing specialist bot's identity/job/voice is wrong and needs a SOUL rewrite (human gate)
- `bots/` in the vault needs a specialist note, roster row, or `making-bots.md` changelog
- A shared skill is about to be copied into a profile (stop; symlink files instead)

## Not For

- Standing up a plain (non-specialist) profile, providers or model config → use `hermes-profile-setup` instead
- Authoring a brand-new skill from scratch → use `hermes-agent-skill-authoring` instead
- Evolving or auditing existing skills → use `hermes-self-evolution-gepa` / `hermes-skills-optimization` instead
- Hermes core internals, config or provider plumbing → use `hermes-core-architecture`, `hermes-config-management` or `hermes-provider-config` instead
- Dispatching work between bots by kanban → use `kanban-orchestrator` or `kanban-worker` instead
- Operating the inference server, ComfyUI or any other service → use that service's own skill (`self-hosted-app-deployment`) instead
- Rewriting the default `~/.hermes/SOUL.md`, or spawning `botmaker-2`. `@hermes` is not the bot coordinator — you are.

## Prerequisites

- Hermes CLI (`hermes profile create --help`)
- Canonical skills live under `~/.hermes/skills/` (default Hermes home), **not** `$HERMES_HOME/skills` when you are the botmaker profile
- Vault: `~/wiki/` (see `references/vault.md`)
- Human guide, fleet roster, changelog: vault `bots/making-bots.md` (create it on first ship). Method lives here only; fleet state lives there only — patch a lesson's one owner and log one changelog line.

## How to Run

1. Interview. Refuse to scaffold until job / independence failure / not-list are sharp. See Procedure.
2. Draft a one-screen SOUL (`references/soul-craft.md`). Stop. Your human signs it.
3. Scaffold (`references/process.md`). **Alias preflight first.** `--no-skills`, pin the brain, file-level skill links, USER.md lockstep sentence if the skill is shared.
4. Kickoff in the **child's** Bot Chat. Do not babysit its tools. Do not write its `MEMORY.md`.
5. After certification: vault note + roster row (`references/vault.md`). Not before.

## Quick Reference

| Need | Do |
|---|---|
| New bot | Alias preflight (Procedure C) → Interview → SOUL draft → human sign-off → `hermes profile create NAME --no-skills --description "…"` |
| Pin a brain | `hermes -p NAME config set model.provider …` then `model.default …`. Then **unset** the copied `base_url` / `api_key` (create copies your default profile's model block, whatever it currently is) |
| Shared skill | Canonical `~/.hermes/skills/<cat>/<name>/`; profile files via `scripts/link_skill_tree.py`. Never a directory symlink. Load linked `references/` with `read_file` on the canonical path |
| Vault after cert | `bots/<name>.md` (`type: bot-reference`), roster row on `making-bots.md`, one line on `Home.md` |
| Child memory | Child writes it. You do not. |

## Procedure

### A. Interview (before any `profile create`)

Ask, and do not proceed until 1–3 are sharp:

1. One-sentence job. If "and also," split into two bots. Job may be a CLI, an HTTP API, a GUI sock — ComfyUI counts. "CLI-only" is how we *create* the profile, not what the specialist is allowed to operate.
2. Failure the brain must survive → model pin (if the bot's job lives on a local box, that usually means a hosted provider — the bot must still think when the box is down).
3. What it is not.
4. Does default Hermes need the same skill? → canonical under `~/.hermes/skills/` + file-level symlinks.
5. Who is the client to ping (`@hermes`, another specialist, nobody).
6. Voice: inherit vs write. Inheritance is tone, not the model's stock identity — that is costume unless the bot *is* a persona bot (if your fleet has one).

### B. SOUL draft

Write one screen. Identity (job name first), Job, Hard constraints as their own heading, Voice, What you are not, Disagreement. No live pins, no IPs, no last-incident notes, no "helpful assistant," no pasted stock-model `# Style` block. Full rules in `references/soul-craft.md`.

**Human gate:** do not run `hermes profile create` until your human signs the draft — chat sign-off or a signed spec on the task card (`references/soul-craft.md` §Human gate). Iterate in the conversation or on the card, not on disk.

### C. Scaffold

Full mechanics and the command sequence: `references/process.md`. The stop points:

**Data-policy preflight — before you pin the brain.** Some tiers are cheap *because* the vendor trains on your prompts; Meta's `-contributor` id is the live case and it reads as a discount. Check the chosen model against `hermes_cli/model_data_policy_guard.py` before pinning, and never let a price-only request carry a data-rights decision — `references/process.md` §Data-policy preflight.

**Alias preflight — mandatory, before any `profile create NAME`.** The default alias wrapper can destroy a real CLI through a `~/.local/bin` symlink:

```text
zsh -lc 'which -a NAME'
# and, even if which is empty:
test -e "$HOME/.local/bin/NAME" || test -L "$HOME/.local/bin/NAME"
```

If **either** finds anything: `--no-alias` (rationale and the landmines: `references/process.md` §--no-skills).

- `--no-skills`; never `--clone` / desktop clone. Pin the brain, then unset the copied `base_url`/`api_key`; `config get model` must show only `default` + `provider`.
- **Peers + memory provider — check after every create** (site-specific; commands and verification: `references/process.md` §Independence). The invariant: every rostered profile has every peer it must reach. Do not print keys.
- Sibling-profile CLI from this profile: always prefix `HERMES_HOME=$HOME/.hermes`.
- By default, `SOUL.md` writes prompt your human (`security.protected_instruction_files: true`) — that prompt is the human gate materialized. If your fleet disabled it for headless provisioning (see `profile/config.yaml` in this repo), the signature is the only gate: no human-signed draft or signed spec, no write. If a write is blocked anyway, stop — do **not** sneak it in via the shell.
- Never hand-edit `config.yaml` — `config set` only (your human may hand-edit their own; you do not). Never copy credentials. Never print `auth.api_key` / `secret_key`.

Then: write signed `SOUL.md`, thin `memories/USER.md` — if the skill is shared, include the **lockstep sentence**: one line stating that the canonical skill lives under `~/.hermes/skills/<category>/<name>/`, the profile files are symlinks, and process changes patch the canonical tree (so later sessions do not re-flag the drift). Then empty-or-tiny `memories/MEMORY.md` (the child fills this). Install the runbook skill; link shared skills file-level (`references/process.md` §Shared skills). Not every specialist needs a custom skill — `@hostadmin` is `hermes-agent` + earned MEMORY. Do not invent a runbook so the folder looks complete.

Stop. Do not fill the child's `MEMORY.md`. Do not add a vault roster row yet.

### D. Certification (child's Bot Chat)

Kickoff: first look at the real box/job → one failure path → client ping if there is a client. The child patches its own skill + `MEMORY.md`. You may `message_agent` one job ("first look") and then get out.

Certified when it has done the job against the live system, rewritten the stale bits of its runbook (if it has one), and pinged the client (or you agreed there isn't one). A first look that finds nothing broken is still a first look — do not invent a failure to practice. Your human saying "document it in the vault" is a ship signal. Uncertified profiles do not get a `bots/<name>.md` or a roster row unless your human overrides.

### E. Vault

Only after D. See `references/vault.md`.

## Pitfalls

Numbered failure modes for a bot build. The mechanism lives with its owner; the row names the owner.

1. **Skill invisible / empty index** — never directory-symlink a skill (rglob) See `references/process.md` §Shared skills.
2. **`skill_view`/`skill_manage` `file_path` rejected** — file-symlink escape — `read_file` canonical See `references/process.md` §Shared skills.
3. **Second copy after a patch** — `skill_manage` unlinks — patch canonical, `ls -l` See `references/process.md` §Shared skills.
4. **"Independent" bot on default's provider** — unset the create-leftover `base_url`/`api_key` See `references/process.md` §Independence.
5. **DM acks then vanishes** — a peer missing on the sender profile See `references/process.md` §Independence.
6. **Mnemosyne version `(not set)`** — `mnemosyne version` + `memory.provider mnemosyne` See `references/process.md` §Independence.
7. **Real CLI destroyed by alias** — preflight before `profile create` See `references/process.md` §--no-skills.
8. **Cheap tier that trains on prompts** — name the data-rights tradeoff; "it's cheaper" is not consent See `references/process.md` §Data-policy preflight.
9. **A fix reported "verified" still shows old behaviour** — a patched `.py` is inert in any process started before the edit — restart, then re-test from a fresh process
10. **A bot's roster lists agents that cannot receive** — rosters enumerate `profiles/` **directories**, so tombstoned leftovers appear as live targets. Filter on the tombstone marker (`profiles/.deleted/<name>`), and make the predicate **fail open** so a broken lookup cannot hide a teammate
11. **`Unknown skill(s)` at worker init** — link the injected skill file-level; don't always-load See `references/process.md` §--no-skills.
12. **`ui_meta` empty / `toolsets` says `hermes-cli`** — title in `profile.yaml`; spec list is `platform_toolsets.cli` See `references/process.md` §Scaffold sequence.
13. **Worker files to the wrong board / sibling inherits kanban env** — strip `HERMES_KANBAN_*`; one terminal call per worker See `references/process.md` §Kanban intake.
14. **Child sounds like a costume** — identity = job name; inherit tone, not self See `references/soul-craft.md`.
15. **SOUL written unsigned** — the signature is the gate See `references/soul-craft.md` §Human gate.
16. **Uncertified bot in the vault; persona in `bots/`** — write after certification only See `references/vault.md`.
17. **Filling child MEMORY · `botmaker-2` · default SOUL · operating services** — constitution See `profile/SOUL.md`.
18. **`--no-skills` and `--no-alias` are independent decisions.** Passing one does not imply the other: the alias preflight decides `--no-alias` on its own evidence (`which -a NAME` plus the `$HOME/.local/bin/NAME` symlink test), and skipping either flag silently leaves a bundled-skills tree or a destroyed real CLI.
19. **A DM that acks then vanishes is an independence finding, not a chat bug.** Treat it as a peer-roster defect on the *sender* profile (§Independence); retry loops in the conversation hide the missing peer and certify nothing.

## Verification

A new bot is done when:

1. `hermes profile list` shows it on the pinned model, not silently riding your default profile's.
2. `hermes -p NAME config get model` is only provider + default + base_url (optional).
3. `.no-bundled-skills` exists in the profile root.
4. (If your fleet has peers) `hermes -p NAME peer list` shows every peer it must reach — or DMs will ack then vanish.
5. `hermes mnemosynce version` lists a version number (not `(blank)`). `memory.provider` is `mnemosyne`.
6. `SOUL.md` matches the signed draft (one screen).
7. Shared skills: `ls -l` on profile `SKILL.md` shows `l` (symlink), canonical is a regular file. `rglob` from the profile skills dir finds `SKILL.md`.
8. After certification only: vault note + roster row + Home line + `making-bots.md` changelog.
9. `python3 "$HOME/.hermes/skills/autonomous-ai-agents/botmaker/scripts/drift_check.py"` exits 0.
