---
name: texas-electricity
description: ESI ID lookups, TDSP identification, and Texas deregulated electricity market research. Use when the user asks about Texas electricity meters, ESI/ESID numbers, which utility serves an area, or looking up addresses from meter identifiers and vice versa.
version: 1.1.0
author: hermes-curator
tags: [texas, electricity, esiid, esid, tdsp, oncor, deregulated]
metadata:
  hermes:
    trigger_conditions:
      - "what's my ESI ID"
      - "look up this ESI ID"
      - "find ESI for address"
      - "which utility serves this area"
      - "Texas electricity plan shopping"
      - "SmartMeterTexas questions"
      - "ESID lookup"
      - "ESI ID Texas"
      - "TDSP prefix"
      - "Oncor vs CenterPoint"
      - "electricityplans.com esid"
      - "energybot esi lookup"
      - "TEMP meter ESI"
---

# Texas Electricity & ESI ID Lookup

Texas deregulated electricity market — ESI ID bidirectional lookups, TDSP identification, and market structure.

## Trigger

- "what's my ESI ID" / "look up this ESI ID" / "find ESI for address"
- "which utility serves this area"
- Texas electricity plan shopping, SmartMeterTexas questions
- Any mention of ESID, ESI-ID, ESIID in Texas context

## Not For
- **Comparing retail electricity rates/plans** — this skill resolves meters and TDSPs, not rate shopping. → use the REP comparison sites directly (or `product-price-monitor` for price alerts).
- **Out-of-state utility lookups** — ERCOT/ESI IDs only exist in the Texas deregulated market → check the local utility's own lookup.
- **Solar net-metering / export rate questions** — meter identity is covered, but interconnection/export policy is REP/TDSP-specific → refer to the customer's REP.
- **SmartMeterTexas usage data downloads** — this skill finds the ESI ID; the data portal itself needs the account login → see SmartMeterTexas directly.

## Texas Electricity Market Structure

Texas has deregulated electricity in most areas. Two entities serve each address:
- **TDSP (TDU):** Transmission and Distribution Service Provider — owns the wires/meter. You can't choose this.
- **REP:** Retail Electric Provider — you buy power from them. You CAN shop around.

An **ESI ID** (Electric Service Identifier) is a 17-22 digit number ERCOT assigns to every meter location. It's the permanent ID for the physical address — stays the same even when providers change or meters are replaced.

## TDSP Prefix Reference

| Prefix (first 7-10 digits) | TDSP | Territory |
|---|---|---|
| `1044372000` | Oncor | Dallas/Fort Worth, Princeton, North Texas |
| `1017699` | Oncor (legacy prefix) | Same as above |
| `1008901` | CenterPoint Energy | Houston area |
| `100327` | AEP Texas Central | South/Central Texas |
| `100328` | AEP Texas North | West Texas |
| `101288` | TNMP (Texas-New Mexico Power) | Gulf Coast, West Texas |
| `100430` | Sharyland | Various |

## Bidirectional ESI ID Lookup

### Primary Tool: ElectricityPlans.com

URL: `https://electricityplans.com/texas/esid-lookup/`

This is the most reliable free tool. It has a **combobox that accepts BOTH addresses and ESI IDs** — making it bidirectional.

**Address → ESI:**
1. Navigate to the page
2. Type a complete address into the combobox textbox (e.g., `105 Rita Dr, Princeton, TX`)
3. Autocomplete populates results in format: `ADDRESS, CITY, TX, ZIP | ESI_ID`
4. Extract results via `browser_console` (see technique below)

**ESI → Address:**
1. Navigate to the page
2. Type the full ESI ID into the same combobox
3. Autocomplete returns matching address(es)
4. Extract results via `browser_console`

### Extracting Autocomplete Results (JavaScript)

The ElectricityPlans combobox populates `[role="option"]` elements in a listbox. Extract them with:

```javascript
Array.from(document.querySelectorAll('[role="option"]')).map(el => el.textContent).filter(Boolean)
```

Each result is pipe-delimited: `ADDRESS | ESI_ID`

### Alternative Tools

- **ElectricChoice.com** (`electricchoice.com/esi-id`): Also bidirectional, but uses a slower form-submit model rather than autocomplete. Useful as fallback.
- **EnergyBot.com** (`energybot.com/esid-lookup.html`): Address→ESI only. Not bidirectional.

## Pitfalls

1. **Reverse lookup is NOT publicly available through ERCOT directly** — all public tools go address→ESI. Only REPs/TDSPs with ERCOT market system credentials can do ESI→address lookups directly. Recovery: use the ElectricityPlans combobox (the rare exception that offers both directions); don't waste time on ERCOT's public portal.
2. **TEMP meters** — construction/temporary meters show as separate entries with their own ESI IDs. A single address may have both a main meter and a TEMP meter in the database. Recovery: pick the non-TEMP entry for a permanent service, or confirm which meter the customer's bill references.
3. **Oncor prefix confusion** — ElectricityChoice.com lists Oncor's prefix as `1040051` — this is wrong for most lookups. The actual common Oncor prefix is `1044372000`. Recovery: verify with the ESI ID on the customer's bill if there's ambiguity.
4. **New construction** — meters set up in the last 24 hours may not appear in public databases yet. The TDSP needs time to register them with ERCOT. Recovery: retry after 24–48h, or check the TDSP's own lookup.
5. **Prefix mismatch = wrong territory** — if someone in Princeton, TX (Oncor territory) gets an ESI starting `1008901` (CenterPoint), something is wrong. Recovery: re-verify the address and re-run the lookup; don't trust a mismatched prefix.
6. **Browser autocomplete extraction misses results** — the ElectricityPlans combobox populates `[role="option"]` elements; scraping the rendered list instead of waiting for autocomplete can return empty. Recovery: wait for the listbox, then extract with `Array.from(document.querySelectorAll('[role="option"]')).map(el => el.textContent).filter(Boolean)`.
7. **Assuming one ESI per address** — a property can have multiple meters (main + TEMP + separate outbuildings). Recovery: list ALL autocomplete results and disambiguate by address suffix/meter type before reporting.

## Verification

After finding an ESI ID, verify that the TDSP prefix matches the expected utility for the area. If someone in Princeton, TX gets an ESI ID starting with `1008901` (CenterPoint), something is wrong — Princeton is Oncor territory.

## References

- `references/tdsp-prefixes.md` — Full TDSP prefix reference with territory maps
- `references/lookup-technique.md` — Step-by-step browser automation technique for ElectricityPlans
