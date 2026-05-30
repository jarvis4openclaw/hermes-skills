---
name: mission-control-openclaw-websocket-401-troubleshooting
description: Diagnose Mission Control "WebSocket error" incidents by separating OpenClaw gateway auth/pairing failures from Hermes API failures.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mission-control, openclaw, websocket, 401, pairing, troubleshooting]
---

# Mission Control OpenClaw WebSocket 401 Troubleshooting

Use when Mission Control shows generic WebSocket errors and you need exact root cause fast.

## What this catches
- OpenClaw gateway auth failures (`401 Unauthorized`)
- OpenClaw gateway WS policy failures (`1008 pairing required`)
- Misleading UI symptoms that look like "WebSocket broken" but are really bad token/pairing config
- Confusion between Hermes API (`:8642`) vs OpenClaw gateway (`:18789`)

## Fast triage (do in order)
1) Check Mission Control runtime log
- File: `.data/mc.log`
- Look for:
  - `Gateway channel status failed with status 401`
  - `gateway closed (1008): pairing required`
  - `Gateway target: ws://127.0.0.1:18789`

2) Confirm which backend is failing
- Hermes API health should be checked separately:
  - `curl -i http://127.0.0.1:8642/health`
- OpenClaw channel endpoint check:
  - `curl -i http://127.0.0.1:18789/api/channels/status`
- Interpretation:
  - `8642 = 200` and `18789 = 401` => problem is OpenClaw gateway auth/pairing, not Hermes API.

3) Map log error to code path
- In Mission Control source, search for the exact error string.
- Example known path:
  - `src/app/api/channels/route.ts` throws `Gateway channel status failed with status ${res.status}`.
- This proves the failing call is MC -> OpenClaw `/api/channels/status`.

4) Verify token sourcing and env config
- Check MC env for:
  - `OPENCLAW_GATEWAY_HOST`
  - `OPENCLAW_GATEWAY_PORT`
  - `OPENCLAW_GATEWAY_TOKEN`
- Check for malformed lines or comment corruption in `.env` (e.g., truncated/merged token line).
- Check token-loading logic in `src/lib/gateway-runtime.ts` (`getDetectedGatewayToken`).

5) Verify OpenClaw gateway auth policy in config
- OpenClaw config is usually under `~/.openclaw/openclaw.json` (or backup variant).
- Inspect:
  - `gateway.auth.mode` (often `token`)
  - `gateway.auth.token`
  - `gateway.bind`
  - `gateway.controlUi.allowedOrigins`

## High-confidence diagnosis patterns
### Pattern A — token/auth break
If all are true:
- MC logs show `Gateway channel status failed with status 401`
- OpenClaw endpoint probes on `:18789` reject unauthenticated access
- Hermes health on `:8642` is OK

Then primary fault is OpenClaw auth credential mismatch (usually bad/missing `OPENCLAW_GATEWAY_TOKEN`).

### Pattern B — secure-context/device-identity break (common after token fix)
If token is fixed but browser still shows WebSocket error, reproduce with explicit Origin and valid token.

Node probe:
- Connect to `ws://127.0.0.1:18789`
- Set `Origin: http://<lan-ip>:3000`
- Send `connect` with `client.id=openclaw-control-ui` and valid auth token

If gateway returns `CONTROL_UI_DEVICE_IDENTITY_REQUIRED` and closes `1008` with reason like:
- `control ui requires device identity (use HTTPS or localhost secure context)`

Then fault is browser security context, not token.

## Common fix targets
- Set/repair `OPENCLAW_GATEWAY_TOKEN` in Mission Control env
- Ensure token matches gateway `gateway.auth.token`
- Ensure MC origin is in `gateway.controlUi.allowedOrigins`
- If error is `CONTROL_UI_DEVICE_IDENTITY_REQUIRED`, open MC over HTTPS (or localhost) so WebCrypto device signing is available
- Restart MC after env edits so new token is loaded
## 403 reverse-proxy triage (important)
When switching MC to a domain behind Nginx Proxy Manager (or another reverse proxy), a `403` may come from the proxy, not Mission Control.

Use this discriminator test:
- Direct backend with Host header:
  - `curl -i -H "Host: <domain>" http://127.0.0.1:3000/login`
- Public URL:
  - `curl -i https://<domain>/login`

Interpretation:
- If direct backend is `200` but public URL is `403` with `server: openresty`, the block is in NPM (Access List/custom nginx rules), not MC.
- If response includes MC/Next headers (`x-request-id`, CSP from MC, `X-Powered-By: Next.js`) and returns `403`, host allowlist is still blocking in MC.

Corroborating code/docs:
- `src/proxy.ts` enforces host allowlist and returns `403 Forbidden` when host is not matched.
- `docs/SECURITY-HARDENING.md` documents domain allowlisting via `MC_ALLOWED_HOSTS=mc.example.com,localhost`.

## Pitfalls
- Don’t treat generic "WebSocket error" as transport failure first.
- Don’t debug Hermes `/health` if OpenClaw `/api/channels/status` is 401.
- Don’t assume missing connectivity when logs explicitly show `pairing required`.
- Don’t assume all `403` responses come from Mission Control; verify whether reverse proxy generated the response first.
