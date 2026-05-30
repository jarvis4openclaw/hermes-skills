# PBS Storage Setup & Recovery — Session Detail

## Environment
- **PBS:** 4.2.0 on same host as PVE 9.1.9 (192.168.100.23)
- **Datastore:** `backups` at `/mnt/backups` (ZFS `zfspool/pbs-backups`)
- **Namespace:** `host` (for PVE config pxar backups)
- **Root namespace:** all CT/VM vzdump backups

## PBS Storage Config Anatomy

`/etc/pve/storage.cfg` entry:
```
pbs: pbs
        datastore backups
        server localhost
        username <auth-id>
        content backup
        fingerprint <sha256-fingerprint>
```

The password/secret is stored via `pvesh set /storage/pbs -password "<value>"`. This writes to `/etc/pve/priv/storage/pbs.pw`.

## Common Breakage Points

### 1. Dummy fingerprint
After pmxcfs wipe, the fingerprint was all zeros. Get real one:
```bash
proxmox-backup-manager cert info | grep -i fingerprint
```

### 2. Wrong username/realm
`root@pbs` does not exist. Proper options:
- `root@pam` — PAM superuser (needs password or Unix socket auth)
- `root@pam!token-name` — API token (needs token secret as password)

### 3. 401 Unauthorized from pvesm
`pvesm` connects via HTTPS (port 8007). Needs API token + password. Even though `proxmox-backup-client` works without password (Unix socket at `/run/proxmox-backup/api.sock`), pvesm does NOT.

Fix: generate API token + set ACLs + use `pvesh set /storage/pbs -password "<token-secret>"`.

## API Token Generation

```bash
# Generate token
proxmox-backup-manager user generate-token root@pam pve-backup

# Grant ACLs (minimum: DatastoreBackup on the datastore)
proxmox-backup-manager acl update /datastore/backups DatastoreAdmin --auth-id root@pam!pve-backup

# Apply to PVE storage
sed -i 's/username root@pam/username root@pam!pve-backup/' /etc/pve/storage.cfg
pvesh set /storage/pbs -password "<token-secret>"
```

## Backup Ownership Pitfall

When switching auth method (e.g., `root@pam` → `root@pam!token`), PBS enforces that the backup group owner matches the auth-id writing to it. Error:

```
Error: backup owner check failed (root@pam!pve-backup != root@pam)
```

**Fix:** Delete old backup group for the affected VM/CT, then re-backup with new auth:

```bash
# List snapshots to find group
proxmox-backup-client snapshot list --repository root@pam@localhost:backups | grep "ct/100"

# Delete each snapshot in the group
proxmox-backup-client forget ct/100/2026-05-20T02:00:09Z --repository root@pam@localhost:backups
proxmox-backup-client forget ct/100/2026-05-21T02:00:01Z --repository root@pam@localhost:backups
# ... etc

# Re-backup with new auth
vzdump 100 --storage pbs --mode snapshot --compress zstd
```

## Creating Backup Jobs

```bash
# Daily at 2am, snapshot mode, zstd compression
pvesh create /cluster/backup --vmid 100 --storage pbs --mode snapshot \
  --schedule "02:00" --compress zstd --enabled 1

# Verify
pvesh get /cluster/backup --output-format json
cat /etc/pve/jobs.cfg
```

**Note:** `--schedule` and `--starttime` are mutually exclusive. Use `--schedule "HH:MM"` for daily at specific time, or cron-style `--schedule "0 2 * * *"`.

## Listing PBS Backups

```bash
# Via PBS client (shows all namespaces/groups)
proxmox-backup-client snapshot list --repository root@pam@localhost:backups

# Via PVE storage plugin (after storage.cfg is fixed)
pvesm list pbs
```

## Bulk Backup Job Creation

When configuring backups for all CTs/VMs at once (e.g., after pmxcfs wipe loses all jobs):

```bash
# Get list of VMIDs
pct list | awk 'NR>1{print $1}'  # CTs
qm list | awk 'NR>1{print $1}'   # VMs

# Create jobs in a loop
for vmid in 101 102 103 104 105 106 109 200 201 202; do
  pvesh create /cluster/backup --vmid $vmid --storage pbs \
    --mode snapshot --schedule "02:00" --compress zstd --enabled 1
done
```

**Important:** `--schedule` and `--starttime` are mutually exclusive. Use `--schedule "HH:MM"` for daily at a specific time.

To verify all jobs:
```bash
pvesh get /cluster/backup --output-format json-pretty
# Or parse next-run timestamps:
pvesh get /cluster/backup --output-format json | python3 -c "
import json,sys
for j in sorted(json.load(sys.stdin), key=lambda x: x['vmid']):
    print(f\"VMID {j['vmid']}: next={j.get('next-run')} enabled={j['enabled']}\")
"
```

## Stale Lock Recovery After Interrupted Backup

When a backup is killed mid-flight (SSH timeout, signal), PBS leaves lock files that prevent snapshot deletion:

```bash
# 1. Verify no vzdump process is still running
ps aux | grep vzdump | grep -v grep

# 2. Remove stale lock files
rm -f /run/proxmox-backup/locks/backups/<ct|vm>-<vmid>*

# 3. Delete partial snapshot
proxmox-backup-client forget <group>/<timestamp> --repository root@pam@localhost:backups

# 4. Restart backup (in background for large VMs)
nohup vzdump <vmid> --storage pbs --mode snapshot --compress zstd \
  > /var/log/vzdump/<name>.log 2>&1 &
```

Lock file naming pattern: `/run/proxmox-backup/locks/backups/<ct|vm>-<vmid>-\<encoded-timestamp\>`

## Large VM Backup Strategy

VMs over ~100GB will hit the 600s foreground timeout. Strategy:

1. Start in background: `nohup vzdump <vmid> --storage pbs --mode snapshot --compress zstd > /var/log/vzdump/<name>.log 2>&1 &`
2. Monitor: `grep "%" /var/log/vzdump/<name>.log | tail -3` or `tail -f /var/log/vzdump/<name>.log`
3. Wait for completion: `while pgrep -f "vzdump <vmid>"; do sleep 60; done`
4. Verify: `proxmox-backup-client snapshot list --repository root@pam@localhost:backups | grep "<ct|vm>/<vmid>"`

Example: VM 102 (startos, 700GB) — ~45 min at ~260 MiB/s write speed.

## Verification Steps After Fix
1. `pvesm list pbs` shows backups (no 401)
2. `vzdump <vmid> --storage pbs --mode snapshot --compress zstd` completes
3. Backup appears in `proxmox-backup-client snapshot list`
4. Job shows in `pvesh get /cluster/backup`
