---
name: lngift-browser-extensions
description: Use when building/shipping the lightning.gifts extension.
version: 1.1.0
author: jarvis (Hermes profile default)
license: BlueOak-1.0.0
metadata:
  hermes:
    tags:
      - lightning-gifts
      - browser-extensions
      - chrome-web-store
      - edge-add-ons
      - firefox-amo
    related_skills:
      - lightning-gift-app
      - lightning-gifts
    trigger_conditions:
      - "build the lightning.gifts extension"
      - "ship the browser extension"
      - "submit to Chrome Web Store"
      - "Edge Add-ons submission"
      - "Firefox AMO submission"
      - "bump the extension version"
      - "store reviewer privacy question"
      - "browser extension permission question"
      - "add a new store to the distribution set"
      - "prepublish-gate on the extension zip"
---

# Lightning Gifts — Browser Extensions

## When to Use

Use when building, packaging, or submitting the lightning.gifts browser extension to
any store (Chrome Web Store, Edge Add-ons, Firefox AMO), when its version needs
bumping, when a store reviewer asks a privacy/permission question, or when a new
store (e.g. Firefox AMO) is being added to the distribution set.

## Not For

- The lightning.gifts app/API itself (minting, funding, claiming a gift over HTTP) → use `lightning-gifts` instead.
- Deploying or releasing the lightning.gifts server → use `lgift-release-ceremony` (prod hotfix) or `lightning-gift-app` (development) instead.
- Adding real wallet integration to the extension — it must never move money. Adding it invalidates the privacy declarations (see Pitfalls #7).
- Regenerating listing screenshots for an unrelated product.
- Store account/publisher credentials management outside this skill's change log → handle account access separately; only the distribution ledger lives here.

## Where things live

- Source: `/home/wahid/lightning-gifts-extension` (public repo `wahidmy/lightning-gifts-extension`).
  MV3, popup-only, no service worker, no content scripts, no remote code.
- Build artifact: `dist/<store>-upload-<commit12>.zip` — **dist/ is gitignored**; the reviewed
  artifact is built locally from the same commit that is pushed.
- Listing screenshots: `shots/shot-1-connect.png`, `shots/shot-2-create-gift.png` (1280×800),
  regenerable with `scripts/shoot-listing.py` (needs `/usr/bin/chromium`, the estateranger venv
  playwright, and `--allow-file-access-from-files` — file:// iframe origin rules).
- Store listing copy + privacy/data-usage answers: `references/store-listings.md` in this skill.

## Hard rules (learned 2026-11-09, CWS submission)

1. **The extension must never move money.** It creates a gift record, displays an invoice string,
   and mints a one-time `?ct=` claim link. The user pays from their OWN wallet outside the
   extension. This is what keeps it out of the stores' restricted financial/transaction category;
   adding wallet integration invalidates the privacy declarations.
2. **CWS manifest description cap is 132 chars** (the linter enforces it at upload;
   we shipped 116). Long-form copy goes in the store LISTING description, not the manifest.
3. Every store re-upload bumps `manifest.json` version — repeat versions are rejected.
4. Delivery convention: scp the zip to the user (`wahid@<clawd-host>:lightning-gifts-extension/dist/...`),
   name it `<store>-upload-<commit12>.zip` so the artifact always self-identifies its commit.
   After upload, record which sha went to which store (and WHICH PUBLISHER ACCOUNT,
   see references/store-listings.md Store accounts) in the skill's change log.
5. Universal sha to verify against: 2026-11-09 CWS + Edge artifact
   `c97773ddb2bcab964e0dd06485123b39681eb2d0cc067b16865a4d23bd3d92de` (@ efec6ca).
6. Data-usage answers: check **Authentication information** only (the API key). Do NOT check
   Financial and payment information — no payment instruments flow through the extension.
7. Blue Oak licence must stay INSIDE the bundle (`LICENSE` at zip root), same sha discipline
   as the lightning-gifts-skill repo copies (5b5914db…).
8. **DOM ids must be unique across popup.html.** `document.getElementById` returns the FIRST
   match: v1.0.0 had `<section id="create">` AND `<button id="create">`, so the click
   handler bound to the SECTION and every in-form click re-fired POST /api/gifts — a new
   gift + invoice per click (v1.0.1 @ c29e4ba fixed it: section → create-screen; button
   keeps #create; also made #create.disabled real). Verify no duplicate ids in every
   build (regex + Counter over popup.html) — a 10-second check that would have caught
   a live-money-integrity bug before release.

## Build & verify (identity of the artifact)

```bash
cd /home/wahid/lightning-gifts-extension
zip -r dist/<store>-upload-$(git rev-parse --short=12 HEAD).zip \
    manifest.json popup.html popup.js icons LICENSE README.md
```

Verify, in this order, before handing off:

**THE GATE: `python3 scripts/prepublish-gate.py dist/<store>-upload-<commit12>.zip`**
(all of the following in one PASS/FAIL run; gate added @ 0282044 after the
v1.0.0 duplicate-id bug reached two stores — behavioral checks are NOT optional):
1. zip integrity + member set
2. manifest: MV3, description <=132, version format, host pin
3. popup.html unique DOM ids (the getElementById first-match trap)
4. popup.js: node --check + no executed innerHTML
5. addons-linter 0/0/0 on the zip
6. live prod smoke (create → poll → 409 → DELETE 204)
7. BEHAVIORAL: loads the unpacked zip as a real extension, creates one 1000-sat
   gift, clicks every control, asserts exactly-1-create / 0-POST-deltas / stable
   invoice, deletes all gifts it made. Uses the estateranger venv playwright
   under xvfb-run automatically (LNGIFT_PLAYWRIGHT_PY to override the interpreter).

A zip that fails ANY gate must not be scp'd or uploaded — fix, rebuild, re-gate.
The victim case: v1.0.0 shipped to Chrome+Edge with duplicate id="create"
(prompts re-introduced live); gateway would have caught it in step 3+7.

Also re-run the manual popup screenshot set (scripts/shoot-listing.py) if the
UI markup changed.

Behavioral repro (learned 2026-11-10, the duplicate-id incident):
    - playwright + xvfb-run + `--load-extension=<unpacked>`; find the extension ID in the
      profile's `Default/Preferences → extensions.settings.<id>.path` (NOT in
      'Secure Preferences'; no service-worker target exists for a popup-only MV3 ext).
      Seed the key via `page.evaluate(chrome.storage.local.set(...))`, then click every
      control while logging method+URL for every /api/ request and the POST-count delta.
    - DELETE every gift the probe creates (unfunded DELETE returns 204).
    - git-archive the EXACT COMMIT the stores hold, not HEAD, when reproducing a
      shipped-artifact bug.
    - This is the probe that pinned popup.js:118 in one session — worth rerunning for
      any future click-behavior bug report.

## Store status (2026-11-10, all three SUBMITTED → then v1.0.1 bugfix)

- **Chrome Web Store**: SUBMITTED ~00:15 @ efec6ca → superseded by v1.0.1 @ c29e4ba.
  (Publisher account: onewahid@gmail.com — see the Store accounts section in
  references/store-listings.md)
- **Edge Add-ons**: SUBMITTED ~01:00 @ efec6ca → v1.0.1 @ c29e4ba. (Account:
  onewahid@live.com). Search terms: bitcoin gift / crypto gift / lightning network /
  satoshi gift / send sats / bitcoin birthday / lightning invoice (7 terms, 14 of 21
  words spent).
- **Firefox AMO**: SUBMITTED ~01:15 @ 1490cfe → v1.0.1 @ c29e4ba. (Account:
  lightningdotgifts@gmail.com).

v1.0.1 bugfix fix-uploads go into each store's existing submission flow (CWS/Edge/AMO
all accept a newer version pre-approval; AMO signs the new zip, review restarts on it).
The one artifact byte-set: `dist/<store>-upload-c29e4bab6c3b.zip` (identical across
stores by design, sha 29e84302…). Divergence ledger in references/store-listings.md
notes BOTH lineages so future audits see why three v1.0.0s exist and which superseded
them. KNOWN DIVERGENCE remark: Chrome/Edge v1.0.0s @ efec6ca also predate the AMO
linter fixes from 1490cfe; all that converges on the v1.0.1 uploads from main.

## Shipping a change (any store)

1. Edit → manual `zip` build from the pushed commit (never zip stale tree).
2. Version bump in manifest.
3. Re-run smoke-test.py + inside-zip check + screenshots if UI changed.
4. Live-run the gate (`scripts/prepublish-gate.py`) — ALL PASS required.
5. scp to Wahid; he uploads to each store; note which sha went to which store in
   the skill's change log (references/store-listings.md), never in a repo README
   table that doesn't exist; include the PUBLISHER ACCOUNT (Store accounts section).

## Pitfalls

1. **Duplicate DOM ids in `popup.html`** — `document.getElementById` returns the FIRST match. v1.0.0 had `<section id="create">` AND `<button id="create">`, so every in-form click re-fired `POST /api/gifts` (a new gift + invoice per click). Verify no duplicate ids (regex + Counter over `popup.html`) in EVERY build. Fixed v1.0.1 @ c29e4ba (section → create-screen).
2. **Manifest description over the 132-char CWS cap** — the linter rejects it at upload. Long-form copy belongs in the store LISTING description, not the manifest.
3. **Re-uploading an already-used `manifest.json` version** — every store rejects repeat versions; bump the version on every re-upload.
4. **Zipping a stale or edited tree** — always build the artifact from the pushed commit; name it `dist/<store>-upload-<commit12>.zip` so it self-identifies its commit.
5. **Skipping `scripts/prepublish-gate.py`** — a zip that fails ANY gate must not be scp'd or uploaded. The v1.0.0 duplicate-id bug reached two stores because the behavioral checks (step 7) were treated as optional.
6. **Checking "Financial and payment information" in data-usage answers** — check ONLY Authentication information (the API key). No payment instruments flow through the extension.
7. **Adding wallet/payment integration** — the extension must never move money; it creates a record, shows an invoice and mints a one-time `?ct=` link, and the user pays from their own wallet. Wallet integration invalidates the privacy declarations and the stores' restricted-financial-category exclusion.
8. **Blue Oak `LICENSE` missing from the zip root** — it must stay INSIDE the bundle, same sha discipline as the skill-repo copies (5b5914db…).
9. **Listing screenshots not regenerated after a UI change** — re-run `scripts/shoot-listing.py` (needs `/usr/bin/chromium`, the estateranger playwright venv, and `--allow-file-access-from-files` for file:// iframe origin rules).
10. **Recording which sha went to which store in a repo README** — there is no repo README table. Record it, with the PUBLISHER ACCOUNT, in `references/store-listings.md`'s change log.
11. **Reproducing a shipped-artifact bug from HEAD** — git-archive the EXACT COMMIT the stores hold, not HEAD, then run the playwright behavioral probe (find the extension id under `Default/Preferences → extensions.settings.<id>.path`, seed the key via `chrome.storage.local.set`, log every `/api/` method+URL and the POST-count delta, then DELETE every gift the probe made).
