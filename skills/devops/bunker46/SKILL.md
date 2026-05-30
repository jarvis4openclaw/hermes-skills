---
name: bunker46
version: 1.0.0
description: Install, configure, and debug bunker46 (NIP-46 Nsec Bunker). Covers Docker deployment, relay management, NIP-46 event pipeline diagnostics, relay connection verification via nsenter, and known client compatibility issues. Use when setting up a new instance, troubleshooting connection failures, or managing relay configuration.
category: devops
trigger_conditions:
  - "install bunker46"
  - "set up bunker46"
  - "deploy bunker46"
  - "bunker46 connection"
  - "nip-46 connect"
  - "bunker46 relay"
  - "bunker46 debug"
  - "nsec bunker"
  - "nip-46 bunker"
  - "bunker46 health"
  - "bunker46 logs"
  - "bunker won't connect"
  - "bunker can't sign"
---

# Bunker46 — NIP-46 Nsec Bunker Management

bunker46 is a self-hosted NIP-46 remote signer (TypeScript, NestJS, Prisma, Docker). Repo: https://github.com/dsbaars/bunker46

## Triggers

- Installing or updating bunker46
- Debugging NIP-46 connection failures (client can't connect)
- Managing relay configuration
- Checking bunker health / relay subscriptions

## Architecture

Bunker46 runs as Docker containers (docker compose):
- `bunker46-server-1` — NestJS backend (port 3000)
- `bunker46-web-1` — Web dashboard (port 8080, proxies to server)
- `bunker46-db-1` — PostgreSQL
- `bunker46-redis-1` — Redis (event streaming / session)

Network: all containers on Docker bridge (`docker compose` default). Expose ports via docker-compose to make web dashboard accessible.

## Installation

Clone the repo and use docker compose:

```bash
git clone https://github.com/dsbaars/bunker46.git /root/bunker46
cd /root/bunker46
cp .env.example .env
```

Key env vars in `.env`:
- `DATABASE_URL=postgresql://bunker46:bunker46@db:5432/bunker46`
- `REDIS_URL=redis://redis:6379`
- `NOSTR_DEFAULT_RELAYS=wss://relay.nsec.app,wss://relay.damus.io,wss://nos.lol`
- `JWT_SECRET=<random>`
- `ENCRYPTION_KEY=<random 32 bytes hex>`

If running on a Proxmox CT without native Docker, install Docker first (detect the OS):

**Alpine/LXC:**
```bash
apk add docker docker-cli-compose
rc-update add docker boot
service docker start
```

**Ubuntu/Debian (e.g. CT 202, Ubuntu 24.04):**
```bash
apt update
apt install -y docker.io docker-compose-plugin
systemctl enable docker
systemctl start docker
```

First run:
```bash
docker compose up -d
# Wait for DB migration
docker compose exec server npx prisma db push
docker compose restart server
```

The web dashboard should be at `http://<host>:8080`.

## NIP-46 Event Pipeline

**How bunker46 receives connect events:**

1. The `BunkerService.onModuleInit()` calls `resumeAllListeners()` which loads all nsec keys from the database
2. For each nsec key, it creates a `SimplePool.subscribe()` subscription on configured relays
3. The subscription filter: `{ kinds: [24133], '#p': [signerPubkeyHex] }`
4. Incoming events are decrypted via NIP-44 v2 first, then NIP-04 fallback
5. Decrypted payload is parsed against `Nip46RequestSchema`
6. For "connect" method: `BunkerRpcHandler` auto-creates a connection (if secret matches) or sends "ack"
7. Response is encrypted and published back to the same relays, tagged with `#p = clientPubkey`

**Key source files:**
- `apps/server/src/bunker/bunker.service.ts` — relay subscription, event handling, listener lifecycle
- `apps/server/src/bunker/bunker-rpc.handler.ts` — RPC command routing (connect/ack, get_public_key, sign_event, etc.)
- `apps/server/src/common/crypto/encryption.service.ts` — Nsec encryption at rest

## Debugging Connection Issues

### Step 1: Check if bunker is listening

```bash
docker logs bunker46-server-1 --tail 20 | grep "Listening for NIP-46"
```

Expected: `Listening for NIP-46 on wss://relay.nsec.app, wss://relay.damus.io, ... for <pubkey>...`

### Step 2: Verify relay WebSocket connections

The container's network connections won't show on the host — use `nsenter` to enter the container's network namespace:

```bash
PID=$(docker inspect --format '{{.State.Pid}}' bunker46-server-1)
nsenter -t $PID -n ss -tn
```

Look for ESTABLISHED connections on port 443 — each is a WebSocket to a relay.

### Step 3: Monitor for incoming connect events

```bash
docker logs -f bunker46-server-1 | grep -E "NIP-46 connect|Failed to decrypt|Invalid NIP-46"
```

- "NIP-46 connect from \<pubkey\>" — event arrived and was decrypted successfully
- "Failed to decrypt NIP-46 message" — event arrived but decryption failed (NIP-44/NIP-04 mismatch)
- "Invalid NIP-46 request schema" — event arrived and decrypted but payload doesn't match expected format
- SILENCE + pending secret registered → **event never reached any relay** (client-side issue)

### Step 4: Check pending secrets

```bash
docker exec bunker46-db-1 psql -U bunker46 -d bunker46 \
  -c "SELECT client_pubkey, name, status, created_at FROM bunker_connections ORDER BY created_at DESC;"
```

### Step 5: Check relay configuration

```bash
docker exec bunker46-db-1 psql -U bunker46 -d bunker46 \
  -c "SELECT url FROM relay_configs;"
```

Default relays are set in `.env` (`NOSTR_DEFAULT_RELAYS`). User-specific relays override defaults and are included in bunker URIs.

### Step 6: Restart to force fresh subscriptions

```bash
docker compose -f /root/bunker46/docker-compose.yml restart server
```

## Relay Configuration

Add a custom relay:
```bash
# Via the bunker46 API or directly in the database:
docker exec bunker46-db-1 psql -U bunker46 -d bunker46 \
  -c "INSERT INTO relay_configs (id, user_id, url) VALUES (gen_random_uuid()::text, '<user_id>', 'wss://relay.example.com');"
```

Remove a relay:
```bash
docker exec bunker46-db-1 psql -U bunker46 -d bunker46 \
  -c "DELETE FROM relay_configs WHERE url = 'wss://relay.example.com';"
```

After changing relays, restart the server so listeners pick up the new relay set.

Note: The bunker URL includes ALL configured relays. Long relay lists can cause issues with some clients. If a client can't connect, try reducing to 1-2 well-known relays (e.g., just `wss://relay.damus.io`).

## Known Client Compatibility

### Vega (hoornet/vega) — CONNECT EVENTS DON'T ARRIVE

Vega's NIP-46 implementation does NOT reliably publish connect events to the relays specified in the bunker URL. The events never reach any relay the bunker listens on — not even hitting decryption. Other clients (Primal, Amethyst, Coracle) connect successfully via the same relays.

Vega README mentions an "embedded strfry relay" — this local relay may interfere with the bunker's relay list. Check Vega's Settings → Relays to ensure at least one of the bunker's relays is listed there.

If Vega must be used, find Vega's pubkey from its settings and pre-create a connection manually via the bunker46 API.

### General compatibility

Bunker46 uses NIP-44 v2 encryption with NIP-04 fallback. Clients using older NIP-04-only implementations should still work. If a client's events arrive but fail to decrypt, the issue is likely the NIP-44 conversation key derivation.

## References

- `references/nip46-debug-pipeline.md` — Detailed event flow diagnostics, diagnostic commands, root cause categories, and Vega-specific investigation notes.

## Pitfalls

- **Port exposure**: Ensure the web dashboard port (default 8080) is exposed in docker-compose.yml if running on a remote CT. Default compose only exposes internally.
- **Secret expiry**: Pending secrets expire after 10 minutes. Generate a fresh bunker URI right before use.
- **Relay filter mismatch**: The bunker subscribes with `#p = signerPubkey`. Client connect events MUST include a `p` tag matching the signer's pubkey, otherwise relays may not forward them.
- **Docker network isolation**: Use `nsenter -t <pid> -n` to inspect container network state. Host-level `ss` won't show container connections.
- **Cascade deletes**: `bunker_connections` has `ON DELETE CASCADE` to `nsec_keys`. Deleting an nsec key deletes all its connections.
- **OS-specific Docker install**: The skill previously only listed Alpine (`apk`) commands. Proxmox CTs may run Ubuntu (e.g. CT 202 is Ubuntu 24.04). Using `apk` on Debian/Ubuntu fails immediately. Always check `/etc/os-release` and use the correct package manager (`apt` for Debian/Ubuntu, `apk` for Alpine).
