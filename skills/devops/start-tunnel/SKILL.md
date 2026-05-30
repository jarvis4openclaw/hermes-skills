---
name: start-tunnel
version: 1.0.0
description: Manage Start9 StartTunnel VPR — SSH access, web UI, subnets, devices, port forwarding, config editing. Use when asked to inspect, troubleshoot, or configure a StartTunnel VPS.
metadata:
  hermes:
    tags: [start-tunnel, start9, vpn, wireguard, port-forwarding, vpr]
    trigger_conditions:
      - "start tunnel"
      - "start-tunnel"
      - "vpr"
      - "virtual private router"
      - "port forward tunnel"
      - "wireguard vps"
      - "tunnel cb"
      - "tunnel web ui"
      - "azure tunnel"
      - "nat port forward fail"
      - "show-config endpoint bug"
      - "tunnel port forward not working"
      - "st-fix-wan-nat"
---

# StartTunnel Management

StartTunnel is a Virtual Private Router (VPR) from Start9 — a WireGuard-based VPN that runs on a cheap VPS. Lets you expose home services without revealing your home IP. Separate product from StartOS.

## When to Use

- Inspecting or troubleshooting port forwards that aren't working
- Changing the web UI listen address (localhost → 0.0.0.0)
- Adding a virtual IP address on cloud providers for the external IP dropdown
- Diagnosing Azure/AWS/GCP NAT issues that silently break port forwarding
- Editing the CBOR binary config file (`tunnel.db`) for webserver, gateway, or WG peer changes
- Setting up WireGuard clients from the tunnel server to remote hosts
- Managing the daemon lifecycle (kill, restart, no systemd service)
- Debugging WireGuard handshake failures (0 handshake, missing peer, key mismatch)
- Applying the `st-fix-wan-nat.sh` automated NAT fix after port forward changes
- Opening cloud firewall rules (NSG/Security Group) for tunnel ports

## Not For

- Managing StartOS servers (services, credentials, mDNS, Tor) → use `startos` instead
- Generic SSH remote command execution → use `ssh-file-deploy` for file transfers, or direct `terminal` SSH calls
- Proxmox virtualization or VM management → use `proxmox-host-management`
- Windows host management over SSH → use `windows-ssh`
- Managing WireGuard on non-tunnel hosts (e.g., direct peer connections) → this skill covers Start9's StartTunnel product specifically
- Diagnosing WebSocket errors on Mission Control → use `mission-control-openclaw-websocket-401-troubleshooting`

## Boss's Server

| Detail | Value |
|--------|-------|
| Host | `azureuser@20.51.120.252` (Azure VM) |
| OS | Debian 13 (trixie) |
| Version | `start-tunnel 0.4.0-beta.9` |
| Config file | `/var/lib/start-tunnel/tunnel.db` (CBOR binary) |
| Daemon | `/usr/bin/start-tunneld` (no systemd service) |
| RPC | `127.0.59.60:5960/rpc/v0` (JSON-RPC) |
| Docs | https://docs.start9.com/start-tunnel/1.0.x/ |

**Important:** The installed version (0.4.0-beta.9) is older than the docs (1.0.x). CLI flags differ — always check `start-tunnel --help` on the server before assuming docs behavior.

## Web UI

The web UI is bound to localhost by default after `web init`. To access it over WireGuard VPN, it must listen on `0.0.0.0:8080` (or the server's WireGuard IP).

### Changing the listen address

**Preferred method — use Python cbor2 (safe, handles any string length):**

```bash
sudo apt install python3-cbor2

cat > /tmp/fix_listen.py << 'EOF'
import cbor2

with open('/var/lib/start-tunnel/tunnel.db', 'rb') as f:
    raw = f.read()
version = cbor2.loads(raw)
version_bytes = cbor2.dumps(version)
config = cbor2.loads(raw[len(version_bytes):])

config['webserver']['listen'] = '0.0.0.0:8080'

with open('/var/lib/start-tunnel/tunnel.db', 'wb') as f:
    f.write(cbor2.dumps(version))
    f.write(cbor2.dumps(config))
EOF

sudo kill $(pgrep start-tunneld) 2>/dev/null; sleep 1
sudo python3 /tmp/fix_listen.py
sudo /usr/bin/start-tunneld &
```

**Fallback — hex-edit the CBOR config file (only for same-length strings):**

```bash
# 1. Stop the daemon
sudo kill $(pgrep start-tunneld)

# 2. The config is CBOR at /var/lib/start-tunnel/tunnel.db
# Strings have length prefixes: 0x60 + byte_length
# "127.0.0.1:8080" = 14 chars → prefix 0x6E
# "0.0.0.0:8080"    = 12 chars → prefix 0x6C

# 3. Patch the prefix byte after the "listen" field name
# Use Python to find "listen" and fix the adjacent prefix byte:
sudo python3 << 'EOF'
with open("/var/lib/start-tunnel/tunnel.db", "rb") as f:
    data = bytearray(f.read())
idx = data.find(b"listen")
if idx >= 0:
    prefix_pos = idx + 6
    # Change 0x6E (14) to 0x6C (12) for "0.0.0.0:8080"
    data[prefix_pos] = 0x6C
    with open("/var/lib/start-tunnel/tunnel.db", "wb") as f:
        f.write(data)
    print("Patched")
EOF

# 4. Restart the daemon
sudo /usr/bin/start-tunneld &>/dev/null &

# 5. Verify
sudo ss -tlnp | grep start-tunneld
```

### Accessing the web UI

Once bound to `0.0.0.0:8080`:
- **Via WireGuard VPN:** `https://<server-wireguard-ip>:8080`
- **Via SSH tunnel (no config changes needed):** `ssh -L 8080:127.0.0.1:8080 azureuser@20.51.120.252` then `https://localhost:8080`
- **Direct public IP:** requires cloud firewall rule (Azure NSG, etc.) to allow inbound 8080

The web UI redirects HTTP → HTTPS and uses a self-signed cert generated during `web init`.

## Port Forwarding

### Creating a Port Forward

In WebUI → Port Forwarding → Add, or via CLI:

```bash
start-tunnel port-forward add <source_port> <target_ip>:<target_port>
```

**Example — forward Bitcoin P2P to a StartOS host on WireGuard:**

```bash
start-tunnel port-forward add 8333 10.59.139.4:56508
```

Start Tunnel auto-creates iptables DNAT rules. No manual iptables work needed.

### External IP Dropdown Empty?

On cloud providers using NAT (Azure, GCP, AWS), the public IP is NOT bound to the VM — the VM only sees a private IP (e.g., `10.0.0.5`). The UI dropdown reads from interface addresses.

**Fix — add the public IP as a virtual address:**

```bash
# Temporary
sudo ip addr add 20.51.120.252/32 dev eth0

# Restart daemon to pick it up
sudo kill $(pgrep start-tunneld)
sudo /usr/bin/start-tunneld &

# Verify detection
sudo python3 -c "
import cbor2
with open('/var/lib/start-tunnel/tunnel.db','rb') as f:
    raw = f.read()
cfg = cbor2.loads(raw[len(cbor2.dumps(cbor2.loads(raw))):])
print(cfg['gateways']['eth0']['ipInfo']['subnets'])
"
```

**Make permanent (Debian):**
```bash
sudo tee -a /etc/network/interfaces << 'EOF'

auto eth0:0
iface eth0:0 inet static
    address 20.51.120.252
    netmask 255.255.255.255
EOF
```

The daemon auto-detects interface IPs on startup and adds them to `subnets`.

### Azure NAT Caveat (Cloud Providers)

On Azure, AWS, and GCP, the cloud fabric rewrites the public IP to the VM's private IP before the packet hits the OS. Start Tunnel's iptables DNAT rules match on `-d <public_ip>` — these never see the public IP, so port forwards silently fail. Verify with `conntrack -L` or `iptables -t nat -L PREROUTING -v` (check packet counts).

**Workaround:** Add an interface-based DNAT rule. See `references/azure-nat-iptables-fix.md`.

**To test a port forward is working end-to-end:** check `sudo conntrack -L -d <target_ip>`. If you see entries with the original client IP, the forward is live.

### Cloud Firewall

Start Tunnel manages iptables. You still need to open ports in the cloud provider's external firewall:

| Provider | How |
|----------|-----|
| Azure | Network Security Group → Add inbound rule |
| AWS | Security Group → Add inbound rule |
| GCP | VPC Firewall Rules → Add |
| Hetzner/DO/Linode | Usually no cloud firewall needed |
| Oracle | Security List + OS firewall (both required) |

## Subnets & Devices

The config at `/var/lib/start-tunnel/tunnel.db` is CBOR (Concise Binary Object Representation), NOT SQLite despite the `.db` extension.

Structure (human-readable fields embedded in binary):
```
migrations
PortForwardEntry
webserver
  enabled: true
  listen: <ip:port>
  certificate
  key: <PEM>
  cert: <PEM chain>
sessions
authPubkeys
gateways
  eth0: {name, secure, ipInfo, subnets, lanIp, wanIp, ...}
  lo:   {name, secure, ipInfo, subnets, lanIp, wanIp, ...}
  wg:   {port, key, subnets, ...}
subnets
  <cidr>:
    name
    clients
      <ip>: {name, key, psk, ...}
portForwards
```

**CBOR string encoding:** text strings are `0x60 + length`. Binary-safe edits must preserve the prefix byte.

**File-level structure:** The file contains TWO CBOR items in sequence: a version integer (27) followed by the config dictionary. To decode: `cbor2.loads(raw)` → gets version, then `cbor2.loads(raw[len(cbor2.dumps(version)):])` → gets config. To encode back: write both items in order. Single-shot `cbor2.loads()` only sees the version integer.

## Common Commands

| Task | Command |
|------|---------|
| Version | `start-tunnel --version` |
| Web UI listen address | `start-tunnel web get-listen` |
| Set web listen | `start-tunnel web set-listen <ip:port>` (see pitfall below) |
| List subnets | `start-tunnel subnet` ... (check `--help`) |
| Add device | `start-tunnel device add <SUBNET> <NAME> [IP]` |
| Show WireGuard config | `start-tunnel device show-config <SUBNET_CIDR> <DEVICE_IP> [WAN_ADDR]` — always pass WAN_ADDR to avoid bug |
| Port forward | `start-tunnel port-forward add <SOURCE> <TARGET>` |
| Auth / password | `start-tunnel auth set-password` / `reset-password` |
| Update check | `start-tunnel update check` |

## Pitfalls

1. **`web set-listen` fails in both daemon states** — When the daemon is running: "Address in use." When stopped: "error sending request." This command is broken in v0.4.0-beta.9. Recovery: stop the daemon, edit the CBOR config directly with `cbor2` Python library, then restart.

2. **Version mismatch between docs and installed version** — Boss's server runs 0.4.0-beta.9. The docs at docs.start9.com are for 1.0.x. CLI flags differ between versions. Always run `start-tunnel --help` on the actual server before using CLI commands from the docs. Recovery: if a command from docs fails, run `--help` and adapt.

3. **No systemd service means no auto-start on reboot** — The daemon runs as a raw process (`/usr/bin/start-tunneld`). After a reboot it won't auto-start, and all port forwards and WireGuard peers go down. Recovery: create a systemd service unit or use `@reboot` crontab entry. In the interim, SSH in and restart manually after any reboot.

4. **CBOR binary config is not SQLite and `sed` will corrupt it** — The `.db` extension is misleading. This is CBOR binary format. String edits with `sed` that change the byte length corrupt the CBOR structure. Always use Python `cbor2` library for any edit. Recovery: if you corrupted the config with `sed`, restore from backup or recreate the config manually.

5. **`show-config` endpoint bug in v0.4.0-beta.9** — Endpoint IP defaults to the web listen address, not the public IP. If listen is `0.0.0.0`, Endpoint becomes `0.0.0.0:51820` — completely broken. Setting `wanIp` in the CBOR config does NOT fix it. Recovery: pass `[WAN_ADDR]` as an explicit third argument, or manually replace the Endpoint address in the generated config.

6. **External IP dropdown is empty on cloud NAT providers** — Azure, AWS, and GCP assign a private IP to the VM; the public IP is translated at the cloud edge and never appears on any interface. The UI dropdown reads interface addresses only. Recovery: add the public IP as a virtual address (`ip addr add <ip>/32 dev eth0`), restart the daemon. Make permanent via `/etc/network/interfaces`.

7. **Azure/AWS/GCP NAT silently rewrites destination IP** — Inbound packets to the public IP arrive at the VM with the PRIVATE IP as the destination (e.g., `10.0.0.5`, not `20.51.120.252`). Start Tunnel's DNAT rules match on destination IP — since they never see the public IP, port forwards silently drop packets with zero packet counts. Recovery: add an interface-based DNAT rule that catches the NAT'd packets: `sudo iptables -t nat -I PREROUTING 1 -i eth0 -p tcp --dport <PUBLIC_PORT> -j DNAT --to-destination <TARGET_IP>:<TARGET_PORT>`. See `references/azure-nat-iptables-fix.md` for automated `st-fix-wan-nat.sh` script.

8. **Custom iptables rules are wiped on daemon restart** — Start Tunnel rebuilds all iptables rules from scratch when the daemon starts. Any custom DNAT rules you add (e.g., the Azure NAT workaround) are removed. Recovery: re-apply custom rules after every daemon restart, or use the `st-fix-wan-nat.sh` script with a systemd service that auto-runs on daemon restart.

9. **After adding new port forwards, `st-fix-wan-nat` must be restarted** — The automated NAT fix script auto-discovers port forwards at startup and never re-scans. New port forwards added via WebUI won't be picked up until the service restarts. Recovery: `sudo systemctl restart st-fix-wan-nat`.

10. **Subnet parameter is CIDR, not the human-readable name** — CLI commands expect the subnet CIDR (e.g., `10.59.139.1/24`), not the friendly name. Passing the name fails with "invalid IP address syntax." Recovery: find the CIDR in the WebUI or by inspecting `tunnel.db` with `cbor2`.

11. **`wg show` handshake = 0 means WireGuard tunnel never established** — If the peer shows no handshake, check: (a) Endpoint address is the tunnel server's public IP (not 127.0.0.1 or 0.0.0.0), (b) UDP 51820 outbound is open on the client firewall, (c) the WireGuard client service is running on the peer. Recovery: test connectivity with `nc -u <tunnel-ip> 51820` from the client first.

12. **CBOR `key` field stores the WireGuard PRIVATE key, not the public key** — In `wg.subnets.<cidr>.clients.<ip>.key`, the value is the client's WireGuard private key. The daemon derives the public key at runtime. If you overwrite this with a public key, the derivation produces a completely different (wrong) public key and handshakes fail. Recovery: use `start-tunnel device add` with a fresh keypair, or manually replace with a valid private key.

13. **Must kill the daemon before editing the CBOR config** — The daemon caches the config in memory and may overwrite your changes on shutdown if it's still running. Always `sudo kill $(pgrep start-tunneld)`, edit the file, then restart. Recovery: if your changes disappeared after a restart, you edited while the daemon was running. Kill, re-edit, restart.

14. **SSH user is `azureuser`, not `root`** — The Azure VM uses the default Azure user. All privileged commands require `sudo`. Recovery: if "Permission denied" for a file operation, prefix with `sudo`.

## References

- `references/show-config-endpoint-bug.md` — Full diagnostic trace of the endpoint generation bug in v0.4.0-beta.9.
- `references/azure-nat-iptables-fix.md` — Why port forwards fail on Azure/AWS/GCP (SDN rewrites destination IP), diagnostic trace, automated `st-fix-wan-nat.sh` script with systemd persistence, and legacy manual workaround.
