---
name: lngift-wallet-directory-refresh
description: Use when the LPK wallet gate reds on freshness or logos.
category: devops
version: 1.1.0
author: Jarvis
license: MIT
metadata:
  hermes:
    tags: [lightning-gifts, lpk, gate, dev]
    related_skills: [lightning-gifts, lgift-release-ceremony]
    trigger_conditions:
      - "refresh the LPK wallets directory"
      - "lpk-directory.test.mjs failed"
      - "lpk-editorial.test.mjs failed"
      - "wallet freshness gate red"
      - "provider has no logo"
      - "unclassified wallet provider"
      - "wallet audit sync_exit=1"
      - "audit_exit=2 wallet"
      - "re-pin the wallets data"
      - "/guide/wallets renders stale info"
      - "provider database update needed"
---

# lightning-gift / LPK wallet-directory refresh

## When to Use

- A dev gate alert names `lpk-directory.test.mjs` — freshness, provenance or logo guards.
- A gate alert names `lpk-editorial.test.mjs` — an unclassified wallet after a refresh.
- The weekly wallet audit reports `sync_exit=1` (upstream moved) or `audit_exit=2`.
- Someone asks to refresh or re-pin the wallets directory data.

## Not For

- Building, running or deploying the lightning.gifts app itself → use `lightning-gift-app` instead.
- Cutting a prod hotfix release/tag → use `lgift-release-ceremony` instead.
- The giver-side HTTP API (minting, paying, claiming, reclaiming a gift) → use `lightning-gifts` instead.
- Verifying a Cloudflare Pages/Workers deploy is actually live → use `static-site-deploy-verify` instead.
- Hand-editing `providers-data.json` to make a red gate pass. Hand edits defeat the sanity gate the sync script exists to enforce — run `lpk-sync-check.mjs --apply` instead.

The `/guide/wallets` page renders from a vendored copy of pseudozach/lightning-pay-kit's
provider database. Three guards can red: the snapshot ages past its limit, a visible
provider has no logo, or a provider has no editorial classification. A refresh trips all
three at once, so do them as one pass.

Dev is CT 123 (`/opt/lightning-gift`); prod is the VPS. Never hand-edit
`providers-data.json` — the sync script is sanity-gated.

## Reading the alert

`pass=684 of 691 tests, 1 failing (floor 650)` is the current wording. An older alert read
`pass=678/145`: the denominator was `MIN_SUITE_PASS`, a floor, not a total — it is not a
ratio. `not ok 341` is the TAP index of the failing assertion, not a count.

## Procedure

1. Confirm it is a real refresh, not a flap:
   `docker compose exec -T app node scripts/lpk-sync-check.mjs` (0 = current, 1 = upstream
   moved, 2 = cannot reach upstream / data failed sanity gates).
2. Back up, then apply **on the CT host** — node is installed there (`/usr/bin/node`),
   despite the comment in `gate-check.sh` claiming otherwise:
   `LPK_APP_ROOT=/opt/lightning-gift/src/app node app/scripts/lpk-sync-check.mjs --apply`
   It rewrites `providers-data.json` + `PROVENANCE.json` together.
3. `node --test tests/lpk-directory.test.mjs` from `src/app`. A logo failure here means a
   newly visible provider lacks `public/lpk/<id>.png`.
4. Curate missing logos into `public/lpk/<id>.png` at 128x128 RGBA and record the source in
   `lib/lpk/logo-sources.json` (house format: `"<id>": "<file> <- <url> (<dims/note>)"`).
   Prefer the vendor's `apple-touch-icon.png`; GitHub org avatars are acceptable when noted.
5. `node --test tests/lpk-editorial.test.mjs`. New providers are fail-closed: unclassified
   ones render nowhere and the test names them.
6. Classify in `lib/lpk/editorial.ts`, then commit, `docker compose build app`,
   `up -d app`, and run the full suite in the container (that is the artefact the gate judges).
7. `bash scripts/gate-check.sh` — exit 0 and a green line in `gate-run.log` is the proof.

## Vocabulary (do not blur these two words)

- **"Supports easy withdrawal"** — the `/guide/wallets` section (formerly "Recommended -
  Supports LNURL-Withdraw", const `EASY_WITHDRAWAL_IDS`). It claims ONE thing: the wallet can
  be paid by LNURL-withdraw. A wallet here is not a recommendation.
- **"Recommended"** — the curated three (`lngiftRecommended` in `lib/items/wallets.ts`):
  Cash App, Strike, Lexe. All three are invoice-flow wallets, none supports LNURL-withdraw,
  which is precisely why the words had to be separated. They lead the tip-form selects, the
  recipient's journey step shows all three (`recommendedLimit: 3`), and
  `DEFAULT_RECOMMENDED_WALLET_ID` (cashapp) sorts first. `getItemScore` gives them +20 so no
  locale/platform match can bury them; `tests/recommended-wallets.test.mjs` pins all of it.
- The directory shows them in the **"Recommend for new users"** block at the top of
  `/guide/wallets` (`NEW_USER_PICK_IDS` in `lib/lpk/editorial.ts`). The snapshot has no row
  for Cash App or Strike, so they are authored cards with `isAffiliate: true` (both links
  are referral links); Lexe resolves to its snapshot row. The test suite ties
  `NEW_USER_PICK_IDS` to the `lngiftRecommended` set so the two cannot drift.

## Pitfalls

1. **The editorial layer is fail-closed.** A refresh that is otherwise perfect still reds
  until every new `category: "wallet"` row is in `RECOMMENDED_IDS` or `OTHER_WALLET_IDS`.
2. **Default new wallets to `OTHER_WALLET_IDS`.** That section only claims the recipient can
  generate an invoice. `RECOMMENDED_IDS` claims LNURL-withdraw support — never assert that
  without vendor evidence.
3. **Local overlays key on id.** When upstream adopts a slug the overlay used (e.g. `cake` ->
  `cake-wallet`), point the overlay at the new id so it retires itself; otherwise the wallet
  renders twice.
4. **Freshness limits must clock something satisfiable.** They read upstream's `updatedAt`,
  so a tight limit reds for as long as upstream stays quiet and no amount of syncing clears
  it. Both gates use 90 days for that reason; upstream drift is the weekly audit's job.
5. **Upstream files node managers as `wallet`** (RTL, ThunderHub, BitBanana). They belong in
  Other, not Recommended.
6. **A retired upstream row must leave Recommended.** Breez Mobile is `retired` with evidence
  that its channels are closed (recovery recovers on-chain only), so it cannot pay an
  invoice. Check `serviceStatus` before trusting a familiar name. Breez's own evidence
  chain, if it is ever questioned: `breez/breez-mobile-recovery` README ("so funds stay
  recoverable after the Breez app leaves the app stores"; "Breez closed its channels with
  the app's users from its side"), PR #1 by `kingonly`, Glow shipped as the replacement in
  Aug 2026, and both old store listings 404.
7. **Promote a wallet to Recommended only on its own code.** LNURL-withdraw means LUD-03:
  read the callback, then post `k1` + `pr`. Bitkit: bitkit-core
  `create_withdraw_callback_url` + Android `LnurlService.requestLnurlWithdraw`.
  Blitz: `processLNUrlWithdraw`. A third-party review is not evidence for a money claim.
8. **Two distinct flake mechanisms — do not confuse them.** (a) All test files share one
  Postgres, and every claim mint runs a global `deleteMany` of used tokens, so parallel
  files delete each other's fixtures: `gate-check.sh` passes `--test-concurrency=1`.
  (b) `tests/claim-tokens.test.mjs` drives the LIVE app over HTTP
  (`BASE_URL || http://localhost:3000`), and the mint limiter is 5/60s per `route:IP`
  in the app's own process — so a second suite run inside a minute reds with "the mint
  refused a correct passphrase". The gate therefore also skips a tick within 90s of the
  last run (`.gate-last-run`). If you red a gate by hand twice in a row, that is why:
  `docker compose restart app` clears the buckets.
9. **The weekly audit alerts on findings, not just staleness.** `lpk-audit-our-wallets.mjs`
  exits 1 for LPK-SAYS-HIDE / UNVERIFIED-BY-LPK / LINK-403 on `lib/items/wallets.ts`. Those
  are editorial calls about the tip form, not covered by the LPK page's classification.
10. **Verifying on the host instead of in the container** — the gate judges the container
  artefact. After editing `lib/lpk/editorial.ts`, `docker compose build app`, `up -d app`, and run
  the full suite inside the container; a host-only run proves nothing about what ships.
