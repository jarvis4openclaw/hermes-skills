---
name: github-issues
description: Create, manage, triage, and close GitHub issues. Search existing issues, add labels, assign people, and link to PRs. Works with gh CLI or falls back to git + GitHub REST API via curl.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Issues, Project-Management, Bug-Tracking, Triage]
    related_skills: [github-auth, github-pr-workflow]
    trigger_conditions:
      - "create issue"
      - "report a bug"
      - "file a ticket"
      - "triage issues"
      - "manage GitHub issues"
      - "add label to issue"
      - "close issue"
      - "search for existing issues"
---

# GitHub Issues

Create, manage, triage, and close GitHub issues using the `gh` CLI or GitHub REST API.

## When to Use

- **Bug reporting**: Documenting reproducible defects with steps to reproduce, expected behavior, and actual behavior before a fix exists.
- **Feature requests**: Proposing enhancements with context and acceptance criteria prior to any implementation work.
- **Batch triage**: Processing a backlog of unlabeled or unassigned issues in a structured, repeatable workflow.
- **Release tracking**: Grouping issues into milestones to monitor progress toward a version or delivery deadline.
- **Cross-team coordination**: Assigning issues to specific team members and tracking resolution status across a project.

## Not For

- **Pull request management**: Use `github-pr-workflow` skill to create branches, open PRs, monitor CI, and merge code.
- **Code review**: Use `github-code-review` skill for inline comments, approval workflows, and review requests.
- **Real-time team communication**: GitHub Issues are asynchronous; use Slack, Teams, or similar tools for immediate coordination.
- **CI/CD pipeline management**: Use GitHub Actions skills for workflow configuration, secrets, and run monitoring.

## Prerequisites

- `gh` CLI authenticated (`gh auth status`)
- Repository context: either `cd` into repo or use `--repo OWNER/REPO`

## Creating Issues

```bash
# Interactive creation (opens editor)
gh issue create

# Non-interactive with body
gh issue create \
  --title "Bug: Login fails on Safari" \
  --body "## Steps to reproduce\n1. ...\n2. ...\n\n## Expected\n...\n\n## Actual\n..." \
  --label bug \
  --assignee @me

# From a template
gh issue create --template bug_report.md

# On a specific repo
gh issue create --repo owner/repo --title "..."
```

## Viewing and Searching Issues

```bash
# List open issues
gh issue list

# Filter by label
gh issue list --label bug --label enhancement

# Filter by assignee
gh issue list --assignee @me

# Search by keyword
gh issue list --search "memory leak"

# View specific issue
gh issue view 42
gh issue view 42 --web   # open in browser

# List closed issues
gh issue list --state closed

# JSON output for scripting
gh issue list --json number,title,labels,assignees --limit 100
```

## Editing Issues

```bash
# Add labels
gh issue edit 42 --add-label bug,urgent

# Remove label
gh issue edit 42 --remove-label wontfix

# Change assignee
gh issue edit 42 --add-assignee username

# Change title
gh issue edit 42 --title "Updated title"

# Add to milestone
gh issue edit 42 --milestone "v2.0"

# Add to project (GitHub Projects v2)
gh issue edit 42 --project "My Project"
```

## Commenting on Issues

```bash
# Add a comment
gh issue comment 42 -b "Investigating this now."

# Edit your last comment
gh issue comment 42 --edit-last -b "Updated info"
```

## Closing and Reopening

```bash
# Close issue
gh issue close 42

# Close with comment
gh issue close 42 -c "Fixed in #67"

# Reopen
gh issue reopen 42
```

## Bulk Operations

```bash
# Close multiple issues
gh issue close 42 43 44

# Transfer issue to another repo
gh issue transfer 42 owner/other-repo

# Pin an issue
gh issue pin 42
gh issue unpin 42

# Lock an issue
gh issue lock 42 --reason spam
gh issue unlock 42
```

## Linking Issues to PRs

In PR description, use:
```
Closes #42
Fixes #42
Resolves #42
```

Or link via CLI:
```bash
# Check PR/issue links
gh pr view --json closingIssuesReferences
```

## Fallback: REST API

```bash
# Create issue
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/issues \
  -d '{"title":"Bug: ...","body":"...","labels":["bug"]}'

# List issues
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/issues?state=open

# Update issue
curl -X PATCH \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/issues/42 \
  -d '{"state":"closed","state_reason":"completed"}'

# Add comment
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/issues/42/comments \
  -d '{"body":"Fixed in commit abc123"}'
```

## Issue Templates

```bash
# View available templates
ls .github/ISSUE_TEMPLATE/

# Create an issue from template URL
open "https://github.com/owner/repo/issues/new?template=bug_report.md"
```

## Labels and Milestones

```bash
# List all labels
gh label list

# Create a label
gh label create priority-high --color FF0000 --description "High priority"

# Delete a label
gh label delete old-label

# List milestones
gh api repos/:owner/:repo/milestones | jq '.[].title'

# Create milestone
gh api repos/:owner/:repo/milestones -X POST \
  -f title="v2.0" -f due_on="2025-12-31T00:00:00Z"
```

## Triage Workflow

```bash
# Morning triage — list unlabeled issues (use REST API for reliability)
gh api repos/:owner/:repo/issues?state=open\&per_page=100 | \
  jq '.[] | select(.labels | length == 0) | .number'

# Apply triage label
gh issue edit <number> --add-label needs-triage

# Batch triage script
for num in 10 11 12 13; do
   gh issue edit $num --add-label triaged --remove-label needs-triage
done
```

## Pitfalls

1. **Creating duplicate issues wastes triage time**: Always search before filing: `gh issue list --search "keyword"` and `gh issue list --search "keyword" --state closed`. Close duplicates immediately with `gh issue close <num> -c "Duplicate of #<original>"` and add the `duplicate` label.

2. **`gh issue list --label ""` does not reliably filter for unlabeled issues**: The empty-string label argument behavior varies across gh CLI versions and may return all issues or error out. Use the REST API instead: `gh api 'repos/:owner/:repo/issues?state=open&per_page=100' | jq '.[] | select(.labels | length == 0) | .number'`.

3. **Label names are case-sensitive**: `Bug` and `bug` are distinct labels. Scripted bulk operations silently fail when the label name doesn't exactly match. Always run `gh label list` to confirm exact names and colors before writing automation scripts.

4. **Issue metadata is partially lost on repo transfer**: `gh issue transfer 42 owner/other-repo` moves the issue body and comments, but project board cards, milestone associations, and cross-repo references are not preserved. Before transferring, add a comment documenting the original repo and issue number, and manually re-add project/milestone associations after the transfer.

5. **Closing issues without linking the fix breaks traceability**: `gh issue close 42` leaves no audit trail. Always use `gh issue close 42 -c "Fixed in PR #<number>"` or include `Closes #42` in the PR body for automatic closure with a traceable link between the issue and the resolving commit.

6. **`--edit-last` flag requires gh CLI >= 2.20**: `gh issue comment 42 --edit-last` is not available in older installations and will throw an unknown flag error. Check your version with `gh --version`. If outdated, upgrade via `brew upgrade gh` or your package manager, or edit the comment via web with `gh issue view 42 --web`.

7. **Missing `--repo` flag silently targets the wrong repository**: Running `gh issue list` outside a cloned git directory, or inside a different repo's directory, targets an unexpected repository without warning. Always append `--repo OWNER/REPO` when scripting from non-repo directories such as cron jobs, CI pipelines, or home directories.
