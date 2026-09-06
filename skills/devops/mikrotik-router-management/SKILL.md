---
name: mikrotik-router-management
version: 1.1.0
description: Manage MikroTik RouterOS configuration via read-only REST API with git versioning, change proposals, and rollback strategy. Use when asked to inspect router config, propose changes, monitor router state, or manage MikroTik infrastructure.
category: devops
metadata:
  hermes:
    tags: [mikrotik, router, routeros, network, config-management, git]
    trigger_conditions:
      - "mikrotik router"
      - "router config"
      - "routeros"
      - "firewall rules"
      - "router backup"
      - "network config"
      - "REST API router"
      - "router rollback"
      - "router diff"
      - "config changed"
      - "what changed since"
      - "review router config"
      - "hardening review"
      - "high-impact fixes"
      - "router security audit"
---

# MikroTik Router Management

Read-only REST API access to MikroTik RouterOS with git-versioned configuration snapshots, change proposal workflow, and multi-layer rollback strategy.

## When to Use

- User asks to **inspect or review** the current MikroTik router configuration (interfaces, firewall, DHCP, routes).
- User asks **what changed on the router** since a given date — diff against the git-versioned snapshots.
- User asks to **propose a configuration change** (firewall rule, WireGuard peer, VLAN) with a rollback plan.
- User asks to **harden or security-audit** the router (open ports, weak rules, exposed services).
- User reports a **router/network problem** and needs to see recent config drift as a cause.
- User wants a **backup / versioned history** of the RouterOS config.

## Not For

- **Writing config changes directly** to the router without a proposal/rollback plan → the read-only workflow deliberately avoids direct writes; use the change-proposal path inside this skill.
- Managing **other network gear** (Ubiquiti, pfSense, OpenWrt) → do not use this skill.
- MikroTik **IPv6 neighbor-discovery / prefix issues** (ND proxying, RA) → use `mikrotik-ipv6-nd-prefix-invalid` instead.
- MikroTik **RouterOS quirks and gotchas** reference → use `mikrotik-routeros-gotchas` instead.
- The user's **work-style preferences** for router tasks → use `mikrotik-user-work-style` instead.
- General network diagnostics outside MikroTik → use `homelab-browser-backends` / network tooling instead.


## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Local Git Repo: ~/mikrotik-config/                     │
│                                                         │
│  snapshots/                  ← Comment-style REFERENCE DUMP (.rsc) — NOT /import-able! │
│    2026-07-08T120000Z.rsc                                │
│                                                         │
│  sections/                   ← Parsed, sectioned config  │
│    interfaces.rsc                                        │
│    firewall.rsc                                          │
│    dhcp.rsc                                              │
│                                                         │
│  proposals/                  ← Pending change proposals  │
│    001-add-wireguard.rsc                                 │
│                                                         │
│  scripts/                    ← Automation                │
│    pull_config.py                                        │
│    rollback.sh                                           │
└─────────────────────────────────────────────────────────┘
```

## Setup (One-Time)

### On the MikroTik Router

1. **Enable REST API (HTTPS)**:
   ```routeros
   /ip service set www-ssl disabled=no port=443
   ```

2. **Create read-only API user**:
   ```routeros
   /user add name=jarvis-ro password=<strong-password> group=read
   ```

3. **Allow API access from Hermes host** (firewall rule):
   ```routeros
   /ip firewall filter add chain=input src-address=192.168.100.52 \
     protocol=tcp dst-port=443 action=accept \
     comment="Jarvis read-only API access"
   ```

4. **Store credentials** in `~/.hermes/.env`:
   ```
   MIKROTIK_HOST=192.168.100.1
   MIKROTIK_USER=jarvis-ro
   MIKROTIK_PASS=<password>
   # NOTE: Use MIKROTIK_PASS, not MIKROTIK_PASSWORD
   ```

### On Hermes Host

1. **Create repo structure**:
   ```bash
   mkdir -p ~/mikrotik-config/{snapshots,sections,proposals,scripts}
   cd ~/mikrotik-config
   git init
   ```

2. **Create pull script** (`scripts/pull_config.py`):
   - Fetch sections via REST API using **POST** method (required on v7.19.x, see pitfall #9)
   - Fetch sections: `/rest/interface/print`, `/rest/ip/firewall/filter/print`, etc.
   - Write to `snapshots/<timestamp>.rsc` and `sections/<name>.rsc`
   - Auto-commit to git with timestamp

3. **Set up periodic snapshots** (system crontab, every 6 hours):
   ```bash
   0 */6 * * * /home/wahid/mikrotik-config/scripts/snapshot_cron.sh >> /home/wahid/mikrotik-config/cron.log 2>&1
   ```
   - Catches drift, detects unauthorized changes

## Workflow

### Read-Only Inspection (Daily Use)

```bash
# Pull latest config
python3 ~/mikrotik-config/scripts/pull_config.py

# Inspect current state
cat ~/mikrotik-config/sections/firewall.rsc
git log --oneline ~/mikrotik-config/
```

**What I can do (read-only):**
- Inspect interfaces, bridges, IPs, DNS, DHCP, firewall rules
- Monitor interface stats, CPU/RAM, active connections, DHCP leases
- View system logs, firewall logs, wireless events
- Check ARP table, routing table, NAT rules, address lists
- Verify changes after you apply them

**What I cannot do (without your approval):**
- Modify firewall rules
- Change interface configs
- Add/remove users
- Modify DHCP/DNS settings
- Any write operation

### Proposing Changes

1. **I generate a change script** (e.g., `proposals/001-add-wireguard.rsc`):
   ```routeros
   # Proposal: Add WireGuard interface
   /interface wireguard add name=wg1 listen-port=51820
   /interface wireguard peers add interface=wg1 allowed-address=10.0.0.2/32 \
     public-key=<peer-key> endpoint-address=1.2.3.4 endpoint-port=51820
   /ip address add address=10.0.0.1/24 interface=wg1
   ```

2. **You review the proposal** (I show you the diff):
   ```bash
   git diff HEAD~1 proposals/001-add-wireguard.rsc
   ```

3. **You apply the script** via WinBox/WebFig/SSH:
   ```routeros
   /import file=proposals/001-add-wireguard.rsc
   ```

4. **I verify the change** (pull_config.py runs again, commits new state)

## Rollback Strategy

### Layer 1: MikroTik Safe Mode (Immediate)

RouterOS has built-in safe mode that auto-reverts changes if your session disconnects:

```routeros
/system safe-mode
```

When active, any config change is **tentative**. If your connection drops (because you broke networking), the router automatically reverts after ~10 minutes.

**Use this before applying any change.** If it breaks, just disconnect — the router heals itself.

### Layer 2: Pre-Change Snapshot (Our Safety Net)

Before you apply anything:

1. I run `pull_config.py` → commits current state as "pre-change"
2. You apply the proposed `.rsc` script
3. **If it breaks:**
   - I fetch the "pre-change" snapshot from git
   - You restore via the router's own `/export` (the authoritative importable file — see
     `references/mikrotik-importable-backup.md`). The per-snapshot `.rsc` in `snapshots/` is a
     reference dump, NOT `/import`-able.

The git repo always has a known-good state we can restore from.

### Layer 3: Scheduled Snapshots (Drift Detection)

Cron job pulls config every 6 hours. If something changes without our knowledge (someone poking in WinBox, DHCP lease weirdness), we catch it:

```
git log shows:
  2026-07-08 12:00  snapshot  ← last known good
  2026-07-08 14:00  snapshot  ← unexpected drift detected
```

### Layer 4: Physical Recovery (Nuclear Option)

If the router is completely unreachable:
- **Console cable** (serial/USB) — bypasses network entirely
- **Netinstall** — factory reset + reload firmware
- **Reset button** — hold 5s for soft reset

## Change Proposal Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. PROPOSE: I generate change script (e.g., add firewall) │
│                                                              │
│  2. SNAPSHOT: pull_config.py → "pre-change" commit           │
│                                                              │
│  3. SAFE MODE: You enable /system safe-mode                  │
│                                                              │
│  4. APPLY: You run the script via terminal/WebFig            │
│     │                                                        │
│     ├── Connection lost? → Wait 10min → auto-revert          │
│     │                                                        │
│     └── Connection OK? → Verify with pull_config.py          │
│           │                                                  │
│           ├── Working as expected? → Disable safe mode       │
│           │                                                  │
│           └── Something wrong? → Paste pre-change config     │
│                                or /import the snapshot file  │
└─────────────────────────────────────────────────────────────┘
```

## REST API Endpoints (Read-Only)

**Full config:**
```
GET /rest/config/print
```

**Sections:**
```
GET /rest/interface/print
GET /rest/ip/address/print
GET /rest/ip/firewall/filter/print
GET /rest/ip/firewall/nat/print
GET /rest/ip/dhcp-server/print
GET /rest/ip/dns/print
GET /rest/bridge/print
GET /rest/system/resource/print
GET /rest/system/health/print
GET /rest/log/print
```

**Active connections:**
```
GET /rest/ip/dhcp-server/lease/print
GET /rest/ip/arp/print
GET /rest/ip/route/print
```

## Git Commit Strategy

- **Snapshots**: `snapshots/<timestamp>.rsc` — full config export
- **Sections**: `sections/<name>.rsc` — parsed, human-readable sections
- **Proposals**: `proposals/<NNN>-<description>.rsc` — pending changes
- **Tags**: `pre-change` — always points to snapshot before last apply

## Pitfalls

1. **Safe mode timeout is ~10 minutes** — If you enable safe mode and lose connection, the router reverts after ~10 minutes. This is intentional. If your change takes longer to verify, disable safe mode manually before the timeout.

2. **REST API requires HTTPS** — RouterOS REST API only works over HTTPS (port 443). HTTP (port 80) is for the legacy web interface. Always use `https://<router-ip>/rest/...`.

3. **Read-only user cannot write** — The `read` group has no write permissions. This is intentional — we propose changes, you apply them. If you need to grant write access (not recommended), use the `write` or `full` group instead.

9. **POST method required for /print endpoints on RouterOS v7.19.x** — The REST API on RouterOS 7.19.4 (and possibly other v7.x versions) requires `POST` instead of `GET` for `/rest/*/print` endpoints. Using `GET` returns `{"error":500,"message":"Internal Server Error"}`. The `pull_config.py` script uses POST via `urllib.request.Request(url, data=b"", method="POST")`. If you switch to `requests` or `curl`, use `-X POST`.

10. **Credential variable name: `MIKROTIK_PASS` not `MIKROTIK_PASSWORD`** — The .env file uses `MIKROTIK_PASS` (not `MIKROTIK_PASSWORD`). The skill's setup section says `MIKROTIK_PASSWORD` but the actual .env uses `MIKROTIK_PASS`. The `pull_config.py` script checks both `MIKROTIK_PASS` (from .env) and `MIKROTIK_PASSWORD` (from env), preferring whichever is set. Use `MIKROTIK_PASS` for consistency.

11. **Cron snapshots via system crontab** — The periodic snapshot job uses the system crontab (`crontab -e`), not Hermes cron jobs. Entry: `0 */6 * * * /home/wahid/mikrotik-config/scripts/snapshot_cron.sh`. The `snapshot_cron.sh` script runs `pull_config.py` and stays silent when there are no changes (empty stdout = no notification for `no_agent` cron jobs).

4. **Firewall rule order matters** — When adding the API access rule, ensure it comes BEFORE any drop/reject rules. RouterOS processes firewall rules top-down.

5. **Git auto-commit can fail** — If the pull script runs while you're manually editing files in the repo, git may refuse to commit. Always commit or stash your changes before running `pull_config.py`.

6. **Large configs may timeout** — If the router has thousands of firewall rules or DHCP leases, the REST API call may timeout. Increase the HTTP timeout in the pull script or fetch sections individually.

7. **Safe mode is session-scoped** — Safe mode only applies to the current terminal/WebFig session. If you close the session, safe mode is disabled. This is why we use git snapshots as a secondary rollback mechanism.

8. **Drift detection is not real-time** — The cron job runs every 6 hours. If someone makes a change at 10 AM and the next snapshot is at 6 PM, you won't detect the drift until then. For critical configs, consider more frequent snapshots or manual checks.

12. **Never diff the raw `.rsc`/`.json` snapshots directly** — They contain counters, timestamps, and per-reboot schema noise that bury real changes. Always diff the git-tracked `sections/` files and strip volatile keys (see `scripts/diff_config.py` and `references/mikrotik-diff-noise.md`). A reboot or firmware upgrade (e.g. 7.19→7.23) produces thousands of fake "changes" — confirm the uptime/version jump first, then hunt for the few real deltas.

13. **Removing an address list does NOT remove rules referencing it** — They silently match nothing (dead, not broken). After any diff that removes an address list, grep the NEW `firewall_filter`/`firewall_nat`/`firewall_mangle`/`firewall_raw` sections for the removed `list=` name.

14. **Two static `ip service` entries can bind the same port** — RouterOS won't error, but one silently fails to bind (e.g. `reverse-proxy` and `www-ssl` both on TCP/443). After an upgrade or diff touching `ip_service`, check for duplicate static ports. **Remediation (the 7.22+ `reverse-proxy` gotcha):** `reverse-proxy` is a *default-on* service added in RouterOS 7.22 that listens on TCP/443 — exactly like `www-ssl` (WebFig). An upgrade will silently enable it and collide with WebFig. The correct fix is to **disable `reverse-proxy`** (`/ip service disable [find name=reverse-proxy]`), NOT www-ssl — your live WebFig session rides www-ssl. Only do this after confirming zero `/ip/reverse-proxy` instances exist (the service is idle otherwise). See `references/mikrotik-hardening-review.md`.

15. **`pull_config.py` NOW captures IPv6 — the IPv4-only blind spot is FIXED (2026-07-12).** Added 13 `ipv6-*` endpoints to the SECTIONS tuple (ipv6_address, ipv6_dhcp_client, ipv6_firewall_filter/nat/mangle/raw/addr_list, ipv6_nd(+prefix), ipv6_pool, ipv6_route, ipv6_settings, ipv6_dhcp_server(+binding)). Snapshots and `git diff` now include full v6 state. Live-probing is still the right move for *verification* right after a change (lease tables/counters are runtime, not config), but the config blind spot is gone. Do not re-add the old "IPv4-only" warning.

16. **Manual `/ipv6 nd prefix` entries stick at `invalid=true` and won't self-heal when you flip the address `advertise` flag.** Symptom: SLAAC clients on a VLAN get no ULA address even though the `/ipv6 address` exists with `advertise=yes`. RouterOS marks a manually-created ND prefix `invalid` when the underlying address had `advertise=no` at creation; flipping `advertise` on the address later does NOT re-validate the manual prefix (confirmed on 7.23.2 — `advertise=yes` alone does nothing). The auto-derived prefix on the master bridge stays valid because it was never manually created. Fix: `remove [find where interface=vlanXX]` the manual entries and let RouterOS auto-derive valid prefixes; if they don't reappear in a few seconds, re-add them fresh (forces re-validation). Full remediation in `references/mikrotik-ipv6-audit.md`.

17. **`ipconfig /release6` does NOT clear a SLAAC-cached address — only DHCPv6 IA_NA leases.** If a client still shows an old ULA after you removed the server that issued it, check type with `netsh interface ipv6 show addresses`: `Public` = SLAAC (RA-cached, lifetime up to 4w2d), `DHCP` = IA_NA. For a `Public`/stale SLAAC address, `netsh interface ipv6 delete address "<adapter>" <addr>` or disable+re-enable the adapter (flushes cached RAs + leases). Router-side tell: if NO `/ipv6 dhcp-server` or `ipv6 pool` serves that prefix anymore, the address is residual — no router change clears it. Don't burn a release6/renew6 cycle on a SLAAC ghost.

18. **Partial firewall-rule field dumps produce FALSE security holes — the #1 cause of "there's a firewall hold" misreads.** When probing `/ipv6 firewall filter print` (or v4) via REST, dump the ENTIRE rule object, never a hand-picked key subset. Two real false positives this session, both from printing only some keys:
  - A rule that prints `in-interface=None` but actually has `in-interface-list=LAN` looks like an empty-matcher "accept everything" → you wrongly conclude the input chain is wide open. Always include `in-interface-list`, `src-address-list`, `dst-address-list` in your probe key list.
  - A `protocol=tcp action=drop` rule with NO `dst-port` looks like "drops all TCP" (web/SSH blocked) → you wrongly conclude the forward chain is broken. But it may match on `tls-host` (SNI/L7 DoH/DoT blocking: `tls-host=*doh*`, `*dot.*`, `*one.*`) — correct and inert (0 packets). Always include `tls-host`, `dst-port`, `connection-state`, `src-address`, `dst-address`.
  Rule of thumb: before reporting ANY firewall hole, print the full rule JSON (every field) and confirm. A "hole" that vanishes once you see `in-interface-list` or `tls-host` was never real. See `references/mikrotik-ipv6-nd-client-diagnosis.md` for the exact full-field probe key list.

19. **ND prefix `invalid` flags FLAP, and "delete prefix before adding the ND interface entry" leaves the VLAN with NO prefix at all.** Refines pitfall 16. The robust ND fix has a strict ORDER: (1) ADD the `/ipv6 nd` *interface* entry FIRST (so RAs fire), THEN (2) remove the static `/ipv6 nd prefix` entries so RouterOS auto-derives dynamic+valid prefixes. Observed this session:
  - Without a parent ND interface entry, static prefix entries FLIP between valid/invalid across polls — the `invalid` state is unstable; never trust a single "valid" reading.
  - Diagnosis correlation: EVERY interface that has an `/ipv6 nd` interface entry has valid prefixes; EVERY one without has invalid/flapping ones (bridge + vlan100 had entries → valid; vlan90/101/200 had none → invalid).
  - Doing it BACKWARDS bites: deleting the static prefix BEFORE the ND interface entry exists, with the address at `advertise=no` (or `advertise=yes` but not yet auto-derived), leaves the interface with NO prefix — confirmed live AND in the committed snapshot (vlan90 prefix absent after the "remove static prefixes" step ran before the ND interface entry was added). Fix: `/ipv6 nd prefix add interface=vlan90 prefix=fd00:cafe:beef:90::/64 autonomous=yes on-link=yes` (valid only because the ND interface entry now exists).

20. **Windows "no IPv6 after adapter reset" is almost always CLIENT-side, not a router firewall hold.** Verify before blaming the router. Check the router-side DHCPv6 binding list for the client's DUID (match by its `fe80::` link-local, visible via `ipconfig`/`netsh`). If OTHER clients on the same VLAN are bound (getting global/ULA leases) but the target box's DUID is ABSENT with no recent `last-seen`, the router is fine and the box isn't soliciting. Confirm the IPv6 forward chain permits that VLAN: ICMPv6 accept + established/related + LAN→WAN/inter-VLAN (a VLAN in the `LAN` interface list is permitted everywhere). Client-side checklist:
  - `netsh interface ipv6 show interfaces` → Router Discovery = **enabled** on the adapter.
  - `ipconfig /all` → IPv6 ticked in adapter properties; a `fe80::` link-local present (proves RA reached it).
  - `netsh int ipv6 reset` does NOT fully apply until **reboot** — the classic "reset → no IPv6" cause. Reboot before concluding the router is at fault.

21. **The per-snapshot `.rsc` in `snapshots/` is a REFERENCE DUMP, NOT `/import`-able.** `pull_config.py` writes a comment-style file (`# [1] ...` + indented `key=value` with NO command verb). If you tell the user to `/import` it, RouterOS rejects it. The footer now says so. The AUTHORITATIVE importable backup is the router's own `/export` (full config) — via WebFig (Files → `/export` button) or SSH `ssh jarvis-ro@192.168.100.1 "/export" > backups/name.rsc`. Full strategy + JSON-derived partial-rsc fallback in `references/mikrotik-importable-backup.md`.

22. **REST `/export` returns `[]` (or "no such command") on RouterOS 7.23.2 — NOT exposed over REST.** Don't waste a call on `/rest/export`. To get the full importable config use SSH `/export` (read-only `jarvis-ro` user + key) or WebFig. REST remains perfect for live *verification* (`print` endpoints), just not for export.

23. **Trust `MIKROTIK_HOST` from `.env`, never the router IP from conversation context.** Context notes like "WebFig via Hermes host on port 32822" or a `.52` address are often stale or refer to the Hermes box, NOT the router (router is `192.168.100.1`). This session burned 4 SSH attempts against `.52` (the Hermes host) before the real target `.100.1` worked. Always read `MIKROTIK_HOST` from `.env` for any SSH/REST target.

24. **`/ipv6 settings disable-link-local-address` changes require a REBOOT to take effect AND to show in `/export`.** Setting `no` in WebFig updates the stored value, but the running state (and the `/export` line) only flips after reboot — a re-pull may still show `yes`, which is expected pre-reboot, not a failed apply. When GENERATING a backup, force-encode `disable-link-local-address=no` so the artifact is correct regardless of pending-reboot state (otherwise a restore re-introduces the bug and breaks DHCPv6-PD + ND after reboot). With `=yes`, link-local addresses do NOT regenerate after reboot → PD/ND break. Treat `=no` as mandatory.

## Config Diff (Noise-Aware) — "what changed since?"

A raw diff between two `.rsc`/`.json` snapshots is **useless**: 90%+ of lines
are reboot counter resets and RouterOS firmware schema churn. Diff the
git-tracked `sections/` instead, and strip volatile keys.

**Quick path — use the bundled script:**

```bash
python3 ~/.hermes/skills/devops/mikrotik-router-management/scripts/diff_config.py
# or: python3 scripts/diff_config.py 2026-07-11T230001Z 2026-07-12T022537Z
```

It strips reboot/upgrade noise and skips pure-runtime sections, printing only
real config deltas. Field-by-field noise profile (incl. 7.19→7.23 schema diffs)
lives in `references/mikrotik-diff-noise.md`.

**Manual path (when you need finer control):**

1. Identify the two snapshot commits:
   ```bash
   git log --oneline -- snapshots/*.rsc | head
   ```
2. Find which `sections/` files changed:
   ```bash
   git diff --name-only <old_commit> <new_commit> -- sections/
   ```
3. Diff each critical section, filtering out volatile keys:
   ```bash
   git diff <old> <new> -- sections/firewall_filter.rsc | grep -E '^[+-]' | grep -vE 'bytes=|packets=|disabled=|dynamic=|invalid='
   ```
4. **Always verify these two upgrade side-effects manually:**
   - **Dangling address-list refs:** if an address list was removed, grep the
     NEW sections for the removed `list=` name. Rules pointing at a missing
     list silently match nothing (dead, not broken).
   - **Static service port collisions:** two static services can bind the same
     port (e.g. `reverse-proxy` and `www-ssl` both TCP/443). Check
     `sections/ip_service.rsc` for duplicate static ports.
5. **Reboot/upgrade signature** (verify before reading the diff): `uptime`
   reset, `version`/`current-firmware` jump, `last-link-up-time` collapse, and
   byte counters near zero all mean the delta is mostly noise. See
   `references/mikrotik-diff-noise.md` for the full field map.

### Post-diff review checklist
- [ ] Identify whether a reboot/upgrade caused the bulk of the noise
- [ ] Confirm any removed firewall address list isn't still referenced by rules
- [ ] Check `ip_service` for static port collisions introduced/left by upgrade
- [ ] Note DNS `dynamic-servers` (IPv6 DNS) changes after upgrade
- [ ] SSH auth setting rename (`always-allow-password-login` → `password-authentication`) is cosmetic, not a regression

## Config Hardening Review (find high-impact fixes)

When asked to "review the config", "surface high-impact fixes", or "audit
router security", work through the checklist in
`references/mikrotik-hardening-review.md`. It captures the recurring findings
with exact remediation commands:

1. **Management-plane exposure** — admin services (ssh/winbox/www-ssl/api)
   bound to `192.168.0.0/16` or empty `address=` are reachable from guest/IoT
   VLANs. Bind to the management VLAN only.
2. **DNS-intercept coverage gaps** — NAT redirect-to-router rules on port 53
   that cover only a `/25` while the subnet is a `/24` let half the VLAN bypass
   your entire DoH/DoT/torrent filtering. Extend the `src-address` to the full
   subnet.
3. **Missing IPv6 firewall** — if DNS/`use-ipv6=yes` is configured but there's
   no `/ipv6 firewall`, every IPv4 protection is wide open on v6 the moment dual
   stack flips on. Add a baseline v6 filter before v6 is assigned.

The reference also documents the `reverse-proxy` default-on 443 collision and
its remediation.

## Verification Checklist

After applying a change:
- [ ] Pull latest config: `python3 scripts/pull_config.py`
- [ ] Verify the change is visible in the new snapshot
- [ ] Test the affected service (e.g., ping through new firewall rule)
- [ ] Check logs for errors: `GET /rest/log/print?topic=system`
- [ ] Disable safe mode if everything works: `/system safe-mode` (toggle off)

## References

- `references/mikrotik-ipv6-nd-client-diagnosis.md` — FULL-field firewall probe pattern (kills false "hole" reports), ND-interface-vs-prefix `invalid` root cause + correct remediation ORDER, and Windows "no IPv6 after reset" client-side diagnosis
- `references/mikrotik-rest-api-endpoints.md` — Full list of REST API endpoints and response formats
- `references/mikrotik-change-proposals.md` — Archive of applied change proposals with outcomes
- `references/mikrotik-diff-noise.md` — Field-by-field reboot/upgrade noise profile (7.19→7.23 schema map, volatile key list)
- `references/mikrotik-ipv6-audit.md` — IPv6 audit + ULA/NAT66 hardening: live-probe verification (still needed for runtime state — ND `invalid` flags, NAT counters, leases), v6 firewall hole classes, baseline v6 filter, and two runtime-only traps (manual ND prefix stuck `invalid=true`; stale SLAAC ULA that `release6/renew6` can't clear)
- `references/mikrotik-hardening-review.md` — Structured config-hardening review: management-plane exposure, DNS-intercept gaps, missing IPv6 firewall, reverse-proxy 443 collision + exact remediation commands
- `scripts/diff_config.py` — Automated noise-aware config diff between two snapshots
- `references/mikrotik-importable-backup.md` — Why the snapshot `.rsc` is NOT `/import`-able, the authoritative `/export` backup method (WebFig + SSH), read-only SSH setup, and the JSON-derived partial-rsc fallback pattern