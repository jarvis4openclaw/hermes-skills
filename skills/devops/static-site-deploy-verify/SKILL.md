---
name: static-site-deploy-verify
description: >
  Verify that static site deployments on git-connected platforms are actually live on the production URL.
  Use after any `git push` to Cloudflare Pages, Vercel, Netlify, GitHub Pages, Render static sites,
  or similar hosts. Trigger when the user says "I don't see my changes" or after declaring a deploy
  successful. Catches production branch mismatches, stale CDN cache, and preview-vs-production drift.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [deploy, static-site, cloudflare, vercel, netlify, github-pages, verify, git]
    related_skills: [ssh-file-deploy, render-deploy, maintain-personal-web-app]
---

# Static Site Deploy Verification

Prevent "I don't see my changes" by verifying the production URL — not just the build status.

## When to Use

- Immediately after `git push` to a static site host with auto-deploy
- When a user reports missing updates on their live site
- After fixing a production branch or DNS setting and declaring success
- Before telling a user "your changes are live"

## Not For

- Server-side app deployments with health checks (use platform-specific skills)
- SSH-based file transfers (use `ssh-file-deploy`)
- Docker/container deploys (use `render-deploy`)

## Steps

### 1. Confirm Build Success

Check that the platform registered the push and the build succeeded.

**Cloudflare Pages:**
```bash
TOKEN=$(grep CLOUDFLARE_PAGES_API_KEY ~/.hermes/.env | cut -d= -f2)
ACCT=<account_id>
PROJECT=<project_name>

curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/$PROJECT/deployments?per_page=1" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)['result'][0]
print(f\"Status: {d['latest_stage']['name']} = {d['latest_stage']['status']}\")
print(f\"Commit: {d['deployment_trigger']['metadata'].get('commit_hash','?')[:8]}\")
print(f\"Branch: {d['deployment_trigger']['metadata'].get('branch','?')}\")
"
```

**Vercel / Netlify / GitHub Pages:** Check the dashboard or use their respective CLIs (`vercel --version`, `netlify status`).

### 2. Verify Production Branch Alignment

**Critical:** Ensure the platform's "production branch" matches the git branch you push to.

```bash
# Cloudflare Pages — check production_branch
TOKEN=$(grep CLOUDFLARE_PAGES_API_KEY ~/.hermes/.env | cut -d= -f2)
ACCT=<account_id>
PROJECT=<project_name>

curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/$PROJECT" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)['result']
print(f\"Production branch: {d['production_branch']}\")
"

# Compare to your local branch
LOCAL_BRANCH=$(git branch --show-current)
echo "Local branch: $LOCAL_BRANCH"
```

If they differ, update the platform setting:
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/$PROJECT" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"production_branch\":\"$LOCAL_BRANCH\"}"
```

### 3. Verify Production URL Content

**Always check the production URL, not just the unique deploy hash URL.**

```bash
PROD_URL="https://example.com"

echo "=== Production URL check ==="
CONTENT=$(curl -s --max-time 15 "$PROD_URL")

# Replace with markers specific to your recent change
echo "$CONTENT" | grep -q "<your-new-content>" && echo "✅ Change visible on production" || echo "❌ Change NOT on production"
```

For JavaScript-rendered sites, also check the served JS/CSS files:
```bash
curl -s --max-time 15 "$PROD_URL/app.js" | grep -q "<new-js-marker>" && echo "✅ JS updated" || echo "❌ JS stale"
```

### 4. Handle CDN Cache Staleness

If the production URL shows old content but the deploy hash URL shows new content, the CDN cache is stale.

**User-side fix (tell the user):**
```
Ctrl + Shift + R   (hard refresh)
```

**Server-side purge (if API permissions allow):**
```bash
# Cloudflare zone purge (requires Zone:Edit permission)
TOKEN=<zone_api_token>  # often different from Pages token
ZONE=<zone_id>

curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/purge_cache" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"purge_everything":true}' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f\"Purge success: {d['success']}\")
if not d['success']:
    print(f\"Error: {d['errors'][0].get('code','?')} - {d['errors'][0].get('message','?')}\")
"
```

## Pitfalls

1. **Production branch ≠ git branch:** Platforms default to `master`; modern repos use `main`. Every push deploys to a preview URL, leaving production stale. Always verify alignment before declaring success.

2. **Checking deploy hash URL instead of production URL:** The unique hash URL (e.g., `https://abc123.pages.dev`) always shows that specific deploy. The production alias (`https://yoursite.pages.dev`) may still point to an older build. Verify both.

3. **CDN cache hides updates:** After a successful deploy, edge caches may serve old assets for minutes. A hard refresh or cache purge is often needed before the user sees changes.

4. **Cache purge API lacks permissions:** The Cloudflare Pages API key often does not have `Zone:Edit` rights. Cache purge fails silently with `success: false`. Verify purge response before assuming it worked.

5. **Colspan mismatch after column removal:** When removing table columns in HTML, update `colspan` attributes on `no-results` rows. A mismatch breaks table layout.

6. **API token scoped to wrong account:** Cloudflare API tokens are scoped to specific accounts. If you manage multiple zones, ensure the token has access to the correct account ID.

## Verification Checklist

Before telling a user "your changes are live":
- [ ] Build status shows `success`
- [ ] Production branch matches git branch
- [ ] Production URL serves the new content (not just the hash URL)
- [ ] User can see changes after a hard refresh (or cache is purged)
