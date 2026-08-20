---
name: polymarket
description: "Query Polymarket: markets, prices, orderbooks, history. Read-only public REST APIs (Gamma, CLOB, Data) with zero auth. Use when the user asks about prediction markets, betting odds, or event probabilities."
version: 1.1.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
platforms: [linux, macos, windows]
metadata:
  hermes:
    trigger_conditions:
      - "what are the odds of X happening"
      - "prediction market prices"
      - "polymarket market data"
      - "betting odds event probabilities"
      - "polymarket orderbook"
      - "polymarket price history"
      - "who's winning this political event market"
      - "gamma api public-search"
      - "clob token ids price query"
      - "data-api trades open interest"
      - "monitor prediction market movements"
      - "polymarket volume in USDC"
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## Typical Workflow

When a user asks about prediction market odds:

1. **Search** using the Gamma API public-search endpoint with their query
2. **Parse** the response — extract events and their nested markets
3. **Present** market question, current prices as percentages, and volume
4. **Deep dive** if asked — use clobTokenIds for orderbook, conditionId for history

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Not For

- **Placing trades / wallet auth** — this skill is read-only. Trading needs EIP-712 wallet signatures (out of scope).
- **Crypto price data (BTC/ETH spot)** → use a dedicated market-data source, not Polymarket
- **Historical long-term analytics beyond price history** → the Data API covers trades/open interest, not deep analytics
- **Betting on other platforms** (Betfair, DraftKings, Kalshi) → each has its own API; Kalshi is a separate product

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## Pitfalls

1. **Double-encoded JSON fields** — `outcomePrices`, `outcomes`, and `clobTokenIds` come back as JSON strings inside JSON. Parse with `json.loads(market['outcomePrices'])` or you'll format `"[0.80, 0.20]"` as literal text.
2. **Empty price history on new markets** — some freshly created markets have no history yet; the Data API returns empty arrays. Report "no data yet" instead of inventing a trend.
3. **Wrong API for the question** — search/discovery → Gamma; live price/orderbook → CLOB; trades/open interest → Data. Mixing them up returns 404s or empty payloads.
4. **ConditionId vs clobTokenIds mixup** — `conditionId` is for price history; `clobTokenIds` (the [Yes, No] pair) is for price/book queries. Passing the wrong one returns nothing useful.
5. **Treating price as fixed odds** — prices ARE probabilities and move; a 0.65 price is a live quote, not a guarantee. Don't present it as settled fact.
6. **Geographic/trading restrictions on reads** — read-only data is globally accessible, but some markets may be geo-restricted; fall back to `web_search`/`web_extract` for those.
