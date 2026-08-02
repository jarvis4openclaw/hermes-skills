---
name: agent-skills-cli
description: >
  Install, update, and safely vet third-party "agent skills" distributed via
  the skills.sh CLI (npx skills) from GitHub repos like heredotnow/skill,
  vercel-labs/agent-skills, etc. Use when the user asks to install a skill
  from a GitHub repo, set up "here.now"/"here-now", or add any agent-skill
  package. Covers non-interactive install (the CLI defaults to an interactive
  agent picker that hangs), where files land on disk, and how to vet bundled
  scripts before trusting them with credentials.
version: 1.1.0
metadata:
  hermes:
    tags: [agent-skills, skills.sh, npx, install, security]
    trigger_conditions:
      - "Install a skill from a GitHub repo"
      - "Set up here.now / here-now / heredotnow skill"
      - "Add an agent-skill package via npx skills"
      - "Vet third-party skill scripts before trusting them"
      - "Install skills non-interactively (avoid the agent picker hang)"
      - "Find where skills.sh installs files"
      - "Understand .agents/skills vs ~/.hermes/skills"
---

# agent-skills-cli (skills.sh)

The `skills` CLI (skills.sh) installs "agent skills" — a `SKILL.md` plus
supporting scripts — from a GitHub repo into agent skill directories. Many
services ship a skill this way (e.g. here.now -> `heredotnow/skill`, Vercel ->
`vercel-labs/agent-skills`). The Hermes desktop app reads skills from
`~/.hermes/skills/`, but these repos target the universal `.agents/skills`
layout; the installer bridges the two.

## Non-interactive install (critical)

`npx skills add <repo> --skill <name> -g` **drops into an interactive TUI**
asking which agents to install to, then waits forever for input. Always pass:

```
npx skills add <owner>/<repo> --skill <name> -g -y -a '*'
```

- `-y`       : skip confirmation prompts
- `-a '*'`   : select ALL agents. This is what writes to the always-included
               **Universal** `.agents/skills` location. Omitting it (or picking
               a single agent) can silently skip the universal dir.
- `-g`       : install globally (user-level) instead of project-local

For a project-local install, drop `-g` but KEEP `-y -a '*'`.

To list what a repo offers without installing: `npx skills add <repo> -l`.

## Where files land

- Primary: `~/.agents/skills/<name>/` (the Universal location).
- Hermes reads from `~/.hermes/skills/`. The installer auto-symlinks the
  universal dir into `~/.hermes/skills/<name>`, so the skill is loadable by
  Hermes immediately. Verify:
  `readlink -f ~/.hermes/skills/<name>/SKILL.md`
- Some agents report "Failed to install: does not support global skill
  installation" (e.g. Eve, PromptScript). That is expected and harmless.

## Vet bundled scripts BEFORE trusting

Packages from these repos are scanned by Gen / Socket / Snyk. A **"High Risk"
on the package is usually the installer's transitive npm dependencies, NOT the
bundled shell scripts.** Before trusting the skill with credentials:

1. Read every script under `scripts/` (and `bin/`).
2. Red flags: `eval`, unquoted variable expansions, `curl ... | bash`, or
   credential exfil to a non-default host.
3. Confirm sane guards. (here.now's `publish.sh`/`drive.sh` explicitly REFUSE
   to send the API key to any base URL other than `https://here.now` — good.)
4. Verify runtime deps the SKILL.md lists (e.g. `jq`, `file`, `curl`) exist;
   syntax-check with `bash -n scripts/*.sh`.
5. Confirm the scripts are executable.

Only store credentials after confirming the scripts are safe.

## When to Use
- The user asks to install any skill distributed via skills.sh / `npx skills` (here.now, Vercel agent-skills, etc.).
- You need a non-interactive install that won't hang on the agent-picker TUI.
- You must verify a third-party skill's bundled scripts before storing credentials.
- You need to know where a skill landed (`~/.agents/skills` vs `~/.hermes/skills`) or why Hermes can't see it.

## Not For
- **Authoring or optimizing Hermes's own SKILL.md files** → use `hermes-agent-skill-authoring` / `writing-great-skills`.
- **Auditing a whole skill tree for token cost / disabled skills** → use `hermes-skills-optimization`.
- **Installing skills through Hermes's own `hermes` CLI or hub** → that's the profile/plugin path (`hermes-profile-setup`, `agent-skills-cli` covers only the external skills.sh ecosystem).
- **Writing a new skill from scratch** → see `writing-great-skills`.

## references/

- `references/here-now-example.md` — full worked example: install here.now,
  vet its scripts, and activate an account via a magic code emailed to an
  AgentMail inbox (request -> retrieve from inbox -> verify -> save key).

## Pitfalls
1. **Running `npx skills add` without `-y -a '*'`** — The CLI drops into an interactive agent-picker TUI and waits forever, hanging cron/automation. Always pass `-y -a '*'` (and `-g` for user-level installs).
2. **Trusting the "High Risk" package label** — The risk flag usually comes from transitive npm deps, not the bundled shell scripts. Vet the scripts themselves (`eval`, `curl | bash`, unquoted vars, non-default hosts) before deciding.
3. **Storing credentials before vetting** — Only add API keys/tokens after reading every `scripts/`/`bin/` file and confirming sane guards (e.g. here.now's publish.sh refuses non-`https://here.now` base URLs).
4. **Ignoring the universal `.agents/skills` location** — Omitting `-a '*'` can skip the Universal dir that Hermes's `~/.hermes/skills/` symlink points to, so the skill never loads.
5. **Assuming the symlink is created** — The installer usually symlinks `~/.agents/skills/<name>` into `~/.hermes/skills/<name>`. Verify with `readlink -f ~/.hermes/skills/<name>/SKILL.md`; if absent, the skill is installed but not loadable.
6. **Missing runtime deps** — SKILL.md may list `jq`, `file`, `curl` etc. Check they exist and `bash -n scripts/*.sh` passes before running anything.
7. **Not checking executable bits** — Scripts without `+x` fail with "Permission denied" at runtime. Confirm they're executable.
8. **Treating "Failed to install" for some agents as fatal** — Eve/PromptScript report unsupported global installs; that's expected and harmless, not a broken install.
9. **Re-running interactive installs in cron** — Any `npx skills` invocation from a cron/non-TTY context must be fully non-interactive (`-y -a '*'`) or it will block forever.
10. **Not keeping the worked example updated** — `references/here-now-example.md` is a step-by-step record; refresh it whenever the CLI flags or install layout change.
