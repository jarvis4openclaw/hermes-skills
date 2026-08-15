---
title: Server Health Check
name: server-health
author: Friday Agent
version: 0.2.0
description: Automated Linux server health checks with memory and reporting. Use when running cron-driven or on-demand health checks (disk, MemAvailable/PSI memory pressure, load, services, logs, network) and only report problems.
tags: [system, monitoring, health, friday]
metadata:
  hermes:
    tags: [server-health, monitoring, systemd, linux, thresholds]
    trigger_conditions:
      - "run a server health check"
      - "check server health"
      - "is the server healthy"
      - "memory pressure check"
      - "disk space warning"
      - "service status check"
      - "log rotation check"
      - "network connectivity check"
      - "friday agent health"
      - "system load check"
---

A skill to perform automated server health checks on a Linux system. Designed for cron-driven use by the Friday agent.

## When to Use

- Cron-driven or on-demand health checks of a Linux server (Friday agent, homelab hosts)
- A user asks "is the server OK?", "run a health check", or reports a slow/degraded host
- Memory-pressure triage where `free` output looks alarming but MemAvailable/PSI say otherwise
- Service status verification (openclaw-gateway, systemd units) after changes
- Log-rotation audits (journald, /var/log growth) before disk runs full
- Pre-backup or pre-maintenance sanity checks

## Not For

- **Deep disk-space recovery** (tiered cleanup, partition resize) → use `disk-space-recovery`
- **Proxmox cluster resource reporting** (multi-host, VM/CT metrics) → use `proxmox-resource-reporting`
- **Journald log rotation configuration** (capping systemd journal size) → use `journald-log-rotation`
- **Backup coverage decisions** (which VM/CT is missing a snapshot) → use `proxmox-backup-coverage`

## Purpose

This skill systematically checks server health across multiple dimensions. It performs threshold-based checks and only reports problems to the user, maintaining silence when all systems are nominal. Results are logged for historical tracking.

## Thresholds

- **Disk space**:
  - Warning: >75% used
  - Critical: >85% used
- **Memory pressure** (use MemAvailable / PSI, NOT raw `used`):
  - Warning: MemAvailable < 20% of total, OR PSI `some avg60` > 1.0
  - Critical: MemAvailable < 10% of total, OR PSI `some avg60` > 5.0
- **System Load**:
  - Warning: Average > number of CPU cores
  - Critical: Average > 2× number of CPU cores
- **Log files**:
  - Warning: >100MB
  - Critical: >1GB

## Process

1. **Check disk usage** (`df -h`)
   - Parse root filesystem (`/`) usage percentage
   - Flag if above warning or critical thresholds

2. **Check memory & CPU**
   - Run `free -h` and parse **MemAvailable**, NOT raw `used`
   - Run `cat /proc/pressure/memory` and check PSI `some avg10/60/300`
   - Run `uptime` and `nproc` to get current load and CPU core count
   - Calculate load vs core ratio
   - **Memory pressure = low MemAvailable OR rising PSI**, even if `used` looks high
   - Flag only on low MemAvailable or rising PSI (see Pitfalls)

> **Authoritative memory signal**: On Linux, `free` shows `buff/cache` reclaimable by the
> kernel on demand. A host with `used` ≈ total but `available` ≈ 12 GiB and PSI ≈ 0.00 is
> **NOT** memory-starved. Treat `MemAvailable` (and PSI) as the real signal, not `used`.
> Deterministic probe: `bash scripts/mem-check.sh`. Detail: `references/linux-memory-pressure.md`.

3. **Check service status**
   - Check if `openclaw-gateway` is active
   - Test health endpoint with `curl http://localhost:8080/health`
   - Flag if service is inactive or health check fails

4. **Check log rotation**
   - List large log files in `/var/log` (>.1GB)
   - Verify existence of logrotate config for critical services
   - Specifically check for systemd journal rotation via `/etc/systemd/journald.conf`
   - Flag unusually large log files or missing rotation, especially for user journals

5. **Check network connectivity**
   - Test connectivity to external API (OpenRouter)
   - Use `curl` or `ping` to verify network path
   - Flag connectivity failures

6. **Check Docker containers (if Docker is present)**
   - Run `docker ps -q` to check running containers
   - Status only, no action

7. **Report**
   - If any checks fail, compile issue list and message the user
   - If all checks pass, log result to `memory/server-health-YYYY-MM-DD.md` and remain silent

## Output

When issues are found, create a structured report including:
- System metrics that exceeded thresholds
- Service status details
- Network connectivity status
- Recommendations for user action

When no issues are found, create a clean log file with timestamp and "All systems nominal" message.

## Pitfalls

1. **The buff/cache trap** — Dashboards that report `used` from `free -h` will always look
  "high" on a healthy Linux box because the kernel uses idle RAM as page cache. This is by
  design and fully reclaimable. Do NOT raise alarms or run `echo 3 > /proc/sys/vm/drop_caches`
  to "fix" it — that destroys I/O performance for zero benefit. Verify with `MemAvailable`
  + `/proc/pressure/memory` first.
2. **Safe service removal** — Before `systemctl stop`/`disable` of any service (especially a
  `systemd --user` unit), confirm it has **zero active consumers**: check established
  connections to its listening ports (`ss -tnp`), whether any running process references it,
  and whether the Hermes browser `engine:` config points at it. If nothing connects and no
  config depends on it, it is safe to drop — reversible via `enable --now`.
3. **Full uninstall footprint (stop != removed)** — Stopping/disabling the unit only halts the
  daemon. To remove the app completely, hunt its whole footprint or it leaves cruft (and, for
  npm/go, re-installable references). Checklist:
  - Binary on PATH: `~/go/bin/<app>`, `~/.local/bin/<app>`, `/usr/local/bin/<app>`
  - Unit file: `~/.config/systemd/user/<app>.service` (disable drops the `default.target.wants`
    symlink; also `rm` the file + `systemctl --user daemon-reload`)
  - App data dir: `~/.pinchtab/`, `~/.config/<app>/`
  - Crash dumps if it wrapped chromium: `~/.config/chromium/Crash Reports/`
  - npm global package (if installed that way): `npm uninstall -g <app>`
  - **Go module cache is read-only** (`~/go/pkg/mod/<module>/` is mode 0444): `rm -rf` fails
    per-file with `Permission denied`. Fix: `chmod -R u+w ~/go/pkg/mod/<module> && rm -rf ~/go/pkg/mod/<module>`
  - Skill/agent drops in OTHER agents: `~/.claude/skills/<app>`, `~/.codex/skills/<app>`,
    `~/clawd/tools/<app>` — these are the app's own dropped-in skill files, not core config;
    safe to `rm -rf` as part of uninstall.
  - Concrete recipe: `references/service-uninstall-recipe.md`.
4. **Ask before wiping other agents' dirs** — When an uninstall touches `~/.claude`, `~/.codex`,
  or `~/clawd`, those belong to other tools. They only contained the app's own dropped-in skill
  files (safe to delete for the app's purpose), but confirm per the user's intent — "completely
  uninstall" implies full removal is fine.
5. **PSI file location varies** — `/proc/pressure/memory` exists only on kernels with PSI
  enabled (CONFIG_PSI). On older kernels the file is absent — fall back to MemAvailable alone
  rather than erroring out the whole check.
6. **MemAvailable vs `free` columns drift** — `free -h` shows `available` in newer procps
  versions but some minimal systems lack it. Parse `/proc/meminfo`'s `MemAvailable:` directly
  for the authoritative number.
7. **Cron silence is the contract** — the skill logs results and stays silent when nominal.
  When running under cron, do NOT invent issues to justify output; the log file is the
  deliverable, and a clean run should produce no user-facing message.
8. **Health endpoint drift** — the openclaw-gateway health probe is hardcoded to
  `http://localhost:8080/health`; if the service moves ports, the check will false-alarm.
  Verify the port from the unit file before flagging.

## Recovery

When disk space is critical (≥85%), reference the `disk-space-recovery` skill for systematic cleanup procedures. It covers tiered recovery from quick wins (temp files, logs, caches) through agent-specific cleanup (OpenClaw npm projects, orphaned session backups) to partition resizing if the VM disk was expanded.
