---
name: mikrotik-routeros-gotchas
description: Recurring MikroTik RouterOS operational gotchas that silently break connectivity or config across reboots — interface-list auto-classification (Detect Internet), DHCPv6-PD failures, DoH "remote disconnected" errors, and ND prefix invalid flags. Use when VLANs/interfaces land in wrong interface list after reboot, DoH errors appear for any provider, boot-time behavior diverges from running config, or DHCPv6 client is stuck "searching...". Diagnose from LIVE state, never from memory of the config.
version: 1.1.0
metadata:
  hermes:
    tags: [mikrotik, routeros, networking, gotchas, homelab]
    trigger_conditions:
      - "VLAN landed in the wrong interface list after reboot"
      - "DoH server connection error: remote disconnected"
      - "DHCPv6 client stuck searching"
      - "IPv6 ND prefix invalid flag"
      - "boot behavior diverges from running config"
      - "interface shows dynamic=true WAN detected"
      - "MikroTik lost outbound connectivity after reboot"
      - "Detect Internet moved my VLAN to WAN"
      - "no SLAAC or IPv6 flapping on RouterOS"
      - "dhcp-server-v6 is read-only"
      - "MikroTik silently breaking config"
      - "router reboot broke VLAN egress"
---

# MikroTik RouterOS operational gotchas

Target: hEX / RouterOS 7.x homelab. Diagnose by reading **LIVE** state (REST API), never from
memory of the saved config. See `scripts/mt_rest_probe.py` for a generic probe harness and
`references/` for per-gotcha detail.

## When to Use

- A VLAN/interfaces land in the wrong interface list right after a router reboot (silent egress loss).
- `dns,error DoH server connection error: remote disconnected while in HTTP exchange` appears for any provider.
- The DHCPv6 client is stuck `searching...` with no prefix delegation.
- An IPv6 ND prefix shows `invalid=true` or SLAAC flaps after boot.
- Any boot-time behavior that diverges from the saved config, or a `dynamic=true` interface list member with a `"WAN detected"` / `"LAN detected"` comment.
- Before blaming the saved config for a problem — verify whether the LIVE state is what you think it is.

## Not For

- **Configuring the router from scratch or day-to-day administration** → use `mikrotik-router-management` instead
- **A dedicated deep-dive on the ND prefix invalid flag** → use `mikrotik-ipv6-nd-prefix-invalid` instead
- **Working style / how the operator prefers to manage the MikroTik** → use `mikrotik-user-work-style` instead
- **Diagnosing why the DHCPv6 client got a PD but VLANs lost address/DNS delivery** → check `mikrotik-routeros-gotchas` Gotcha 3, but the ND companion skill covers the prefix side
- **Reading live config via REST when you just need a quick status** → `mikrotik-router-management` covers the read-only probe pattern

## Gotcha 1 — Detect Internet dumps VLANs into WAN at reboot (silent outbound loss)
Full detail: `references/detect-internet-wan-misfire.md`.

- **Symptom:** after a reboot, a VLAN (e.g. vlan90) loses all outbound connectivity even though the
  config "looks right".
- **Root cause:** `/ip/detect-internet` left enabled (defconf default sets `detect-interface-list=all`).
  At every boot it re-monitors ALL interfaces and dynamically re-classifies them into WAN/LAN lists
  via heuristics, and misfires — adding e.g. `vlan90 → WAN` with `dynamic=true`, comment **"WAN
  detected"**. The firewall's `drop in-interface-list=WAN` then kills that VLAN's egress.
- **Proof (live):** `/interface list member print` shows the interface with `dynamic=true` and
  comment **"WAN detected"** (or "LAN detected" for `lo`). Those exact comment strings are Detect
  Internet's signature — nothing else produces them. A defconf re-run does NOT cause this (defconf
  only fires on *reset*, not reboot), so don't chase that theory.
- **Fix:** `/ip/detect-internet set detect-interface-list=none`. The dynamic members are *owned by
  the service* and auto-remove; the correct static membership (vlan90→LAN) then applies.
- **WebFig:** IP → Detect Internet → Detect Interface List = `none`.
- **Verify:** `/interface list member print where dynamic` → empty after disable + reboot.

## Gotcha 2 — IPv6 ND prefix stuck invalid=true (no SLAAC / flapping)
Covered in depth by the dedicated `mikrotik-ipv6-nd-prefix-invalid` skill. Quick version: a static
`/ipv6 nd prefix` on an interface with NO `/ipv6 nd` interface entry is orphaned → `invalid=true`,
may flap. Add the ND interface entry; keep the static prefix (it validates) OR delete it only if the
address has `advertise=yes` (else no prefix at all).

## Gotcha 3 — DHCPv6 client "searching..." forever (no PD)
Full detail: `references/dhcpv6-client-gotchas.md` (companion to the ND skill). Key points:
- The `dhcp-server-v6` field shown in live `ipv6/dhcp-client/print` is **READ-ONLY** — it mirrors the
  last server heard from. In 7.23.2 you CANNOT `set` it; there is no `dhcp-server-v6` parameter on the
  `set` command. A "stale" value (e.g. `fe80::1111:1111:1111:1111`) means the upstream server went
  silent — it is NOT a config lock you can clear. Do not advise "unpinning" it.
- SOLICIT to `ff02::1:2` with NO Advertise/Reply in debug logs = ISP/modem-side failure. Fix upstream
  (power-cycle modem, call ISP). Then `/ipv6 dhcp-client release` + `renew` (or disable/enable) to
  re-solicit. PD return auto-recreates the global ND prefix on dependent VLANs and resumes DHCPv6
  server bindings.
- Ignore `dhcp,debug received discover ... blocked lease` lines — that's your own IPv4 DHCP server
  seeing a modem broadcast (red herring).
- WARNING: disabling the DHCPv6 *server* list (e.g. `novos-ipv6`) separately stops address/DNS
  delivery to VLAN clients even after PD returns — re-enable it.

## Gotcha 4 — DoH "remote disconnected while in HTTP exchange" (all providers)

Full detail: `references/doh-disconnected-gotcha.md`.

- **Symptom:** RouterOS logs show `dns,error DoH server connection error: remote disconnected while in HTTP exchange`. TLS handshake completes, server drops connection mid-HTTP request.
- **Root cause:** Cross-provider issue — NOT HTTP/3 or provider-specific. Three classes:
  - **Class A: Certificate chain** — RouterOS CA bundle doesn't include the provider's intermediate. Quick test: `set verify-doh-cert=no`. If error stops, import the correct root CA and re-enable.
  - **Class B: Path routing** — RouterOS appends `?dns=<base64>` to the DoH URL. Some path handlers (e.g. `/p2` vs `/dns-query`) may reject it. Try subdomain form or standard `/dns-query` endpoint.
  - **Class C: Anycast node behaviour** — Intermittent drops from aggressive connection handling. Test with known-good baseline (Quad9 `https://dns.quad9.net/dns-query`).
- **Diagnostic order:** (1) verify-doh-cert=no, (2) switch to Quad9, (3) switch provider URL format.
- **Control D specifics:** `https://freedns.controld.com/p2` is a valid DoH endpoint (HTTP/1.1+2). QUIC variant exists but RouterOS doesn't support it. Not an HTTP/3 issue.

## Live diagnosis pattern (the discipline)
1. Pull a fresh config snapshot (git-tracked) before changing anything.
2. Probe LIVE via REST (see `scripts/mt_rest_probe.py`): interface list members, nd prefixes,
   dhcp-client status, addresses, neighbors.
3. Identify `dynamic=true` members and their **comments** — they reveal auto-managed state you did
   not configure. This is how you catch Detect Internet, not a saved-config review.
4. Correlate: invalid flags, empty pools, 0 bindings = downstream of an upstream failure (e.g. no PD
   → no global prefix → no DHCPv6 leases on the global VLAN).
5. Fix at the **ROOT** (the service/config that creates the bad state), not the symptom. Deleting a
   dynamic entry you don't own just gets recreated at next boot.

## Pitfalls

1. **Trusting the saved config instead of live state** — RouterOS diverges from the saved config on boot (Detect Internet re-classification, orphaned ND prefixes, DHCPv6 client state). Always probe LIVE via REST before concluding anything. Recovery: run `scripts/mt_rest_probe.py` and inspect `dynamic=true` members and comments first.
2. **Chasing defconf as the reboot culprit** — defconf only fires on *reset*, not on reboot. If VLANs land in the wrong interface list after a reboot, it's Detect Internet, not defconf. Recovery: check `/ip/detect-internet set detect-interface-list=none` and look for `"WAN detected"` comments.
3. **Deleting dynamic entries you don't own** — A `dynamic=true` member created by Detect Internet gets recreated at every boot. Deleting it fixes nothing. Recovery: disable the owning service (`detect-interface-list=none`), then remove the dynamic member.
4. **Advising the user to "unpin" a stale `dhcp-server-v6` value** — In RouterOS 7.23.2 the field is READ-ONLY; there is no `dhcp-server-v6` parameter on `set`. A stale value means the upstream server went silent, not a config lock. Recovery: fix upstream (power-cycle modem, call ISP), then `/ipv6 dhcp-client release` + `renew`.
5. **Ignoring `dns,error DoH ... remote disconnected` as provider-specific** — It's cross-provider: three classes (cert chain, path routing, anycast behaviour). Recovery: test `verify-doh-cert=no`, then a known-good baseline (Quad9), then provider URL format — in that order.
6. **Disabling the DHCPv6 *server* list while debugging the client** — Stopping `novos-ipv6` separately halts address/DNS delivery to VLAN clients even after PD returns. Recovery: re-enable the server list after fixing the client side.
7. **Treating `invalid=true` ND prefix as a config error to delete** — An orphaned static prefix with no `/ipv6 nd` interface entry flaps. Recovery: add the ND interface entry; keep the static prefix (it validates) or delete it only if the address has `advertise=yes`.
8. **Interpreting `dhcp,debug received discover ... blocked lease` as a fault** — That's your own IPv4 DHCP server seeing a modem broadcast — a red herring. Recovery: ignore it and keep looking at the IPv6 client log.
9. **Fixing the symptom instead of the root service** — Patching a dynamic entry or a child state gets reverted at next boot. Recovery: fix at the ROOT — the service/config that creates the bad state (Detect Internet, ND interface entry, DHCPv6 server list).
10. **Skipping the fresh config snapshot before changing anything** — Without a git-tracked baseline you can't tell whether your change or boot-time classification caused a regression. Recovery: pull a fresh snapshot first, then probe live, then change.

## Verification
- Re-probe live after the change; confirm the bad dynamic entry is gone and static membership holds
  across a reboot.
- For PD: confirm the pool repopulates and dependent VLAN prefixes/bindings resume.
