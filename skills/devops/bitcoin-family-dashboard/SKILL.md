---
name: bitcoin-family-dashboard
version: "2.1.0"
author: jarvis
license: MIT
description: "Maintain the Bitcoin Family Dashboard StartOS package: two-repo structure, master-branch workflow, ExVer tags, community-registry conformance."
metadata:
  hermes:
    tags: [bitcoin, family, dashboard, startos, start9, s9pk, watch-only, descriptor, mempool, bitcoind]
    trigger_conditions:
      - "bitcoin family dashboard"
      - "btcframe"
      - "watch-only wallet"
      - "family member balance"
      - "dashboard config watchOnlyWallets"
      - "bitcoin-family-dashboard"
      - "wallet-helper"
      - "bitcoinfamily"
      - "Start9 community submission"
      - "maintaining the package"
      - "next branch"
      - "ExVer tag"
---

# Bitcoin Family Dashboard — StartOS Package Maintenance

## When to Use

Any work on Wahid's **Bitcoin Family Dashboard** StartOS package: the two-repo
split (app + package wrapper), the master-branch workflow, versioning/tagging,
build → sideload → verify loop, community-registry conformance, and **all
package-maintenance decisions**. This skill encodes the rules from Start9's
*Maintaining a Package* doc plus the project's own conventions.

## Not For

- The **standalone app repo** work (frontend features, index.html, asset changes) unless it also touches the StartOS package — the app repo has its own conventions; this skill maintains the package wrapper and its rules.
- Building/sideloading a **non-StartOS deployment** of the dashboard (plain nginx, docker-compose, k8s) — this skill is StartOS/start-cli specific.
- Generic StartOS service packaging for a NEW project (unrelated to the Bitcoin Family Dashboard) — use `startos-service-packaging` instead.
- StartOS node administration (installing the OS, disk management, marketplace browsing) — use `startos` instead.
- Bitcoin Core / bitcoind node operations outside the dashboard's wallet-helper dependency — use `bitcoin-core` or the relevant node skill instead.
- Designing a different family dashboard or a general watch-only wallet frontend — this skill is about maintaining Wahid's specific package, not greenfield frontend work.

**Be strict.** If Wahid asks for something that would violate a rule below
(version bump on a local push, squash-merging `next`, tagging without the `_W`
suffix, installing to `.31`, deleting `assets/`, editing on the wrong branch),
refuse, cite the rule, and propose the conforming alternative before doing it.

## THE TWO REPOS (do not confuse them)

1. **`wahidsaleemi/bitcoin-family-dashboard`** — the standalone dashboard APP
   repo. Inspired by `btcframe/bitcoinfamily` (NOT a fork anymore — GitHub
   `fork: false`). Default branch **`main`**. Contains only the app:
   `index.html`, `assets/`, `images/`, `btc.png`, `favicon.png`,
   `screenshot.png`, README, LICENSE. No packaging files. This is the
   manifest's `upstreamRepo` / `marketingUrl`.
2. **`wahidsaleemi/bitcoin-family-dashboard-startos`** — the StartOS PACKAGE
   repo. Default branch **`master`** (community convention). Contains
   `startos/` (TS SDK), `bitcoinfamily/` (vendored app — the Docker build
   context), `Dockerfile`, `nginx-templates/`, `docker-entrypoint.d/`,
   `wallet-helper.mjs`, docs. Manifest `packageRepo`. Releases live here.

**The package repo is NOT a fork of the app.** The app is vendored into
`bitcoinfamily/` (static site, no upstream releases to track — see
`UPDATING.md`). Keep the vendored copy in sync when the app changes.

Local workspace: `~/bitcoin-family-dashboard-startos/bitcoin-family-dashboard-startos/`
(clone of the -startos repo, on `master`).

## Machines

- **Dev box ONLY:** `ssh start9@192.168.100.42` (hostname `ancient-ink`, NO
  Bitcoin Core — exercises the public-API/mempool path). Do NOT install to
  `.31` unless Wahid explicitly asks.
- `.31` (`192.168.100.31`) has Bitcoin Core — use only when bitcoind-source
  behavior needs verifying.
- Dashboard serves at a dynamic port; balance/scan APIs reachable on localhost
  inside the box: `start-cli package attach bitcoin-family-dashboard -- curl -s http://127.0.0.1:8090/api/...`.
- On-box config: `/media/startos/data/package-data/volumes/bitcoin-family-dashboard/data/main/config.json`.

## Git Workflow & Branch Rules (Maintaining a Package)

### Base branch

- Base branch is **`master`** (package repo). `build.yml`'s PR target and
  `tagAndRelease.yml`'s push trigger must both say `master` — they already do;
  never rename the base without updating the workflows.
- Ordinary work: feature branch → PR → merge → delete branch.

### The `next` branch

- `next` is a long-lived iteration branch, never deleted. `syncNext.yml`
  carries every base push onto it automatically (creates it on first run).
- After `next` picks up the base, **re-check the version it claims** — the base
  can land/release work `next` is carrying; the version may need reconciling.
- **Merging `next` → base: use `gh pr merge --merge` (merge commit), NEVER
  squash or rebase-merge.** A merge commit leaves `next` an ancestor of base so
  the next sync fast-forwards. Squash re-lands content under a new commit and
  permanently diverges `next`. Feature branches (deleted on merge) may be
  squashed — the rule is about the head branch's **lifetime**.
- Parallel release lines (if ever added): each base gets `next/<base>` (slash
  order forced by git). Not currently used — a plain `next` is the whole story.

### Versioning policy (Wahid's rule)

- **Only bump the package version for GitHub releases, NOT for local dev-box
  pushes.** Keep `startos/versions/current.ts` at the released version
  (`0.2.1:0`) across local iterations. The dev box may show a locally-higher
  patch number because StartOS blocks downgrades — cosmetic.
- ExVer format: `X.Y.Z:W` where `:W` is the wrapper revision (always plain
  integer). Manifest version `0.2.1:0` ↔ git tag **`v0.2.1_0`** (underscore,
  not colon). Existing conformant tags: `v0.1.0_0`, `v0.2.0_0`, `v0.2.1_0`.
- Release notes must exist in ALL five languages (en/es/de/pl/fr) or tsc fails.

### Releasing

1. Bump `startos/versions/current.ts` (version + notes, all 5 langs).
   `npm run check`, commit.
2. Push `master` first, then `git tag -a vX.Y.Z_W` + `git push origin vX.Y.Z_W`.
3. Build the s9pk from that tagged commit (config.yaml backup/sed/restore
   dance), capture SHA-256.
4. `gh release create vX.Y.Z_W --title ... --notes ... bitcoin-family-dashboard_x86_64.s9pk`
   on the **-startos** repo. Releases live on -startos, NOT the app repo.

### Chasing upstream / vendored app

- **Verify the thing you pin actually resolves before pinning** (a release
  existing does not mean the artifact exists). For the vendored static app
  there is no dockerTag — the pin is the `bitcoinfamily/` copy + the app repo's
  `master`.
- **Skip prereleases; don't trust GitHub's "Latest" badge** — read the tag list.
- Scale scrutiny to the jump: patch = bump + verify build; minor = read full
  changelog; major = changelog + migration guide + ask whether a data migration
  is needed.
- Follow `UPDATING.md` (package-specific recipe). If its command contradicts
  observable reality, trust the observation, fix the file in the same change,
  and say so in the PR.
- **When syncing a fork, use the fork parent**
  (`gh api repos/<owner>/<repo> --jq '.parent.full_name'`), NOT the manifest's
  `upstreamRepo` (that points at the upstream software project — unrelated
  history). Not currently a fork, but if it becomes one, remember this.

### Depending on sibling package repos (not currently used — the rules anyway)

- Pin git deps at `#next` (or `#next/<base>`); let `package-lock.json` pin;
  CI installs with `npm ci`.
- `npm update` is a **no-op on git-ref deps** — to refresh, delete the
  git-resolved entries from the lockfile and `npm install`.
- Read lockfile diffs as code review; a moved sibling commit can change what
  ships. Inspect with `start-cli s9pk inspect ... cat javascript.squashfs`.
- Keep ONE copy of `@start9labs/start-sdk`; add an `overrides` entry if a
  sibling pins an older one (symptom: generic type errors like "not assignable
  to type `never`").

## Community-Submission Conformance (done — do not regress)

- Default branch `master`; all four CI workflows present (build/release/
  syncNext/tagAndRelease delegating to `Start9Labs/start-technologies`).
- `UPDATING.md`, `assets/ABOUT.md` (real file, not just `.gitkeep`), `TODO.md`,
  repo-specific `AGENTS.md` present.
- README follows the fixed heading set; documents the watch-scan health check,
  optional bitcoind dependency, wallet-helper subcontainer, ofVolumes backup
  strategy, file-model ownership. Quick Reference YAML complete (no image tags).
- LICENSE = BlueOak-1.0.0 (file + manifest agree). Manifest: `packageRepo` →
  -startos repo, `upstreamRepo`/`marketingUrl` → app repo, `donationUrl` →
  coinos.io/pay/wahid.
- Never delete the `assets/` dir (start-cli ingredient list hardcodes
  `./assets`) — keep at least one real file in it.

## Core Architecture (unchanged)

- **Frontend:** single `bitcoinfamily/index.html`, heavily modified from
  upstream: dark mode, Pexels backgrounds, price sources, rotating charts,
  family CRUD via StartOS Actions, avatar upload/crop, watch-only balances.
- **Balance helper:** `wallet-helper.mjs` — Node on port 8090 in the nginx
  container; parses output descriptors (wpkh/pkh/sh(wpkh)/tr/bare xpub; deps
  bip32@4 / bitcoinjs-lib@6 / tiny-secp256k1 via `package-helper.json`),
  derives addresses, queries bitcoind or the multi-provider public chain
  (mempool.space → blockstream.info → blockcypher.com → blockchain.info).
- **Health check:** `watch-scan` in `startos/main.ts` returns `loading`
  (animated) while scanning, `success` when idle, `failure` when helper
  unreachable — via a custom fn using `subcontainer.exec`, NOT `runHealthScript`
  (which always reports success on exit 0). `loading`/`starting`/`waiting` →
  animated tui-loader; `success` → green check; `failure` → red triangle
  (verified in StartOS UI source `health-check.component.ts`).
- **Scan-status contract:** helper keeps `needsBalance`; `/api/scan-status`
  returns `scanning:true` + `note:'waiting for providers'` until a real balance
  caches; background retry every 2 min while `needsBalance`. Do NOT regress to
  showing "idle" while the balance is unknown.

## Frontend Balance Display (verified pattern)

- `effectiveBtcFor(member)` → watch balance when numeric else
  `member.btcAmount`; `renderMemberBalances(currentPrice)` renders btc/USD/P&L
  from the effective balance. All three call sites (init, fetchWatchBalances,
  updatePrice) MUST use it or USD/P&L drift from displayed BTC.
- Watch-only configured but unresolved → show **"Fetching..."** + tooltip, hide
  USD/P&L (never the stale manual figure).
- No separate badge line under the balance (user preference).

## Build → Sideload → Verify Loop (dev box .42)

1. `npm run check` (tsc) then `npm run build` (ncc).
2. Build s9pk: backup `.startos/config.yaml`, `sed` its `default:` to
   `https://localhost:9999`, run `make x86`, restore the backup.
3. `scp bitcoin-family-dashboard_x86_64.s9pk start9@192.168.100.42:/tmp/`.
4. `ssh start9@192.168.100.42 'start-cli package install -s /tmp/...s9pk'`.
5. Verify: journalctl, curl `/api/wallet-balance` + `/api/scan-status` via
   `package attach`, check the served page for new frontend symbols.
6. Give Wahid SHA-256 + scp command for his handoff.

## GitHub-Side Edits (Wahid edits files directly on GitHub)

Wahid sometimes edits the repo through the GitHub web UI, leaving local behind
origin. Sync pattern: `git fetch`, check divergence with
`git rev-list --left-right --count origin/<branch>...<branch>`, inspect the
remote-only commit before pulling, `git pull --ff-only` only if local is clean
and the diff is additive. Verify no ahead/behind after.

## Pitfalls

1. **mempool.space from StartOS containers: AAAA-only DNS + no IPv6 route** —
   multi-provider chain is the shipped fix (see
   `references/mempool-network-issues.md`).
2. **Never report a bogus 0 when a source fails** — return null so bitcoind
   fallback kicks in.
3. **429 rate limits are NOT network failures; shared egress IPs get
   temp-blocked** — don't diagnose as code bug, keep scans gentle.
4. **Scan sizing (Wahid requirement):** `MAX_RANGE = 200`/branch,
   `GAP_LIMIT = 20`, `SCAN_CONCURRENCY = 5`, `SCAN_BATCH_DELAY_MS = 200`.
5. **Cross-source fallback:** try the chosen source, then the OTHER.
6. **On-box config edits** via sudo python are the fast test path.
7. Verify the SERVED page contains new frontend logic after install (stale
   nginx cache shows old JS while the API works).
8. **DO NOT delete the `assets/` dir** — ingredient list hardcodes it.
9. Probing the helper in-container: see `references/container-probing.md`.
10. Background retry + in-flight guard: `runBalanceScan()` shared between HTTP
    handler and 2-min tick; keep scan execution in a function that returns
    results rather than writing to `res`.
11. **Balance exactly DOUBLE the real amount (330→660) = multisig `<0;1>`
    double-count.** In `deriveAddress()`'s wsh branch, derive the branch being
    scanned (`parsed.trailing`), never each key's own `k.paths[0]` — for a
    `<0;1>` descriptor both scans hit branch 0 and count every UTXO twice.
    Only the mempool path had this bug; `buildScanDescriptor` (bitcoind) was
    correct. Full detail: `references/watch-only-wallet-backend.md` gotcha 3a.
12. In-dialog warnings: `Value.select` `footnote`; **i18n keys are POSITIONAL**
    — inserting a key renumbers default.ts AND every language block; renumber
    together or tsc fails with TS2739.
13. Health-check icon semantics (see Core Architecture).
14. When Wahid says "don't build a package / more changes coming" — commit doc
    changes but HOLD build/sideload until he asks.

## References

- `references/watch-only-wallet-backend.md` — descriptor import + per-member bitcoind wallet pipeline
- `references/frontend-balance-display.md` — watch-overrides-manual UI refactor
- `references/mempool-network-issues.md` — DNS/IPv6 diagnosis + multi-provider fallback chain
- `references/container-probing.md` — node probe scripts inside the StartOS container
- `references/maintaining-a-package.md` — full Start9 maintenance ruleset quick-reference
