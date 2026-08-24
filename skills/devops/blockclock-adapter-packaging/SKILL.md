---
name: blockclock-adapter-packaging
version: 1.1.0
author: jarvis
license: MIT
description: "Build/troubleshoot the StartOS Blockclock Adapter s9pk."
metadata:
  hermes:
    tags: [blockclock, startos, start9, coinkite, bitcoin]
    trigger_conditions:
      - "blockclock"
      - "coinkite"
      - "BLOCKCLOCK"
      - "s9pk startos blockclock"
      - "blockclock adapter"
      - "clock shows wrong value"
      - "start9 blockclock package"
      - "push to blockclock"
      - "blockclock 429"
      - "blockclock pair parameter"
---

## When to Use

Building/updating the `.s9pk` package, troubleshooting push failures (400/429), understanding BLOCKCLOCK firmware API constraints (v1.2.3).

## Not For

- Generic StartOS service packaging (different manifest shape, lifecycle, SDK version) → use `startos-service-packaging` instead
- Building a StartOS package from scratch for a different service (the Blockclock adapter has its own manifest, metrics config, and firmware constraints) → use `startos` instead
- Flashing or re-flashing the physical BLOCKCLOCK firmware — the adapter only pushes display data via the HTTP API
- Network isolation / firewall debugging on the Start9 LAN — the adapter talks to a fixed local clock IP; connectivity is a Start9/homelab concern, not the adapter

## Firmware API Constraints (v1.2.3, Empirically Probed)

**Push endpoint:** `GET /api/show/number/<val>?tl=<l>&br=<l>&pair=<l>` or `/api/show/text/<txt>` for hashrate.

| Param | Rules | Example |
|-------|-------|---------|
| `tl` / `br` | Any printable; spaces, parens fine | `sats/USD` |
| `pair` | **No spaces** (400). Plain words max 4 chars. Slash pairs exempt. Verified: BLK/H, AGE, FEE, BTC/USD, SAT/USD, F/N9 | `FEE` |

Branding `(Start9)` goes in `tl`/`br`. `pair` must be space-free.

**Rate limiting:** global across ALL endpoints. Occasional 429 is normal — status polls (3s) and pushes (60s+) share same budget. Retries next cycle.

**Button advance error:** with Data Backend = `127.0.0.1`, middle-right press briefly shows "Network connection problem" — press wakes dead backend pull. Adapter replaces within ~10-40s. Cosmetic.

## Metrics and Display

| # | Metric | `tl` | Main | `br` | `pair` |
|---|--------|------|------|------|--------|
| 1 | block_height | Block Height | height | Local Node (Start9) | — |
| 2 | block_age | Block Age | mins×10 | Minutes (Start9) | AGE |
| 3 | fastest_fee | Fastest Fee | sats/vB | sat/vB (Start9) | sat/vB |
| 4 | btc_price | BTC Price | rounded $ | BTC/USD (Start9) | BTC/USD |
| 5 | moscow_time | sats/USD | 100M÷price | Sats per Dollar (Start9) | SAT/USD |
| 6 | hash_rate | Pool Hash | compacted | hash/s (Start9) | — (text) |
| 7 | blocks_found | Blocks Found | count | Pool (Start9) | F/N9 |

Pool metrics auto-stripped without Pool API URL.

## Build & Test Pipeline

1. Edit source, run `python3 -m unittest discover -s tests`
2. `npx tsc --noEmit` then `npm run build`
3. Rebuild s9pk: `start-cli -H https://localhost:1234 s9pk pack --arch=x86_64 -o blockclock-adapter_x86_64.s9pk`
4. Probe live clock (8-10s between calls): `curl -s -m 5 "http://$CLOCK/api/show/number/1?tl=Test&br=Test+%28Start9%29"`

## Pitfalls

1. **`pair` with spaces returns 400** — the `pair` display segment must be space-free and plain words are capped at 4 chars (slash pairs like `BTC/USD` are exempt). Put branding and any multi-word text in `tl`/`br` instead.
2. **Global rate limit (429)** — the 3s status polls and 60s+ pushes share ONE budget across all endpoints. Occasional 429 is expected; retry on the next cycle rather than hammering.
3. **Button advance shows "Network connection problem"** — with Data Backend = `127.0.0.1`, pressing middle-right briefly shows the error because the backend pull is dead. Press once to wake the backend; the adapter replaces the display within ~10-40s. Cosmetic, not a push failure.
4. **Probing too fast corrupts results** — the clock's HTTP API is slow and the display is shared; 8-10s between probe calls is the empirical floor. Faster probing triggers the global rate limit or shows stale values.
5. **Hashrate is text-only** — the hashrate metric uses `/api/show/text/<txt>`; it cannot carry `pair` styling. Don't try to force it into the numeric endpoint.
6. **Metrics stripped without Pool API URL** — pool metrics (hash_rate, blocks_found) are silently gated by `resolveEnabledMetrics()`; if the pool URL is missing the rows disappear. Check the store config before reporting them missing.

## First-Run

- No start without BLOCKCLOCK URL — `main.ts` throws i18n'd error; `init/taskSetBlockclock.ts` creates critical task on install
- Pool metrics gated by `resolveEnabledMetrics()` in store.json.ts

## Known Quirks

- Unconditional pool fetch upstream — patched to skip when pool metrics disabled
- Defaults triad → consolidated into `storeDefaults` from zod schema
- `moscow_time` is internal id only; on-screen: `sats/USD` / `Sats per Dollar (Start9)`