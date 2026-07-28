---
name: nas-management
description: Manage the NAS (192.168.100.33 / nas.wahidsaleemi.net) — Debian 12 LXC on Proxmox with Cockpit, Samba, NFS, and ZFS storage.
tags: [nas, samba, nfs, zfs, cockpit, file-sharing, debian]
version: 1.1.0
metadata:
  hermes:
    trigger_conditions:
      - "Manage NAS storage"
      - "Check NAS disk space"
      - "NAS Samba share permissions"
      - "NAS NFS export configuration"
      - "NAS ZFS pool health"
      - "NAS Cockpit status"
      - "NAS cloud backup restic"
      - "NAS SMB permissions Windows"
      - "NAS archive share guest access"
      - "NAS systemd service failed"
      - "NAS Samba user password"
      - "NAS SSH access"
      - "NAS security audit"
---

# NAS Management

## System Overview

|| Property | Value |
||----------|-------|
|| Hostname | nas |
|| FQDN | nas.wahidsaleemi.net |
|| IP | 192.168.100.33 |
|| OS | Debian 12 (bookworm) |
|| Virtualization | LXC container on Proxmox (kernel 7.0.6-2-pve) |
|| SSH | `ssh root@192.168.100.33` (always as root) |
|| Cockpit | v337, https://192.168.100.33:9090 |
|| Cockpit Plugins | file-sharing 4.6.0, cockpit-navigator, cockpit-identities, cockpit-45drives-hardware, cockpit-storaged, cockpit-networkmanager |

## When to Use

- **Managing Samba/CIFS file shares** — Create, modify, or troubleshoot shared folders accessible from Windows/macOS/Linux clients on the LAN
- **Monitoring ZFS pool health** — Check scrub status, disk errors, pool capacity, and dataset usage
- **Configuring NFS exports** — Set up or update NFS mounts for Linux clients or Proxmox hosts
- **Troubleshooting Windows file access issues** — Diagnose "can't modify/delete files" errors, permission mapping, or credential caching
- **Managing cloud backups via Restic** — Monitor or trigger restic backups to Backblaze B2 from the Proxmox host
- **Checking system health** — Review journalctl errors, failed systemd units, pending updates
- **Adding Samba users** — Create or update Samba passwords for authenticated access

## Not For

- **Managing cloud storage (S3, GDrive, OneDrive)** → use dedicated cloud storage tools (rclone, restic) instead
- **Virtual machine disk provisioning** → use Proxmox storage management (`pvesm`) instead
- **Network file system design** → this covers a specific existing NAS; for new NAS architecture use Proxmox + ZFS guides
- **Container storage configuration** → manage container volumes through Proxmox CT storage options instead

## Storage Layout

| ZFS Dataset | Mount | Size | Purpose |
|-------------|-------|------|---------|
| zfspool/data | /zfspool/files | ~23T | Primary file share |
| zfspool/backups | /archive | ~24T | Backup/archive share |
| Root (ext4) | / | 7.8G | System only |

ZFS pool name: `zfspool`. Datasets mounted via ZFS (not fstab — fstab is unconfigured).

## Samba Shares (Registry-based)

Config: `/etc/samba/smb.conf` → uses `include = registry`. All shares managed via `net conf` (Cockpit UI).

| Share | Path | Guest | Notes |
|-------|------|-------|-------|
| files | /zfspool/files | No | Primary share, auth required, valid users empty (any auth user) |
| archive | /archive | Yes | Wide open — guest ok, no user restriction |
| homes | %H | No | Home dirs, read only |

Samba passwords: `pdbedit -L` to list, `smbpasswd -a <user>` to add.

## NFS Exports

Managed by cockpit-file-sharing via `/etc/exports.d/cockpit-file-sharing.exports`.

| Export | Clients | Options | Status |
|--------|---------|---------|--------|
| /zfspool/files/media | * | rw,sync,no_subtree_check | Active |

## Key Config Files

- `/etc/samba/smb.conf` — Samba (registry include)
- `/etc/exports.d/cockpit-file-sharing.exports` — NFS exports
- `/etc/cockpit/cockpit.conf` — Cockpit config (does not exist yet)
- `/etc/apt/apt.conf.d/20auto-upgrades` — unattended upgrades (enabled)

## Management Commands

```bash
# Samba
net conf list                          # List all shares
net conf showshare <name>              # Show all parameters for a share
net conf getparm <share> "<param>"     # Read a single share parameter (e.g. net conf getparm archive "guest ok")
net conf setparm <share> "<param>" "<value>"  # Set a single share parameter (e.g. net conf setparm archive "guest ok" "no")
smbclient -L localhost -U%             # Test share listing
smbstatus                              # Show connected users, their UID, access mode, and file locks (key for debugging permissions)
systemctl reload smbd                  # Apply changes
pdbedit -L                             # List samba users
pdbedit -L -v                          # Verbose user details (SID, flags, etc.)
smbpasswd -a <user>                    # Add/change samba password

# NFS
cat /etc/exports.d/cockpit-file-sharing.exports  # Current exports
exportfs -v                            # Show active exports
showmount -e localhost                 # Verify exports
systemctl reload nfs-kernel-server     # Apply changes

# ZFS
zpool list                             # Pool health
zpool status                           # Detailed status (scrub, errors)
zfs list                               # All datasets
zfs get all <dataset>                  # Dataset properties
zfs set <property>=<value> <dataset>   # Set property

# Cockpit
systemctl status cockpit               # Service status
cockpit-bridge --version               # Version check

# System
journalctl -p err --since '24 hours ago'  # Recent errors
systemctl --failed                     # Failed units
apt list --upgradable                  # Pending updates
```

## Fixed Issues History

| # | Issue | Fix Applied | Date |
|---|-------|-------------|------|
| 1 | NFS exporting empty /media | Changed to `/zfspool/files/media` | 2026-06-27 |
| 2 | systemd-networkd-wait-online timeout | Masked `systemd-networkd.service` and `systemd-networkd-wait-online.service` (LXC networking handled by Proxmox) | 2026-06-27 |
| 3 | blkmapd (nfs-blkmap) fails | `systemctl disable --now nfs-blkmap.service` | 2026-06-27 |
| 4 | openipmi.service fails | Masked by Boss (effective after reboot) | 2026-06-27 |
| 5 | ssh.socket conflict with ssh.service | Disabled `ssh.socket`, `ssh.service` now starts directly | 2026-06-27 |
| 6 | Windows can't modify/delete files on archive share | `guest ok = yes` caused silent fallback to nobody/readonly; `acl_xattr:ignore system acls = yes` ignored Linux perms. Fixed by setting both to `no`. Also fixed `vm-backups` dir owned by `root:root` (755) → `root:sambausers` (775) | 2026-06-27 |

## Active Design Decisions

| Decision | Rationale |
|----------|-----------|
| **No firewall** | Home lab, no external access |
| **archive share: guest ok, no restrictions** | Simplicity and ease of use |
| **wahid not in sudoers** | Boss logs in as root for admin tasks |
| **SSH as root only** | Boss preference, home lab environment |

## Samba Permissions Troubleshooting

### Debugging "can't modify/delete files" from Windows

1. **Check who's actually connected and what UID they map to:**
   ```bash
   smbstatus
   ```
   Look at the "Locked files" section — if User(ID) is `65534` (nobody) and R/W is `RDONLY`, the user is falling back to guest access.

2. **Common cause: `acl_xattr:ignore system acls = yes`**
   This tells Samba to ignore Linux filesystem permissions and only use stored NT ACLs (extended attributes). If no NT ACLs are stored, access defaults to restrictive/readonly.
   **Fix:** `net conf setparm <share> "acl xattr:ignore system acls" "no"` — Samba will then fall back to Linux filesystem permissions.

3. **Common cause: `guest ok = yes`**
   Windows silently falls back to guest credentials even when you provide a username/password, especially if the share was previously connected as guest.
   **Fix:** `net conf setparm <share> "guest ok" "no"`

4. **Windows credential caching:**
   Windows caches SMB credentials per session. "Disconnect" in Explorer does NOT drop the connection. Must run `net use * /delete` from Command Prompt to fully clear, then remap.

5. **Directory ownership matters:**
   Even if the parent directory has correct group permissions, subdirectories created by root (e.g., via backup jobs) may be `root:root` with 755. Fix with `chown -R root:sambausers <dir>` and `chmod -R 775 <dir>`.

### Share permission model (current)

| Setting | Effect |
|---------|--------|
| `guest ok = no` | Forces authentication — no anonymous access |
| `acl_xattr:ignore system acls = no` | Falls back to Linux filesystem perms when no NT ACLs stored |
| `read only = no` | Share is writable (not read-only) |
| `valid users =` (empty) | Any authenticated Samba user can access |
| `map acl inherit = yes` | Inherited ACLs are mapped |

## Cloud Backup (Restic → Backblaze B2)

Scripts live on the **Proxmox host** (not the NAS LXC):

| Script | ZFS Dataset | Restic Tag | B2 Bucket |
|--------|-------------|------------|-----------|
| `/root/backup-files.sh` | zfspool/data | data | `s3:s3.us-west-004.backblazeb2.com/pve-myfiles` |
| `/root/backup-archive.sh` | zfspool/backups | archive | `s3:s3.us-west-004.backblazeb2.com/pve-archive` |

**Schedule:** Two separate systemd timers (one per dataset), both set to days 7, 14, 21, 28 at 11pm:
- `restic-data-backup.timer` → `restic-data-backup.service` → runs `backup-files.sh`
- `restic-archive-backup.timer` → `restic-archive-backup.service` → runs `backup-archive.sh`

**How it works (atomic):**
1. Cleanup old temp snapshots
2. `zfs snap -r zfspool/<dataset>@restic-<uuid>` — frozen point-in-time
3. Restic backs up from `.zfs/snapshot/` paths (not live FS)
4. `restic check` + `restic forget --prune` (retention policy)
5. Snapshot deleted via trap

**Key files:**
- `/etc/systemd/system/restic-data-backup.timer` — data backup schedule
- `/etc/systemd/system/restic-data-backup.service` — runs backup-files.sh
- `/etc/systemd/system/restic-archive-backup.timer` — archive backup schedule
- `/etc/systemd/system/restic-archive-backup.service` — runs backup-archive.sh
- `/root/restic-restore-helper.sh` — helper script for restore operations
- `/etc/restic-password` — restic repo password
- `/etc/restic-archive.env` — environment (repo URL, credentials)

**Management commands (on Proxmox host):**
```bash
systemctl status restic-data-backup.timer          # Data timer status
systemctl status restic-archive-backup.timer       # Archive timer status
systemctl list-timers restic-data-backup.timer     # Next data run time
systemctl list-timers restic-archive-backup.timer  # Next archive run time
systemctl enable --now restic-data-backup.timer    # Enable data timer
systemctl enable --now restic-archive-backup.timer # Enable archive timer
systemctl status restic-data-backup.service        # Data service status
systemctl status restic-archive-backup.service     # Archive service status
```

**Restore procedure:**
```bash
# Prerequisites
source /etc/restic-archive.env                # or restic-data.env
export RESTIC_PASSWORD_FILE=/etc/restic-password

# Browse available snapshots
restic snapshots
restic snapshots --json | jq '.[] | {id: .short_id, time: .time, tags: .tags}'

# List files in a snapshot
restic ls <snapshot-id>

# Restore
restic restore latest --target /tmp/restore-test
restic restore <snapshot-id> --target /path/to/restore
restic restore latest --target /tmp/restore --include /path/subdir

# Mount for browsing (useful!)
mkdir /tmp/restic-mount
restic mount /tmp/restic-mount
# Browse at /tmp/restic-mount/snapshots/...
fusermount -u /tmp/restic-mount
```

## Pitfalls

1. **SSH as root requires explicit key** — The NAS only accepts root login via SSH key. `sudo ssh wahid@192.168.100.33` will fail. Always use `ssh root@192.168.100.33` with the `id_ed25519` key. The API key pattern from PVE does not apply here.

2. **Samba guest credentials cached on Windows** — Windows caches SMB credentials per session. Disconnecting in Explorer does NOT clear them. Users must run `net use * /delete` from Command Prompt to fully clear cached credentials before reconnecting with different credentials.

3. **`guest ok = yes` silently forces readonly** — When `guest ok = yes` is set, Windows may silently fall back to guest credentials even when a valid username and password are provided, especially if the share was previously connected as guest. The fallback maps to user ID 65534 (nobody) with readonly access. Fix: set `guest ok = no`.

4. **`acl_xattr:ignore system acls = yes` overrides Linux permissions** — This setting tells Samba to use only stored NT ACLs (extended attributes) and ignore Linux filesystem permissions. If no NT ACLs are stored, access defaults to restrictive/readonly. Fix: set `acl xattr:ignore system acls = no`.

5. **Directory ownership by root blocks writes** — Backup jobs or root-owned processes that create directories under Samba shares result in `root:root` with 755 permissions, making them unwritable by Samba users. Fix: `chown -R root:sambausers <dir>` and `chmod -R 775 <dir>`.

6. **Snapshots created by restic backup may persist on failure** — The backup script creates a ZFS snapshot (`zfspool/<dataset>@restic-<uuid>`) and deletes it via trap on exit. If the process is killed with SIGKILL (not SIGTERM), the trap doesn't fire and snapshots accumulate. Monitor with `zfs list -t snapshot | grep restic` and clean stale ones.

7. **Restoring from restic requires correct environment** — The restic restore scripts need `RESTIC_PASSWORD_FILE=/etc/restic-password` and the correct env file sourced. Without the password file, restic prompts interactively and fails in cron context.

8. **Cockpit changes may not persist across restarts** — Some Cockpit UI changes (especially file-sharing plugin) may not survive a reboot of the LXC. Always verify with `systemctl status smbd nfs-kernel-server` and `net conf list` after reboot.

9. **NFS exports with `*` as client are wide open** — The current NFS export uses `*` as client, allowing any host on any network to mount. This is intentional for the home lab but is a security risk if the NAS is ever exposed externally. Review on each management session.

10. **Samba user passwords are separate from system passwords** — Adding a Linux user (`useradd`) does not create a Samba user. Use `smbpasswd -a <user>` to set a Samba password. The Samba password database is managed independently of `/etc/shadow`.

## Rules

1. **No changes without Boss approval** — always present findings and get explicit go-ahead
2. **Be proactive** — recommend enhancements, security hardening, performance tuning
3. **Review logs** — check for errors, failed services, disk health on each management session
4. **Backup before changes** — always make a timestamped backup of any config file before modifying. Use `.bak.YYYYMMDD-HHMMSS` suffix. Never append to or overwrite without a recent backup.
5. **SSH as root** — always use root@192.168.100.33 (or root@nas.wahidsaleemi.net)

## Backup Examples

```bash
# Backup a file before editing
cp /etc/exports.d/cockpit-file-sharing.exports \
   /etc/exports.d/cockpit-file-sharing.exports.bak.$(date +%Y%m%d-%H%M%S)

# Verify backup exists before modifying
ls -la /etc/exports.d/*.bak.*
```

## Proactive Recommendations Checklist

When doing a management session, check and recommend on:
- [ ] ZFS pool health (scrub status, errors)
- [ ] Disk space trends
- [ ] Failed systemd units
- [ ] Journal errors (last 24h)
- [ ] Pending security updates
- [ ] Samba share permissions (security review)
- [ ] NFS export security (currently wide open to * — intentional for home lab)
- [ ] Firewall status (none — intentional)
- [ ] Backup strategy
- [ ] Cockpit SSL/cert config
