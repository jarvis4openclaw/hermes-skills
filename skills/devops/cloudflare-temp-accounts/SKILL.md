---
name: cloudflare-temp-accounts
description: Deploy Cloudflare Workers/APIs without a permanent account using temporary accounts. An agent iterates on a deployment for 60 minutes using `wrangler deploy --temporary` with zero auth, then hands a claim URL to a human to make it permanent — otherwise everything is auto-deleted. Use when a background agent must ship or demo a Worker with no Cloudflare account, API token, or human in the loop.
version: 1.0.0
tags: [cloudflare, workers, agents, temporary-accounts, wrangler, deploy, zero-auth]
metadata:
  hermes:
    tags: [cloudflare, workers, wrangler, deploy, agents, prototyping, zero-auth]
    related_skills: [render-deploy, static-site-deploy-verify, caddy-proxy-management, exa-web-search-free]
    trigger_conditions:
      - "deploy a worker without a cloudflare account"
      - "wrangler deploy --temporary"
      - "temporary cloudflare account"
      - "claim url for a deployment"
      - "cloudflare without api token"
      - "deploy without auth"
      - "ephemeral cloudflare deployment"
      - "agent needs to deploy something"
      - "no human in the loop for auth"
      - "prototype a worker and discard it"
      - "hand off a deployment for a human to claim"
      - "zero-auth deploy"
      - "cloudflare claim deployments"
---

# Cloudflare Temporary Accounts for AI Agents

Deploy Workers, APIs, and other Cloudflare resources **without any pre-existing Cloudflare account or API token**. Temporary accounts live 60 minutes — iterate freely, then claim to make permanent.

## When to Use

- AI agent needs to deploy/test Cloudflare Workers without human auth setup
- Quick prototyping — spin up, test, iterate, discard or claim
- Background agent sessions with no human in the loop for auth
- Trial-and-error workflows where you don't want to pollute a real account

## Not For

- **Production deployments that must persist beyond 60 minutes unclaimed** — the temp account and every resource in it are deleted on expiry. There is no extension.
- **Anything that must survive unclaimed** (custom domains, KV namespaces, Durable Objects, bindings) — claim first, or provision it on a real account.
- **Static sites on a permanent Cloudflare account** — use `static-site-deploy-verify` instead; the old `cloudflare-pages-deploy` / `cloudflare-pages-static-site` references are dead (those skills no longer exist in this tree).
- **Deploying an app where a git-push deploy is the norm** → use `render-deploy` instead.
- **Reverse-proxy or TLS routing work on a self-hosted box** → use `caddy-proxy-management` instead.
- **A deployment you cannot hand to a human to claim** — an unclaimed temp account is guaranteed data loss, so use the real account path.

## Prerequisites

- **Node.js** (for `npx wrangler`)
- **No Cloudflare account or API token needed** — that's the whole point ★

## How It Works

| Step | What Happens |
|------|-------------|
| 1. Agent runs | `wrangler deploy --temporary` |
| 2. Cloudflare | Creates temp account + issues API token to wrangler |
| 3. Agent gets | A **claim URL** + 60-minute window |
| 4. Agent iterates | Re-runs same command, reuses temp account |
| 5. Human claims | Opens claim URL → sign up/in → account becomes permanent |
| 6. Expiry | Unclaimed after 60 min → auto-deleted with all resources |

## Workflow

### 1. Initial Deploy

```bash
npx wrangler deploy --temporary
```

Wrangler will:
- Provision a temporary Cloudflare account
- Issue a scoped API token
- Return a **claim URL** (save this!)
- Deploy your Worker/API

### 2. Iterate (within 60 min)

```bash
# Edit code, then redeploy — same temp account is reused
npx wrangler deploy --temporary
```

No re-auth needed. The temp account persists across wrangler invocations within the window.

### 3. Verify

```bash
# Curl the preview URL from deploy output
curl -sL "<preview-url>" | head -20
```

### 4. Claim (Human Step)

Open the **claim URL** in a browser:
- Sign up for a new Cloudflare account, OR sign in to existing one
- Click "Claim" to make the temp account permanent
- All resources (Workers, KV, Durable Objects, bindings, domains) persist

### 5. If Not Claimed

After 60 minutes, everything is automatically deleted. No cleanup needed.

## Example: Agent-Driven Hello World

```bash
# Agent creates a simple Worker
cat > src/index.ts << 'EOF'
export default {
  fetch(request: Request): Response {
    return new Response("Hello from a temp account!");
  }
};
EOF

# Deploy to temporary account
npx wrangler deploy --temporary
# → Outputs claim URL + preview URL

# Iterate: change text, redeploy
# Edit src/index.ts...
npx wrangler deploy --temporary
# → Same temp account, updated Worker
```

## Related Cloudflare Agent Initiatives

- **Stripe partnership** — agents can provision Cloudflare + start subscriptions + register domains
- **WorkOS auth.md** — agents provision accounts via standard OAuth
- **isitagentready.com** — check if apps are agent-friendly

## Pitfalls

Each entry keeps the symptom → cause → fix shape the old subsections used, now in one flat,
scannable list.

1. **The 60-minute window expires mid-work and everything vanishes** — The temp account and every
   resource in it are deleted; there is no extension and no recovery. Claim early (step 4 of the
   workflow) as soon as a deployment looks worth keeping, and tell the human the deadline *with* the
   claim URL.

2. **The claim URL is lost** — It appears once, in the `wrangler deploy --temporary` output. Capture it
   from the first deploy and hand it to the human immediately; a redeploy will not reprint the original
   claim URL reliably, and an unclaimed deployment is deleted regardless.

3. **`--temporary` is not recognised** — The installed wrangler is too old. Run
   `npx wrangler@latest deploy --temporary`, or `npm update wrangler`, then retry.

4. **`wrangler deploy` prompts for login and blocks a headless run** — The temp path still expects an
   interactive terminal for its own provision step. If the environment has no TTY, run it with a PTY
   (`pty=true` on the background runner) rather than trying to pass credentials it does not want.

5. **Resource limits on temp accounts are not the documented permanent ones** — Quotas and feature
   availability are lower and can change. Check the current claim-deployments docs before planning a
   large build, and keep the prototype small enough to iterate inside the window.

6. **A redeploy silently starts a *new* temp account** — Iterating works because the command reuses the
   temp account, but only while the original auth context is present (same working directory, same
   wrangler session). If a redeploy reports a fresh claim URL, you lost the first account and its
   resources — stop and re-hand the new URL.

7. **Curl-ing the preview URL returns a Cloudflare error page, not your Worker** — Check the exact host
   from the deploy output; `*.workers.dev` previews can lag a few seconds behind the deploy. Re-read the
   deploy output rather than editing code, and confirm with `curl -sL -o /dev/null -w '%{http_code}'`.

8. **Assuming the resources survive because the claim URL was opened** — Opening the URL is not
   claiming; the human must sign up or sign in and click Claim. Verify by checking the resources still
   exist under the claimed account before declaring success.

9. **Handing the claim URL over a channel that expires or is unread** — The URL is single-use and
   time-bounded; paste it where the human will actually see it in the next few minutes, and state the
   deadline in the same message.

10. **Treating the temp account as a safe place for secrets** — Anything deployed is reachable on a
    public preview URL until deletion. Never put real API keys or user data in a Worker you are merely
    prototyping with.

11. **Reporting "deployed" without a reachable check** — A successful `wrangler deploy` exit code is not
    a working deployment. Fetch the preview URL and report the observed HTTP status and body snippet.

## Commands Reference

| Action | Command |
|--------|---------|
| Deploy to temp account | `npx wrangler deploy --temporary` |
| Redeploy (iterate) | `npx wrangler deploy --temporary` (same command) |
| Update wrangler | `npm update wrangler` |
| Check wrangler version | `npx wrangler --version` |

## See Also

- `cloudflare-pages-deploy` — permanent account Pages deployment
- `cloudflare-pages-static-site` — static sites with Git auto-deploy
- [Official docs: Claim Deployments](https://developers.cloudflare.com/workers/platform/claim-deployments/)
- [isitagentready.com](https://isitagentready.com/)
