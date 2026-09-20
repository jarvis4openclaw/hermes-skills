---
name: lightning-gift-app
description: Work on the Send Bitcoin Lightning gift app (the lightsats fork) — verifying which build is actually deployed on CT 123, running the in-container test suite and contrast guard, and measuring UI state without touching the frozen good copy.
version: 1.1.0
category: devops
metadata:
  hermes:
    tags: [lightning, lightsats, nextjs, proxmox, docker, verification, gift]
    related_skills: [sendbitcoin-gift-site, proxmox-ssh-lifecycle, ssh-file-deploy, caddy-proxy-management]
    trigger_conditions:
      - "lightning-gift"
      - "lngift.wahidsaleemi.net"
      - "lightsats"
      - "CT 123"
      - "the dev copy of the gift app"
      - "giftmode branch"
      - "is the fix deployed"
      - "which build is live"
      - "contrast guard"
      - "gift ladder"
      - "seed a reviewer account"
      - "tip status / Tip.status"
      - "LNbits FakeWallet"
      - "the test suite baseline"
      - "dock geometry / first-paint probe"
      - "feature removal evidence"
---

# lightning-gift-app — Send Bitcoin Lightning

A stripped-down fork of **lightsats** (MIT) optimised for gift-giving over Lightning. Two independent
copies exist on Proxmox host **white**, deliberately kept apart (see the wiki for the rationale and the
full decision tables).

| Copy | Container | Address | Role |
|---|---|---|---|
| **GOOD** | CT 122 `lightsats` | 192.168.100.28 → `lightsats.wahidsaleemi.net` | frozen, known-good — **never** a target of dev work |
| **DEV** | CT 123 `lightning-gift` | 192.168.100.29 → `lngift.wahidsaleemi.net` | the copy being modified |

- **Source on CT 123:** `/opt/lightning-gift/src` — working branch **`giftmode`**, rollback tag
  `pre-removals-2026-09-15`. Repo layout: `app/` (Next.js 12.3.7 + NextUI v1 beta), `scheduler/`, `postgres/`, `scripts/`.
- **Compose:** `/opt/lightning-gift/docker-compose.yml` (project `lightning-gift`; services `app`, `db`, `lnbits`, `mailhog`, `scheduler`).
- **Wiki (LLM Wiki):** `~/wiki/projects/lightning-gift.md` — **singular** filename, despite how people say it out loud.

Hard boundaries: the dev copy has its **own** Postgres and its **own** LNbits. Never run Prisma
migrations or mint/delete LNbits wallets against the good copy — that is the one failure mode the whole
two-copy arrangement exists to prevent.

## When to Use

- Any change, measurement or review of the Send Bitcoin Lightning app on Proxmox host **white** (CT 122 good / CT 123 dev)
- Someone (human or another agent) reports a fix shipped and you have to establish which build is live
- Running or interpreting the in-container test suite (the 51-test baseline) or the contrast guard
- Measuring UI state, first paint, layout geometry, contrast ratios or dock behaviour in the running app
- Seeding dev data — reviewer accounts, gift ladders, mixed tip states — for a demo or a review
- Proving a feature removal three ways (source, database, live HTTP) or a "nothing does X" claim
- Handing harness artifacts, diffs or findings to another session or to your human

## Not For

- The sendbitcoin.gift static site, its deploy or the printed greeting card → use `sendbitcoin-gift-site` instead
- Turning a CT/VM up, down or back up; consoles and node-side lifecycle → use `proxmox-ssh-lifecycle` or `proxmox-host-management` instead
- The Caddy vhost, TLS or edge routing itself → use `caddy-proxy-management` instead
- Deploying or packaging an unrelated containerised app → use `self-hosted-app-deployment` instead
- Generic "edit a file locally, put it on a remote host, restart the service" mechanics → use `ssh-file-deploy` instead
- The P2TR timelock / lockbox crypto rather than the app around it → use `bitcoin-script-engineering` instead
- A generic contrast/token/a11y methodology for any built page → use `web-quality-audit` instead (this skill covers *this* app's guard and harness)
- Working the kanban card lifecycle that produced the task → use `kanban-worker` instead

## Verify deployed state before claiming anything

```bash
# 1. HTTP — direct, then through Caddy
curl -s -o /dev/null -w "%{http_code}\n" -m 10 http://192.168.100.29:3000/
curl -sk -o /dev/null -w "%{http_code}\n" -m 10 --resolve lngift.wahidsaleemi.net:443:192.168.100.53 https://lngift.wahidsaleemi.net/

# 2. Repo truth
ssh root@192.168.100.29 'cd /opt/lightning-gift/src && git branch --show-current && git log --oneline -3 && git status -sb'
```

The `*.wahidsaleemi.net` wildcard does **not** resolve from the agent host (`getent hosts` returns
nothing), so plain `curl https://lngift.wahidsaleemi.net/` exits `000` and reads as "the app is down" when
it is up. Pin the Caddy container with `--resolve ...:443:192.168.100.53` (CT 107). Treat a `000` without
`--resolve` as a DNS artifact, not an outage.

`git status` clean + a commit hash is not deployment evidence on its own: a container serving the
previous build answers 200 just as happily. Rebuild after every source change:
`docker compose -f /opt/lightning-gift/docker-compose.yml build app && ... up -d app`.

**The converse also holds: what is running may match no commit at all.** A rebuild fired while the tree
is dirty produces an image no commit describes, and HTTP 200 will never tell you. Compare the three
timestamps — dirty files, image, container:

```bash
ssh root@192.168.100.29 'cd /opt/lightning-gift/src/app && git log --oneline -1 && git status --porcelain; \
  docker inspect -f "image_created={{.Created}}" lngift-app:local; \
  docker inspect -f "container_created={{.Created}} started={{.State.StartedAt}}" lngift-app'
```

An image `Created` later than the newest modified file, with the container created after the image, means
the deployed build **includes uncommitted work**. Report that as the state of the system — it is the
gating fact for review and for measuring anything — instead of quoting HEAD as though it were deployed.

**When someone reports a fix shipped, prove which build is live from a rendered artifact.** Pick
something the new commit introduced that no earlier build can render — an alpha value in a border, a new
glyph slot, a chip's 12×12 svg — and confirm it in the DOM. HEAD, a clean tree and a fresh image
timestamp are all compatible with the previous build still answering 200, and with another writer
rebuilding mid-measurement; the rendered artifact is not.

**Batch the LAN steps into one command.** Every direct-to-CT-123 step (an `ssh`, or an HTTP call at the
raw 192.168.100.29 address) can raise an approval prompt, and a prompt that expires leaves the command
unrun while looking like nothing happened. Put a whole sequence in **one** command — seed + verify +
suite + guard — and say in the report which single approval it needs; when a prompt does expire, report
that plainly and hand the user the exact action instead of re-issuing the same call.

**One writer per checkout.** This tree is worked by more than one session and more than one bot profile.
Before mutating it, look for in-flight work (`ps -ef | grep -E "ssh -N|yarn build|docker compose build"`,
`ss -tnp`, `find app -newermt '-90 minutes'`), leave another writer's uncommitted files untouched, and
say so in the report. An untracked file created by the other session is also why a file can appear in a
commit while `git status` showed nothing.

**Re-measure, don't re-read, after a fix lands.** A builder's "verified" is a self-report: run the same
probe that produced the before numbers and quote both, with the run counts. Where a check cannot be
re-run (the in-container suite, the token guard), label it as reported rather than folding it into your
measurement — an absent check is information, a silent one looks like a pass. Full recipe, probe list
(now including the multi-option comparison and dock-geometry probes) and sampling rules:
`references/ui-verification.md`.

## Running the test suite

There is **no `node` on the CT host** — the suite runs inside the app container:

```bash
ssh root@192.168.100.29 'docker compose -f /opt/lightning-gift/docker-compose.yml exec -T app node --test tests/'
```

`app/tests/` holds `phase2-validation.test.mjs` (source-cleanliness greps + live HTTP + Postgres
assertions), `email-render.test.mjs`, `mjml-render.test.mjs`, `nwc-custody.test.mjs` and
`phase8-nostr.test.mjs`. **51 tests is the baseline** (25 → 34 → 51 as the phase-8 Nostr/NWC and
render tests landed) — anything below it is either a regression or a harness abort, and the two are
not the same thing. Confirm the CURRENT baseline before reading any failure as a regression. Full
recipe, including how to tell them apart and the fix for the `psql`-in-container abort:
`references/test-harness.md`.

**Run the suite in the app service, not in a `node:20-alpine` sidecar.** The alpine runner aborts the four
`db:` tests as `ERR_TEST_FAILURE` on `libssl.so.1.1` (missing for Prisma's musl engine) and reports
**30/34** — which reads exactly like a regression and is not one. `exec -T app node --test tests/` is the
only reading that means anything.

**A test that runs in the app image must not depend on a host binary** (e.g. shelling out to `psql`) — the
image ships no Postgres client, so those assertions die as `ERR_TEST_FAILURE` while the database is
perfectly fine. Reach for the client that is already installed (`@prisma/client`, verified loadable
in-container) or run the check from the `db` service, where `psql` does exist.

## The contrast guard — it runs in the image now

`scripts/check-contrast.mjs` resolves its source **dual-path** (`findThemeSource()` reads
`../app/theme.ts` from a repo-root checkout or `../theme.ts` from the in-image copy — one file serves
both layouts, no fork to drift) and is **baked into the app image**: `app/scripts/` is inside the
build context. CT 123 has no node on the host, but the image does — run it in-container:

```bash
ssh root@192.168.100.29 'docker compose -f /opt/lightning-gift/docker-compose.yml exec -T app node scripts/check-contrast.mjs </dev/null; echo "exit=$?"'
# equivalent: ... exec -T app yarn contrast   (npm script added to app/package.json)
```

The host-checkout recipe below remains the fallback for an image older than the guard commit:

```bash
mkdir -p /tmp/cc/scripts /tmp/cc/app
ssh root@192.168.100.29 'cd /opt/lightning-gift/src && cat scripts/check-contrast.mjs' > /tmp/cc/scripts/check-contrast.mjs
ssh root@192.168.100.29 'cd /opt/lightning-gift/src && cat app/theme.ts'           > /tmp/cc/app/theme.ts
cd /tmp/cc && node scripts/check-contrast.mjs; echo "exit=$?"
```

It asserts pairings **by token name**, so a palette refactor that replaces a flat token with a ramp
breaks it: rebuilding gray into `gray50…gray900` makes the `secondary text` pairing fail as `missing
token: gray` until the guard is re-pointed at `gray700` — a failing guard, not a skip. Nothing runs it
(no CI), so the drift is silent: re-run it after **any** token rename and put its exit code in the
verification record beside the test count.

## Feature-removal claims need three-way evidence

Every removal in this repo (leaderboards, achievements, advertisements, tip groups, Metabase, admin
trim) is asserted three ways, and a removal only "holds" when all three agree:

1. **Source** — `grep` for the identifiers across the tree (the suite encodes these as regex greps).
2. **Database** — the table/enum/column is gone from Postgres (`db` container, not the app container).
3. **Live HTTP** — the removed routes 404/301 and the retained ones answer 200.

Quoting SQL through `ssh` + `docker compose exec` is the fragile part — prefer stdin or `sh -c` over
nested `-c "...'...'..."` layers; a mis-quoted `\'` produces a bare SQL syntax error that looks like a
broken database.

**A "nothing does X" claim is proved by enumerating the writers, not by reading the file you suspect.**
For a state machine like `Tip.status`, grep the enum member across `pages/` and `lib/` to list every
writer, then grep each candidate helper's call sites (`grep -rn "markTipAsUnseen" --include=*.ts*`) — a
helper referenced only by its own declaration has no callers, and a handler whose file contains none of
the relevant vocabulary is not quietly doing the work. Report the mechanism too (which route was *meant*
to do it, and what removed it), or the next session re-derives the wrong fix.

## Pitfalls

1. **Image builds need the Sentry CDN.** `@sentry/cli`'s postinstall downloads `sentry-cli` from
  `downloads.sentry-cdn.com`, and CT 123 resolves that name IPv6-first over a dead IPv6 path, so the
  builder stage's `yarn install` intermittently dies with `ECONNREFUSED` / `000` while DNS itself is
  fine. A failed build leaves the **previous** image in place, so an app that answers 200 proves nothing:
  check `docker inspect -f '{{.Created}}' lngift-app:local` against your change, retry the build (it
  succeeds on a warm answer), and only if it keeps failing pin the host via the build's `extra_hosts`.
2. **A claim about the app's source is a self-report until you read the source.** A rendered page showing
  an empty region where a section should be is not the same fact as the section being deleted: the home
  page renders its body past an early return gated on `pageLoaded`, which flips on window `load`, so a
  headless capture can show a void (failed embeds, or the gate never opening on a slow first paint) while
  the markup is fully intact. Check the file and the gate before speccing a replacement.
3. **A paint bug cannot be proved by sampling after `Page.navigate`.** The first samples read the
  *previous* document — the navbar fill you measure belongs to the old page, which manufactures a
  flash that isn't there. Install the recorder with `Page.addScriptToEvaluateOnNewDocument` (it runs
  before the inlined `THEME_INIT_SCRIPT`) and stamp every sample with `data-theme` and
  `location.pathname`, so a stale-document frame is identifiable rather than reported. Working
  examples: `~/lngift-harness/jg-firstpaint-probe.mjs`, `jg-close-ui-findings.mjs`,
  `jg-chips-six.mjs`, `jg-signin-copy-deep.mjs` — see `references/ui-verification.md`.
4. **The pre-paint theme stamp is not the last writer.** `lib/useThemeMode.tsx` starts at
  `useState("light")` and writes `data-theme` from a mount effect, so dark mode still gets a 1–2 frame
  (12–34 ms) cream repaint after hydration even though the inline init script stamped `dark`
  correctly. A green first-paint check on the initial value does not cover the hydration overwrite.
5. **A fill that is invisible is a different defect from a label that is unreadable.** The `/signin`
  Copy button's label is now 13.54:1 (dark) — fixed — while its fill measures 1.16:1 against the card
  it sits on with `border: 0 none`, so the control has no 3:1 boundary. Measure the label against the
  fill *and* the fill against what it sits on; a finding that quotes one ratio usually has two halves.
6. **CDP `clip` is in *document* coordinates; element geometry is in *viewport* coordinates.** A clipped
  capture of a sticky band (navbar + docked CTA) while the page is scrolled returns blank page surface —
  it reads as "the app painted nothing". Capture the viewport unclipped at `deviceScaleFactor: 1`
  (1 image px = 1 CSS px) and sample in viewport coordinates; that is what `jg-dock-shadow-probe.mjs` +
  `jg-dockband-sample.py` do.
7. **A script delivered over ssh on stdin (`ssh host 'bash -s' < script.sh`) loses its tail to any remote
  command that reads stdin** — `docker compose exec -T db psql …` swallows every following line and the
  run ends mid-script with a 0 exit code. Put `</dev/null` on every such command.
8. **A one-viewport page cannot be scrolled to bring a target into a sticky band.** With option C's Done
  section collapsed the phone page is barely taller than the viewport, so `scrollTo` clamps and the group
  header never reaches the dock — expand the disclosures first, then position the rule. Same family as
  the 1×1 px switch: verify the scroll actually landed (`scrollY` before/after) before concluding.
9. **The v2 design tokens must survive "fixes".** The house palette is `#FF8000` brand, `#CC6200` control
  boundaries, `#B05700` body links, `#FFFDF9` paper, `#1A1611` ink. The primary button is **ink on orange
  (7.15:1)**; white on `#FF8000` is 2.52:1 and fails AA. Framework defaults (NextUI `primary` blue,
  `$white` as a surface token) are unmapped tokens, not decisions — they are the usual source of
  "why is there blue/grey on this page".
10. **"Exactly one X" is a geometry claim, not a DOM count.** One affordance can be two nested nodes at
  identical coordinates (the create CTA is a `static` wrapper plus a `relative` inner), so a raw
  `querySelectorAll` count reports 2 for a page that shows one button — and an acceptance gate written
  that way fails every variant equally, control included. Dedupe by text + rounded box and quote both
  numbers ("1 visual / 2 nodes").
11. **Verify the interaction landed; a dispatched click that misses is silent.** CDP input does not hit a
  target outside the viewport (a header at y=1414 in a 900 px viewport does nothing), and a coordinate
  click at a 1×1 px `Switch` input does not toggle on the narrow phone viewport at all (0/2 checked; the
  same click works on desktop). Scroll the target into view, re-read the state you expected to change,
  and fall back to `el.click()` — then report the target's size, because a target a machine cannot hit is
  usually one a thumb cannot hit either.
12. **Measure the state the question is about, not the top of the page.** A docked/sticky claim is not
  testable at first paint: scroll to the row the design exists for and record the docked geometry (pill
  top against navbar bottom). Read the container's **own** computed background and border rather than the
  blend a pixel sample suggests — a probe that samples beside a sticky pill can report a tint the element
  never had.
13. **A control that no longer exists cannot be re-measured.** Once the fix ships, the pre-fix page is gone.
  Freeze the control's numbers in the record and mark the harness's control option unready, rather than
  re-running it and reporting the new build as "before".
14. **NextUI v1-beta renders hash classes, not semantic ones.** A `[class*="nextui-card"]` selector
  matches nothing even when the component is on the page — classes come out as `nextui-c-XXXX`.
  Identify Cards by geometry (border-radius ≥ 10px plus a wide, tall box) or by an inline-style marker.
  And isolate ONE probe variable at a time when a check misses: a selector that misses on every auth
  state reads as an auth-state problem when it never was — the diagnostic that flips only the selector
  is what attributes the miss correctly.
15. **The logo and favicon are four assets that move together.** The inline mark (`Logo.tsx`, bolt
  `var(--nextui-colors-primary, #FF8000)`), `app/public/images/logo.svg` (print companion),
  `favicon.svg` and `favicon.ico`. Changing the bolt's colour means the favicon tile swaps to the ink
  `#1A1611` (orange-on-orange is invisible) and **`favicon.ico` must be regenerated** — it is a
  separate binary asset that silently lags the SVG (rasterise headless at 48px, assemble 16/32/48
  with PIL, pixel-verify tile + bolt + transparent corners before shipping).
16. **Verify a third-party URL swap with a live request before committing.** Provider version migrations
  (DiceBear's avatar API: voxel-art exists at 10.x, not 7.x) leave the old path 404ing while the code
  still merges and tests green — curl the new URL first; the rendered avatar is the final proof.
17. **Don't touch the good copy.** No migrations, no LNbits user operations, no branch switches in CT 122's
  clone, ever.

## Seeding dev data (reviewer accounts, mixed-state gift ladders)

The harness lives in the repo at `src/harness/` (59 probes/harnesses/seeds + a `SHA256SUMS` manifest,
committed) and on the agent host at `/home/wahid/lngift-harness/` — `seed-reviewer.py`,
`seed-withdrawn-fix.py`, `inject-reviewer-session.mjs`, `verify-session.py`, `HANDOFF.md`. Session
jars and secrets live **outside** the repo (runtime-loaded from files that never enter git) — keep
that boundary when adding files: screen for embedded values before committing any harness code.

- **Headless sign-in.** `POST /api/auth/csrf` → `POST /api/auth/2fa/send {email,locale,callbackUrl}`
  → read Mailhog (`/api/v2/messages`; the mail is 
  rendered MJML with `=\r\n` soft breaks) → the link is `${APP_URL}/verify/<jwt>`, **not**
  `/verify-signin/` → `POST /api/auth/callback/2fa` (form-encoded) with `csrfToken`, `token`,
  `callbackUrl`, `json=true`. The cookie is `__Secure-next-auth.session-token`, so a browser only ever
  sends it over https, and a CDP `Network.setCookie` bound to a different host is dropped silently:
  drive the https origin itself (`chromium --host-resolver-rules="MAP <host> <caddy-ip>"`).
- **Funding is self-verified, from both routes a party may open first (`lib/pollFundingStatus.ts`).**
  Since `cdd5826` (and `5185596`, which extracted the helper and added the recipient side) every GET of an
  `UNFUNDED` gift asks LNbits whether its funding invoice has been paid and flips it to `UNSEEN`. The
  sender's tip page (`hooks/useTip.ts` `pollTipConfig`) and the recipient's claim page
  (`hooks/usePublicTip.ts`, `refreshInterval: 1000`) both re-GET at 1s, so the flip lands within ~1s of
  the invoice being settled, whichever side is looking. The public route is unauthenticated, so an
  anonymous visitor holding the link triggers the read too — that is the point: a payer who settles the
  invoice and closes the tab must not strand the gift at `UNFUNDED` while the recipient polls a route that
  can never change its status. Obsolete fallback, for a build older than `cdd5826` only: settle the invoice
  in LNbits for real, then flip with `POST /api/admin/tips/{id}/changeStatus` as a `SUPERADMIN` (insert
  the `UserRole` row if the dev DB has none) — say so when handing a ladder to a reviewer. The 410 on
  `pages/api/webhooks/invoices.ts` is **upstream's deliberate design**, not our breakage. Details,
  evidence and the wallet-scoping trap that fakes a pass: `references/funding-path.md`.
- **FakeWallet constraints.** `pay_invoice` accepts only invoices minted by the same instance
  (`payment_secrets` is in-memory, lost on restart) and enforces `wallet.balance_msat`, so a payer needs
  a credited `apipayments` row first (the `Admin credit` pattern); the wallet endpoint reports `balance`,
  not `balance_msat`.
- **Ladder transitions that are genuinely app-produced:** `markSeen` (public route), `claim` (tippee
  session, requires status `SEEN` first), `POST /api/invoices {invoice, flow:"tippee"}` — **omit** the
  `tipId` key, `null` is rejected by `LnbitsWalletWhereUniqueInput` — and `reclaim` (tipper session,
  `refundableTipStatuses`). The tippee withdrawal sweeps every claimed non-expired gift of that session
  user and demands the invoice equal their exact sum: order the claims, there is no per-gift selector.
- **Ladder states are fixtures, so never mutate the ladder to get a new render state.** Other agents
  measure against this ladder, and a transition that consumes a state (a tippee withdrawal sweeps every
  claimed gift) silently removes a rung they depend on. Seed a **second** account for a new state — a
  one-gift account is the natural partner to the seven-gift ladder, not a reason to trim the ladder — and
  run state-consuming transitions *after* the renders that need the states, then re-seed the consumed
  rung with `seed-withdrawn-fix.py`.
- **`/dashboard` hides states by default.** `SentTips` filters `completedTipStatuses` and old (expired)
  gifts behind two `Switch`es whose inputs are 1×1 px — click the inputs, not the labels, or the list
  looks like it is missing rows. For an all-states measurement flip **both** by coordinate
  (`Input.dispatchMouseEvent` at the input's box): with them off, WITHDRAWN and RECLAIMED are not in the
  DOM at all. `jg-chips-six.mjs` does exactly this — use it rather than declaring six states verified
  from the four the default view shows.

## Handing artifacts to another agent or session

Remote trees come across without scp gymnastics:

```bash
mkdir -p /home/wahid/lngift-harness && cd /home/wahid/lngift-harness
ssh root@192.168.100.29 'cd /opt/lightning-gift/src && tar czf - app/tests app/package.json app/scripts | base64' \
  > harness.b64 && base64 -d harness.b64 | tar xzf - && rm -f harness.b64
```

State the provenance when handing the copy off (which host, which commit it was pulled from) — a
patched copy that silently diverges from the deployed tree is worse than no copy.

**Anything written for the user to review goes in `/home/wahid/clawd/tmp/` — never `/tmp`.** Plans,
reports, diffs and hand-offs all belong there: the user reads them from their own machine, and the agent
host's `/tmp` is awkward for them to reach. State the absolute path in plain text, since the TUI has no
attachment channel.

## Related

- `~/wiki/projects/lightning-gift.md` — topology, phase decisions, open questions, deployment record.
- `sendbitcoin-gift-site` — the sibling product; its v2 tokens are this app's palette. The reference
  values live locally at `/home/wahid/timelock-gift/public/v2/tokens.css` (the live reference site is
  unreachable from this host).
- `proxmox-ssh-lifecycle` — CT/VM lifecycle on the Proxmox hosts.
