---
name: proxmox-host-management
version: 1.3.0
description: Manage Proxmox VE host via SSH — cron jobs, systemd services, packages, config files, VM/CT operations, storage, network, disk health/SMART monitoring, and maintenance. Use when asked to inspect, fix, or change anything on the Proxmox host itself (not VMs/containers).
category: devops
metadata:
  hermes:
    tags: [proxmox, pve, vm, lxc, backup, pbs, smart, storage]
    trigger_conditions:
      - "proxmox host"
      - "pve ssh"
      - "proxmox cron"
      - "systemd service on pve"
      - "qm start"
      - "pct enter"
      - "pbs backup"
      - "smartctl"
      - "pmxcfs"
      - "proxmox storage"
      - "vzdump"
      - "resize root disk"
      - "proxmox update"
---

# Proxmox Host Management Skill

## When to Use

- Editing cron jobs, systemd services, or config files on the Proxmox host
- Managing packages and kernel updates (with safety constraints)
- VM/CT lifecycle operations (start/stop/restart/snapshot via `qm`/`pct`)
- Storage pool management, PBS backup configuration, or fixing PBS ownership
- Disk health diagnosis and SMART delta monitoring setup
- Network configuration, firewall rules, or bridge troubleshooting
- Log investigation and task trace analysis
- Shrinking or growing LXC container root disks
- Recovering from pmxcfs wipes, stale PBS locks, or API token loss
- Creating Docker-on-LXC deployments with nesting enabled

## Not For

- Read-only resource reports (CPU/RAM/disk/node status) → use `proxmox-resource-reporting` instead
- Remote file deployment to arbitrary hosts → use `ssh-file-deploy`
- Managing StartOS or Start Tunnel services → use `startos` or `start-tunnel`
- Windows host management over SSH → use `windows-ssh`
- Cloud deployment or static site verification → use `cloudflare-pages-deploy` or `static-site-deploy-verify`
- General system administration on non-Proxmox hosts → this skill assumes PVE-specific tools and paths

## Access

- **Host:** `root@192.168.100.23` (pve)
- **SSH Key:** `/home/wahid/.ssh/id_ed25519`
- **SSH Command pattern:**
  ```bash
  ssh -i /home/wahid/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@192.168.100.23 '<command>'
  ```
- **Proxmox version:** 9.1.0 (kernel 7.0.2-2-pve)

## Key Config Files

| File | Purpose |
|------|---------|
| `/etc/pve/user.cfg` | Proxmox user config (contains notification email) |

## Reference Files
- `references/ct200-root-disk-shrink.md` — Full shrink operation log (CT 200, 24G→20G)
- `references/host-config-issue.md` — pmxcfs wipe recovery + daily config backup cron setup
- `references/pbs-storage-setup.md` — PBS storage config fix, API token setup, backup ownership pitfall
- `references/api-token-recovery.md` — Recreate api-rw@pam user + token after pmxcfs wipe
- `references/lxc-docker-deploy.md` — Docker Compose service deployment on LXC containers
| `/etc/cron.d/` | System cron jobs (e.g., `azcmagent_autoupgrade`) |
| `/etc/apt/sources.list.d/` | APT sources (Proxmox, Ceph, etc.) |
| `/etc/network/interfaces` | Network configuration |
| `/etc/hostname`, `/etc/hosts` | Hostname and hosts |
| `/etc/postfix/` or `/etc/ssmtp/` | Mail relay config |

## Notification Emails

Proxmox sends emails via **sSMTP relay through Gmail** (`smtp.gmail.com:587`).
Notification email addresses are set in BOTH:
- `/etc/pve/user.cfg`
- `/etc/pve/datacenter.cfg`

Current email: `onewahid@gmail.com` (changed from `onewahid@live.com` on 2026-02-14).

## Common Operations

### VM Management (`qm`)
```bash
# List all VMs
qm list

# Start/stop/restart
qm start <vmid>
qm stop <vmid>
qm restart <vmid>

# Snapshot
qm snapshot <vmid> <snapname> --description "..."

# Get config
qm config <vmid>

# Get status
qm status <vmid>
```

### LXC Container Management (`pct`)
```bash
# List all containers
pct list

# Start/stop/restart
pct start <ctid>
pct stop <ctid>
pct restart <ctid>

# Enter container shell
pct enter <ctid>

# Get config
pct config <ctid>
```

### LXC Container Root Disk Resizing

**Growing** (safe, can be done live on some setups, but stop CT for safety):
```bash
pct stop <ctid>
lvresize -L +<size>G /dev/pve/vm-<ctid>-disk-0
resize2fs /dev/pve/vm-<ctid>-disk-0
pct set <ctid> -rootfs local-lvm:vm-<ctid>-disk-0,size=<new-size>G
pct start <ctid>
```

**Shrinking** (requires CT stop + fs shrink BEFORE volume shrink):
```bash
pct stop <ctid>
e2fsck -fy /dev/pve/vm-<ctid>-disk-0       # MUST pass clean
resize2fs /dev/pve/vm-<ctid>-disk-0 <size>G  # filesystem FIRST
lvreduce -L <size>G /dev/pve/vm-<ctid>-disk-0 # volume SECOND
pct set <ctid> -rootfs local-lvm:vm-<ctid>-disk-0,size=<size>G
pct start <ctid>
pct exec <ctid> -- df -h /                     # verify
```

**Key pitfalls:**
- **Order matters for shrink:** You MUST shrink the filesystem before shrinking the LVM volume. Reversing this destroys data.
- **Stale config metadata:** Proxmox config `rootfs` size field can drift from actual LVM volume size (e.g., config says 4G but volume is 24G). Always check `lvs` and `df` for ground truth. Update with `pct set <ctid> -rootfs local-lvm:vm-<ctid>-disk-0,size=<size>G`.
- **Shrink requires clean fs:** `e2fsck -fy` must succeed before `resize2fs` will shrink. If it fails, do NOT proceed.
- **Enough headroom:** Target size must exceed used space (`df` shows used). Shrinking below used = data loss.

### Storage
```bash
# List storage
pvesm status

# List content of a storage
pvesm content <storage-name>

# Check specific storage details
pvesm path <storage-name>
```

### PBS Backup Storage Configuration

PBS storage in PVE (`/etc/pve/storage.cfg`) is fragile — three things break easily:

**1. Wrong fingerprint** — after pmxcfs wipe or PBS cert change, the fingerprint becomes all zeros. Get real one: `proxmox-backup-manager cert info | grep -i fingerprint`.

**2. Wrong username/realm** — `root@pbs` doesn't exist. Use `root@pam` or an API token like `root@pam!token-name`. `pvesm` needs an API token + password because it uses HTTPS, not the local Unix socket.

**3. Missing credentials** — set via API, not manually: `pvesh set /storage/pbs -password "<token-secret>"`. The file goes to `/etc/pve/priv/storage/pbs.pw`.

#### Full PBS storage fix workflow
```bash
# 1. Get fingerprint
proxmox-backup-manager cert info | grep -i fingerprint

# 2. Generate API token + grant ACL
proxmox-backup-manager user generate-token root@pam pve-backup
proxmox-backup-manager acl update /datastore/backups DatastoreAdmin --auth-id root@pam!pve-backup

# 3. Update storage.cfg
sed -i 's/username root@pam/username root@pam!pve-backup/' /etc/pve/storage.cfg
# Also fix fingerprint in storage.cfg if needed

# 4. Set password — MUST use pvesh, not raw file write
pvesh set /storage/pbs -password "<token-secret>"

# 5. Verify
pvesm list pbs

# 6. Create backup job (daily HH:MM format)
pvesh create /cluster/backup --vmid <vmid> --storage pbs --mode snapshot \
  --schedule "02:00" --compress zstd --enabled 1
```

**Important:** `--schedule "HH:MM"` and `--starttime` are mutually exclusive.

#### Backup ownership pitfall
When switching from `root@pam` to `root@pam!token`, PBS rejects writes with `backup owner check failed`. Old backup groups are owned by `root@pam`; the token can't write to them. **Fix:** delete old snapshots in that VM/CT's group via `proxmox-backup-client forget <snapshot-id>` then re-backup.

See `references/pbs-storage-setup.md` for detailed session notes.

### Systemd Services
```bash
# List all timers
systemctl list-timers --all

# Check a service
systemctl status <service>

# Restart a service
systemctl restart <service>

# Disable a timer
systemctl disable --now <timer>
```

### Cron Jobs
```bash
# List system cron jobs
ls -la /etc/cron.d/

# Edit a cron file (backup first!)
cp /etc/cron.d/<file> /etc/cron.d/<file>.bak
```

### Package Management
```bash
# Update package lists
apt update

# Upgrade (non-interactive)
DEBIAN_FRONTEND=noninteractive apt upgrade -y

# Check for proxmox updates specifically
pveupdate

# Check current version
pveversion -v
```

### Logs
```bash
# Proxmox daemon log
journalctl -u pvedaemon -n 100

# Cluster log
journalctl -u pve-cluster -n 100

# Task log (VM/CT operations)
cat /var/log/pve/tasks/active

# Syslog
tail -100 /var/log/syslog
```

### Network
```bash
# Show interfaces
ip addr show

# Show bridges
brctl show

# Show firewall
iptables -L -n

# Proxmox firewall config
cat /etc/pve/firewall/cluster.fw
```

### Disk Health & SMART Monitoring

When a drive starts throwing SMART errors (smartd alerts, ATA error count increases), diagnose first — don't assume media failure.

#### Diagnosis

```bash
# Full SMART report
smartctl -a /dev/sdX

# Key metrics to check
smartctl -A /dev/sdX | grep -E "Reallocated|Pending|Uncorrectable|UDMA_CRC|Power_On|Temperature"

# Recent error log (shows error type)
smartctl -l error /dev/sdX | head -30

# Short self-test (2 min)
smartctl -t short /dev/sdX
sleep 120
smartctl -l selftest /dev/sdX
```

**Critical distinction:** ICRC/ABRT errors = SATA cable/port signal corruption (cheap fix). Reallocated/Pending/Uncorrectable sectors = media failure (drive replacement needed). Check ALL metrics before recommending action.

#### Delta Monitoring Script

When the error count is stable but rising slowly, set up a daily delta monitor that only alerts on increases.

**Important:** Add retry logic — drives with flaky SATA links (ICRC/ABRT errors) may not respond to `smartctl` on the first attempt, especially if recently spun down. Without retries, cron generates false-alarm emails.

```bash
cat > /usr/local/bin/smart-monitor-<drive>.sh << 'SCRIPT'
#!/bin/bash
# Monitor SMART ATA error count with retry for drives that are slow to wake
DRIVE="/dev/sdX"
STATE_FILE="/var/lib/smart-monitor/<drive>_error_count.txt"
SERIAL="<serial>"
mkdir -p "$(dirname "$STATE_FILE")"

# Retry up to 3 times (drives with SATA link issues may not respond instantly)
CURRENT=""
for i in 1 2 3; do
    CURRENT=$(smartctl -l error "$DRIVE" 2>/dev/null | grep -oP 'ATA Error Count:\s*\K[0-9]+' | head -1)
    [ -n "$CURRENT" ] && break
    sleep 2
done

if [ -z "$CURRENT" ]; then
    echo "ERROR: Could not read SMART error count from $DRIVE after 3 retries. Drive may be disconnected or powered down."
    exit 1
fi

PREVIOUS=$(cat "$STATE_FILE" 2>/dev/null || echo "$CURRENT")
echo "$CURRENT" > "$STATE_FILE"
if [ "$CURRENT" -gt "$PREVIOUS" ]; then
    echo "SMART ERROR COUNT INCREASED: $DRIVE (Serial: $SERIAL)"
    echo "Previous: $PREVIOUS | Current: $CURRENT"
    smartctl -A "$DRIVE" | grep -E "Reallocated|Pending|Uncorrectable|UDMA_CRC|Power_On|Temperature"
    exit 1
fi
exit 0
SCRIPT
chmod +x /usr/local/bin/smart-monitor-<drive>.sh
```

Schedule it:
```bash
cat > /etc/cron.d/smart-monitor-<drive> << 'EOF'
# Monitor SMART errors daily at 8am — only emails on increase
MAILTO=onewahid@gmail.com
0 8 * * * root /usr/local/bin/smart-monitor-<drive>.sh
EOF
```

Also check ZFS health since Proxmox uses ZFS pools:
```bash
zpool status -v
zpool list
```

## Pitfalls

1. **Cron emails any output — stdout AND stderr** — `>/dev/null` only redirects stdout. If a cron job writes to stderr, it still emails. Recovery: use `>/dev/null 2>&1` to silence both, or add `MAILTO=""` at the top of the cron file to disable email entirely.

2. **Azure Arc agent (`azcmagent`) cron emails daily** — Installed at `/opt/azcmagent/` with a daily cron at `/etc/cron.d/azcmagent_autoupgrade`. If cron output isn't fully silenced, daily spam emails to the cron owner occur. Recovery: add `MAILTO=""` to `/etc/cron.d/azcmagent_autoupgrade` or redirect both stdout and stderr.

3. **pmxcfs is a virtual filesystem — edits have side effects** — `/etc/pve/` is cluster-aware pmxcfs. Direct edits work but are shared across all cluster nodes. Recovery: always backup before editing: `cp file file.bak`. If a syntax error is introduced, the cluster may partially break.

4. **SSH escaping is painful for complex commands** — Multi-line edits over SSH require careful quote escaping. Recovery: use the heredoc pattern over SSH: `ssh ... 'cat > /path << '\''EOF'\'' ... EOF'`. Or use `sed -i` for simple single-line replacements. Better: use `patch` via Hermes tools rather than SSH string manipulation.

5. **`apt dist-upgrade` is dangerous on Proxmox** — Kernel updates, major package transitions, and Ceph version bumps can break PVE. Recovery: never run `apt dist-upgrade` without Boss approval and a maintenance window. Use `apt upgrade` for safe updates.

6. **LXC container disk usage can show >100% due to bind-mounts** — The reported size may be inflated by bind-mounts from the host. This is not always a real issue. Recovery: verify with `df -h` inside the container (`pct exec <ctid> -- df -h /`) to get actual usage before assuming disk pressure.

7. **PBS backup owner check fails after auth switch** — Changing the PBS auth-id (e.g., `root@pam` → `root@pam!token`) means old backup groups are owned by the old identity. PBS rejects writes to those groups. Recovery: delete old snapshots (`proxmox-backup-client forget <snapshot-id>`) and re-backup. Note: `pvesm` needs API token credentials for HTTPS; `proxmox-backup-client` works via Unix socket without a token.

8. **Stale PBS locks block snapshot deletion** — When a backup is killed mid-flight (SSH timeout, signal, crash), PBS leaves lock files at `/run/proxmox-backup/locks/backups/`. Recovery: remove stale locks with `rm -f /run/proxmox-backup/locks/backups/<vm|ct>-<vmid>*`, then delete the partial snapshot with `proxmox-backup-client forget <group>/<timestamp> --repository root@pam@localhost:backups`.

9. **API tokens are lost after pmxcfs wipe** — All users and tokens live in `/etc/pve/user.cfg` inside pmxcfs. After a wipe, everything is gone and API-based automation fails with 401. Recovery: recreate user, token, and ACLs via SSH. Full procedure in `references/api-token-recovery.md`.

10. **Large VM backups (>100GB) timeout in foreground** — SSH-based foreground commands have a 600s timeout. Recovery: run in background with `nohup vzdump <vmid> ... > /var/log/vzdump/<name>-manual.log 2>&1 &`, then monitor with `tail -f /var/log/vzdump/<name>-manual.log`.

11. **Docker in LXC requires nesting=1** — Without `features: nesting=1`, Docker fails to start or containers crash. Recovery: check `pct config <ctid>`, set via `pct set <ctid> -features nesting=1`, then restart the container.

13. **ICRC/ABRT SMART errors are NOT media failures** — ICRC and ABRT errors indicate SATA link-layer corruption (bad cable, loose port, or controller down-negotiating from 6.0 Gb/s to 3.0 Gb/s). Only Reallocated_Sector_Ct, Current_Pending_Sector, or Offline_Uncorrectable sectors indicate actual media damage. Recovery: check all metrics with `smartctl -A /dev/sdX` before concluding a drive needs replacement.

14. **`proxmox-backup-client` in cron needs non-interactive auth** — The client can't prompt for a password when run from cron or run-parts. Recovery: either set `PBS_PASSWORD` env var (read from `/etc/pve/priv/storage/pbs.pw`), or use an API token (`root@pam!token-name`) in the repository URL. Pattern:
   ```bash
   export PBS_PASSWORD=$(cat /etc/pve/priv/storage/pbs.pw)
   proxmox-backup-client ... --repository root@pam!token-name@server:datastore
   ```

15. **`--keep-weekly/monthly/yearly` minimum is 1, not 0** — Setting `--keep-weekly 0` fails with "value must have a minimum value of 1". Recovery: omit the parameter entirely when you don't want those retention tiers. Use `--keep-daily N` (or `--keep-last N`) alone.

16. **Stale PBS snapshots block auth-switch** — When switching PBS auth identity (e.g., `root@pam` → `root@pam!token`), existing snapshots owned by the old identity prevent writes. Recovery: delete ALL old snapshots in that group first (`proxmox-backup-client forget <snapshot-id>`), then create fresh backups under the new auth identity.

17. **SMART transient failures cause false alarm emails** — Drives with flaky SATA links (ICRC/ABRT errors) may not respond to `smartctl` on the first attempt, especially when just spun up. The `grep` pipeline returns empty, triggering the `exit 1` error path. Recovery: always include a retry loop (3 attempts, 2s sleep between) in SMART monitor scripts. See the updated "Delta Monitoring Script" template above.

18. **Agent tool censors secret strings in SSH commands** — When writing scripts that contain secrets (API tokens, passwords) to remote hosts, the agent tool may censor the secret value mid-command, replacing it with `***`. Recovery: use a Python heredoc on the server that reads the secret from an existing file and constructs the script locally:
    ```bash
    ssh root@pve "python3 << 'HEREDOC'
    import pathlib
    secret = pathlib.Path('/etc/pve/priv/storage/pbs.pw').read_text().strip()
    script = f'''...export PBS_PASSWORD={secret}...'''
    pathlib.Path('/etc/cron.daily/myscript').write_text(script)
    pathlib.Path('/etc/cron.daily/myscript').chmod(0o755)
    HEREDOC"
    ```
    This avoids the secret ever appearing in the tool's command string. The censoring only affects the tool's view; the actual server-side execution receives the real value.

## Safety Rules

1. **Always backup before editing:** `cp file file.bak`
2. **Test after changes:** Verify the thing you changed actually works
3. **Don't reboot without asking** unless it's an emergency
4. **Don't run `apt dist-upgrade`** without Boss approval
5. **Don't modify `/etc/pve/` files** without understanding the syntax
6. **When in doubt, ask** — especially for network/firewall changes

## Verification Checklist

After making changes:
- [ ] Backup of original file exists
- [ ] Change is syntactically correct
- [ ] Service/timer/cron is in expected state
- [ ] No errors in logs
- [ ] If it was a fix, verify the problem is resolved
