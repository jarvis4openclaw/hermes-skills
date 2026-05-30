# NIP-46 Debug Pipeline — Bunker46 Event Flow Diagnostics

This reference covers the end-to-end debugging path used when a Nostr client fails to connect to bunker46. Written from the 2026-05-25 Vega debugging session.

## Event Flow

```
Client → Relay (wss://relay.nsec.app) → bunker46-server-1 (SimplePool subscription)
                                              ↓
                                       handleIncomingEvent()
                                              ↓
                                       NIP-44 v2 decrypt → NIP-04 fallback
                                              ↓
                                       Nip46RequestSchema.parse()
                                              ↓
                                       BunkerRpcHandler (connect/ack)
```

## Diagnostic Commands

### 1. Check bunker listener status
```bash
ssh root@<ct-ip> 'docker logs bunker46-server-1 --tail 30 | grep -E "Listening for|Resumed listeners"'
```
Healthy output: `Listening for NIP-46 on wss://relay.nsec.app, wss://relay.damus.io, ... for <pubkey>...`

### 2. Inspect container network connections (NOT host-level)
```bash
ssh root@<ct-ip> 'PID=$(docker inspect --format "{{.State.Pid}}" bunker46-server-1) && nsenter -t $PID -n ss -tn'
```
Look for ESTABLISHED connections on :443 to relay IPs. Without `nsenter`, you see only the Docker bridge connection to the host — useless for relay diagnostics.

### 3. Verify relay subscriptions are live
```bash
ssh root@<ct-ip> 'docker logs bunker46-server-1 --since 5m | grep -E "subscribe|unsubscribe|close"'
```
SimplePool should maintain persistent WebSocket connections. If you see frequent reconnects, the relay is unstable.

### 4. Monitor for actual NIP-46 events
```bash
ssh root@<ct-ip> 'docker logs -f bunker46-server-1 | grep -E "NIP-46 connect|decrypt|pending secret"'
```

Interpretation:
- "NIP-46 connect from <pubkey>" → SUCCESS: event arrived and was decrypted
- "Failed to decrypt NIP-46 message" → event arrived, encryption failed
- "Invalid NIP-46 request schema" → event decrypted but payload malformed
- "Registered pending secret" with NO follow-up → client never sent event

### 5. Check database for existing connections
```bash
ssh root@<ct-ip> "docker exec bunker46-db-1 psql -U bunker46 -d bunker46 -c \"
SELECT id, client_pubkey, name, status, created_at 
FROM bunker_connections 
ORDER BY created_at DESC 
LIMIT 10;\"" 
```

### 6. Check relay configs
```bash
ssh root@<ct-ip> "docker exec bunker46-db-1 psql -U bunker46 -d bunker46 -c 'SELECT url FROM relay_configs;'"
```

## Root Cause Categories

### Events never arrive (no log output)
**Client-side issue.** The relay subscription is healthy (verified by other successful connects). Root causes:
- Client sends to wrong relay (not in bunker URL relay list)
- Client doesn't include `p` tag matching signer pubkey in kind 24133 event
- Client has local relay that intercepts before publishing to bunker relays
- Client's WebSocket connection to relay fails silently

### Events arrive but fail decryption
- NIP-44 v2 conversation key mismatch (client using different NIP-44 version)
- NIP-04 fallback also fails (incorrect shared secret derivation)
- Event content format not matching expected encryption wrapper

### Events decrypt but fail validation
- Client sending non-standard NIP-46 request format
- Missing required fields in connect payload

## Vega-Specific Investigation (2026-05-25)

- Vega README claims NIP-46 support with bunker:// URI
- Uses embedded strfry relay — possible interference with external relay publishing
- No NIP-46 related issues filed on Vega's GitHub (repo: hoornet/vega)
- Tested with 3 and 4 relay configs — events never reached bunker46 in either case
- Other clients (Primal, Amethyst) connect fine via same relays
- Conclusion: Vega NIP-46 client implementation bug — events not published to specified relays
