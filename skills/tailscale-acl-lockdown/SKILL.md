---
name: tailscale-acl-lockdown
description: Use when locking down a Tailscale tailnet ACL with tags and per-port grants, or debugging why grants are not applying.
version: 1.1.0
author: jarvis
license: MIT
metadata:
  hermes:
    tags: [tailscale, acl, network, security, tags, oauth]
    related_skills: [hermes-webui-tailscale, mikrotik-router-management, proxmox-ssh-lifecycle]
    trigger_conditions:
      - "Tailscale ACL"
      - "lock down the tailnet"
      - "tailnet grants"
      - "tailscale tags"
      - "tagOwners"
      - "Tailscale ACL validate"
      - "tailscale oauth client"
      - "tailscale if-match etag"
      - "restrict tailnet access"
      - "tailscale per-port grants"
      - "tailscale device tags"
      - "tailscale acl rollback"
      - "invalid address tailscale acl"
---

# Tailscale ACL lockdown (tags + per-port grants)

Flow: inventory → port map → draft → tag servers/devices → validate → push → verify.

## When to Use

- Restricting which devices on a tailnet can reach which ports.
- Converting a permissive (allow-all) tailnet into tag-based grants.
- Investigating why a grant appears correct but traffic is still allowed or still blocked.
- Tagging devices, or fixing "requested tags ... are invalid or not permitted".
- Needing an ACL change that is reversible with a saved rollback document.
- Debugging Tailscale ACL API errors (405/404/etag/"invalid address").

## Not For

- **Exposing a Hermes web UI over Tailscale (serve/funnel plumbing)** → use `hermes-webui-tailscale` instead
- **Router, firewall, or IPv6 ND configuration on the local network** → use `mikrotik-router-management` instead
- **Proxmox host SSH access and lifecycle** → use `proxmox-ssh-lifecycle` instead
- **Windows-side SSH setup** → use `windows-ssh` instead
- **Deploying files over SSH** → use `ssh-file-deploy` instead
- **NAS/SMB share configuration** → use `nas-management` instead

## API mechanics (verified 2026-10-25)

- Auth: mint token via `curl -d client_id=$TS_OAUTH_CLIENT_ID -d client_secret=$TS_OAUTH_CLIENT_SECRET https://api.tailscale.com/api/v2/oauth/token` → access_token (Bearer). Short-lived — mint per working session.
- **Set ACL: `POST /api/v2/tailnet/-/acl`** with `If-Match: "<etag-with-quotes>"`. PUT is now 405.
- Validate: `POST /api/v2/tailnet/-/acl/validate` — empty body `{}` = pass.
- **Tag a device: `POST /api/v2/device/{id}/tags`** `{"tags":["tag:x"]}` — old singular `/tag` is 404.
- Grants: inside `ip`, **one range per entry** — `["tcp:22","tcp:445"]` not `["tcp:22,445"]`.
- **dst must be `100.x` IPs or `tag:` selectors — MagicDNS hostnames fail as "invalid address".**

## Procedure

1. Inventory devices and current ACL; record the live etag.
2. Map required ports per device class.
3. Draft the target policy with `tagOwners` and grants.
4. Push an intermediate policy = current allow-all + only `tagOwners` (zero access change).
5. Tag every device; validate the final policy; push final; verify with real traffic tests.
6. Keep the rollback JSON until verification passes.

## Pitfalls

1. **Groups trap** — a single-owner tailnet must NOT rely on `groups:`; declaring the user in groups leaves *untagged* devices implicitly allowed to reach each other regardless of grants (observed: phone accepted ports never granted). Tag **every** device; tags replace user identity and rules apply between tags.
2. **Tag before restrict** — a device cannot take a tag absent from the live policy (`"requested tags ... are invalid or not permitted"`). Safe sequence: push intermediate = current allow-all + only `tagOwners` (zero access change), tag all devices, validate final, push final.
3. **Validate failing with everything `got: Drop`** — that means devices are not yet tagged. Tag first, then validate again.
4. **Stale etag** — refetch the etag immediately before the POST; an old `If-Match` is rejected.
5. **Using PUT for the ACL** — PUT is now 405. Use `POST /api/v2/tailnet/-/acl` with `If-Match`.
6. **Reusing a long-lived token** — OAuth access tokens are short-lived; mint per working session rather than caching one in a script.
7. **Singular `/tag` endpoint** — `POST /api/v2/device/{id}/tags` (plural); the old singular `/tag` returns 404.
8. **Comma-joined port ranges** — inside `ip`, each entry is one range: `["tcp:22","tcp:445"]`. `["tcp:22,445"]` does not do what it reads like.
9. **MagicDNS hostnames in `dst`** — ACL `dst` accepts only `100.x` IPs or `tag:` selectors; hostnames fail as "invalid address".
10. **Quoting the etag without its quotes** — `If-Match` needs the quoted form exactly as returned.
11. **Assuming port 22 is Tailscale SSH** — with RunSSH off, port 22 is plain sshd, fully controlled by grants. Do not assume Tailscale intercepts it.
12. **No saved rollback** — keep the allow-all intermediate JSON (`{"grants":[{"src":["*"],"dst":["*"],"ip":["*"]}]}` + tagOwners) until the final policy is verified, and keep the ability to untag a device from the admin UI.

## Rollback

Untag a device (admin UI) to return it to owner. Recovery push: saved allow-all intermediate (`{"grants":[{"src":["*"],"dst":["*"],"ip":["*"]}]}` + tagOwners). Keep that JSON until verified.

## Device map (Wahid's tailnet, onewahid@gmail.com)

- clawd 100.81.6.21 / opengym 100.75.53.1 = tag:server
- Darkmode 100.81.30.91 / T14-WASALEEM 100.70.0.61 / WASALEEMP52 100.118.224.74 = tag:desktops
- iPhone localhost 100.84.85.118 = tag:mobile
- Legal ports: desktops→clawd 22/445/9119/32848, desktops→opengym 22/8080, mobile→clawd 22/9119. Change → edit grants + tests, validate, push.
