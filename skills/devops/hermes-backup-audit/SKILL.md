---
name: hermes-backup-audit
description: Use when auditing whether a Hermes backup would restore the setup, its integrity, currency, or leaked secrets.
version: 1.1.0
author: jarvis
license: MIT
metadata:
  hermes:
    tags: [hermes, backup, audit, secrets, restore, git]
    related_skills: [hermes-config-backup, clawd-workspace-backup, hermes-config-management]
    trigger_conditions:
      - "audit the Hermes backup"
      - "would the backup restore"
      - "backup integrity check"
      - "backup currency"
      - "hermes-backups repo"
      - "did the weekly backup run"
      - "scan the backup for secrets"
      - "restore coverage"
      - "is the backup complete"
      - "backup git fsck"
      - "were keys exposed in the backup repo"
      - "hermes-config-backup audit"
      - "backup restore gaps"
---

# Hermes backup audit

## When to Use

- Asked whether a Hermes backup would restore the setup.
- Auditing backup integrity, currency, or tracked scope.
- Scanning the backup repo for exposed secrets or literal API keys.
- Checking whether the weekly `hermes-config-backup` job actually ran and produced a new commit.
- Producing a restore verdict before a risky config or migration change.
- Explaining what the backup does NOT cover.

## Not For

- **Running or fixing the weekly backup job itself** → use `hermes-config-backup` instead
- **Backing up the `clawd` workspace rather than `~/.hermes`** → use `clawd-workspace-backup` instead
- **Editing `~/.hermes/config.yaml` content** → use `hermes-config-management` instead
- **Repairing config after a destructive change** → use `hermes-config-post-audit-recovery` instead
- **Auditing a profile's config inheritance** → use `hermes-subprofile-config` instead
- **Deciding whether a cron alert is a false positive** → use `hermes-cron-false-positive-triage` instead

## Facts

The Hermes backup is **not a zip**. It is a **git repo** at `/home/wahid/.cache/hermes-backups` (~280MB, remote `github.com/jarvis4openclaw/hermes-backups.git`), produced weekly by cron `hermes-config-backup` (Sun 04:00). At the 2026-10-12 audit: HEAD `05679a0`, 11,920 tracked files, 21 commits, `git fsck` clean.

## Audit procedure

1. **Integrity**: `git fsck` in the repo — exit 0 and 0 missing/corrupt objects is the pass bar.
2. **Currency**: `git log -1`; state the backup date and its gap to "now" in days. A backup older than the last config change is a partial verdict, not a pass.
3. **Scope**: list top-level tracked paths (config.yaml, SOUL.md, etc.) and answer "would this bring the setup back, and what is NOT covered" — the honest verdict has been "partially", never yes.
4. **Secrets scan**: use a path-aware, value-shaped scan. An older length-based heuristic counted `${VAR}` references as literal values (e.g. `${COMMANDCODE_API_KEY}`, 22 chars) and produced a retracted "10 keys exposed" claim (2026-10-12). Ground truth then: `~/.hermes/config.yaml` had NO literal secrets; provider keys were already `${VAR}` references at lines 43 (commandcode), 56 (venice), 168 (tavily), 169 (brave), 533 (sendblue), 1030 (webhook).

Completion criterion: a verdict naming repo, HEAD/date, fsck result, restore scope and gaps — with the secrets claim split into literal values vs `${VAR}` references.

## Pitfalls

1. **Expecting a zip archive** — the backup is a git repo at `/home/wahid/.cache/hermes-backups` (~280MB). Do not go looking for an archive file.
2. **Length-based secret heuristic** — it counts `${VAR}` references (22 chars) as literal values and produced a retracted "10 keys exposed" claim on 2026-10-12. Use a path-aware, value-shaped scan.
3. **Reporting a pass on `git fsck` alone** — integrity is not coverage or currency. fsck clean says nothing about whether the setup is restorable.
4. **Ignoring the currency gap** — compute days between HEAD and now. If the backup predates the last config change, the verdict is partial, not pass.
5. **Answering "would it restore?" with yes** — the honest verdict has consistently been "partially". Name explicitly what is NOT covered.
6. **Not naming HEAD** — always report repo path, HEAD sha, commit count, and date; a verdict without them cannot be re-audited.
7. **Reading a masked value and calling it a leak** — `read_file` renders secrets as `***`. Read raw content programmatically before making any exposure claim.
8. **Assuming everything under `~/.hermes` is tracked** — large databases and caches (e.g. a ~880MB `state.db`) are typically excluded. List tracked top-level paths to establish real scope.
9. **Auditing the working tree instead of HEAD** — uncommitted local changes are not in the backup. Audit the committed content.
10. **Auditing the wrong repo** — `~/.cache/hermes-backups`, not `~/hermes-skills` (skill backups) or `~/hermes-agent-self-evolution` (GEPA reports).
11. **Pasting literal values when citing findings** — quote line numbers and `${VAR}` names, never the resolved secret.
12. **Treating a `${VAR}` reference as proof of rotation** — indirection proves the key is not inline; it says nothing about whether the underlying secret was rotated.
