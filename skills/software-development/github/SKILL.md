---
name: github
description: "GitHub via gh CLI: PRs, issues, reviews, repos, auth."
version: 2.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, gh, git, pull-requests, issues, code-review, repos, auth, ci]
    category: software-development
    related_skills: [github-auth, github-pr-workflow, github-code-review, code-review]
    trigger_conditions:
      - "open a pull request"
      - "create a GitHub issue"
      - "review this PR"
      - "why did CI fail / check gh pr checks"
      - "gh auth status broken"
      - "clone or fork a repo"
      - "carry an issue to a PR"
      - "sweep for duplicate issues before filing"
      - "gh cli command for X"
      - "github api endpoint not in gh porcelain"
      - "is the PR merged"
      - "set up GitHub auth on a new machine"
      - "label / assign / close an issue"
---

# GitHub

Work GitHub end to end with the `gh` CLI (REST fallback where noted): auth,
issues, the PR lifecycle, issue-to-PR delivery, code review, and repo
management. This skill consolidates six former skills; each workflow lives
complete in its reference file — ALWAYS read the matching reference before
starting that workflow, the body below only routes.

## Routing

| Task | Read first |
|---|---|
| Auth broken / new machine / token or SSH setup / gh login | `references/auth.md` |
| Create, triage, label, assign, close issues | `references/issues.md` |
| Branch, commit, open PR, watch CI, merge | `references/pr-workflow.md` |
| Carry an ISSUE to a verified PR (full delivery loop) | `references/issue-to-pr.md` |
| Review someone's PR: diffs, inline comments, verdict | `references/code-review.md` |
| Clone/create/fork repos, remotes, releases | `references/repo-management.md` |

Supporting assets: `scripts/gh-env.sh` + `scripts/git-credential-token.py`
(auth helpers), `templates/` (PR bodies, bug report, feature request),
`references/ci-troubleshooting.md`, `references/conventional-commits.md`,
`references/github-api-cheatsheet.md`, `references/review-output-template.md`.

## When to Use

- Any GitHub work driven through the `gh` CLI: auth, issues, PRs, review, repos, releases.
- You need to pick the correct workflow before acting — this skill routes to the right reference.
- Diagnosing broken auth on a machine (`gh auth status` fails or returns the wrong account).
- Opening, watching, or merging a PR and needing honest CI/merge state.
- Triaging or filing issues, including duplicate sweeps and labelling.
- Reviewing another person's PR and producing a verdict with evidence.
- Cloning, forking, or managing remotes and releases.

## Not For

- **Setting up GitHub auth from scratch** (tokens, SSH, `gh login`) → use `github-auth` instead.
- **The full branch→commit→PR→CI→merge lifecycle in depth** → use `github-pr-workflow` instead.
- **Reviewing a PR with inline comments via `gh` or REST** → use `github-code-review` instead.
- **General code-review policy (security/quality focus), not GitHub mechanics** → use `code-review` instead.
- **Carrying one issue all the way to a verified merged PR** → use `github-issue-to-pr` instead.
- **Clone/create/fork, remotes, and releases** → use `github-repo-management` instead.
- **Preventing false-success Git sync runs** (script permissions, repo root) → use `github-sync-script-preflight` instead.

## Core discipline (applies to every workflow)

- Preflight once per session: `gh auth status` — if it fails, go to
  `references/auth.md` before anything else.
- Prefer `gh` over raw REST; drop to `gh api` only for endpoints the
  porcelain lacks (the cheatsheet lists them).
- Never report CI green without checking `gh pr checks` yourself; never
  claim merged without verifying `state,mergedAt`.
- Read full context before writing: `gh issue view --comments` /
  `gh pr view --comments` — decisions live in threads, not titles.
- Sweep for duplicates before creating anything:
  `gh pr list --search` / `gh issue list --search`.

## Pitfalls

1. **Reporting CI green without reading `gh pr checks`** — a green badge in a browser or an assumed
   pass is not evidence. Recovery: run `gh pr checks <n>` and quote its output.
2. **Claiming a PR is merged without verifying state** — read
   `gh pr view <n> --json state,mergedAt`; a merge commit in the log does not mean it merged.
   Recovery: never assert merged from memory.
3. **Assuming `gh` auth is fine** — a stale or scoped-down token fails only on the write call, not
   the read. Recovery: preflight `gh auth status` once per session, and re-check on any 403 before
   blaming the command.
4. **Reading the title instead of the thread** — decisions live in comments. Recovery:
   `gh issue view --comments` / `gh pr view --comments` before writing anything.
5. **Filing a duplicate** — `gh pr list --search` / `gh issue list --search` first; near-identical
   titles are common. Recovery: sweep before creating.
6. **Using raw REST where porcelain exists** — `gh api` bypasses porcelain pagination and readable
   errors. Recovery: prefer `gh` subcommands; drop to `gh api` only for endpoints the porcelain
   lacks (see `references/github-api-cheatsheet.md`).
7. **Skipping the reference file and improvising a workflow** — each workflow is complete in
   `references/*.md`; the body only routes. Recovery: read the matching reference before starting.
8. **Assuming a fine-grained PAT can open the PR** — a token may push to a fork while being unable
   to open an upstream PR. Recovery: confirm the token's scope before promising a PR, and check
   `github-sync-script-preflight` / `references/auth.md`.
9. **Trusting a cached remote state** — `gh` output is a point-in-time read; the branch can move
   between the read and the write. Recovery: re-read immediately before merge or close.
10. **Printing a token or secret into output** — `gh auth token` and env dumps emit live
    credentials, and anything the job prints is delivered. Recovery: never echo a token; mask or
    omit it.
11. **Assuming `gh` is installed** — the skill assumes the CLI, but minimal hosts may only have
    `git`. Recovery: `command -v gh` first; fall back to the `scripts/gh-env.sh` helper and the
    REST path in `references/auth.md`.

## Verification

- The workflow's own reference file defines done for that task.
- Cross-cutting: every claim about remote state (CI, merge, release,
  issue state) is backed by a fresh `gh` read, never memory.
