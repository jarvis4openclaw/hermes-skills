# Proxmox VE 9.x Configuration Loss & Recovery — Full Technical Summary

## Overview
This document summarizes the issues encountered on a Proxmox VE 9.1.9 system after a complete loss of the Proxmox configuration database (`pmxcfs`), the steps taken to restore functionality, and the long‑term backup strategy implemented using Proxmox Backup Server (PBS) 4.2.0.

It includes:

- What broke
- What was restored
- What could not be restored
- How configuration backups were implemented
- The cron jobs created for automated backups and pruning
- **Auth fixes applied 2026-05-29 (token auth, prune params)**

This document is intended for ingestion by an AI agent for future troubleshooting or automation.

---

# 1. Initial Problem: pmxcfs Database Wiped

### Symptoms
- `/etc/pve` was empty or partially missing
- VM and CT configuration files were gone
- Storage configuration (`storage.cfg`) was missing
- User and ACL files were missing
- vzdump backup schedules were missing
- Proxmox UI showed no VMs or CTs

### Cause
The Proxmox cluster filesystem (`pmxcfs`) stores all node configuration under:

```
/etc/pve
/var/lib/pve-cluster/config.db
```

A corruption or wipe of this database results in total loss of configuration.

---

# 2. Manual Recovery Steps Performed

## 2.1 Recreated `storage.cfg`
A new `/etc/pve/storage.cfg` was created manually to restore storage definitions.

## 2.2 Restored VM and CT Configuration Files
Recovered `.conf` files were placed into:

```
/etc/pve/nodes/<node>/qemu-server/<VMID>.conf
/etc/pve/nodes/<node>/lxc/<CTID>.conf
```

After this, VMs and CTs reappeared in the UI.

## 2.3 Networking Verified
`/etc/network/interfaces` was intact and required no restoration.

## 2.4 Confirmed No Host Backups or ZFS Snapshots
- No PBS host backups existed
- Only a single ZFS snapshot existed for an unrelated dataset
- No `.pxar` archives containing PVE configs were found

## 2.5 PBS User/ACL Files Found (Not PVE Files)
Located:

```
/etc/proxmox-backup/user.cfg
/etc/proxmox-backup/acl.cfg
```

These belong to PBS, not PVE, and cannot restore PVE users or ACLs.

---

# 3. Why PBS Host Backups Could Not Be Used

### Reason
Proxmox VE 9.x does **not yet include** the `pve-host-backup` package required to register a PVE node with PBS for Host Backups.

Therefore, the PBS UI did not show:

```
Administration → Host Backups
```

This feature is available only for PVE 8.x at the time of this incident.

---

# 4. Implemented Solution: PBS File Backups for PVE Configuration

Since Host Backups are not available on PVE 9.x, we implemented **manual file‑level backups** using `proxmox-backup-client`.

A dedicated PBS namespace was created:

```
Datastore: backups
Namespace: host
```

---

# 5. Working Backup Command (Token Auth)

This command successfully backs up all critical PVE configuration directories.

**IMPORTANT:** Uses `root@pam!pve-backup` API token, NOT bare `root@pam`. Token secret is stored at `/etc/pve/priv/storage/pbs.pw`. The `PBS_PASSWORD` env var is required for non-interactive/cron use.

```
export PBS_PASSWORD=*** /etc/pve/priv/storage/pbs.pw)
export PBS_FINGERPRINT=e3:5e:85:70:18:4d:cb:cd:fb:d8:c8:b5:79:d7:d6:96:4a:71:4b:e0:ec:03:81:94:6b:83:85:bb:e0:44:2e:7c

proxmox-backup-client backup \
  etc-pve.pxar:/etc/pve \
  pve-cluster.pxar:/var/lib/pve-cluster \
  network.pxar:/etc/network \
  firewall.pxar:/etc/pve/firewall \
  priv.pxar:/etc/pve/priv \
  --exclude /var/lib/vz \
  --exclude /mnt/backups \
  --repository root@pam!pve-backup@192.168.100.23:backups \
  --ns host
```

This captures:

- pmxcfs database
- all PVE configuration files
- networking
- firewall rules
- user/ACL directories
- vzdump schedules (if present)

---

# 6. Working Backup Cron Job (Updated 2026-05-29)

Location: `/etc/cron.daily/pve-config-backup`

```bash
#!/bin/bash

export PBS_PASSWORD=*** /etc/pve/priv/storage/pbs.pw)
export PBS_FINGERPRINT=e3:5e:85:70:18:4d:cb:cd:fb:d8:c8:b5:79:d7:d6:96:4a:71:4b:e0:ec:03:81:94:6b:83:85:bb:e0:44:2e:7c

proxmox-backup-client backup \
  etc-pve.pxar:/etc/pve \
  pve-cluster.pxar:/var/lib/pve-cluster \
  network.pxar:/etc/network \
  firewall.pxar:/etc/pve/firewall \
  priv.pxar:/etc/pve/priv \
  --exclude /var/lib/vz \
  --exclude /mnt/backups \
  --repository root@pam!pve-backup@192.168.100.23:backups \
  --ns host
```

Permissions: `chmod +x /etc/cron.daily/pve-config-backup`

This ensures **daily configuration backups** to PBS.

---

# 7. Working Prune Cron Job (Updated 2026-05-29)

Location: `/etc/cron.daily/pve-config-prune`

```bash
#!/bin/bash

export PBS_PASSWORD=*** /etc/pve/priv/storage/pbs.pw)
export PBS_FINGERPRINT=e3:5e:85:70:18:4d:cb:cd:fb:d8:c8:b5:79:d7:d6:96:4a:71:4b:e0:ec:03:81:94:6b:83:85:bb:e0:44:2e:7c

proxmox-backup-client prune host/pve \
  --repository root@pam!pve-backup@192.168.100.23:backups \
  --ns host \
  --keep-daily 14
```

Permissions: `chmod +x /etc/cron.daily/pve-config-prune`

### Prune parameter notes:
- `host/pve` is the **backup group** — must be specified (was missing in original)
- `--keep-weekly/monthly/yearly` have **minimum value 1** — omit them if not wanted (original set them to 0, which is invalid)
- `PBS_PASSWORD` is required for non-interactive auth from cron

---

# 8. Auth Fixes Applied (2026-05-29)

### Problems:
1. **"no password input mechanism available"** — Cron jobs ran `root@pam` without `PBS_PASSWORD`, so PBS couldn't authenticate
2. **Prune missing `<group>` argument** — Original script had no backup group name
3. **Invalid `--keep-weekly/monthly/yearly 0`** — Minimum allowed value is 1

### Fixes:
1. Switched repository from `root@pam@` to `root@pam!pve-backup@` (API token)
2. Added `PBS_PASSWORD` sourced from `/etc/pve/priv/storage/pbs.pw`
3. Added `host/pve` group argument to prune command
4. Removed zero-value keep flags (just `--keep-daily 14`)
5. Deleted stale snapshot `host/pve/2026-05-23T21:15:49Z` owned by `root@pam` (incompatible with token auth)

---

# 9. Current Protection Level

With the above in place, the system is now protected against:

- pmxcfs corruption
- accidental deletion of `/etc/pve`
- loss of VM/CT configuration
- loss of storage.cfg
- loss of firewall rules
- loss of vzdump schedules
- loss of user/ACL configuration

Restoration can be performed using:

```
proxmox-backup-client restore <archive> <target-path> --repository ... --ns host
```

---

# 10. Recommended Future Enhancements

- Enable PBS datastore verification jobs
- Add email notifications for backup failures
- Add weekly integrity checks for `/var/lib/pve-cluster`
- When Proxmox releases `pve-host-backup` for PVE 9.x, migrate to Host Backups
