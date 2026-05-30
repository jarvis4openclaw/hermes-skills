---
name: cloudflare-pages-deploy
description: Deploy static sites to Cloudflare Pages via wrangler CLI — project creation, direct upload, custom domains, DNS/SSL, GitHub auto-deploy, and token management.
category: devops
tags: [cloudflare, pages, deploy, static-site, wrangler, dns, custom-domain]
---

# Cloudflare Pages Deploy

Deploy static sites (HTML/CSS/JS/JSON) to Cloudflare Pages using `wrangler` direct upload — no Git integration required. Handles project creation, deployment, custom domain setup, and DNS/SSL provisioning.

## When to Use

- User wants to host a static site on Cloudflare Pages
- User already has Cloudflare DNS and wants a custom domain on Pages
- Deploying a site from a local directory (not via Git integration)
- Site has no build step — raw static files ready to serve

## Prerequisites

- **Cloudflare API Token** with `Account.Cloudflare Pages:Edit` permission
  - Create at: https://dash.cloudflare.com/profile/api-tokens
  - Permission: Account → Cloudflare Pages → Edit
- **Account ID** from Cloudflare dashboard (sidebar or URL)
- **Node.js** available (`npx` is enough — wrangler auto-installs)

## Workflow

### 1. Export Credentials

```bash
export CLOUDFLARE_API_TOKEN=<token>
export CLOUDFLARE_ACCOUNT_ID=<account_id>
```

Store the token securely (e.g., `~/.hermes/.env`). Never commit it.

### 2. Create the Pages Project

```bash
npx wrangler pages project create <project-name> --production-branch=main
```

This returns the `*.pages.dev` URL. Project creation is idempotent — re-running when it exists returns an error (8000007), which is fine.

### 3. Deploy Static Files

```bash
cd /path/to/site
npx wrangler pages deploy . --project-name=<project-name>
```

All files in the directory are uploaded. The deploy returns a preview URL (`<hash>.<project>.pages.dev`) and the site is live immediately at `<project>.pages.dev`.

### 4. Add Custom Domain

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/<project>/domains" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"subdomain.example.com"}'
```

Cloudflare auto-provisions SSL (Google CA) and attempts DNS setup for same-account zones.

### 5. Verify Deployment

Check domain status:
```bash
curl -s \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/<project>/domains/<domain>" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

Fields to watch: `status`, `verification_data.status`, `validation_data.status`.

Test the site:
```bash
curl -sL "http://<project>.pages.dev" | head -20   # verify content served
```

## GitHub Auto-Deploy Setup

After initial deploy, choose one of these two approaches for push-to-deploy:

### Option A: Cloudflare Pages Native Git Integration (Recommended)

One-time setup in the Cloudflare Dashboard — no YAML, no tokens, no maintenance:

1. **Cloudflare Dashboard → Pages → <project> → Settings → Builds & deployments**
2. Click **Connect to Git** → authorize GitHub
3. Select the repo and set production branch to `main`

Every `git push` auto-deploys. Zero workflow files needed. This is the cleanest approach when the repo is on GitHub.

### Option B: GitHub Actions

Use `wrangler-action` to deploy on push. Create `.github/workflows/deploy.yml` (template in `references/github-actions-workflow.yml`).

**Prerequisites:**
- `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as GitHub repository secrets:
  ```bash
  gh secret set CLOUDFLARE_API_TOKEN --body "cfut_xxxx"
  gh secret set CLOUDFLARE_ACCOUNT_ID --body "239c7bfe..."
  ```
- GitHub token MUST have `workflow` scope to push `.github/workflows/` files. If push is rejected with "refusing to allow a Personal Access Token to create or update workflow without `workflow` scope", either:
  - Switch to Option A (native Git integration — no token scope issue), or
  - Refresh the GitHub token via `gh auth refresh -h github.com -s workflow`

## Pitfalls

### DNS Auto-Provisioning Stall

**Symptom:** Custom domain stays `pending` for minutes after adding. `dig` returns no resolution.

**Cause:** Cloudflare Pages sometimes doesn't auto-create the CNAME DNS record even for same-account zones, or it delays.

**Fix:** Manually create the CNAME record (via API if token has `Zone:DNS:Edit`, or in dashboard):
- Name: `<subdomain>` (e.g., `wallets`)
- Target: `<project>.pages.dev`
- Proxy: ON (orange cloud)

SSL provisions automatically once the CNAME resolves.

### Token Scope Strategy

Two tiers of API token, depending on how much automation you want:

| Tier | Permissions | Can Do |
|------|------------|--------|
| **Minimal** | `Pages:Edit` only | Create/deploy projects, add custom domains. DNS must be done in dashboard. |
| **Full** | `Pages:Edit` + `Zone:DNS:Edit` + `SSL:Edit` | Everything above + create DNS CNAME records programmatically. Use when the user wants CLI-driven DNS management. |

Use minimal by default; upgrade to full only when the user explicitly asks for DNS automation.

### Project Not Found (Error 8000007)

`wrangler pages deploy` requires the project to exist first. Run `wrangler pages project create` before deploying.

### SSL Certificate Delay

New deployments + custom domains take 1-5 minutes for SSL provisioning. The pages.dev URL may return TLS errors during this window. HTTP (non-SSL) access typically works immediately and redirects to HTTPS once the cert is ready.

### Stale DNS After Domain Move

**Symptom:** After moving a custom domain from Project A to Project B, `wallets.wahid.my` returns HTTP 522 (connection timeout) even though the domain was added to Project B.

**Cause:** The DNS CNAME record still points to `<old-project>.pages.dev`. Cloudflare doesn't auto-update the CNAME when you move a domain between projects.

**Fix:** Manually update the CNAME target via API or dashboard to point to `<new-project>.pages.dev`. See "Moving a Domain Between Projects" above for the exact API commands.

### GitHub Token Workflow Scope

GitHub Personal Access Tokens without `workflow` scope cannot push `.github/workflows/` files. The error is: `refusing to allow a Personal Access Token to create or update workflow without 'workflow' scope`. Fix by refreshing the token or using Cloudflare's native Git integration instead.

### Moving a Domain Between Projects

When the user creates a replacement project (e.g., switching from direct-upload to Git-connected), you need to move the custom domain:

**Step 1 — Remove domain from old project:**
```bash
curl -s -X DELETE \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/<old-project>/domains/<domain>" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

**Step 2 — Add domain to new project:**
```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects/<new-project>/domains" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"subdomain.example.com"}'
```

**Step 3 — Update DNS CNAME** (the old CNAME still points to the old project's pages.dev):
```bash
# Find the CNAME record
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=CNAME&name=<domain>" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"

# Update its content to the new project
curl -s -X PATCH \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/<record_id>" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"<new-project>.pages.dev"}'
```

Token needs `Zone:DNS:Edit` for the DNS update step.

### Git-Connected Project: Build Settings

When creating a Pages project **with Git integration** (Cloudflare Dashboard → Pages → Create → Connect to Git):

- **Framework preset:** `None` (for raw static sites with no framework)
- **Build command:** Leave **BLANK** — no build step needed
- **Build output directory:** `.` (or `/` — site files are at repo root)

Cloudflare defaults to `npx wrangler deploy` which is for Workers, not static Pages. Override it.

### CDN Cache Staleness on Custom Domains

**Symptom:** `git push` → deploy succeeds, hash URL (`<hash>.<project>.pages.dev`) shows correct content, but the custom domain still serves old/previous content.

**Cause:** Cloudflare Pages custom domains route through the CDN, which caches HTML aggressively. The `<hash>.<project>.pages.dev` URL bypasses this cache layer and always serves fresh.

**Fix:**

1. **Verify the truth:** Always check the latest hash deploy URL first:
   ```bash
   curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<name>/deployments?per_page=1" \
     -H "Authorization: Bearer $TOKEN" | python3 -c "
   import json,sys; d=json.load(sys.stdin)['result'][0]
   print(d.get('url','?'))
   "
   ```
   If the hash URL shows correct content → deploy is good. The custom domain just has stale cache.

2. **User-side fix:** Hard refresh (`Ctrl+Shift+R` or `Cmd+Shift+R`). Cache usually expires in ~15 minutes.

3. **Purge (if token has Zone permissions):**
   ```bash
   curl -s -X POST "https://api.cloudflare.com/client/v4/zones/<zone_id>/purge_cache" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"files":["https://custom.domain/path"]}'
   ```
   Requires `Zone:Cache:Purge` permission. Pages API tokens usually don't have this.

**Key insight:** NEVER conclude a deploy failed just because the custom domain shows old content. Always check the hash deploy URL first — it's the ground truth.

### Lightning Donate Button (Companion Pattern)

See `references/lightning-donate-button.md` — floating donate FAB + modal with BOLT12 offer QR (reusable) or BOLT11 invoice QR (one-shot). Use BOLT12 for any static/permanent donate button; BOLT11 is for temporary/demo use only.

## Commands Reference

| Action | Command |
|--------|---------|
| Create project | `npx wrangler pages project create <name> --production-branch=main` |
| Deploy directory | `npx wrangler pages deploy <dir> --project-name=<name>` |
| Add custom domain | `POST /accounts/:id/pages/projects/:name/domains` |
| Check domain status | `GET /accounts/:id/pages/projects/:name/domains/:domain` |
| Delete domain | `DELETE /accounts/:id/pages/projects/:name/domains/:domain` |
| Update DNS CNAME | `PATCH /zones/:id/dns_records/:rid` with `{"content":"new-target"}` |
| List deployments | `npx wrangler pages deployment list --project-name=<name>` |

## See Also

- `references/cloudflare-pages-api.md` — full API reference for Pages endpoints
- `references/lightning-donate-button.md` — floating Lightning donate button + QR modal pattern
- `render-deploy` — alternative for Render hosting
