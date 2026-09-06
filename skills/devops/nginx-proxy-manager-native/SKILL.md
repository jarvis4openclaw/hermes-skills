---
name: nginx-proxy-manager-native
description: "Manage Nginx Proxy Manager on a native (non-Docker) OpenResty installation. Covers dual-nginx config test requirement, SSL cert API, common config fixes, and reverse proxy setup. ⚠️ Being replaced by Caddy + CaddyUI on CT 107 (2026-06-30)."
version: 1.2.0
metadata:
  hermes:
    tags: [npm, nginx, openresty, reverse-proxy, ssl, letsencrypt, infrastructure]
    trigger_conditions:
      - "npm proxy host"
      - "nginx proxy manager"
      - "letsencrypt cert"
      - "reverse proxy setup"
      - "sendblue.wahidsaleemi.net"
      - "192.168.100.53"
      - "nginx config error"
      - "openresty nginx"
---

# Nginx Proxy Manager — Native OpenResty Installation

## When to Use

- User asks to **manage, fix, or troubleshoot** Nginx Proxy Manager on the **native OpenResty** host (CT 106, 192.168.100.53).
- User hits an **NPM cert-creation 500 error** or config-test failure on the dual-nginx host.
- User asks to **add/remove a reverse proxy host** through NPM's API or files.
- User asks about **SSL / Let's Encrypt** certs on this specific NPM host.
- Migration work: **understanding the old NPM setup** while moving to Caddy.

## Not For

- **New** reverse-proxy management on the homelab → the migration is to Caddy + CaddyUI; use `caddy-proxy-management` instead (Caddy on CT 107, same IP).
- Docker / jc21 NPM container management → use the Docker-NPM path or `homelab-browser-backends` instead.
- General nginx (non-NPM) server config → do not use this skill.
- TLS/cert management on non-NPM hosts → use `caddy-proxy-management` or the relevant skill instead.


**⚠️ MIGRATION STATUS (2026-06-30):** NPM on CT 106 is being replaced by Caddy + CaddyUI on CT 107 (same IP 192.168.100.53). This skill documents the old NPM setup for historical reference and troubleshooting during the transition. For new proxy management, use `caddy-proxy-management` instead.

Manage proxy hosts, SSL certificates, and nginx configuration on the nginxproxymanager host (CT 106, IP 192.168.100.53). This is a **native** OpenResty install, NOT the official jc21 Docker image — different troubleshooting rules apply.

## Host Details

- **IP:** 192.168.100.53
- **SSH:** `root@192.168.100.53`
- **Web UI:** `http://192.168.100.53:81`
- **NPM Login:** `onewahid@gmail.com`
- **Binary:** `/usr/local/openresty/nginx/sbin/nginx` (OpenResty 1.31.1.1)
- **System nginx:** `/usr/sbin/nginx` (Debian 1.26.3) — also present, used by NPM API internals
- **Main config:** `/usr/local/openresty/nginx/conf/nginx.conf` (symlinked from `/etc/nginx/nginx.conf`)
- **Data configs:** `/data/nginx/proxy_host/*.conf`, `/data/nginx/custom/*.conf`
- **Include files:** `/usr/local/openresty/nginx/conf/conf.d/include/` AND `/etc/nginx/conf.d/include/` (must exist in BOTH)
- **Service:** `nginx.service` with systemd override pointing to OpenResty binary

## Critical Architecture: Dual Nginx Binaries

This host has **two** nginx binaries:
1. **OpenResty** at `/usr/local/openresty/nginx/sbin/nginx` — used by systemd service
2. **System nginx** at `/usr/sbin/nginx` (Debian package) — used by NPM's API for config tests

**Any config change must pass `nginx -t` on BOTH binaries.** NPM's cert creation API internally runs `/usr/sbin/nginx -t` to validate before requesting certs. If the system nginx test fails, cert creation returns a 500 error even though the OpenResty service is running fine.

```bash
# Test both
/usr/local/openresty/nginx/sbin/nginx -t
/usr/sbin/nginx -t
```

## API Authentication

```bash
TOKEN=$(curl -s -X POST http://localhost:81/api/tokens \
  -H 'Content-Type: application/json' \
  -d '{"identity":"onewahid@gmail.com","secret":"<password>"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])')
```

## SSL Certificate Creation

### Option 1: NPM API (Let's Encrypt HTTP-01)

**⚠️ Requires system nginx to pass `nginx -t`** — see Pitfalls below. If system nginx lacks the `stream` module .so, use Option 2 instead.

**API Endpoint:** `POST /api/nginx/certificates`

**Required payload (correct schema):**
```json
{
  "provider": "letsencrypt",
  "domain_names": ["subdomain.example.com"],
  "meta": {
    "dns_challenge": false
  }
}
```

**⚠️ Common pitfalls:**
- `provider` is required at top level (not in meta)
- `meta` accepts ONLY: `dns_challenge`, `dns_provider`, `dns_provider_credentials`, `propagation_seconds`, `key_type`, `certificate`, `certificate_key`
- `meta` does NOT accept `letsencrypt_email` or `letsencrypt_agree` — these are handled internally
- Passing extra meta fields → 400 error: `"data/meta must NOT have additional properties"`
- If nginx config test fails → 500 error with the nginx test output in `debug.stack`

**Full request:**
```bash
curl -s -X POST http://localhost:81/api/nginx/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"provider":"letsencrypt","domain_names":["subdomain.example.com"],"meta":{"dns_challenge":false}}'
```

### Option 2: External Certbot + Manual Import (Recommended for complex setups)

When NPM's API can't create certs (e.g., system nginx lacks modules, need DNS-01 challenge, etc.), use external certbot and manually import:

**Step 1: Obtain cert with certbot**
```bash
# Example: Azure DNS challenge
certbot certonly --authenticator dns-azure \
  --dns-azure-credentials /etc/letsencrypt/azure.ini \
  --dns-azure-propagation-seconds 120 \
  -d subdomain.example.com \
  --non-interactive --agree-tos --email you@example.com
```

**Step 2: Import cert into NPM via API**
```bash
# Read cert files
CERT=$(cat /etc/letsencrypt/live/subdomain.example.com/fullchain.pem | awk '{printf "%s\\n", $0}')
KEY=$(cat /etc/letsencrypt/live/subdomain.example.com/privkey.pem | awk '{printf "%s\\n", $0}')

# Import as "other" provider
curl -s -X POST http://localhost:81/api/nginx/certificates \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"provider\":\"other\",\"nice_name\":\"subdomain.example.com\",\"domain_names\":[\"subdomain.example.com\"],\"meta\":{\"certificate\":\"$CERT\",\"certificate_key\":\"$KEY\"}}"
```

**Step 3: Copy cert files to NPM's custom_ssl directory**
```bash
# NPM expects certs at /data/custom_ssl/npm-<cert_id>/
CERT_ID=$(curl -s http://localhost:81/api/nginx/certificates -H "Authorization: Bearer $TOKEN" | python3 -c 'import json,sys; certs=json.load(sys.stdin); print([c["id"] for c in certs if "subdomain.example.com" in c["domain_names"]][0])')
mkdir -p /data/custom_ssl/npm-$CERT_ID
cp /etc/letsencrypt/live/subdomain.example.com/fullchain.pem /data/custom_ssl/npm-$CERT_ID/fullchain.pem
cp /etc/letsencrypt/live/subdomain.example.com/privkey.pem /data/custom_ssl/npm-$CERT_ID/privkey.pem
chmod 600 /data/custom_ssl/npm-$CERT_ID/*.pem
```

**Step 4: Enable SSL on proxy host**
```bash
curl -s -X PUT http://localhost:81/api/nginx/proxy-hosts/<host_id> \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"certificate_id\":$CERT_ID,\"ssl_forced\":true,\"http2_support\":true}"
```

**⚠️ Pitfall:** If NPM returns 500 when enabling SSL, check that the cert files exist at `/data/custom_ssl/npm-<cert_id>/`. The API import doesn't automatically copy files to disk.

## Common Config Fixes

See `references/native-install-config-fixes.md` for detailed fix steps including:
- Missing `proxy.conf` include file
- Missing `proxy` log format definition
- `stream` directive unknown (system nginx lacks .so module)
- Duplicate `proxy_http_version` directive
- NPM regenerating proxy_host configs from database (reverting manual edits)

## Adding a Reverse Proxy Host

1. **Create proxy host via API or web UI** — forward to target host:port
2. **Request SSL cert** via API (see above)
3. **Enable SSL on the proxy host** — NPM links the cert to the proxy host
4. **Verify** — `curl -sk https://subdomain.example.com/health` should reach the backend

## Pitfalls

1. **Dual config test** — Always verify both OpenResty AND system nginx pass `nginx -t`. NPM API uses system nginx.
2. **Include files in two paths** — Include files must exist at both `/usr/local/openresty/nginx/conf/conf.d/include/` and `/etc/nginx/conf.d/include/`. Copy from OpenResty path to system path.
3. **`proxy` log format not defined** — NPM-generated proxy_host configs use `access_log ... proxy;` but this format must be manually defined in `log.conf`. Without it, config test fails.
4. **`stream` block breaks system nginx** — System nginx (Debian package) has `stream` as a dynamic module but the .so files may not be installed. Comment out the `stream {}` block in nginx.conf if no stream configs exist.
5. **NPM regenerates proxy_host configs** — Requesting a cert or modifying a proxy host via the API regenerates the .conf file from NPM's database. Manual edits to log_format in proxy_host configs get reverted. Fix by defining the log format globally, not per-host.
6. **Duplicate `proxy_http_version`** — If `proxy_http_version 1.1` is set in the `http {}` block of nginx.conf AND in the included `proxy.conf`, system nginx errors. Remove from proxy.conf since it's inherited.
7. **`http2 off` deprecation** — NPM generates `http2 off;` in proxy_host configs. This is a non-breaking warning, not an error.
8. **Config test during cert request reverts edits** — The cert creation process regenerates configs AND runs nginx -t. If any config issue exists, it reports a 500 and you may not realize the config was also regenerated.
9. **PID file mismatch** — OpenResty's nginx.conf may have `pid` commented out, causing NPM to fail when reloading. Uncomment or add `pid /run/nginx.pid;` in nginx.conf's main context. After changing, restart nginx: `systemctl restart nginx`.
10. **proxy_pass scheme mismatch** — When creating proxy_host configs, ensure the scheme matches the backend. If backend is HTTP, use `proxy_pass http://...` not `https://`. A 502 error often indicates scheme mismatch.
11. **Port forwarding required** — NPM handles internal routing, but external access requires port forwarding on the router/firewall. Forward ports 80/443 from public IP to NPM server's internal IP.
12. **MikroTik RouterOS intercepts port 443** — If the router has its own HTTPS management interface on port 443, it will intercept external requests before they reach NPM. Symptoms: `curl` from outside shows MikroTik login page, SSL cert shows `CN=MikroTik-*`, or `openssl s_client` reveals MikroTik as issuer. Fix: change MikroTik's HTTPS management port to something else (e.g., 8443) in WinBox → IP → Services → https, then update port forwarding rules to forward 443 to NPM's internal IP.

**Correct MikroTik NAT rule format** — When forwarding both HTTP (80) and HTTPS (443) to NPM, use either two separate rules or one rule with `to-ports=0-1` (preserves original port mapping: 80→80, 443→443). Do NOT use `to-ports=443` for both ports — this maps port 80 traffic to port 443 on NPM, breaking HTTP access (connection refused because NPM's port 443 expects TLS, not plain HTTP).
```
# Correct single rule (preserves original ports):
/ip firewall nat add action=dst-nat chain=dstnat comment="Inbound to nginx" \
  dst-port=80,443 in-interface-list=WAN protocol=tcp \
  to-addresses=192.168.100.53 to-ports=0-1

# Or two separate rules:
/ip firewall nat add action=dst-nat chain=dstnat dst-port=80 in-interface-list=WAN protocol=tcp to-addresses=192.168.100.53 to-ports=80
/ip firewall nat add action=dst-nat chain=dstnat dst-port=443 in-interface-list=WAN protocol=tcp to-addresses=192.168.100.53 to-ports=443
```
**Also:** Verify the `WAN` interface list includes the correct WAN interface (`/interface list member print where list=WAN`). If the WAN interface is missing from the list, the NAT rule won't match any traffic.
13. **proxy_pass missing in NPM-generated config** — NPM's proxy_host configs may not include `proxy_pass` directive if the proxy host was created via API but the backend scheme/port weren't set correctly. If you get 404 from openresty (not from backend), check that the proxy_host config has `proxy_pass http://<backend_ip>:<port>;` in the location block. Fix: add it manually or recreate the proxy host via NPM web UI with correct backend settings.

## Related Skills

- `sendblue-sms` — Sendblue webhook setup uses NPM reverse proxy at `sendblue.wahidsaleemi.net`
- `webhook-subscriptions` — Hermes webhook platform that receives POSTs through NPM
- `ssh-file-deploy` — For deploying config files to remote hosts via SSH
