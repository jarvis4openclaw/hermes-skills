---
name: startos
version: 1.0.0
description: Manage StartOS servers — SSH access, finding service credentials, checking service health, understanding network exposure (mDNS, Tor). Use when asked to inspect, troubleshoot, or configure anything on a StartOS host.
metadata:
  hermes:
    tags: [startos, start9, bitcoin-core, mDNS, tor, rpc, credentials]
    trigger_conditions:
      - "startos"
      - "start9"
      - "bitcoin rpc credentials"
      - "stats.yaml"
      - ".local hostname"
      - "mdns resolve"
      - "sparrow wallet"
      - "start-cli"
      - "cookie auth"
      - "bitcoin.conf"
      - "startos service"
      - "tor .onion"
      - "wireguard startos"
---

# StartOS Management

## When to Use

- Extracting RPC credentials (username/password/cookie) for Bitcoin Core or other services
- Diagnosing `.local` hostname resolution failures (mDNS)
- Connecting wallets (Sparrow, Specter) to StartOS-hosted services
- Troubleshooting service network exposure (LAN vs Tor vs Web proxy paths)
- Checking service health, disk usage, or resource metrics via `start-cli`
- Setting up WireGuard tunnel clients on StartOS for remote access
- Port forwarding from Start Tunnel to StartOS services
- Finding service native config files (bitcoin.conf, lnd.conf) on disk
- Understanding SSH access (key-based, host key drift, no root)

## Not For

- Managing the Start Tunnel VPR itself (config, daemon, port forwards on the tunnel server) → use `start-tunnel`
- General SSH operations or file deployment to arbitrary hosts → use `ssh-file-deploy` or direct `terminal` SSH
- Proxmox VE host or VM management → use `proxmox-host-management`
- Resource reporting from Proxmox → use `proxmox-resource-reporting`
- Windows host management → use `windows-ssh`
- Generic wallet software support — this skill covers the StartOS service side only

## SSH Access

StartOS uses key-based SSH. The user is `start9` (root disabled). The `start9` user has `sudo`.

```bash
ssh -i ~/.ssh/id_ed25519 start9@<IP>
```

**Host key changes on version updates** (e.g., beta8 → beta9). Fix with:
```bash
ssh-keygen -f ~/.ssh/known_hosts -R <IP>
ssh-keyscan -H <IP> >> ~/.ssh/known_hosts
```

## Finding Service Credentials

Service data lives under:
```
/media/startos/data/package-data/volumes/<service>/data/main/
```

### Quick Connect URLs & Credentials (stats.yaml)

Every StartOS service exposes a `start9/` subdirectory in its data volume containing:

| File | Purpose |
|------|---------|
| `config.yaml` | User-facing config (translated to native format) |
| `stats.yaml` | Quick Connect URLs, RPC credentials, sync status, disk usage |

**Read stats.yaml to get RPC credentials instantly:**
```bash
sudo cat /media/startos/data/package-data/volumes/<service>/data/main/start9/stats.yaml
```

This file ALWAYS contains (for RPC-enabled services):
- `RPC Username` / `RPC Password` (plaintext, masked in WebUI)
- LAN Quick Connect URL (`.local` mDNS hostname)
- Tor Quick Connect URL (`.onion` address)
- Blockchain sync summary, disk usage, peer counts

### Service Native Config

The service's own config (e.g., `bitcoin.conf`, `lnd.conf`) is in the same parent directory:
```bash
sudo cat /media/startos/data/package-data/volumes/<service>/data/main/bitcoin.conf
```

Use this to see actual bind addresses, ports, whitelist rules, ZMQ endpoints, etc.

## Service Network Exposure

StartOS reverse-proxies ALL service traffic through its `startd` daemon. Services are NOT directly accessible by IP:port. Three access paths:

| Path | Format | Requires |
|------|--------|----------|
| LAN (mDNS) | `<hostname>.local:<port>` | mDNS resolver (macOS/Linux native; Windows: Bonjour) |
| Tor | `<hostname>.onion:<port>` | Tor daemon or Tor Browser |
| Web proxy | `https://<IP>/rpc/<service>/` | Browser/curl with StartOS session cookie |

**Key insight:** Ports shown in `stats.yaml` (e.g., `8332`) are startd proxy forwardings — they won't appear in `ss -tlnp` output. The actual internal bind (e.g., `rpcbind=127.0.0.1:58332` from `bitcoin.conf`) is container-local only.

## Common Commands (0.4.0-beta.x)

| Task | Command |
|------|---------|
| List installed services | `start-cli package list` |
| Server metrics (JSON) | `start-cli server metrics --format json` |
| OS version & hardware | `start-cli server device-info` |
| Service logs | `start-cli package logs <id>` |
| Restart service | `start-cli package restart <id>` |
| Attach to container shell | `start-cli package attach <id>` |
| Server host addresses | `start-cli server host address list` |
| Server host bindings | `start-cli server host binding list` |
| Rebuild service container | `start-cli package rebuild <id>` |
| System restart | `start-cli server restart` |
| Check for updates | `start-cli server update` |

**Note:** `start-cli package info` and `start-cli package config` are NOT valid subcommands in 0.4.0-beta9.

## Checking Listening Ports

StartOS runs many startd proxy ports. Filter for the service you care about:
```bash
sudo ss -tlnp | grep startd
```

Or check the service's own config for internal bind addresses.

## Disk & Resource Checks

```bash
start-cli server metrics --format json
```
Returns CPU%, RAM (total/used/available, including ZRAM), disk (used/available/capacity), temperature.

## Troubleshooting .local Hostname Resolution (0.4.0)

When a `.local` hostname from `stats.yaml` doesn't resolve or returns "connection refused":

1. **Check mDNS status on StartOS:**
   ```bash
   ssh start9@<ip> 'resolvectl status ens18 | grep mDNS'
   # OR: resolvectl mdns
   ```
   If output shows `-mDNS`, mDNS is DISABLED. **Fix:** `sudo resolvectl mdns ens18 yes`

2. **Check avahi registrations:**
   ```bash
   ssh start9@<ip> 'avahi-browse -at 2>/dev/null | head -20'
   ```
   No StartOS service entries = startd isn't announcing services. mDNS enable alone may not fix this.

3. **Check startd DNS (port 53):**
   ```bash
   ssh start9@<ip> 'dig +short +time=2 +tries=1 @127.0.0.1 -p 53 <hostname>.local'
   ```
   Timeout = startd DNS not responding. This is a startd bug in some 0.4.0-beta builds.

4. **Check port bindings:**
   ```bash
   ssh start9@<ip> 'start-cli server host binding list'
   ```
   Empty table = NO bindings configured → no service ports exposed to LAN. The `.local` hostname exists in name only.

5. **Verify the port is actually open:**
   ```bash
   ssh start9@<ip> 'sudo ss -tlnp | grep -E ":8332|:8333"'
   ```
   If nothing shows, the port isn't listening on the host — mDNS alone won't help. A binding must be created in StartOS WebUI or via CLI.

**When .local fails entirely:** Use Tor. Sparrow supports SOCKS5 proxy natively. The `.onion` address from `stats.yaml` works without any LAN configuration.

## Remote Access via VPN Tunnel (Start Tunnel Integration)

When StartOS lives behind NAT and `.local`/Tor are insufficient, a WireGuard tunnel via Start Tunnel provides reliable access without exposing the StartOS IP.

### Setting up WireGuard Client on StartOS

The StartOS device must connect as a WireGuard peer. Generate the config from the Start Tunnel server:

```bash
# On the Start Tunnel server
start-tunnel device show-config <subnet> <startos-ip> [wan-addr]
```

**CRITICAL BUG (v0.4.0-beta.9):** `show-config` copies the web listen IP into the Endpoint field. If listen is `0.0.0.0`, Endpoint becomes `0.0.0.0:51820` (broken). **Always manually replace** with the tunnel server's public IP before pasting into StartOS:

```
Endpoint = 20.51.120.252:51820   # ← replace whatever show-config gives you
```

Install and start WireGuard on StartOS:

```bash
# Create the tunnel config (adjust keys from show-config output)
sudo tee /etc/wireguard/start-tunnel.conf << 'EOF'
[Interface]
Address = 10.59.139.4/24
PrivateKey = <from show-config>

[Peer]
PublicKey = <server pubkey>
PresharedKey = <from show-config>
AllowedIPs = 10.59.139.0/24
Endpoint = <public-ip>:51820
PersistentKeepalive = 25
EOF

sudo wg-quick up start-tunnel
sudo systemctl enable wg-quick@start-tunnel
```

Verify: `wg show` should show `latest handshake: X seconds ago` for the StartOS peer.

### Port Forwarding to StartOS Services

Once the tunnel is up, forward public ports to the StartOS WireGuard IP:

1. In Start Tunnel WebUI: Port Forwarding → Add
2. External IP: the tunnel server's public IP
3. Source Port: the public port you want (e.g., `8333` for Bitcoin P2P)
4. Target: `10.59.139.4:<startos-peer-port>` (the port StartOS assigned, e.g., `56508`)

Start Tunnel handles iptables automatically. You only need to open the port in your cloud provider's NSG (e.g., Azure Network Security Group for inbound TCP/UDP).

### Getting StartOS Service Ports

```bash
ssh start9@<startos-ip> 'start-cli package logs bitcoind | grep -i "p2p\|peer\|listening"'
# OR read the service's native config:
sudo cat /media/startos/data/package-data/volumes/bitcoind/data/main/bitcoin.conf | grep -E "bind|port"
```

The port shown in the StartOS WebUI under Bitcoin Core → Interfaces is the startd-forwarded P2P port — that's your `<startos-peer-port>`.

**Full reference:** `references/start-tunnel-integration.md`

## Pitfalls

1. **mDNS may be OFF by default on 0.4.0** — `systemd-resolved` in StartOS 0.4.0-beta may ship with `mDNS=no`. Always check with `resolvectl mdns ens18` before suggesting `.local` hostname connections. Recovery: `sudo resolvectl mdns ens18 yes`.

2. **mDNS must work on the CLIENT too** — Windows users must install Apple Bonjour (bundled with iTunes, or standalone). macOS and Linux support mDNS natively. Recovery: on Windows, install Bonjour or use Tor as fallback.

3. **Ports in `stats.yaml` won't show in `ss -tlnp`** — These are startd proxy forwardings, not process-level binds. Recovery: read the service's native config file (`bitcoin.conf`) for the actual internal bind address.

4. **Empty binding list means no LAN exposure** — `start-cli server host binding list` returning an empty table means NO services are exposed to LAN. `.local` hostnames may exist but have no ports behind them. Recovery: create bindings in the StartOS WebUI.

5. **Bitcoin Core RPC password mismatch (0.4.0)** — The RPC password shown in StartOS WebUI / `stats.yaml` does NOT always match the `rpcauth` hash in `bitcoin.conf`. If password auth returns `401 Unauthorized`, the hash is stale. Recovery: use **cookie auth** (see `references/bitcoin-core-credentials.md`) or force regeneration by toggling the RPC password in WebUI → Bitcoin Core → Settings.

6. **Cookie auth is the reliable fallback** — When password auth fails, read `/media/startos/data/package-data/volumes/bitcoind/data/main/.cookie` and use `__cookie__:<hex>` as the Basic Auth username:password. This bypasses the `rpcauth` hash entirely. Recovery: always try cookie auth before debugging password auth.

7. **Sparrow NPE on 401 is an auth failure, not a Sparrow bug** — If Sparrow throws `Cannot invoke "ErrorMessage.toString()" because "<parameter1>" is null`, it's receiving a `401 Unauthorized` with an empty JSON-RPC error body. Fix the auth (usually switch to cookie auth) rather than debugging Sparrow.

8. **Host key drifts on every OS version update** — StartOS updates regenerate SSH host keys. Recovery: keyscan after every version bump (`ssh-keygen -R <IP> && ssh-keyscan -H <IP> >> ~/.ssh/known_hosts`).

9. **No root SSH — only `start9` user** — Use `sudo` for privileged commands. `sudo -i` / `sudo su` not needed — just prefix commands with `sudo`. Recovery: if you get "Permission denied", add `sudo`.

10. **Boot disk pressure is common** — StartOS often has a tight boot disk (730GB with blockchain). Recovery: monitor with `start-cli server metrics`, consider offloading data or attaching external storage.

11. **WireGuard `show-config` endpoint IP bug (v0.4.0-beta.9)** — Endpoint defaults to web listen IP instead of WAN IP. Recovery: always manually replace the Endpoint with the tunnel server's public IP, or pass `[WAN_ADDR]` as an explicit third argument.

12. **WireGuard handshake = 0 on StartOS peer** — The tunnel shows "latest handshake: X seconds ago" only if the StartOS WireGuard client is running and can reach the tunnel server. Recovery: verify (a) `wg-quick@start-tunnel` is active, (b) Endpoint is the tunnel's public IP, (c) UDP 51820 outbound is open on the StartOS network.

13. **WireGuard key mismatch** — If `wg show` on the tunnel server shows a different public key than expected, StartOS was configured with a different keypair. Recovery: compare public keys on both ends, then either regenerate from Start Tunnel or update the peer key in the tunnel's CBOR config.

14. **AllowedIPs = 0.0.0.0/0 routes ALL StartOS traffic through the tunnel** — This breaks local services and internet access unless the tunnel server has NAT masquerading. Recovery: always use `AllowedIPs = 10.59.139.0/24` (the tunnel subnet only). The tunnel is for forwarding, not for StartOS egress.

15. **StartOS assigns random peer ports** — The P2P/peer port is assigned by startd (e.g., 56508), not the standard 8333. Recovery: find the assigned port in the StartOS WebUI under the service's Interfaces tab before setting up port forwards.

16. **Backups overwrite, no point-in-time history** — Each backup target overwrites the previous backup for that target. Recovery: configure multiple backup targets if you need point-in-time recovery.

## References

- `references/bitcoin-core-credentials.md` — Step-by-step pattern for extracting Bitcoin Core RPC credentials from StartOS and connecting wallets (Sparrow, Specter, etc.). Covers stats.yaml, bitcoin.conf, LAN vs Tor connectivity, and Sparrow-specific wallet configuration.
- `references/start-tunnel-integration.md` — WireGuard client setup on StartOS for Start Tunnel, port forwarding, endpoint IP bug workaround, Azure NSG configuration.
