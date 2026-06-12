---
name: github-auth
description: Set up GitHub authentication for the agent using git (universally available) or the gh CLI. Covers HTTPS tokens, SSH keys, credential helpers, and gh auth — with a detection flow to pick the right method automatically.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Authentication, Git, gh-cli, SSH, Setup]
    related_skills: [github-pr-workflow, github-code-review, github-issues, github-repo-management]
    trigger_conditions:
      - user needs to authenticate with GitHub for git operations
      - user gets authentication errors on git push, pull, or clone
      - user needs to set up a personal access token or SSH key for GitHub
      - user asks how to configure gh CLI authentication
      - user is setting up a new machine or environment to work with GitHub
      - user encounters "Permission denied", "Authentication failed", or 403 errors from GitHub
      - phrases: "github login", "git auth", "set up github", "personal access token", "ssh key github"
---

# GitHub Authentication Setup

This skill sets up authentication so the agent can work with GitHub repositories, PRs, issues, and CI. It covers two paths:

- **`git` (always available)** — uses HTTPS personal access tokens or SSH keys
- **`gh` CLI (if installed)** — richer GitHub API access with a simpler auth flow

## When to Use

- First-time GitHub setup on a new machine or container
- `git push` fails with "Authentication failed" or "Permission denied"
- `gh auth status` shows "not authenticated"
- Setting up a Personal Access Token (PAT) for API access
- Configuring SSH key authentication for passwordless git operations
- Switching between multiple GitHub accounts on one machine
- Extracting credentials from git's credential store for API scripts
- Resolving expired token / stale credential issues

## Not For

- **Creating/managing GitHub repos** → use `github-repo-management` instead
- **Submitting pull requests** → use `github-pr-workflow` instead
- **Reviewing PRs** → use `github-code-review` instead
- **Managing issues** → use `github-issues` instead
- **Git workflow basics (commit, branch, merge)** → use git directly or `github-pr-workflow`
- **GitHub Actions / CI configuration** → this is YAML-based; not auth-related
- **OAuth app / GitHub App setup** → this skill covers personal auth only

## Detection Flow

When a user asks you to work with GitHub, run this check first:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Decision tree:**
1. If `gh auth status` shows authenticated → you're good, use `gh` for everything
2. If `gh` is installed but not authenticated → use "gh auth" method below
3. If `gh` is not installed → use "git-only" method below (no sudo needed)

---

## Method 1: Git-Only Authentication (No gh, No sudo)

This works on any machine with `git` installed. No root access needed.

### Option A: HTTPS with Personal Access Token (Recommended)

This is the most portable method — works everywhere, no SSH config needed.

**Step 1: Create a personal access token**

Tell the user to go to: **https://github.com/settings/tokens**

- Click "Generate new token (classic)"
- Give it a name like "hermes-agent"
- Select scopes:
  - `repo` (full repository access — read, write, push, PRs)
  - `workflow` (trigger and manage GitHub Actions)
  - `read:org` (if working with organization repos)
- Set expiration (90 days is a good default)
- Copy the token — it won't be shown again

**Step 2: Configure git to store the token**

```bash
# Set up the credential helper to cache credentials
# "store" saves to ~/.git-credentials in plaintext (simple, persistent)
git config --global credential.helper store

# Now do a test operation that triggers auth — git will prompt for credentials
# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

After entering credentials once, they're saved and reused for all future operations.

**Alternative: cache helper (credentials expire from memory)**

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'
```

**Alternative: set the token directly in the remote URL (per-repo)**

```bash
# Embed token in the remote URL (avoids credential prompts entirely)
git remote set-url origin https://<username>:<token>@github.com/<owner>/<repo>.git
```

**Step 3: Configure git identity**

```bash
# Required for commits — set name and email
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

**Step 4: Verify**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --global user.name
git config --global user.email
```

### Option B: SSH Key Authentication

Good for users who prefer SSH or already have keys set up.

**Step 1: Check for existing SSH keys**

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"
```

**Step 2: Generate a key if needed**

```bash
# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""

# Display the public key for them to add to GitHub
cat ~/.ssh/id_ed25519.pub
```

Tell the user to add the public key at: **https://github.com/settings/keys**
- Click "New SSH key"
- Paste the public key content
- Give it a title like "hermes-agent-<machine-name>"

**Step 3: Test the connection**

```bash
ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."
```

**Step 4: Configure git to use SSH for GitHub**

```bash
# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

**Step 5: Configure git identity**

```bash
git config --global user.name "Their Name"
git config --global user.email "their-email@example.com"
```

---

## Method 2: gh CLI Authentication

If `gh` is installed, it handles both API access and git credentials in one step.

### Interactive Browser Login (Desktop)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

### Token-Based Login (Headless / SSH Servers)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

### Verify

```bash
gh auth status
```

---

## Using the GitHub API Without gh

When `gh` is not available, you can still access the full GitHub API using `curl` with a personal access token. This is how the other GitHub skills implement their fallbacks.

### Setting the Token for API Calls

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="***"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

### Extracting the Token from Git Credentials

If git credentials are already configured (via credential.helper store), the token can be extracted:

```bash
# Read from git credential store
grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|'
```

### Helper: Detect Auth Method

Use this pattern at the start of any GitHub workflow:

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=***
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=***
elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=*** ~/.hermes/.env; then
  export GITHUB_TOKEN=*** "^GITHUB_TOKEN=*** ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  echo "AUTH_METHOD=***
elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
  export GITHUB_TOKEN=*** "github.com" ~/.git-credentials | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
  echo "AUTH_METHOD=***
else
  echo "AUTH_METHOD=***
  echo "Need to set up authentication first"
fi
```

---

## Pitfalls

1. **Token missing required scopes causes silent 403 failures** — A PAT created with only `public_repo` scope will silently fail on private repos. Fix: use `repo` + `workflow` + `read:org` as the baseline. If an operation returns HTTP 403, regenerate the token with broader scopes.

2. **Expired token produces cryptic authentication errors** — When a stored token expires, `git push` returns `fatal: Authentication failed` with no hint about expiry. Fix: check token expiry at https://github.com/settings/tokens. Clear stale credentials with `git credential reject`, then re-authenticate.

3. **SSH key generated but not loaded into ssh-agent** — Generating a key file is not sufficient — it must be loaded into the running ssh-agent for passwordless use. Fix: run `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519`. Add to `~/.bashrc` for persistence.

4. **Multiple GitHub accounts collide in the credential store** — The `store` helper saves one credential per host, so adding a second GitHub account overwrites the first. Fix: use SSH with different host aliases in `~/.ssh/config`, or embed tokens directly in per-repo remote URLs.

5. **Port 22 blocked on corporate or cloud networks** — `ssh -T git@github.com` hangs silently. Fix: add to `~/.ssh/config`:
   ```
   Host github.com
     Hostname ssh.github.com
     Port 443
     User git
   ```

6. **gh auth setup-git not run after gh auth login** — `gh auth login` authenticates the CLI but does NOT configure git's credential helper. Fix: always run `gh auth setup-git` immediately after login.

7. **Global git identity leaks personal email into work commits** — `--global user.email` applies to every repo on the machine. Fix: use `git config --local user.email "work@company.com"` inside specific repos to override.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `git push` asks for password | GitHub disabled password auth. Use a personal access token as the password, or switch to SSH |
| `remote: Permission to X denied` | Token may lack `repo` scope — regenerate with correct scopes |
| `fatal: Authentication failed` | Cached credentials may be stale — run `git credential reject` then re-authenticate |
| `ssh: connect to host github.com port 22: Connection refused` | Try SSH over HTTPS port: add `Host github.com` with `Port 443` and `Hostname ssh.github.com` to `~/.ssh/config` |
| Credentials not persisting | Check `git config --global credential.helper` — must be `store` or `cache` |
| Multiple GitHub accounts | Use SSH with different keys per host alias in `~/.ssh/config`, or per-repo credential URLs |
| `gh: command not found` + no sudo | Use git-only Method 1 above — no installation needed |
