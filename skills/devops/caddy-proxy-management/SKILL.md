---
name: caddy-proxy-management
description: "Manage Caddy reverse proxy with CaddyUI web interface — deploy on Proxmox LXC with Docker, configure proxy hosts, SSL, HSTS, WebSockets, and DNS-01 challenges."
version: 1.1.0
tags: [caddy, caddyui, reverse-proxy, ssl, letsencrypt, docker, infrastructure]
metadata:
  hermes:
    tags: [caddy, caddyui, reverse-proxy, ssl, letsencrypt, docker, infrastructure]
    trigger_conditions:
      - "caddy proxy"
      - "caddyui"
      - "reverse proxy"
      - "proxy host"
      - "Caddyfile"
      - "HSTS"
      - "websocket proxy"
      - "DNS-01 challenge"
      - "wildcard cert"
      - "192.168.100.53"
      - "CT 107"
      - "azure dns caddy"
---

# Caddy + CaddyUI Proxy Management

Manage reverse proxy hosts, SSL certificates, and routing on the caddy-proxy host (CT 107, IP 192.168.100.53). Caddy replaces the old NPM (CT 106) with automatic HTTPS, zero-config WebSockets, and HTTP/2.

## When to Use

- Adding, updating, or removing a reverse-proxy host / domain (via CaddyUI, its REST API, or the Caddyfile).
- Diagnosing certificate failures (DNS-01 Azure challenges, stale `_acme-challenge` TXT records, HTTP-01 404s).
- Enabling HSTS, WebSocket proxying, wildcard certs, or redirection hosts.
- Switching the DNS provider module (Cloudflare ↔ Azure) and rebuilding the custom Caddy image.
- Any work touching CT 107, the caddy-proxy stack, or domains served through it (photos/ha/ai/sendblue/relay).

## Not For

- Nginx Proxy Manager on CT 106 (legacy, being replaced) → use `nginx-proxy-manager-native` instead.
- Creating/managing the Proxmox CT itself (Docker install, MAC takeover) → use `proxmox-host-management` / `proxmox-ssh-lifecycle` instead.
- The NOSTR relay service behind the proxy (its config, Blossom, HAVEN) → use `haven-relay-management` / `nostr-relay-hosting` instead.
- General Let's Encrypt / cert automation on non-Caddy servers → use `caddy-proxy-management`'s references only if the target is this CT; otherwise treat as generic TLS work.
- Hermes gateway platform setup (only touches Caddy when it proxies gateway traffic) → use `hermes-gateway-platforms` instead.

## Host Details

- **CT ID:** 107
- **Hostname:** caddy-proxy
- **IP:** 192.168.100.53
- **SSH:** `ssh -i /home/wahid/.ssh/id_ed25519 root@192.168.100.53`
- **CaddyUI Web UI:** `http://192.168.100.53:8081`
- **Caddy Admin API:** `http://localhost:2019` (inside container)
- **Docker Compose:** `/opt/caddyui/docker-compose.yml`
- **Docker volumes:** `caddy_data`, `caddy_config`, `caddyui_data`

## Architecture

| Component | Container | Ports | Notes |
|-----------|-----------|-------|-------|
| Caddy | `caddy` | 80, 443, 443/udp | Custom build with Azure DNS module (was Cloudflare, switched 2026-06-30) |
| CaddyUI | `caddyui` | 8081→8080 | Web UI for managing proxy hosts |

**Key:** Caddy is a single binary that handles reverse proxy, automatic HTTPS, HTTP/2, and WebSocket passthrough — all automatically. No separate nginx, no database, no Node.js.

## Docker Compose Stack

The stack lives at `/opt/caddyui/` on CT 107:

```bash
cd /opt/caddyui
docker compose up -d      # start
docker compose down       # stop
docker compose pull       # update CaddyUI image
docker compose build      # rebuild Caddy (after Dockerfile.caddy changes)
docker compose logs -f    # follow logs
```

### Custom Caddy Build

Caddy is built from `Dockerfile.caddy` (see `templates/Dockerfile.caddy`) which adds the Azure DNS module via `xcaddy`. This enables DNS-01 challenges for wildcard certificates using Azure DNS.

**Rebuild after changes:**
```bash
docker compose build caddy && docker compose up -d --force-recreate caddy
```

**Warning:** `docker compose restart` does NOT pick up image changes. You must use `--force-recreate` or `docker compose up -d --force-recreate caddy` to load a newly built image.

**Switching DNS providers:** To switch from Cloudflare to Azure (or vice versa), update the `xcaddy build --with` line in `Dockerfile.caddy`, rebuild, and force-recreate. Current Dockerfile uses `github.com/caddy-dns/azure`.

### Docker Compose File

See `templates/docker-compose.yml` for the complete stack definition.

## Proxy Hosts

| Domain | Backend | WebSocket | Notes |
|--------|---------|-----------|-------|
| `photos.wahidsaleemi.net` | `192.168.100.58:2283` | Yes | Immich |
| `ha.wahidsaleemi.net` | `192.168.200.20:8123` | No | Home Assistant |
| `ai.wahidsaleemi.net` | `192.168.100.52:18789` | No | AI service |
| `sendblue.wahidsaleemi.net` | `192.168.100.52:8644` | Yes | Sendblue SMS |

## CaddyUI Web UI

Access at `http://192.168.100.53:8081`. Manage proxy hosts, redirections, certificates, and raw routes through the browser.

### Adding a Proxy Host

1. Navigate to Proxy Hosts → Add
2. Set domain name(s)
3. Set upstream URL (e.g., `http://192.168.100.58:2283`)
4. Enable HTTPS (automatic Let's Encrypt)
5. For WebSocket hosts: Caddy handles WebSocket upgrade automatically — no special config needed
6. Save — Caddy reloads automatically

### HSTS Configuration

HSTS is set globally in the Caddyfile. Via CaddyUI, add to Settings → Global options or Raw Routes.

### Redirection Hosts

CaddyUI has a dedicated Redirection Hosts section. Set source domain → target URL, choose 301/302.

## CaddyUI REST API

The API lives at `/api/v1/` on port 8081. Use API tokens (created in CaddyUI → Settings → API Tokens) for auth.

**Key patterns:**
- **List hosts:** `GET /api/v1/proxy-hosts`
- **Create host:** `POST /api/v1/proxy-hosts` with `{"domains":"app.example.com","forward_scheme":"http","forward_host":"192.168.100.50","forward_port":3000,"enabled":true}`
- **Update host:** `PUT /api/v1/proxy-hosts/{id}` (PATCH returns 405 — use PUT)
- **Delete host:** `DELETE /api/v1/proxy-hosts/{id}`

**Critical:** `domains` must be a STRING, not an array. Passing `["app.example.com"]` returns a deserialization error.

**Full API reference:** See `references/caddyui-api-reference.md` for field types, common workflows, and pitfalls.

## Caddy Features (Automatic)

- **HTTPS:** Automatic Let's Encrypt certs for all domains
- **HTTP/2:** Enabled by default with HTTPS
- **WebSockets:** Automatic detection and passthrough — no config needed
- **Cert renewal:** Automatic, silent, no cron required
- **OCSP stapling:** Automatic

## DNS-01 Challenges (Wildcard Certs) — RESOLVED ✅

The custom Caddy build includes the **Azure DNS module** (`github.com/caddy-dns/azure`). Wildcard cert for `*.wahidsaleemi.net` is **working and auto-renewing** via DNS-01 challenges.

### Service Principal Credentials

| Field | Value |
|-------|-------|
| **Client ID** | `d2940298-b944-4067-b9ba-2713e49b8428` |
| **Tenant ID** | `9e63e5a0-2e7c-4f87-ab1a-891f90632e5c` |
| **Subscription ID** | `a5a18f86-fd5e-4ef7-8290-844ab6974f14` |
| **Resource Group** | `rg-homelab` |
| **Client Secret** | In `/opt/caddyui/Caddyfile` (explicit in `dns azure {}` block) |

### Caddyfile Configuration

**ALL five fields are REQUIRED in the Caddyfile block** — `subscription_id`, `resource_group_name`, `tenant_id`, `client_id`, `client_secret`. The Azure DNS plugin (`libdns/azure`) does NOT read `AZURE_CLIENT_ID`/`AZURE_CLIENT_SECRET` from environment variables — it falls back to Managed Identity (which times out inside Docker/LXC). Credentials MUST be explicit in the Caddyfile.

```caddy
*.wahidsaleemi.net {
  tls {
    dns azure {
      subscription_id a5a18f86-fd5e-4ef7-8290-844ab6974f14
      resource_group_name rg-homelab
      tenant_id 9e63e5a0-2e7c-4f87-ab1a-891f90632e5c
      client_id d2940298-b944-4067-b9ba-2713e49b8428
      client_secret <secret>
    }
  }
  # ... proxy handlers
}
```

### Stale Record Cleanup

If a challenge fails, stale `_acme-challenge` TXT records block retries with `412 PreconditionFailed`. See `references/caddyfile-azure-dns.md` for the full REST API cleanup procedure (works from any machine, no `az` CLI needed).

### Testing

**Hairpin NAT warning:** You cannot test Caddy from inside the LAN when DNS points to the WAN IP — the router won't loop back. Test from outside, or use `--resolve` to test locally:
```bash
curl -k --resolve ha.wahidsaleemi.net:443:127.0.0.1 https://ha.wahidsaleemi.net
```

See `references/caddyfile-azure-dns.md` and `references/azure-arc-setup.md` for full details.

## Pitfalls

1. **IPv6 does not route on this CT — always force IPv4** — The CT has IPv6 addresses but IPv6 packets don't route. `ping google.com` resolves to IPv6 and gets 100% packet loss. All network commands must force IPv4: `curl -4`, `wget --inet4-only` (or `-4`), `apt -o Acquire::ForceIPv4=true`, `dig @8.8.8.8 domain A`. SSH itself is unaffected (uses IPv4 already).
2. **Azure Arc `azcmagent connect` requires interactive device code auth** — The command displays a device code and waits for the user to complete browser auth at `https://login.microsoft.com/device`. When run via SSH from the agent, it times out (120s-300s isn't enough for the user to see the code and authenticate). **Solution:** Either run with a 600s timeout, or have the user run the command directly on the CT console where they can see the code immediately.
3. **`aka.ms/InstallAzcmAgent.sh` is broken** — The redirect URL returns a Bing search page instead of the install script. Use the Microsoft package repository method instead: `curl -4 https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb` → `dpkg -i` → `apt install azcmagent`.
4. **Docker Hub image name mismatch** — The GitHub org is `X4Applegate` but the Docker Hub image is `applegater/caddyui`. Using `x4applegate/caddyui` will fail with "pull access denied".
5. **Custom Caddy build required for DNS-01** — The stock `caddy:2` image does NOT include DNS provider modules. You must build with `xcaddy` via `Dockerfile.caddy` to get Cloudflare DNS support.
6. **Caddy Admin API is container-internal** — The admin API listens on `0.0.0.0:2019` inside the Docker network. CaddyUI connects to it via `http://caddy:2019`. Do NOT expose port 2019 to the host.
7. **MAC address takeover** — CT 107 uses the same MAC (`BC:24:11:27:D2:30`) as the old CT 106 to inherit the same DHCP IP (192.168.100.53). Stop the old CT first to avoid IP conflicts.
8. **CaddyUI first-run setup** — On first access, CaddyUI redirects to create an admin account. This is a one-time setup step that must be done in the browser.
9. **Docker on LXC requires nesting=1** — The CT must have `features: nesting=1` in its Proxmox config. Without it, Docker containers will fail to start.
10. **Caddy handles WebSocket automatically** — Unlike NPM where you had to enable "WebSocket Upgrade" per host, Caddy detects `Upgrade: websocket` headers and passes them through with zero configuration. The CaddyUI API field `websocket_support` exists but is not needed for WebSocket to work.
11. **HSTS must be configured explicitly** — Caddy does NOT add HSTS headers by default. Setting `hsts_preload: true` via the API or UI adds the `Strict-Transport-Security` header.
12. **DNS records must be updated separately** — Migrating to a new proxy server does NOT automatically update DNS. Each domain's A record must be manually pointed to the new proxy IP (192.168.100.53). Check with `dig +short <domain>` before testing.

13. **Router port forwarding must point to CT 107** — Even with correct DNS, external traffic won't reach Caddy unless the router forwards ports 80 and 443 (TCP + UDP for 443) to 192.168.100.53. After migration, verify router config. Test internally first with `curl -k --resolve <domain>:443:127.0.0.1 https://<domain>` from inside the container.

14. **Cert storage location** — Caddy stores certs in `/data/caddy/certificates/<ca-directory>/<domain>/`. For Let's Encrypt production, the CA directory is `acme-v02.api.letsencrypt.org-directory`. Wildcard certs are stored as `wildcard_.wahidsaleemi.net/` (underscore replaces asterisk). Check with `docker exec caddy find /data/caddy/certificates -type f`.

15. **`az` CLI hangs from Proxmox/CT hosts** — Azure AD API calls timeout from CT 107 and the Proxmox host. Use curl to call Azure REST API directly for DNS record management. See `references/caddyfile-azure-dns.md` for the curl pattern.

16. **CaddyUI API returns 303→/login without an API token** — `curl http://192.168.100.53:8081/api/v1/proxy-hosts` (no token) redirects to `/login` with HTTP 303 instead of returning JSON or an explicit 401. The API is unusable until you create a token (CaddyUI → Settings → API Tokens). If you don't have a token, don't fight the auth wall — **fall back to editing the Caddyfile directly** (pitfall #17).

17. **CaddyUI container is distroless — no shell** — `docker exec caddyui sh -c "..."` fails with `exec: "sh": executable file not found in $PATH`. You cannot inspect or modify CaddyUI's internals from inside the container. Manage hosts via the CaddyUI web UI/API, or edit the Caddyfile on the host.

18. **Direct Caddyfile editing is the reliable no-token path** — The Caddyfile is bind-mounted from the host: `/opt/caddyui/Caddyfile` (CT 107 host path) → `/etc/caddy/Caddyfile` (inside the `caddy` container). Edit the host file; Caddy watches it and reloads gracefully on save. Add a site block per domain:
   ```caddy
   relay.wahid.my {
     reverse_proxy 192.168.100.51:3355
   }
   ```
   For domains NOT covered by the Azure DNS-01 wildcard block (e.g. `*.wahid.my` on Cloudflare DNS), Caddy auto-issues a Let's Encrypt cert via **HTTP-01** as long as port 80 from the internet reaches CT 107 — no DNS-01 module needed for single (non-wildcard) domains. Note the Caddyfile is `{"admin off" ...}` — CaddyUI owns the config, so keep edits additive and minimal.

19. **`admin off` in the Caddyfile breaks `caddy reload` — restart the container instead** — With `admin off`, `docker exec caddy caddy reload --config ...` fails with `Error: sending configuration to instance: performing request: Post "http://0.0.0.0:2019/load": connect: connection refused` (the admin API on :2019 is disabled). `caddy validate` still works (it just parses the file) but does NOT apply changes. **The reliable apply path is `docker restart caddy`** after editing the bind-mounted `/opt/caddyui/Caddyfile`. Validate first, then restart:
   ```bash
   pct exec 107 -- docker exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
   pct exec 107 -- docker restart caddy
   ```

20. **Cert challenge failures (404/unauthorized) usually mean DNS still points elsewhere** — When adding a new domain and Caddy logs `challenge failed ... Invalid response from https://<domain>/.well-known/acme-challenge/...: 404`, the domain's DNS is still pointing at the OLD host (e.g. a previous cloud provider's CNAME/IP). The Let's Encrypt validation server follows DNS, so it never reaches Caddy. Fix order: (1) update the DNS record at the authoritative nameserver to point at the homelab WAN IP, (2) verify with `dig @<authoritative-ns> +short <domain>` (NOT the local resolver, which caches — check `dig +short <domain> NS` to find the authority), then (3) `docker restart caddy` to trigger a fresh cert attempt.

21. **WebSocket domains behind Cloudflare DNS need `proxied=false` (grey cloud)** — For long-lived WebSocket services (Nostr relays, push streams) whose DNS lives in Cloudflare, the record MUST be a direct record with proxy disabled. The Cloudflare proxy terminates/limits long-lived connections and breaks the relay protocol. Set the record via API (`{"proxied":false}`) or the dashboard grey-cloud icon. This applies to `relay.wahid.my` (A → `64.25.11.235`, proxied=false, verified working).

## Related Skills

- `nginx-proxy-manager-native` — Old NPM setup on CT 106 (being replaced)
- `proxmox-host-management` — Proxmox CT creation, Docker install, MAC address takeover
- `hermes-gateway-platforms` — If Caddy proxies Hermes gateway traffic