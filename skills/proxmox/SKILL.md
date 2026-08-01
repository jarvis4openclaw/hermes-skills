---
name: proxmox
description: Manage Proxmox VE clusters via REST API. Use when user asks to list, start, stop, restart VMs or LXC containers, check node status, create snapshots, view tasks, or manage Proxmox infrastructure. Requires API token or credentials configured.
version: 1.1.0
metadata:
  hermes:
    tags: [proxmox, pve, virtualization, lxc, qemu, homelab]
    trigger_conditions:
      - "list VMs or containers on Proxmox"
      - "start/stop/restart a VM or LXC"
      - "check node status"
      - "create a Proxmox snapshot"
      - "manage Proxmox infrastructure"
      - "Proxmox cluster status"
      - "list storage on PVE"
      - "create an LXC container"
      - "run a command inside a CT"
      - "pve cluster resources"
      - "proxmox backups"
      - "view Proxmox tasks"
---

# Proxmox VE Management

## When to Use

- User asks to list, start, stop, restart, or reboot VMs or LXC containers on any PVE node.
- Checking node/cluster health, storage usage, or recent task history.
- Creating snapshots before an update, or rolling back after a bad change.
- Creating or cloning LXC containers, or running commands inside a CT via `pct exec`.
- Listing or starting backups on PVE storage.

## Not For

- **Deep-dive on the PVE host itself (cron jobs, systemd services, host-level fixes)** → use `proxmox-host-management` instead
- **Migrating a physical Windows machine to a VM (P2V)** → use `proxmox-p2v-migration` instead
- **Generating detailed resource/capacity reports from the cluster** → use `proxmox-resource-reporting` instead
- **SSH-key and lifecycle management of CTs/VMs** → use `proxmox-ssh-lifecycle` instead
- **Querying the Pulse monitoring dashboard for Proxmox** → use `pulse-proxmox-monitor` instead
- **Managing the Proxmox host when you only have SSH root access (no API token)** → prefer the `proxmox-host-management` skill's SSH-first patterns

## Configuration

Set environment variables or store in `~/.proxmox-credentials`:

```bash
# Option 1: API Token (recommended)
export PROXMOX_HOST="https://192.168.1.100:8006"
export PROXMOX_TOKEN_ID="user@pam!tokenname"
export PROXMOX_TOKEN_SECRET="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Option 2: Credentials file
cat > ~/.proxmox-credentials << 'EOF'
PROXMOX_HOST=https://192.168.1.100:8006
PROXMOX_TOKEN_ID=user@pam!monitoring
PROXMOX_TOKEN_SECRET=your-token-secret
EOF
chmod 600 ~/.proxmox-credentials
```

Create API token in Proxmox: Datacenter → Permissions → API Tokens → Add

## CLI Usage

```bash
# Load credentials
source ~/.proxmox-credentials 2>/dev/null

# Auth header for API token
AUTH="Authorization: PVEAPIToken=$PROXMOX_TOKEN_ID=$PROXMOX_TOKEN_SECRET"
```

## Common Operations

### Cluster & Nodes

```bash
# Cluster status
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/cluster/status" | jq

# List nodes
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes" | jq '.data[] | {node, status, cpu, mem: (.mem/.maxmem*100|round)}'

# Node status
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/status" | jq
```

### List VMs & Containers

```bash
# All VMs on a node
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu" | jq '.data[] | {vmid, name, status, mem: .mem, cpu: (.cpu*100|round)}'

# All LXC containers on a node
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/lxc" | jq '.data[] | {vmid, name, status}'

# Cluster-wide resources
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/cluster/resources?type=vm" | jq '.data[] | {node, vmid, name, type, status}'
```

### VM/Container Control

```bash
# Start VM
curl -ks -X POST -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/status/start"

# Stop VM
curl -ks -X POST -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/status/stop"

# Shutdown VM (graceful)
curl -ks -X POST -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/status/shutdown"

# Reboot VM
curl -ks -X POST -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/status/reboot"

# Same for LXC: replace /qemu/ with /lxc/
```

### Snapshots

```bash
# List snapshots
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/snapshot" | jq

# Create snapshot
curl -ks -X POST -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/snapshot" \
  -d "snapname=snap1" -d "description=Before update"

# Rollback
curl -ks -X POST -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/snapshot/{snapname}/rollback"

# Delete snapshot
curl -ks -X DELETE -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/qemu/{vmid}/snapshot/{snapname}"
```

### Tasks & Logs

```bash
# Recent tasks
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/tasks" | jq '.data[:10] | .[] | {upid, type, status, user}'

# Task log
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/tasks/{upid}/log" | jq -r '.data[].t'
```

### Storage

```bash
# List storage
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/storage" | jq '.data[] | {storage, type, active, used_fraction: (.used/.total*100|round|tostring + "%")}'

# Storage content
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/storage/{storage}/content" | jq
```

### Backups

```bash
# List backups
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/storage/{storage}/content?content=backup" | jq

# Start backup
curl -ks -X POST -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/vzdump" \
  -d "vmid={vmid}" -d "storage={storage}" -d "mode=snapshot"
```

## Helper Script

Use `scripts/pve.sh` for common operations:

```bash
./scripts/pve.sh status          # Cluster overview
./scripts/pve.sh vms             # List all VMs
./scripts/pve.sh start {vmid}    # Start VM
./scripts/pve.sh stop {vmid}     # Stop VM
```

### Create LXC Container

```bash
# Find next available VMID
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/cluster/resources?type=vm" \
  | jq '[.data[] | .vmid] | max + 1'

# List available CT templates on storage
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/storage/local/content" \
  | jq '.data[] | select(.volid | test("vztmpl")) | .volid'

# Create unprivileged CT (adjust params as needed)
curl -ks -X POST -H "$AUTH" \
  "$PROXMOX_HOST/api2/json/nodes/{node}/lxc" \
  -d "vmid={vmid}" \
  -d "hostname=kitten-tts" \
  -d "ostemplate=local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst" \
  -d "storage=zfspool" \
  -d "cores=2" \
  -d "memory=2048" \
  -d "rootfs=zfspool:8" \
  -d "net0=name=eth0,bridge=vmbr0,ip=dhcp,firewall=1" \
  -d "unprivileged=1" \
  -d "features=nesting=1" \
  -d "start=1"

# Check creation task status (returns UPID)
curl -ks -H "$AUTH" "$PROXMOX_HOST/api2/json/nodes/{node}/tasks/{upid}/status" | jq
```

### Execute Commands Inside LXC

```bash
# Run a command inside a running CT (use pct exec via SSH to Proxmox host)
ssh root@{proxmox-ip} "pct exec {vmid} -- apt-get update"
ssh root@{proxmox-ip} "pct exec {vmid} -- bash -c 'curl -fsSL https://example.com/install.sh | bash'"
```

## Pitfalls

1. **Using `$PROXMOX_HOST` with a stale example IP** — The skill's default host is `https://192.168.1.100:8006` (an example). Wahid's real PVE host is `192.168.100.23` (SSH root via id_ed25519). Recovery: set `PROXMOX_HOST=https://192.168.100.23:8006` in `~/.proxmox-credentials` before any API call, or use SSH-based tooling.
2. **Forgetting `-k` on self-signed certs** — PVE uses a self-signed cert by default; `curl` fails with TLS verification errors. Recovery: always pass `-k` (or `-k` in the `AUTH` curl pattern shown above).
3. **Hardcoding node names and VMIDs** — The examples use `{node}` / `{vmid}` placeholders; substituting a VMID that doesn't exist on the target node returns a 404. Recovery: resolve real IDs from `/cluster/resources?type=vm` first.
4. **Creating an LXC container with the wrong template path** — The example hardcodes `debian-13-standard_13.1-2_amd64.tar.zst` on `local`. That template may not exist on the target host. Recovery: list `local/content` vztmpl entries first, then create.
5. **Assuming API tokens are available** — API token auth requires an explicit token created in the Datacenter UI; if only SSH root access exists, `curl` calls fail with 401. Recovery: use `ssh root@192.168.100.23 pct ...` / `qm ...` for direct control.
6. **Missing `start=1` when creating a CT** — Without it the container is created stopped and the user thinks creation failed. Recovery: pass `start=1` or `pct start <vmid>` explicitly.
7. **Forgetting CSRF only applies to non-token auth** — API tokens skip CSRF, but cookie/session auth requires `CSRFPreventionToken`. Recovery: stick to token auth for scripted curl, or fetch the CSRF token from `/access/ticket`.
8. **Rolling back without a prior snapshot** — `/snapshot/{snapname}/rollback` fails if the snapshot doesn't exist. Recovery: list snapshots first (`/snapshot`) and confirm the name before rolling back.

## Notes

- Replace `{node}`, `{vmid}`, `{storage}`, `{snapname}` with actual values
- API tokens don't need CSRF tokens for POST/PUT/DELETE
- Use `-k` to skip SSL verification for self-signed certs
- Task operations return UPID for tracking async jobs
- For CT creation, `unprivileged=1` is the default safe choice; `features=nesting=1` needed if running containers inside
- Use `start=1` to auto-start the CT after creation
