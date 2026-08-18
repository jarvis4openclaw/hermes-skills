---
name: mikrotik-ipv6-nd-prefix-invalid
description: Diagnose and fix MikroTik RouterOS /ipv6 nd prefix entries stuck at invalid=true (no SLAAC, no RA). Covers the ND-interface-entry vs static-prefix gotcha, the address advertise flag, and the flapping-prefix symptom. Use when a VLAN/bridge subnet has no ND prefix, hosts don't get IPv6, or prefixes flip valid/invalid across re-probes.
version: 1.1.0
metadata:
  hermes:
    tags: [mikrotik, routeros, ipv6, nd, slaac, ra, prefix, invalid, dhcpv6]
    trigger_conditions:
      - "ipv6 nd prefix invalid"
      - "no SLAAC on MikroTik"
      - "hosts not getting IPv6"
      - "VLAN has no ND prefix"
      - "prefix flapping valid invalid"
      - "MikroTik IPv6 Router Advertisement not sent"
      - "advertise flag RouterOS"
      - "dhcp-server-v6 stale value"
      - "MikroTik IPv6 static prefix orphaned"
      - "dynamic prefix not derived RouterOS"
---

# MikroTik IPv6 ND prefix invalid=true — the flapping gotcha

## When to Use

- `/ipv6 nd prefix print` shows `invalid=true` (or the flag flaps) on a VLAN/bridge interface.
- A host isn't getting an IPv6 address via SLAAC on a subnet that has an address assigned.
- A WAN DHCPv6 client is stuck `searching...` with a stale-looking `dhcp-server-v6` value.

## Not For

- **IPv6 routing/bridging config beyond ND** → use `mikrotik-router-management` / `mikrotik-routeros-gotchas`.
- **General RouterOS admin** (users, firewall, backup) → use `mikrotik-user-work-style` / `mikrotik-router-management`.
- **DHCPv6 client on other vendors** (Ubiquiti, OpenWrt) → this is RouterOS-specific.

## Trigger
`/ipv6 nd prefix print` shows `invalid=true` (or the flag flaps between valid/invalid across
re-probes) on a VLAN or bridge interface, OR a host isn't getting an IPv6 address via SLAAC on a
subnet that has a ULA/global address assigned.

## Root cause
RouterOS only sends Router Advertisements (RAs) on interfaces that have an **`/ipv6 nd` interface
entry**. A manual (static) `/ipv6 nd prefix` entry for an interface that has NO corresponding
`/ipv6 nd` interface entry is orphaned → RouterOS marks it `invalid=true` and never advertises it.
Because validity is continuously re-evaluated, an orphaned static prefix may **flap** (valid one
probe, invalid the next) — that flapping is the classic symptom of a missing ND interface entry,
not bad prefix syntax.

Second cause: if the `/ipv6 address` on the interface has `advertise=no`, RouterOS will NOT
auto-derive a *dynamic* ND prefix from it even after you add the ND interface entry. Static entries
are unaffected by this flag, but dynamic derivation needs `advertise=yes`.

## The robust fix (do BOTH steps)
1. **Add the missing `/ipv6 nd` interface entry** so RAs flow:
```
/ipv6 nd
add interface=<iface> managed-address-configuration=yes other-configuration=yes advertise-dns=yes dns=2620:fe::fe,2606:4700:4700::1001
```
(M=yes → DHCPv6 address; O=yes → DHCPv6 other/options; advertise-dns + DNS = RDNSS.)

2. **Then either:**
   - **Keep the static prefix** — it becomes valid once the ND interface entry exists. Verify
     `ipv6 nd prefix print` shows `invalid=false` for that interface. OR
   - **Delete the static prefix and let RouterOS derive it dynamically** — BUT only works if the
     interface's `/ipv6 address` has `advertise=yes`. Without that, no dynamic prefix appears and
     the subnet regresses to having NO prefix at all:
```
/ipv6 nd prefix remove [find where interface=<iface>]
```
     Then confirm a new entry appears with the `D` (dynamic) flag and no `I`.

## Verification
- `ipv6 nd print` — interface present in the ND interface list.
- `ipv6 nd prefix print` — every interface with an ND entry shows `invalid=false`; ideally
  `dynamic=yes` (D flag) when using auto-derivation.
- `ipv6 address print` — `advertise=yes` on the subnet address if relying on dynamic prefixes.
- `ipv6 dhcp-server binding print` — clients on that subnet getting leases = real proof RAs + DHCPv6 deliver.

## Pitfalls
1. **Do NOT delete a static prefix unless the address has `advertise=yes`** — otherwise the subnet has no ND prefix at all (regression, not fix). This bit vlan90: the static prefix was deleted but `advertise=no` on the address prevented re-derivation.
2. **`advertise=yes` on the address does NOT validate a static prefix** — it only governs dynamic derivation. Don't conflate the two.
3. **The `invalid` flag can flap during the re-evaluation window** — between adding the ND entry and RouterOS re-evaluating, the flag may still read invalid. Re-probe AFTER the interface entry is present, not before.
4. **Adding the ND interface entry alone won't fix a malformed prefix entry** — but in practice the missing ND entry is the cause; verify `invalid=false` after adding it before suspecting syntax.
5. **`dhcp-server-v6` is READ-ONLY — do not chase it as a lock** — a stale-looking value (e.g. `fe80::1111:1111:1111:1111`) is a mirror of the last upstream server heard from; RouterOS 7.23.2 has NO `dhcp-server-v6` parameter on `set`. It means the upstream went silent; fix upstream (modem/ISP) + `release`/`renew`. See the `mikrotik-routeros-gotchas` skill reference for full detail.
6. **Missing ND interface entry is the #1 cause — check the correlation rule first** — every interface WITH an `/ipv6 nd` interface entry has valid prefixes; every interface WITHOUT has invalid ones (or none). If you see `invalid=true` and the interface isn't in `ipv6 nd print`, that's your cause — full stop.
7. **Verify with DHCPv6 leases, not just flags** — `ipv6 dhcp-server binding print` showing clients on that subnet is real proof RAs + DHCPv6 deliver; flag prints alone can lie during propagation.

## RELATED GOTCHA — "dhcp-server-v6" is NOT a settable lock (do not chase it)
When an ether2 (WAN) DHCPv6 client is stuck `searching...`, the live print may show a
`dhcp-server-v6` value that looks like a stale pin (e.g. `fe80::1111:1111:1111:1111`). It is
**READ-ONLY** — a mirror of the last server heard from. In RouterOS 7.23.2 there is **no
`dhcp-server-v6` parameter on the `set` command** (the user will not find it in tab-complete). A
stale value means the upstream server went silent; it is NOT a config lock you can clear. Do NOT
advise "unpin dhcp-server-v6". The fix is upstream (modem/ISP) + `release`/`renew`. Full detail in
the `mikrotik-routeros-gotchas` skill (`references/dhcpv6-client-gotchas.md`).

## Correlation rule (fast diagnostic)
Across live probes: **every interface WITH an `/ipv6 nd` interface entry has valid prefixes; every
interface WITHOUT has invalid ones (or none).** If you see `invalid=true` and the interface isn't in
`ipv6 nd print`, that's your cause — full stop.
