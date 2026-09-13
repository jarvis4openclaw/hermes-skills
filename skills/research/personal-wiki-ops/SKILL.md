---
name: personal-wiki-ops
description: "Operating the user's personal LLM-Wiki knowledge base (~/wiki): auto-ingest policy, archive-not-delete convention, and the Mnemosyne-vs-Wiki decision."
version: 1.1.0
author: jarvis
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [wiki, knowledge-base, memory, notes, personal]
    category: research
    related_skills: [llm-wiki, obsidian-vault, lightrag]
    trigger_conditions:
      - "user shares an in-domain fact (infra, provider, side-hustle)"
      - "put this in the wiki"
      - "wiki mentioned in context of personal knowledge"
      - "should I use the wiki or memory for this"
      - "archive or remove a wiki page"
      - "delete a wiki page"
      - "personal wiki"
      - "LLM-Wiki"
      - "auto-ingest the wiki"
      - "WIKI_PATH"
      - "wiki vs Mnemosyne"
      - "wiki operating policy"
      - "wiki SCHEMA"
      - "~/wiki"
---

# Personal Wiki Ops

Operating the user's personal LLM-Wiki at `~/wiki` (default `WIKI_PATH`). The generic structure,
SCHEMA templates, ingest/lint mechanics live in the **bundled `llm-wiki` skill** — load it for
those. This skill carries the **user-locked operating policy** that the generic skill does not,
and the decision framework for when to use the wiki vs. agent memory.

## When to Use

- The user shares an **in-domain fact** (homelab/infra, provider/model, Crave Net side-hustle, recurring entity, architecture decision + rationale) that should be filed automatically.
- The user says "put this in the wiki", "add that to my wiki", or references `~/wiki` directly.
- You must decide **Mnemosyne vs Wiki** for a piece of information — "will the user want to READ this later?" vs "do I need to REMEMBER their preference?".
- The user asks to **remove or delete** a wiki page and you need the archive-not-delete convention.
- You are deciding whether an item falls inside the in-domain scope or the hard-exclusion list (secrets values, ephemeral status, troubleshooting chatter, bare opinion).
- You need the exact user-locked operating policy to paste into a new wiki's `SCHEMA.md`.
- You are reviewing whether earlier auto-ingest behaviour was correct after the 2026-07-11 lock.

## Not For

- **Generic LLM-Wiki structure, SCHEMA templates, ingest/lint mechanics** → use `llm-wiki` instead
- **Architecture and comparison of wiki-style knowledge tools generally** → use `agent-wikis` instead
- **Operating the Mnemosyne / memory provider stack itself** → use `hermes-memory-provider-management` instead
- **Routine memory pruning and maintenance passes** → use `memory-maintenance` instead
- **Obsidian vault mechanics unrelated to the personal wiki policy** → use `obsidian-vault` instead
- **Graph-retrieval / LightRAG indexing pipelines** → use `lightrag` instead

## Activation
Load this alongside `llm-wiki` whenever the user shares in-domain facts or talks about the wiki.
The user does **NOT** need to say "put this in the wiki" — auto-ingest is the standing rule.

## Locked decision (2026-07-11): auto-ingest = "in-domain facts" on FIRST mention
- File in-domain facts **automatically on first mention**. No per-message instruction required.
- After filing, give a one-line `filed:` summary so the user keeps visibility.
- To **EXCLUDE** a specific item, the user says so explicitly.

### In-domain scope
- **Homelab/infra:** hosts, IPs, hostnames, services, ports, URLs, versions, topology, storage
- **Provider/model:** pricing, limits, endpoints, ZDR status, capabilities, comparisons
- **Crave Net (side hustle):** architecture, product decisions, roadmap, integrations
- **Recurring entities** & architecture decisions + their rationale

### Hard exclusions (never auto-file)
- **Secrets / credential VALUES** — record only the *location/reference* (e.g. "API key in
  Studio > API Keys"), never the value.
- One-off troubleshooting chatter
- Ephemeral task status ("it's deploying now")
- Bare opinion without durable value

## Removal convention: ARCHIVE, don't delete
When the user says remove/delete a wiki page: move it to `_archive/<section>/` (reversible),
remove the entry from `index.md`, and log the action in `log.md`. **Never hard-delete.**
Confirmed by the user 2026-07-11 when removing `commandcode-provider.md` — archived to
`_archive/entities/` instead of deleting.

## Mnemosyne vs Wiki — they are complementary, not competing
- **Mnemosyne (agent memory):** machine recall of user preferences, past work, contradictions.
  Auto-extracted from chats; the user never browses it. Sufficient for operational memory — do
  NOT duplicate wiki content into it.
- **LLM-Wiki (this):** human-navigable, compounding KB of *external/knowledge* facts the user
  can read in Obsidian. Use for durable infra/provider/side-hustle knowledge worth browsing.

Rule of thumb:
- "Will the user want to READ and cross-reference this later?" → **Wiki.**
- "Do I (the agent) need to REMEMBER the user's preference/state?" → **Mnemosyne.**

## Pitfalls

1. **Waiting for "put this in the wiki"** — auto-ingest on first mention is the locked policy. Waiting is friction the user explicitly rejected on 2026-07-11.
2. **Hard-deleting a wiki page because the user said "delete"** — move it to `_archive/<section>/`, drop the entry from `index.md`, and log it in `log.md`. Never hard-delete; the convention was confirmed when `commandcode-provider.md` was archived instead of removed.
3. **Filing credential VALUES into the wiki** — record only the *location/reference* (e.g. "API key in Studio > API Keys"), never the value. Ever.
4. **Duplicating wiki facts into Mnemosyne** — they serve different readers. Mnemosyne is machine recall of user preference/state; the wiki is a human-navigable external-knowledge KB.
5. **Filing ephemeral status or chatter** — "it's deploying now", one-off troubleshooting back-and-forth, and bare opinion without durable value are on the hard-exclusion list. Do not file them.
6. **Filing the user's own preferences/state into the wiki** — ask "will the user want to READ and cross-reference this later?" If yes → Wiki. If it is a preference/state the agent must recall → Mnemosyne.
7. **Inserting a revised section above the old one and stopping there** — anchoring a `patch` on the *following* heading (e.g. replacing `## Related`) appends new text while the superseded draft stays put, leaving two contradictory copies. After any structural insert into a long page, re-read the section and delete the old copy; verify with a count of the section heading, which must equal 1.
8. **Silently filing without the `filed:` summary** — always give a one-line `filed:` note after filing so the user keeps visibility; the exclusion path must be explicit and visible too.
9. **Skipping the `index.md` / `log.md` updates on archive** — an archived page that is still listed in `index.md` is a broken link, and an unlogged move is unauditable.
10. **Assuming the wiki lives at the default path** — resolve `WIKI_PATH` first; do not hard-code `~/wiki` in scripts when the env var is set.
11. **Re-implementing generic ingest/lint mechanics in this skill** — those live in the bundled `llm-wiki` skill. This skill carries only the user-locked policy and the wiki-vs-memory decision framework.
12. **Treating auto-ingest as licence to file secrets or one-off chatter** — the standing rule is "in-domain facts on FIRST mention", scoped by the in-domain and hard-exclusion lists, not "file everything".
13. **Filing a fact as in-domain when it is actually a secret location plus value** — split it: file the location/reference, and leave the value out entirely.

## References
- `references/operating-policy.md` — exact SCHEMA auto-ingest text + decision log to paste into
  a new wiki's SCHEMA.md.
