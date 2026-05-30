---
name: codex
description: Delegate coding tasks to OpenAI Codex CLI agent. Use for building features, refactoring, PR reviews, and batch issue fixing. Requires the codex CLI and a git repository.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
    trigger_conditions:
      - user asks to build, implement, or add a feature to a codebase autonomously
      - user wants to refactor, clean up, or improve existing code with an agent
      - user requests automated PR review or batch code review
      - user wants to fix multiple GitHub issues in parallel using worktrees
      - user asks to "use codex", "have codex do it", or "run codex on this"
      - phrase matches: "codex exec", "batch fix issues", "parallel PR review", "autonomous coding"
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to Use

- Building new features autonomously in an existing codebase
- Refactoring modules without step-by-step guidance
- Running parallel PR reviews across multiple open PRs
- Batch-fixing multiple GitHub issues simultaneously using worktrees
- Scratch prototypes where you need a full coding agent loop

## Not For

- Simple file reads, edits, or grep — use terminal/read_file/patch directly
- Projects with no git history (Codex requires a git repo)
- Tasks requiring human visual/UI feedback in the loop
- Secret injection at runtime without environment setup

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- OpenAI API key configured
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --yolo exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
terminal(command="git worktree prune", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Pitfalls

1. **Missing `pty=true` causes hang** — Codex is an interactive TUI app. Without `pty=true`, the process blocks waiting for terminal input and never progresses. Always add `pty=true`.

2. **Running outside a git repo** — Codex immediately errors with "not a git repository". Fix: `cd $(mktemp -d) && git init` before any Codex call for scratch work.

3. **OpenAI API key not set** — Codex silently fails or returns an auth error. Fix: ensure `OPENAI_API_KEY` is exported in the environment, or set it inline: `OPENAI_API_KEY=*** codex exec '...'`.

4. **`--yolo` modifying files outside the intended worktree** — With `--yolo`, Codex has full filesystem access. If `workdir` is set to the main repo instead of an isolated worktree, it can corrupt the main branch. Always point `workdir` to the isolated `/tmp/issue-XX` path.

5. **Worktrees not cleaned up after use** — Leftover worktrees accumulate and confuse `git status`. Always run `git worktree remove /tmp/issue-XX` followed by `git worktree prune` after pushing PRs.

6. **Long tasks silently stalling waiting for input** — Codex may pause mid-task awaiting user confirmation without a clear prompt. Fix: periodically run `process(action="poll")` and if output is stalled, send `process(action="submit", data="yes")` or inspect with `process(action="log")`.

7. **`codex review --base` branch name mismatch** — If the cloned repo's default branch is `master` but you pass `--base origin/main`, the diff is empty or incorrect. Fix: check `git remote show origin | grep HEAD` first and use the correct base branch name.

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work
