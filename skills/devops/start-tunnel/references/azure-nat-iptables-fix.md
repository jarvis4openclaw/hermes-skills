# Azure NAT iptables DNAT Fix

## Problem

Start Tunnel creates port forward iptables rules that match on destination IP:

```bash
# What Start Tunnel creates:
iptables -t nat -A PREROUTING -d 20.51.120.252 -p tcp --dport 8333 \
  -j DNAT --to-destination 10.59.139.4:56508
```

Azure's SDN rewrites the destination from the public IP to the VM's private IP before the packet reaches the OS. The VM sees:

```
src=64.25.11.235 dst=10.0.0.5 dport=8333
```

The DNAT rule matches `-d 20.51.120.252` — never fires. Packet counter stays at 0.

## Diagnostic Trace

```bash
# 1. Check if packets are matching the DNAT rule:
sudo iptables -t nat -L PREROUTING -n -v
# Look at the first column (pkts) — 0 means NO matches

# 2. Check conntrack to see actual flow:
sudo conntrack -L -d 10.59.139.4
# If this shows entries, forwarding IS working
# If empty, the packet isn't reaching the right chain

# 3. Also check reply direction:
sudo conntrack -L --reply-src 10.59.139.4
# Successful connection looks like:
#   src=<client_ip> dst=10.0.0.5 dport=8333
#     → DNAT →
#   src=<client_ip> dst=10.59.139.4 dport=56508
```

## Workaround

Add an interface-based DNAT rule BEFORE Start Tunnel's chain:

```bash
sudo iptables -t nat -I PREROUTING 1 -i eth0 -p tcp --dport <PUBLIC_PORT> \
  -j DNAT --to-destination <TARGET_IP>:<TARGET_PORT>
```

Example:

```bash
sudo iptables -t nat -I PREROUTING 1 -i eth0 -p tcp --dport 8333 \
  -j DNAT --to-destination 10.59.139.4:56508
```

This matches on the incoming interface (`eth0`) and port, regardless of destination IP.

## Automation (Recommended)

Rather than manually adding one iptables rule per port forward, use `st-fix-wan-nat.sh` — a script that auto-discovers ALL Start Tunnel port forwards and adds interface-based DNAT rules generically.

### How it works

1. Scans iptables `PREROUTING` chain for Start Tunnel's subchains (named `*_PREROUTING`)
2. Extracts DNAT rules from each subchain to discover source port → target mappings
3. For each port forward, adds `-i eth0` interface-based DNAT rule (idempotent — skips if already present)
4. Runs as a systemd oneshot service triggered after `start-tunneld` starts

### Deploy the script

```bash
cat << 'SCRIPT' | sudo tee /usr/local/bin/st-fix-wan-nat.sh > /dev/null
#!/bin/bash
# Fix ALL Start Tunnel port forwards for Azure NAT
# Azure rewrites dest IP from public to private, so DNAT rules matching
# destination IP never fire. This adds interface-based (-i eth0) rules.

MAX_WAIT=60
ELAPSED=0

echo "[st-fix-wan-nat] Waiting for start-tunneld..."
while ! pgrep -x start-tunneld > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "[st-fix-wan-nat] ERROR: start-tunneld did not start"
        exit 1
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done
sleep 3

# Discover port forwards from iptables subchains
PORT_FORWARDS=$(python3 << 'PYEOF'
import subprocess, re

out = subprocess.run(['iptables', '-t', 'nat', '-L', 'PREROUTING', '-n'],
                     capture_output=True, text=True).stdout
subchains = set()
for line in out.split('\n'):
    m = re.search(r'(\w+_PREROUTING)\b', line)
    if m and m.group(1) != 'PREROUTING':
        subchains.add(m.group(1))

forwards = set()
for chain in sorted(subchains):
    detail = subprocess.run(['iptables', '-t', 'nat', '-L', chain, '-n'],
                           capture_output=True, text=True).stdout
    for line in detail.split('\n'):
        if 'DNAT' in line and 'dpt:' in line and 'to:' in line:
            dpt_m = re.search(r'dpt:(\d+)', line)
            to_m = re.search(r'to:([\d.]+:\d+)', line)
            if dpt_m and to_m:
                src = dpt_m.group(1)
                tgt = to_m.group(1)
                if int(src) != int(tgt.split(':')[-1]):
                    forwards.add(f'{src}|{tgt}')

for fw in sorted(forwards):
    print(fw)
PYEOF
)

echo "$PORT_FORWARDS" | while IFS='|' read -r src target; do
    [ -z "$src" ] && continue
    if iptables -t nat -C PREROUTING -i eth0 -p tcp --dport "$src" -j DNAT --to-destination "$target" 2>/dev/null; then
        echo "[st-fix-wan-nat] OK   eth0:$src -> $target"
    else
        iptables -t nat -I PREROUTING 1 -i eth0 -p tcp --dport "$src" -j DNAT --to-destination "$target"
        echo "[st-fix-wan-nat] ADD  eth0:$src -> $target"
    fi
done
SCRIPT

sudo chmod +x /usr/local/bin/st-fix-wan-nat.sh
```

### Create systemd service

```bash
cat << 'UNIT' | sudo tee /etc/systemd/system/st-fix-wan-nat.service > /dev/null
[Unit]
Description=Fix Start Tunnel port forwards for Azure NAT
After=network.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/st-fix-wan-nat.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now st-fix-wan-nat
```

### Operational notes

- **Idempotent:** Safe to run repeatedly — checks if rule exists before adding
- **Self-discovering:** No hardcoded ports. Add a new port forward in Start Tunnel UI, then `sudo systemctl restart st-fix-wan-nat`
- **Boot-safe:** Waits for `start-tunneld` to start before scanning
- **After daemon restart:** Run `sudo /usr/local/bin/st-fix-wan-nat.sh` to re-apply after `sudo kill $(pgrep start-tunneld) && sudo /usr/bin/start-tunneld &`

## Manual Persistence (Legacy)

Start Tunnel rebuilds iptables on every daemon restart, wiping custom rules. Options:

1. **systemd override:** Create `/etc/systemd/system/start-tunneld.service` with `ExecStartPost` that re-adds the rule.
2. **Cron @reboot:** `@reboot sleep 10 && iptables -t nat -I PREROUTING 1 -i eth0 -p tcp --dport 8333 -j DNAT --to-destination 10.59.139.4:56508`
3. **Script:** `/usr/local/bin/st-nat-fix.sh` triggered by systemd or cron.

## Verification

```bash
# Test from an external host:
nc -zv <public_ip> <port>

# Check packet counters (should show >0):
sudo iptables -t nat -L PREROUTING -n -v | head -5

# Check connection tracking:
sudo conntrack -L --reply-src <target_ip>
```

Note: `nc` to a Bitcoin P2P port will timeout because Bitcoin expects a version handshake, not a raw TCP probe. Use conntrack to verify the connection established instead.

## Why This Happens (All Cloud Providers)

| Provider | Behavior |
|----------|----------|
| Azure | Public IP is SDN-level NAT → VM sees private IP |
| AWS | Elastic IP is 1:1 NAT → VM sees private IP (unless assigned to ENI) |
| GCP | External IP is SDN-level NAT → VM sees private IP |
| Hetzner/DigitalOcean | Public IP IS on the interface → DNAT works without workaround |
