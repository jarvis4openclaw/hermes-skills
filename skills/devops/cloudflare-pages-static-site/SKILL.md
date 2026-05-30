---
name: cloudflare-pages-static-site
description: Deploy static sites to Cloudflare Pages with custom domains, auto-deploy from Git, and wrangler CLI.
tags: [cloudflare, pages, static-site, deployment, dns, cdn]
version: 1.0.0
---

# Cloudflare Pages Static Site Deployment

Deploy HTML/CSS/JS static sites to Cloudflare Pages with zero build steps, custom domains, and Git auto-deploy.

## When to Use

- Pure static sites (no backend, no framework build step)
- Free hosting with global CDN + auto HTTPS
- Custom domains already on Cloudflare DNS
- Want auto-deploy on every `git push`

## Prerequisites

- Cloudflare API token with permissions: `Account:Cloudflare Pages:Edit`, `Zone:DNS:Edit`
- `npx wrangler` available (auto-installed on first use)
- GitHub repo with static files at root or a subdirectory

## Quick Deploy (wrangler CLI)

```bash
# Set env vars (or use .env)
export CLOUDFLARE_API_TOKEN=<token>
export CLOUDFLARE_ACCOUNT_ID=<account_id>

# Create project (one time)
npx wrangler pages project create <project-name> --production-branch=main

# Deploy current directory
npx wrangler pages deploy . --project-name=<project-name>
```

## Custom Domain

### Add domain to Pages project

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project-name>/domains" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"subdomain.example.com"}'
```

### Update DNS CNAME (same-account zone)

Cloudflare usually auto-creates the CNAME. If not:

```bash
# Find record
curl -s "https://api.cloudflare.com/client/v4/zones/<zone_id>/dns_records?type=CNAME&name=subdomain.example.com" \
  -H "Authorization: Bearer $TOKEN"

# Update
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/<zone_id>/dns_records/<record_id>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"<project-name>.pages.dev"}'
```

## Git-Connected Auto-Deploy (Recommended)

1. Cloudflare Dashboard → Pages → Project → Settings → Builds & deployments
2. Connect to Git → authorize GitHub → select repo
3. **Build command**: leave blank (static site, no build)
4. **Build output directory**: `.` (or subdirectory)
5. **Production branch**: MUST match your repo's default branch (`main`, `master`, etc.)

Every `git push` to the production branch triggers an automatic deployment.

## ⚠️ CRITICAL PITFALL: Production Branch Mismatch

**Symptom**: `git push` deploys successfully (new hash URL works) but `pages.dev` and custom domain still show old content.

**Root cause**: Cloudflare Pages production branch ≠ repo default branch.

**Check:**
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project-name>" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)['result']
print(f'Production branch: {d[\"production_branch\"]}')
"
```

**Fix:**
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project-name>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"production_branch":"main"}'
```

Then retrigger a deployment:
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project-name>/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"branch":"main"}'
```

## Verification

```bash
# Check latest deployment
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project-name>/deployments?per_page=1" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)['result'][0]
print(f'Status: {d[\"latest_stage\"][\"status\"]} | Commit: {d[\"deployment_trigger\"][\"metadata\"].get(\"commit_hash\",\"?\")[:8]}')
print(f'URL: {d.get(\"url\",\"?\")}')
"

# Check domain status
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project-name>/domains/<domain>" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)['result']
print(f'Status: {d[\"status\"]} | SSL: {d[\"validation_data\"][\"status\"]}')
"
```

## Moving a Domain Between Projects

1. Delete domain from old project
2. Add domain to new project
3. Update DNS CNAME to point to new project's `pages.dev` URL

## ⚠️ PITFALL: CDN Cache Staleness on Custom Domains

**Symptom:** Deploy succeeds but custom domain shows old content, even though `<hash>.<project>.pages.dev` shows the new content.

**Cause:** Custom domains route through CDN which caches HTML. Hash URLs bypass this cache layer.

**Rule:** ALWAYS verify with the hash deploy URL first — it's ground truth. Custom domain stale = cache, not deploy failure. Hard refresh or wait 15 min.

## References

- `references/cloudflare-pages-api.md` — Full API curl examples
- `references/wrangler-commands.md` — Common wrangler CLI patterns
