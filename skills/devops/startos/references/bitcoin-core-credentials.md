# Finding Bitcoin Core RPC Credentials on StartOS

This is the reproducible pattern used to connect wallets (Sparrow, Specter, etc.)
to a StartOS-hosted Bitcoin Core node.

## Step 1: SSH In

```bash
ssh start9@<startos-ip>   # key auth, not password
```

## Step 2: Read stats.yaml

```bash
sudo cat /media/startos/data/package-data/volumes/bitcoind/data/main/start9/stats.yaml
```

This always contains:
- `RPC Username` — plaintext (e.g., `bitcoin`)
- `RPC Password` — plaintext but masked in WebUI
- `LAN Quick Connect` — `btcstandup://user:pass@<hostname>.local:8332`
- `Tor Quick Connect` — `btcstandup://user:pass@<hostname>.onion:8332`
- `Blockchain Sync Summary` — block height and percentage
- `Disk Usage` — blockchain size
- `Connections` — peer count (in/out)

**WARNING:** The `RPC Password` from `stats.yaml` does NOT always match the `rpcauth` hash in `bitcoin.conf`. StartOS generates the `rpcauth` line when the password is changed in the WebUI, but the UI display and `stats.yaml` can drift from the actual hash. If you get `401 Unauthorized` with the stats.yaml password, the hash is stale. Use **cookie auth** (see Step 2b below) as the reliable fallback.

## Step 2b: Cookie Auth (Reliable Fallback)

When password auth fails, use Bitcoin Core's `.cookie` file directly. The cookie is regenerated on every Bitcoin Core restart, but it always works.

```bash
# Read the cookie from the StartOS host
sudo cat /media/startos/data/package-data/volumes/bitcoind/data/main/.cookie
```

Output format: `__cookie__:<64-char-hex>`

Use it as Basic Auth `username:password`:
```bash
COOKIE=$(sudo cat /media/startos/data/package-data/volumes/bitcoind/data/main/.cookie)
curl -sk -u "$COOKIE" \
  -H "Content-Type: application/json" \
  -d '{"method":"getblockchaininfo","params":[],"id":1}' \
  https://<startos-ip>:<bitcoin-rpc-port>
```

For Sparrow: copy the cookie string to your client machine and use **Cookie** auth mode, pointing Sparrow at a local file containing the cookie string. Or shell-export: copy the file via SCP and point Sparrow at it.

## Step 3: Read bitcoin.conf (for details)

```bash
sudo cat /media/startos/data/package-data/volumes/bitcoind/data/main/bitcoin.conf
```

Key settings to note:
- `rpcbind=127.0.0.1:58332` — internal RPC bind (not LAN-accessible)
- `rpcauth=` — the hashed auth line
- `rpccookiefile=.cookie` — cookie auth fallback
- `bind=0.0.0.0:58333` + `whitebind=0.0.0.0:8333` — P2P ports
- `prune=500000` — pruning enabled at 500GB
- `txindex=0` — no transaction index (pruned node)
- `zmqpub*` — ZMQ endpoints for Lightning integration

## For Wallet Connection (Sparrow, etc.)

In StartOS 0.4.0, each service gets its own port on the server's main address (not per-service `.local` hostnames). Find the Bitcoin RPC port by checking the StartOS WebUI under Bitcoin Core → Service Interfaces → API, or from the LAN Quick Connect URL in `stats.yaml`. In 0.3.x, the port was always 8332. In 0.4.0, it can be any port (e.g., 62642).

Connect to: `https://<server-ip>:<rpc-port>` (or `https://<server-name>.local:<rpc-port>` if mDNS is working).

**Sparrow NPE diagnostic:** If Sparrow throws `Cannot invoke "ErrorMessage.toString()" because "<parameter1>" is null`, this is NOT a Sparrow bug — it's a `401 Unauthorized` with an empty JSON-RPC error body. The fix is the auth, not Sparrow. Use cookie auth or fix the password mismatch.

### Diagnostics Checklist (when .local hostname fails)

Before giving up on LAN, run these checks **on the StartOS host**:

```bash
# 1. Is mDNS enabled? (0.4.0 often ships with it OFF)
resolvectl mdns ens18          # if -mDNS → disabled → sudo resolvectl mdns ens18 yes

# 2. Are services actually announced?
avahi-browse -at 2>/dev/null | head -20   # no StartOS entries = not announcing

# 3. Are port bindings configured?
start-cli server host binding list         # empty = no LAN exposure configured

# 4. Is the port actually listening?
sudo ss -tlnp | grep -E ":8332|:8333"     # nothing = no port open
```

**Common failure pattern (0.4.0-beta):** `resolvectl mdns ens18` shows `-mDNS`. The fix is `sudo resolvectl mdns ens18 yes`, BUT this alone may not help if startd hasn't created port bindings. Check step 3 — if bindings are empty, services aren't exposed to LAN at all.

**When all checks fail:** Use Tor. Sparrow supports SOCKS5 proxy natively — connect via the `.onion` address from `stats.yaml`. No LAN configuration needed.

### Wallet Configuration

In Sparrow: select **"Bitcoin Core (RPC)"** — NOT "Electrum" unless electrs is installed. Enter the `<hostname>.local:8332` URL (or `.onion`) plus the RPC credentials from `stats.yaml`.

If mDNS isn't available on the client (common on Windows without Bonjour): use the **Tor Quick Connect** URL instead via Sparrow's SOCKS5 proxy setting (`127.0.0.1:9050`).

## Check If Electrum Server Exists

```bash
start-cli package list | grep -i electrs
```

If not listed, Sparrow must use Bitcoin Core RPC (slower but fully functional).
