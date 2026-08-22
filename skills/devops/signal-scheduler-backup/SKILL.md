---
name: signal-scheduler-backup
description: Daily SQLite DB, .env, and uploads backup from CT 200 to NAS via rsync.
version: 1.1.0
metadata:
  hermes:
    tags: [backup, sqlite, rsync, nas, signal-scheduler, proxmox]
    trigger_conditions:
      - "signal scheduler backup"
      - "backup scheduler.db"
      - "CT 200 backup to NAS"
      - "restore signal scheduler database"
      - "rsync scheduler db nas"
      - "backup failed integrity check"
      - "0-byte sqlite backup"
      - "scheduler.db corrupted"
      - "restore uploads from NAS"
      - "signal scheduler disaster recovery"
---

# Signal Scheduler Backup

Automated daily backup for the Signal Scheduler (CT 200).

## When to Use

- The user asks whether the Signal Scheduler DB / uploads are backed up, or asks to verify the last backup.
- A backup job failed (check `/var/log/signal-scheduler-backup.log` for errors).
- Restoring the scheduler DB or uploads after corruption or a CT rebuild.
- Setting up or modifying the daily 03:17 backup cron.
- Any "disaster recovery" question for the Signal Scheduler (CT 200).

## Not For

- Backing up other CTs or services → each VM/CT has its own backup path; this skill covers CT 200's Signal Scheduler only.
- The Signal Scheduler app itself (deploy, config, messaging logic) → see the Signal Scheduler deployment skill / project docs.
- NAS storage administration beyond the backup target path → storage quota, snapshotting, and NAS health live outside this skill.
- Generic rsync usage → use the rsync docs; this skill is the CT-200-specific invocation with the ed25519 key.

## Components

- **Backup Script**: `/usr/local/bin/signal-scheduler-backup.sh`
- **Schedule**: `17 3 * * *` (Daily at 03:17)
- **Log**: `/var/log/signal-scheduler-backup.log`
- **Backup Destination**: `root@192.168.100.33:/archive/vm-backups/signal-scheduler/`

## Backup Logic

1. **Atomic SQLite Backup**: Uses `sqlite3 .backup` to avoid locking or corruption of the live database while the scheduler is running.
2. **Integrity Check**: Runs `PRAGMA integrity_check` on the temporary backup before sync.
3. **Synchronization**:
   - `scheduler.db` pushed to NAS.
   - `.env` (secrets) pushed to NAS.
   - `uploads/` directory pushed (rsync incremental).
4. **Retention**:
   - Keeps the live `.db` snapshot on NAS.
   - Rotates timestamped `.bak` files on the NAS, keeping only the last 14.

## Manual Restoration

If the local DB is corrupted:

```bash
# 1. Pull the backup from NAS
rsync -avz -e "ssh -i /root/.ssh/signal-scheduler-backup" \
  root@192.168.100.33:/archive/vm-backups/signal-scheduler/scheduler.db \
  /opt/signal-scheduler/data/scheduler.db

# 2. Restart services
systemctl restart signal-scheduler signal-scheduler-web
```

## Troubleshooting

- **Check logs**: `tail -f /var/log/signal-scheduler-backup.log`
- **Test run**: `/usr/local/bin/signal-scheduler-backup.sh`
- **SSH Connectivity**: The CT 200 uses `/root/.ssh/signal-scheduler-backup` (ed25519) to authenticate to the NAS as root.

## Pitfalls

1. **Do not edit the script without re-testing** — Small quoting errors in the sqlite3 command can lead to 0-byte database files. Recovery: run `bash -x /usr/local/bin/signal-scheduler-backup.sh` after any edit and verify the NAS file is non-zero before trusting the next backup.

2. **Never write the backup script via quoted SSH heredoc** — Using `cat << "EOF"` writes literal `$TMP_DIR`, `$NAS_DIR`, etc. into the file; at runtime those expand to empty strings, so `sqlite3 .backup` writes to `/scheduler.db` and produces 0-byte backups. Recovery: use `write_file`/`scp` from the agent or manage quoting carefully. If you suspect it happened, check `grep -E '\$[A-Z_]+' /usr/local/bin/signal-scheduler-backup.sh` — literal `$TMP_DIR` in the file means it's broken.

3. **0-byte DB means the last backup is worthless** — A successful-looking run can still ship an empty file. Recovery: after each run, verify `ls -l` on the NAS target; if zero, restore from the last good `.bak` rotation entry.

4. **`sqlite3 .backup` requires the DB to be unlocked** — If the scheduler holds a write lock, `.backup` can fail or produce a partial snapshot. Recovery: check `lsof /opt/signal-scheduler/data/scheduler.db` and confirm no in-flight job before diagnosing the backup itself.

5. **SSH key path is root-scoped** — The restore snippet uses `-i /root/.ssh/signal-scheduler-backup`. Running it as a non-root user fails auth. Recovery: run restore as root, or copy the key to the invoking user's `~/.ssh` and update the path.

6. **Maintain consistency with GitHub** — Ensure the local DB matches the commit on GitHub when possible. The script overwrites the NAS file but keeps timestamped historical copies as a secondary safety; don't rely on the single latest copy alone.

7. **Check the log before assuming success** — `tail -f /var/log/signal-scheduler-backup.log` shows rsync exit codes and integrity-check output. Recovery: grep for `error`/`rsync:` lines; a clean log with a non-zero NAS file is the only "done" signal.
