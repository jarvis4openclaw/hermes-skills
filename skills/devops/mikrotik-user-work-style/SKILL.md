---
name: mikrotik-user-work-style
description: Working style and preferences for managing MikroTik RouterOS hEX (ROS 7.23.2) with this user. Apply whenever the user asks for RouterOS config review, IPv6 changes, firewall fixes, or MikroTik troubleshooting. Use to avoid proposing unvalidated commands or making live changes.
version: 1.1.0
metadata:
  hermes:
    tags: [mikrotik, routeros, work-style, preferences]
    trigger_conditions:
      - "Review or fix MikroTik RouterOS config"
      - "Change IPv6 / firewall on the hEX router"
      - "Troubleshoot MikroTik connectivity or routing"
      - "Propose RouterOS commands for the user to run"
      - "Inspect ~/mikrotik-config or pull RouterOS config"
      - "Ask how to present RouterOS findings"
      - "Reference the user's RouterOS setup (vlan100, ULA, NAT66)"
---

# MikroTik RouterOS — user work style and constraints

## Execution model
- **Assistant is read-only.** The user applies ALL changes themselves via WebFig or terminal.
- Do NOT attempt to execute live RouterOS configuration writes. REST API probes for inspection only.

## Required pre-analysis ritual
1. **Take a fresh snapshot first** using `python3 scripts/pull_config.py` in `~/mikrotik-config`.
2. **Validate all proposed commands against running firmware** (currently RouterOS 7.23.2) before giving them to the user. If unsure, say so and ask the user to check `?` help or tab-completion on the device.
3. **Read the relevant section files** under `~/mikrotik-config/sections/` after the pull, then correlate with live probes if needed.

## Review / fix style
- Present findings **ranked by severity** (critical → high → medium → low).
- Give exact CLI commands the user can paste, plus the WinBox menu path when the CLI path is non-obvious or the user prefers GUI.
- Explain **why** a setting is wrong and what will break if left unchanged.
- Mention when a fix is **optional** vs. **required**.

## Design intent to preserve
- **vlan100** gets a **global IPv6 prefix** from ISP delegated `/56` (pool `novos-pool6`).
- **bridge, vlan90, vlan101, vlan200** use **ULA `fd00:cafe:beef::/48`** with **NAT66 masquerade** to WAN.
- DNS filtering: IPv4 via redirect address list; IPv6 redirected to CleanBrowsing (UDP + TCP).

## When to Use
- Any RouterOS config review or change request (IPv6, firewall, routing, DNS).
- Before proposing CLI commands the user will paste into WebFig/terminal.
- When interpreting `~/mikrotik-config` snapshots or live REST API probes.
- When the fix involves the vlan100/vlan90/vlan101/vlan200 topology or ULA/NAT66 design.

## Not For
- **Reading router state via the REST API for reporting** → use `mikrotik-router-management` (read-only API queries + git versioning).
- **IPv6 ND prefix invalid / SLAAC troubleshooting** → use `mikrotik-ipv6-nd-prefix-invalid` (dedicated diagnosis flow).
- **Recurring silent gotchas (interface-list, DHCPv6-PD, DoH, ND flags)** → use `mikrotik-routeros-gotchas` (broad operational failures).
- **Applying changes directly to the router** → this skill is read-only-by-design; hand commands to the user, never execute writes.

## Known traps verified on ROS 7.23.2
- `/interface detect-internet` is the v7 path; `/ip/detect-internet` is v6 and does NOT exist. Disable via `detect-interface-list=none`. The REST API does not expose this menu. Detect via dynamic list members with comments "WAN detected" / "LAN detected".
- ND prefixes become `invalid=true` when the interface has no `/ipv6 nd` interface entry. Static prefixes must not be deleted unless the address has `advertise=yes` (dynamic re-derivation won't happen otherwise).
- `disable-link-local-address=true` in IPv6 settings breaks DHCPv6-PD behavior on WAN.
- The `dhcp-server-v6` field on a DHCPv6 client is **read-only** in ROS 7.23.2 — not settable.
- `tls-host` matching (firewall) is inherently fragile for DNS blocking. Use port-based rules for DoH (tcp 443 to known IPs) and DoT (tcp 853) instead.
- Forward chain DNS/QUIC blocks with no source/destination scoping will kill legitimate traffic once IPv6 flows — scope with `in-interface-list=LAN` or place after the `established,related` accept.

## Pitfalls
1. **Proposing write commands without a fresh snapshot** — Config may have drifted since the last pull. Always run `python3 scripts/pull_config.py` in `~/mikrotik-config` first and review the updated `sections/` files before recommending anything.
2. **Assuming the assistant may apply changes** — This user applies all RouterOS changes themselves. Never execute live config writes; present paste-ready commands instead.
3. **Quoting v6 paths on ROS 7.23.2** — `/ip/detect-internet` does not exist on v7; using it produces a confusing "no such command" error. Use `/interface detect-internet` and `detect-interface-list=none`.
4. **Deleting static ND prefixes blindly** — If the interface lacks an `/ipv6 nd` entry the prefix goes `invalid=true`; deletion without `advertise=yes` prevents dynamic re-derivation. Verify the ND interface entry before touching prefixes.
5. **Enabling `disable-link-local-address`** — Breaks DHCPv6-PD on WAN. Keep it disabled (false) unless the user explicitly wants it.
6. **Trying to set `dhcp-server-v6`** — Read-only in ROS 7.23.2. Any proposed set command will fail; plan around it.
7. **Unscoped DNS/QUIC firewall rules** — Blocks without `in-interface-list` scoping kill legitimate traffic once IPv6 flows. Scope or place after `established,related` accept.
8. **Suggesting `tls-host` matching for DoH/DoT blocking** — Fragile and version-dependent. Use port-based rules (tcp 443 to known DoH IPs, tcp 853 for DoT) instead.
9. **Overriding the user's design intent** — Preserve vlan100 global IPv6 (pool `novos-pool6`) and ULA `fd00:cafe:beef::/48` + NAT66 for the other VLANs; propose changes within this topology unless the user asks to redesign it.
10. **Presenting findings without severity ranking** — The user expects critical → high → medium → low ordering with exact CLI + WinBox path and a clear required-vs-optional label on each fix.
