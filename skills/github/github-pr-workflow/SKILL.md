---
name: github-pr-workflow
description: Full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge. Works with gh CLI or falls back to git + GitHub REST API via curl.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
    related_skills: [github-auth, github-code-review]
    trigger_conditions:
      - "create pull request"
      - "open a PR"
      - "merge feature branch"
      - "CI failing on PR"
      - "push changes for review"
      - "submit code for review"
      - "create branch and commit"
      - "pull request workflow"
---

# GitHub PR Workflow

Full pull request lifecycle automation — branch creation, commits, PR opening, CI monitoring, auto-fix, and merge.

## When to Use

- **New feature or bugfix**: Any code change that requires peer review before merging to main/master.
- **Open-source contributions**: Contributing to external repositories via fork + PR.
- **CI-gated deployments**: When code changes must pass automated tests and checks before reaching production.
- **Collaborative refactors**: Large or risky changes that benefit from staged, reviewable commits.
- **Compliance workflows**: Regulated environments requiring documented review trails before merging.

## Not For

- **Issue tracking**: Use `github-issues` skill to create, triage, and manage GitHub issues — not this skill.
- **Code review responses**: Use `github-code-review` skill for detailed inline review and approval workflows.
- **Direct wiki edits**: GitHub wiki pages are edited directly, not via PRs.
- **Emergency hotfixes bypassing review**: Follow your team's break-glass procedure instead of standard PR flow.

## Prerequisites

- `gh` CLI authenticated (run `gh auth status` to verify)
- Git configured with user.name and user.email
- Push access to repository (or fork for external contributions)

## Phase 1 — Branch Setup

```bash
# Start from clean main/master
git checkout main && git pull origin main

# Create feature branch (use kebab-case)
git checkout -b feat/my-feature   # feature
git checkout -b fix/bug-name      # bugfix
git checkout -b chore/task-name   # chores
git checkout -b docs/update-name  # docs
```

## Phase 2 — Make Changes + Commit

```bash
# Stage changes
git add -p                          # interactive (preferred)
git add path/to/file                # specific file
git add .                           # all (last resort)

# Commit with conventional commits format
git commit -m "feat: add user authentication"
git commit -m "fix: resolve memory leak in cache"
git commit -m "docs: update API reference"
git commit -m "chore: bump version to 2.1.0"

# Amend last commit (before push)
git commit --amend --no-edit
```

## Phase 3 — Open Pull Request

```bash
# Push branch
git push -u origin HEAD

# Create PR with gh CLI (interactive)
gh pr create

# Create PR non-interactively
gh pr create \
  --title "feat: add user authentication" \
  --body "## Summary\n\nAdds OAuth2 login flow.\n\n## Changes\n- ..." \
  --base main \
  --assignee @me \
  --label enhancement

# Create draft PR
gh pr create --draft --title "WIP: feature name"
```

## Phase 4 — CI Monitoring + Auto-Fix

```bash
# Check PR status
gh pr status
gh pr view --web    # open in browser

# Watch CI checks
gh pr checks --watch

# View failed check logs
gh run list --branch $(git branch --show-current)
gh run view <run-id> --log-failed

# Re-run failed CI
gh run rerun <run-id> --failed
```

### Auto-fix CI failures

```bash
# Lint fixes
npm run lint -- --fix      # Node.js
python -m black .          # Python
gofmt -w .                 # Go

# Type check fix loop
python -m mypy . 2>&1 | head -20   # identify errors
# fix, then push
git add -p && git commit -m "fix: resolve type errors" && git push
```

## Phase 5 — Review + Merge

```bash
# Request review
gh pr edit --add-reviewer teammate1,teammate2

# Respond to review comments
# ... make changes ...
git add -p && git commit -m "fix: address review feedback"
git push

# Merge PR (after approval)
gh pr merge --squash --delete-branch
gh pr merge --merge --delete-branch   # merge commit
gh pr merge --rebase --delete-branch  # rebase

# Check merge status
gh pr view --json state,mergedAt
```

## Fallback: REST API (no gh CLI)

```bash
# Create PR via API
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/pulls \
  -d '{"title":"feat: my feature","body":"...","head":"feat/my-feature","base":"main"}'

# List PRs
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/pulls

# Merge via API
curl -X PUT \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/pulls/PR_NUMBER/merge \
  -d '{"merge_method":"squash"}'
```

## PR Templates

Keep a `~/.hermes/templates/pr_body.md`:

```markdown
## Summary
<!-- What does this PR do? -->

## Changes
- 

## Testing
- [ ] Unit tests
- [ ] Integration tests  
- [ ] Manual QA

## Screenshots
<!-- If applicable -->
```

## Conflict Resolution

```bash
# Update branch with latest main
git fetch origin
git rebase origin/main

# If conflicts arise:
git status                          # see conflicted files
git diff --diff-filter=U            # see conflict markers
# edit files to resolve
git add <resolved-file>
git rebase --continue

# Abort rebase
git rebase --abort
```

## Cleanup

```bash
# Delete local branch after merge
git branch -d feat/my-feature

# Prune remote tracking branches
git remote prune origin

# Delete remote branch manually
git push origin --delete feat/my-feature
```

## GitHub CLI Shortcuts

```bash
gh pr list                          # list open PRs
gh pr checkout 123                  # checkout PR #123
gh pr diff 123                      # show PR diff
gh pr comment 123 -b "LGTM!"       # add comment
gh pr ready 123                     # mark draft as ready
gh pr close 123                     # close without merging
```

## Signing Commits (Optional)

```bash
# Sign with SSH key (git 2.34+)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true

# Verify signatures
git log --show-signature
```

## Pitfalls

1. **Pushing directly to main is rejected by branch protection**: Always create a feature branch first (`git checkout -b fix/my-fix`). If you accidentally committed to main, use `git branch fix/my-fix && git reset --hard origin/main` to recover your work onto a new branch.

2. **Stale branch accumulates conflicts over time**: Long-lived branches diverge from main and become painful to merge. Run `git fetch origin && git rebase origin/main` at least daily on active branches. Use `git log --oneline origin/main..HEAD` to see how far behind you are.

3. **`git add .` stages unintended files**: Build artifacts, `.env` files, and editor configs sneak in. Always use `git add -p` for interactive staging, and verify with `git diff --cached` before committing. Retroactively fix with `git rm --cached <file>` and update `.gitignore`.

4. **CI fails due to missing secrets in fork PRs**: Workflows that reference `${{ secrets.API_KEY }}` silently receive empty values on fork PRs for security reasons. In GitHub Actions settings, explicitly enable "Allow fork pull requests to access secrets" only for trusted collaborators, or redesign the workflow to skip secret-dependent steps on forks.

5. **PR created against wrong base branch**: `gh pr create` defaults to the repository's default branch. When targeting a release branch explicitly pass `--base release/2.0`. Verify afterward with `gh pr view --json baseRefName`; change it with `gh pr edit --base <correct-branch>` before review begins.

6. **Squash merge silently discards intermediate commit history**: After `gh pr merge --squash`, individual commits are gone and `git bisect` granularity is lost. If bisectability or audit trail matters, use `--merge` instead. Decide merge strategy as a team convention and document it in `CONTRIBUTING.md`.

7. **`gh pr checks --watch` exits immediately when checks are still queued**: If CI runners are busy, checks may not have started yet and the command reports 0 results then exits. Use a retry loop: `until gh pr checks 2>&1 | grep -qE '(pass|fail|error)'; do echo 'Waiting for checks...'; sleep 15; done && gh pr checks --watch` to poll until at least one check is active.
