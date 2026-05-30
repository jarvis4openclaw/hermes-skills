# Docker Service Deployment on Proxmox LXC Containers

Pattern for deploying Docker Compose-based services on Proxmox LXC containers.

## Prerequisites Check

Before deploying, check the CT config for Docker compatibility:

```
pct config <ctid> | grep features
```

Docker requires `nesting=1` on the LXC. If missing, stop the CT, add `features: nesting=1` in Proxmox UI or via `pct set`, then restart.

Check resources:
```
pct exec <ctid> -- free -h          # RAM — Docker + DB + app stack can need 1-2GB+
pct exec <ctid> -- df -h /          # Disk — images + volumes add up fast
pct exec <ctid> -- docker --version 2>&1  # Is Docker already installed?
```

## SSH Access

Prefer **direct SSH** to the CT's IP when available — faster and fewer escaping issues than `pct exec`:
```
ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@<ct-ip> '<command>'
```

Fallback: `pct exec <ctid> -- <command>` through the Proxmox host.

## Docker Install (Ubuntu/Debian CT)

On a fresh CT without Docker:
```
apt-get update -qq
apt-get install -y -qq ca-certificates curl
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sh /tmp/get-docker.sh
```

This installs Docker Engine + compose plugin (modern `docker compose`, not legacy `docker-compose`). Verify with `docker --version`.

**Storage driver:** Modern Docker in LXC uses `overlayfs` with containerd snapshotter — works out of the box. No special config needed.

## Deployment Pattern

1. **Clone the repo** into `/root/<project>/` on the CT
2. **Review** `docker-compose.yml` and `.env.example` for required env vars
3. **Generate secrets** using `openssl rand -hex 32` for JWT secrets, encryption keys, etc.
4. **Create `.env`** with all required variables at the repo root
5. **Build and start:** `docker compose up -d --build`
6. **Verify:**
   ```
   docker ps                    # all containers Up/healthy
   curl -s http://localhost:<port> | head -20  # frontend serves HTML
   docker logs <container> --tail 20           # no errors in server logs
   ```

## .env Secret Generation

Pattern for creating a .env with generated secrets on the CT in one shot:
```
cat > /root/<project>/.env << ENVEOF
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://<ct-ip>:<web-port>
ALLOW_REGISTRATION=true
LOG_LEVEL=info
ENVEOF
```

**Important:** After writing, verify non-secret values are correct before deploying:
```
grep CORS_ORIGINS /root/<project>/.env
grep ALLOW_REGISTRATION /root/<project>/.env
```

The terminal output may censor hex strings as `***` — that's fine, the file still has the real values.

## Post-Deploy Verification

```
# All containers healthy?
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Frontend responds?
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:<web-port>

# API responds?
curl -s http://localhost:<api-port>/api  # 404 on root /api is normal for NestJS

# Server logs (look for "successfully started" or errors)
docker logs <server-container> --tail 30
```

## Known Constraints

- **Memory:** 2GB RAM is tight for PostgreSQL + Redis + API server + web server. Monitor with `docker stats` — if OOM kills start happening, increase CT RAM.
- **WebAuthn/Passkeys:** Won't work on a local IP without HTTPS + real domain. Username/password + TOTP fallback is fine.
- **Health checks:** Docker's "(health: starting)" label appears for the first check interval — wait 30-60s before worrying about it. Not all services define explicit healthchecks in compose.
- **Port exposure:** Docker compose exposes ports to 0.0.0.0 by default. On a trusted LAN (192.168.x.x) this is fine. For public exposure, add a reverse proxy with HTTPS.

## Debugging Container Network Connectivity

To check if a Docker container has active WebSocket/outbound connections (e.g., to relay servers):

```bash
# Get the container's PID
PID=$(docker inspect --format '{{.State.Pid}}' <container-name>)

# Enter container's network namespace and list TCP connections
nsenter -t $PID -n ss -tn
```

Look for ESTABLISHED connections to expected external hosts. If connections are missing or stale, restart the container: `docker compose restart <service>`.

## Bunker46 Deployment (Example)

**Repo:** https://github.com/dsbaars/bunker46 (NIP-46 Nsec Bunker, TypeScript monorepo)
**Deployed on:** CT 202 (nostrX, 192.168.100.54)

### Stack
- 4 Docker Compose services: `postgres:17-alpine`, `redis:7-alpine`, NestJS server (port 3000), Caddy+Vue web (port 8080)
- Built from source via `docker compose up -d --build` (pnpm monorepo)
- Database tables: `users`, `nsec_keys`, `bunker_connections`, `relay_configs`, `signing_logs`, `sessions`, `passkeys`, `connection_permissions`

### Required .env Variables
```
JWT_SECRET=<openssl rand -hex 32>
JWT_REFRESH_SECRET=<openssl rand -hex 32>
ENCRYPTION_KEY=<openssl rand -hex 32>
CORS_ORIGINS=http://<ct-ip>:8080
WEBAUTHN_RP_NAME=Bunker46
WEBAUTHN_RP_ID=<ct-ip>
WEBAUTHN_ORIGIN=http://<ct-ip>:8080
ALLOW_REGISTRATION=true
LOG_LEVEL=info
```

### Relay Management
Default relays: `relay.nsec.app`, `relay.damus.io`, `nos.lol` (hardcoded in `packages/config/src/constants.ts`).
Custom relays are stored in the `relay_configs` table. To remove a custom relay:
```bash
docker exec bunker46-db-1 psql -U bunker46 -d bunker46 \
  -c "DELETE FROM relay_configs WHERE url = 'wss://custom.relay';"
```
Then restart server to pick up the new relay list: `docker compose restart server`.
Restarting also forces fresh SimplePool subscriptions — useful when relay connections appear stale.

## Debugging NIP-46 Connection Issues (bunker46)

### One-Time Secret Mechanism
Each `bunker://` URI contains a one-time secret. The first client to send a valid `connect` request with that secret consumes it — subsequent clients get "Unknown client" / "No matching pending secret." This is by design. For multi-client setups, generate separate bunker URLs per client.

### Diagnostic Log Analysis
The bunker server logs follow a consistent pattern for every NIP-46 connect attempt:

```
[Nest] LOG [BunkerService] Registered pending secret for <signerPubkey>...
[Nest] LOG [BunkerService] NIP-46 connect from <clientPubkey>... (id: <rid>)
[Nest] LOG [BunkerRpcHandler] Auto-creating connection for <clientPubkey>... via bunker:// URI
[Nest] LOG [BunkerRpcHandler] Connection <id> activated for <clientPubkey>...
[Nest] LOG [BunkerService] NIP-46 response sent for connect to <clientPubkey>...
```

Failure signature — if decryption fails silently:
- No log entry at all for the client → event never reached the relay or relay didn't forward it
- "Failed to decrypt NIP-46 message" → encryption mismatch (try disabling custom relays)

### "didn't respond within 15 seconds" (Client Timeout)
This means the client sent the connect event but the bunker never responded. Check in order:
1. **Relay mismatch:** The bunker URL includes relays the client may not support. Simplify by removing custom relays and sticking to defaults.
2. **Subscription freshness:** Restart the bunker server to force fresh WebSocket relay subscriptions.
3. **Event never arrived at bunker:** Check logs for the client's pubkey. If missing, the relay didn't forward the event (subscription filter mismatch or relay connectivity issue).
4. **Decryption failure:** If bunker subscribes but can't decrypt, it logs a warning but sends no response — the client times out.

### Race Condition: Multiple Clients Competing
If multiple Nostr clients (Primal, Amethyst, browser extensions, Vega) are running, they may race to consume the one-time secret before the intended client. Close all other Nostr apps before pasting the bunker URL into the target client.
