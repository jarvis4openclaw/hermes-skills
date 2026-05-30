# Start Tunnel Integration

How to connect a StartOS host to Start Tunnel via WireGuard and forward ports.

## WireGuard Client Setup on StartOS

StartOS (0.4.0-beta) does not have a built-in WireGuard client UI for external tunnels. Install and configure manually.

### Step 1: Generate Config from Tunnel Server

```bash
# On the Start Tunnel server (20.51.120.252)
start-tunnel device show-config 10.59.139.1/24 10.59.139.4 20.51.120.252
```

**BUG (v0.4.0-beta.9):** Without the explicit WAN_ADDR argument, Endpoint defaults to the web listen IP (0.0.0.0:51820) — broken. Always pass the public IP or manually replace before using.

### Step 2: Apply on StartOS

```bash
ssh start9@<startos-ip>

# Create tunnel config
sudo tee /etc/wireguard/start-tunnel.conf << 'EOF'
[Interface]
Address = 10.59.139.4/24
PrivateKey = <from show-config>

[Peer]
PublicKey = <server pubkey>
PresharedKey = <from show-config>
AllowedIPs = 10.59.139.0/24
Endpoint = 20.51.120.252:51820
PersistentKeepalive = 25
EOF

sudo wg-quick up start-tunnel
sudo systemctl enable wg-quick@start-tunnel
```

### Step 3: Verify

```bash
# On StartOS
wg show
# Should show latest handshake: X seconds ago

# On tunnel server
sudo wg show
# Peer 10.59.139.4 should show endpoint + handshake time
```

## Port Forwarding

### Find StartOS Service Port

StartOS assigns random ports via startd. Find them in WebUI → Service → Interfaces tab. For Bitcoin Core, look for "P2P" or "Peer Port" (e.g., 56508). Not the internal 8333.

### Create Port Forward in Start Tunnel

In Start Tunnel WebUI → Port Forwarding → Add:
- External IP: `20.51.120.252` (the tunnel server's public IP)
- Source Port: e.g., `8333`
- Target: `10.59.139.4:<startos-peer-port>` (WireGuard IP + StartOS port)
- Protocol: TCP (or TCP+UDP for Bitcoin)

### Cloud Firewall

Start Tunnel manages iptables automatically. Only the cloud provider's external firewall needs manual rules:
- **Azure:** Network Security Group → Add inbound rule for the source port
- **Hetzner/DigitalOcean/etc:** Usually no cloud firewall; Start Tunnel iptables handles it

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `wg show` shows handshake: 0 | Endpoint wrong or firewall blocking | Check Endpoint is public IP, verify UDP 51820 outbound |
| Port forward not working | StartOS WireGuard handshake dead | Fix handshake, restart wg-quick on StartOS |
| No external IP in dropdown | Public IP not visible to the VM | Add virtual IP: `ip addr add <pub-ip>/32 dev eth0` |
| Config shows wrong endpoint | Bug in show-config | Pass WAN_ADDR explicitly or manually replace |
