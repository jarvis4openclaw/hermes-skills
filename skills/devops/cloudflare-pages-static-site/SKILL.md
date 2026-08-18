---
name: cloudflare-pages-static-site
description: Deploy static sites to Cloudflare Pages with custom domains, auto-deploy from Git, and wrangler CLI.
tags: [cloudflare, pages, static-site, deployment, dns, cdn]
version: 1.1.0
metadata:
  hermes:
    tags: [cloudflare, pages, static-site, deployment, dns, cdn]
    trigger_conditions:
      - "deploy static site to Cloudflare Pages"
      - "Cloudflare Pages custom domain"
      - "wrangler pages deploy"
      - "pages.dev shows old content"
      - "production branch mismatch Cloudflare"
      - "CDN cache stale custom domain"
      - "move domain between Pages projects"
      - "auto-deploy static site from git push"
      - "Cloudflare Pages DNS CNAME"
      - "check Cloudflare Pages deployment status"
      - "Cloudflare Pages build output directory"
      - "create Cloudflare Pages project"
      - "wallets.wahidsaleemi.net or bitcoin-fits deploy"
---

# Cloudflare Pages Static Site Deployment

Deploy HTML/CSS/JS static sites to Cloudflare Pages with zero build steps, custom domains, and Git auto-deploy.

## When to Use

- Pure static sites (no backend, no framework build step)
- Free hosting with global CDN + auto HTTPS
- Custom domains already on Cloudflare DNS
- Want auto-deploy on every `git push`

## Not For

- **Workers/APIs or dynamic backends** → use `cloudflare-temp-accounts` or a Workers skill; Pages is static-only.
- **Deploying a generated site with a build step** (Next.js, Astro SSR) → use `cloudflare-pages-deploy` (build-aware) instead.
- **Non-Cloudflare hosting** (VPS, StartOS, Nginx Proxy Manager) → use the relevant self-hosting skill.
- **Debugging DNS/zone-level issues unrelated to Pages** → use `caddy-proxy-management` / `nginx-proxy-manager-native` as appropriate.

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

## Pitfalls (numbered)

1. **Production branch mismatch (the silent-deploy trap)** — `git push` succeeds and a hash URL deploys, but `pages.dev`/custom domain still serve old content. Root cause: the Pages project's `production_branch` ≠ repo default branch. Always check via the API (`/projects/<name>` → `production_branch`) and PATCH it to match, then retrigger a deployment. See the CRITICAL PITFALL section above for exact curl commands.
2. **CDN cache staleness on custom domains** — custom domains route through the CDN which caches HTML; the hash URL bypasses that layer. ALWAYS verify with the hash deploy URL first — it is ground truth. Custom-domain staleness = cache, not deploy failure. Hard refresh or wait ~15 min.
3. **`npx wrangler` auto-install can fail on first run** — if `npx` prompts for install confirmation in a non-TTY/cron context it hangs. Run `npx --yes wrangler ...` or install wrangler explicitly (`npm i -g wrangler`) before scripting deploys.
4. **API token scope mismatch** — the token needs BOTH `Account:Cloudflare Pages:Edit` AND `Zone:DNS:Edit`. A Pages-only token 403s on domain/DNS calls. Verify with `wrangler whoami` before starting.
5. **CNAME not auto-created on cross-zone domains** — Cloudflare auto-creates the CNAME only when the domain is in the same zone as the project. For external zones, create the CNAME manually and point it at `<project>.pages.dev`.
6. **`Authorization: Bearer ***` in pasted snippets** — masked tokens in docs/chat are display artifacts. Always read the real token from the env/credential store; never paste a masked value into a curl call.
7. **Deployment `latest_stage.status` is not final** — a "success" stage can still be followed by a failed route/dns step. Check the domain `status` and `validation_data.status` too (see Verification section).
8. **Production branch change needs a retrigger** — PATCHing `production_branch` does NOT redeploy automatically. POST a fresh deployment on the corrected branch afterward.
9. **`git add` on the wrong branch** — the Pages Git integration deploys whatever branch is marked production. Committing to a feature branch will NOT update the live site; push to the production branch.
10. **Domain move leaves a stale CNAME** — when moving a domain between projects, delete the old project's domain FIRST, then add to the new project, then update the CNAME. Leaving the old record pointing at the retired project keeps serving old content.

## References

- `references/cloudflare-pages-api.md` — Full API curl examples
- `references/wrangler-commands.md` — Common wrangler CLI patterns
