---
name: bitcoin-payment-rails
description: "Use when designing a Bitcoin payment or donation rail."
version: 1.1.0
metadata:
  hermes:
    tags: [bitcoin, bip21, lightning, lnurl, payments, donations, anonymity, privacy]
    trigger_conditions:
      - "how should we charge for this"
      - "add a donation / tip / support link"
      - "how do we receive payment"
      - "BIP21"
      - "lightning address"
      - "anonymity of receiving payments"
      - "should we use on-chain or Lightning"
      - "prefill the payment amount in a QR"
      - "LNURL-pay endpoint"
      - "is accepting Bitcoin anonymous"
      - "custodial vs self-hosted node for payments"
      - "collection fee exceeds the payment"
---

# Bitcoin Payment Rails

Designing the *money comes in* side of a Bitcoin product: requests people actually complete, on rails
whose privacy properties match what the product promises. Applies to the gift/lockbox work, the
wallets comparison site, dashboards, and any side-hustle asking for sats.

## When to Use

- Designing the receive side of a Bitcoin product: checkout, donate/tip link, support ask, or paywall.
- Choosing between on-chain (BIP21), Lightning Address/LNURL, or a hybrid for a given audience.
- Deciding how to express the amount so payers cannot get it wrong (prefilled vs suggested).
- Assessing the privacy of *receiving* — and qualifying what "anonymous" actually means.
- Adding a second, non-donation payment into the same transaction instead of paying twice.
- Reviewing an existing flow for a bare address, an unenforceable fee, or an unrecoverable mis-send.
- Sizing a payment so its collection cost does not exceed its value.

## Not For

- **Implementing the Taproot lockbox scripts, signing, or fee rules themselves** → use `bitcoin-script-engineering` instead.
- **Deploying or verifying sendbitcoin.gift** (md5-gated ssh deploy, printed artifacts) → use `sendbitcoin-gift-site` instead.
- **Ops on lightning-gifts** (the lightsats fork: CT 123 dev, production, its ops) → use `lightning-gift-app` instead.
- **The wallets-comparison site** → use `update-lightning-wallets-site` instead.
- **The Bitcoin Fits / family-dashboard site** → use `bitcoin-fits-site` instead.
- **Storing or retrieving private keys and credentials** → use `bitwarden-cli` (or `vault-cli-cron` for unattended jobs) instead.

## Always-on rules

1. **Never show a bare address as a payment request.** A bare address makes the payer type the amount,
   which is the top cause of wrong-amount sends. Emit a BIP21 URI (on-chain) or a Lightning
   Address/LNURL (off-chain) instead — see `references/rail-comparison.md` for formats and examples.
2. **Check what the code already emits before designing anything.** `grep -rn "bitcoin:" src/` — zero
   hits means every request in the app is a bare address, which is the cheapest available win and
   applies to the *existing* flow (e.g. a deposit step that says "send exactly X") as well as any new ask.
3. **Never make the payer pay twice.** A separate second transaction costs a whole input plus change
   (~150+ vB), so a small fee is destroyed by its own collection cost. Fold the extra payment into the
   *same* transaction as a second output: a P2TR output is 43 bytes, so the marginal cost is ~43 vB —
   roughly 3–4× cheaper than a second transaction. BIP21 cannot express two outputs; use an
   unsigned/output-only PSBT or explicit multi-recipient instructions.
4. **Size the payment to the rail.** Spending a P2TR input costs ~58 vB, so a fixed on-chain amount can
   cost more to *collect* than it is worth at moderate fee rates. Size it generously, or wait for cheap
   blocks (a donation has no urgency — unlike a toll). Small recurring amounts belong on Lightning.
5. **Match the rail to the anonymity requirement, and qualify "anonymous".** A custodial Lightning
   provider sees the account identity, the login IP/fingerprint and the entire payment history in one
   place. Anonymous *relative to other users* is not anonymous *against the custodian or a subpoena*.
   See the anonymity section below before calling any rail anonymous.
6. **Keep payment targets physically apart.** Never render a donation/tip target in the same block as a
   deposit address. Two addresses side by side invites sending one payment to the other, and with no
   custodian in the design that money is unrecoverable.
7. **Do not design a toll into a serverless product.** If the client generates the artifact and the
   artifact is self-contained (the recipient never needs the site), nothing can be gated on payment —
   the page is static and there are no accounts. Enforcement requires either **custody** (a third key in
   every artifact, which breaks a non-custodial promise) or a **server** that gates artifact generation
   (which reintroduces hosting and its footprint). Present the choice explicitly rather than shipping a
   fee that silently cannot be collected.

## BIP21 — the on-chain payment request

```
bitcoin:<address>?amount=<BTC>&label=<name>&message=<note>
bitcoin:bc1q...?amount=0.00002&label=sendbitcoin.gift&message=Hosting%20support
```

- Scanning prefills the **address and the amount**; `label`/`message` are commonly ignored by wallets.
- `amount` is in **BTC, not sats** — 2,000 sats is `0.00002`. A sats value here is off by 10^8.
- URL-encode every value; escape `&` and `?`.
- The `req-` prefix marks a parameter as required — a wallet that cannot honour it must refuse rather
  than silently send something else. Use it when a wrong amount is worse than no payment.
- **Single payment only:** BIP21 cannot carry a fee plus a payment, and there is no multi-output form.

## Lightning Address — the off-chain request

- Form is `name@domain`, resolved via `https://<domain>/.well-known/lnurlp/<name>` (LUD-16) to an
  LNURL-pay endpoint, which returns an invoice.
- The endpoint advertises **min/max sendable only** — the *wallet* asks the sender for the amount. There
  is no reliable standard for prefilling a fixed amount (`lightning:name@domain?amount=2000` is honoured
  by some wallets and ignored by others), so a "send just N sats" ask degrades to a suggestion.
- **A static page cannot mint a fixed-amount invoice** — that needs the provider's API and credentials,
  which would be published in the bundle. Don't promise prefilled Lightning amounts on a static site.
- Not universal: hardware wallets, many exchanges and on-chain-only users cannot pay it. If it is the
  only rail, those payers are simply blocked.

## Anonymity of receiving

- **On-chain is a permanent public ledger of income**, and *spending* is what links the operator to it —
  not the address alone. Deriving a fresh address per request from an embedded xpub (public key on the
  site, watch-only descriptor for collection) removes visible linkage *between* payments, but the
  operator's own spend still links them, so hygiene matters more than derivation.
- **Lightning removes the public ledger entirely** — there is no chain-analysis surface at all, which is
  categorically stronger than any on-chain address scheme. That is the main reason to prefer it for a
  published donation handle.
- **Custody is the trade.** A self-hosted node needs inbound liquidity and a public node identity; a
  custodial account sidesteps both but makes the operator a creditor. To be anonymous *against the
  custodian*: create and access the account over Tor/VPN, use an identity with no link to the operator
  (prefer a signup path that avoids email), and never deposit from or withdraw to a KYC'd exchange.
- **Spending hygiene:** never co-spend received funds with the operator's other coins
  (common-input-ownership links them); move value out via a swap service rather than a KYC exchange.
- Off-chain handles accept every payer's invoice independently, so there is no address-reuse question —
  but the handle itself is a static public identifier: pseudonymous, not anonymous.

## Pitfalls

1. **`amount` in sats, not BTC** — the single most likely BIP21 bug; off by 10^8.
2. **Assuming a scanned QR prefills the amount** — a bare-address QR never does, and a Lightning Address
   generally cannot. Verify what the wallet will actually receive.
3. **Calling a custodial account anonymous because it was not KYC'd** — the custodian still sees the IP,
   the login identity and the whole history. Anonymity comes from *access* hygiene, not from a missing
   KYC step.
4. **Publishing one static receive address for donations** — a permanent, browsable ledger of income.
5. **Shipping an unenforceable fee** — see rule 7; decide custody-vs-server consciously or make it a
   request and frame it honestly.
6. **Placing the ask next to the deposit address** — mis-sends are unrecoverable with no custodian.
7. **Assuming Lightning Address reaches every payer** — offer an on-chain BIP21 fallback as a second,
   clearly labelled option. A hybrid `bitcoin:<addr>?lightning=<invoice>` QR is not available to a
   static page, since that parameter needs a BOLT11 invoice the page cannot mint.
8. **Friction kills voluntary payments** — a donation only happens if it is effortless; the ergonomics
   of the ask matter more than its wording.

## Support files

- `references/rail-comparison.md` — rail-by-rail comparison (amount prefill, fees, UTXO ops, public
  ledger, anonymity, payer compatibility, uptime) and the recommended dual-rail layout.
