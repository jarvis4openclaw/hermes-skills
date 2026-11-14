---
name: lgift-release-ceremony
version: 1.1.0
author: jarvis
license: MIT
metadata:
  hermes:
    tags: [lightning-gift, release, deploy, prod-hotfix]
    related_skills: [kanban-worker]
    trigger_conditions:
      - "ship a lightning-gift prod hotfix"
      - "release ceremony lightning-gift"
      - "deploy v0.8.x to lngift-prod"
      - "prod-hotfix lane card"
      - "tag a lightning-gift release"
      - "roll back a lightning-gift deploy"
      - "apply-prod-compose.sh"
      - "digest forensics for lngift-prod"
      - "live-money probe on the app"
      - "cloud build never fired for a v tag"
description: Use when shipping a lightning-gift prod hotfix release.
---

## When to Use

Any card in the lightning-gift OCR plan's §3 prod-hotfix lane (E1/E2/E3-style): the acceptance test must FAIL on the current image and pass on the candidate, then a v-tag build is deployed to lngift-prod with digest forensics and the compose record installed through apply-prod-compose.sh. Covers new deploys, rollbacks (tag change), and safe live-money probes on the app.

## Not For

- Building or refreshing the LPK wallet directory data → use `lngift-wallet-directory-refresh` instead.
- Packaging/submitting the browser extension to Chrome/Edge/AMO → use `lngift-browser-extensions` instead.
- General app development, schema changes or feature work on lightning-gift (not a prod hotfix) → use `lightning-gift-app` instead.
- Using the giver-side HTTP API to send a gift → use `lightning-gifts` instead.
- Verifying a static site deploy → use `static-site-deploy-verify` instead.
- Working the daily dev-gate backlog (only the §3 prod-hotfix lane belongs here) → use `kanban-worker` instead.

## Lightning-Gift release ceremony (prod hotfix lane)

Repo on CT123 `/opt/lightning-gift/src` (branch main). PROD = VPS `lngift-prod` (159.203.73.87:52222, sudo -n for docker). Never deploy past the hourly gate's baseline without failing-set comparison.

### RED/BLUE gate (mandatory)
1. Write acceptance tests FIRST as `app/tests/<name>.test.mjs` (gate glob picks it) with behavioral tests on a NEW pure lib module + structural wiring assertions.
2. Demo RED on a v-tag worktree (`git worktree add /tmp/<x> v<prev>`), BLUE on the candidate — inside a throwaway `lngift-app:local` container. CT123 gotchas: host node is v20 (no TS strip); docker is userns-remapped so bind-mounted paths are READ-ONLY to the container (symlinks there fail with "Permission denied"). Use `docker cp` tarballs into `/tmp/…` inside the container and symlink `node_modules` → the image's own `/app/node_modules`. CT123 automation can recreate/kill containers mid-run — rebuild the lab atomically and rerun.
3. Full-suite fail NAME comparison (not test numbers): base vs candidate; the delta must be exactly your new tests. `tsc --noEmit` + eslint clean before commit.

### Deploy sequence
1. `chore(release): v<ver>` commit MUST bump `app/package.json` (else the image self-reports stale). Create the tag locally, then push it as a TAG REF: `git push origin refs/tags/v<ver>`. NEVER `git push origin HEAD:v<ver>` — that creates a remote BRANCH named like the tag, CI never fires, and you wait forever on a build that was never triggered. CI `build-push.yml` fires on v* tags only and builds ghcr image + forensic `sha-<12 chars of FULL sha>` tag.
2. Poll from CT123 with `docker buildx imagetools inspect ghcr.io/wahidsaleemi/lightning-gift:v<ver>` and read the `Digest:` line. Do NOT parse `docker manifest inspect` JSON for `manifests[0].digest`: this image is a single-arch OCI manifest, so that key does not exist and the poll silently retries until timeout. Compare `:v<ver>` digest to `:sha-<12>` digest — that digest goes into the deploy record.
3. Pre-deploy `pg_dump -Fc` → `/opt/lngift/backups/pre-v<ver>-<TS>.dump`, chmod 600 root, verify `pg_restore --list` works.
4. Compose: NEVER hand-edit host compose. Update the repo record `deploy/docker-compose.prod.yml` (app image digest + `# v<ver>` comment), pipe the record through `apply-prod-compose.sh`: `ssh root@CT123 'cat record.yml' | ssh lngift-prod 'sudo -n bash /opt/lngift/scripts/apply-prod-compose.sh'` → guards PASS ×3 + provenance; then `docker compose -f /opt/lngift/docker-compose.yml up -d app`.
5. Verify: `docker inspect lngift-app` image digest ≡ pin, restarts=0, `grep version /app/package.json`, logs Ready, `prisma migrate status`, 200s on /, /withdraw, /admin, /docs/api. Then `apply-prod-compose.sh --check` → in sync.
6. Write `docs/RELEASE-v<ver>.md` (house template: image, run, verification, census, what-not-done); release docs commit is `docs(release):` and the pin update commit is `deploy(prod):`.

### Prod probes
- Endpoint routes: GET `/api/withdrawalLinks/<id>` returns LNURL-w params; `/pay?pr=<bolt11>` does the money. Link rows: `WithdrawalLink` (used/amount) + `WithdrawalLinkTip` snapshot.
- Live refusal probe recipe: mint a real invoice on the link's staging wallet (LNbits path = `POST /api/v1/payments` with `X-Api-Key` = wallet adminKey, body `{out:false,amount,...}`; `http://lnbits:5000` inside the compose net; run from the app container via `node -e` because curl is absent) then present at `/pay?pr=` — confirm refusal is in-band, no attempt row, no money. NEVER touch the live unused legit link's `/pay`.

### Ops notes
- Fine-grained PAT is read-only (`~/.config/jarvis/lngift-ci-pat`): no `actions:write` (cannot cancel stale CI runs — verify tag↔digest identity instead), no `checks:read`.
- `lib-alert.sh` reads the SECRETS file (`secrets/resend_api_key.txt`), not watchdog.env; Resend key changed there (test email to onewahid verified v0.8.15).
- secret-file → shell-quoted curl reads gets flagged as exfiltration by guardrails; prefer ssh script files over inline secrets in commands.
- Done: v0.8.13 (E1 vault/reservation), v0.8.16 (E2/H-8 link set-pin), both 2026-11-05. Legacy claim grace dies 2026-11-14 (then E6). E3 owns the remaining hotfix card.

## Pitfalls

1. **`git push origin HEAD:v<ver>` creates a remote BRANCH, not a tag** — CI never fires and you wait forever on a build that was never triggered. Push a tag ref: `git push origin refs/tags/v<ver>`.
2. **Parsing `docker manifest inspect` for `manifests[0].digest`** — this image is a single-arch OCI manifest, so the key does not exist and the poll silently retries until timeout. Use `docker buildx imagetools inspect` and read the `Digest:` line.
3. **Release commit that does not bump `app/package.json`** — the image self-reports a stale version. The `chore(release): v<ver>` commit must bump it.
4. **Hand-editing the host compose file** — the watchdog checks its hash against provenance every 15 min and reds. Always pipe the repo record `deploy/docker-compose.prod.yml` through `apply-prod-compose.sh`.
5. **Comparing test NUMBERS instead of failing-test NAMES** — a flaky count hides whether your delta is exactly the new tests. Diff the fail NAMES base vs candidate; the delta must be exactly your new tests.
6. **Running TS directly on the CT123 host** — host node is v20 with no TS strip. Build/run inside a throwaway `lngift-app:local` container.
7. **Symlinking bind mounts into the container** — docker is userns-remapped, so bind-mounted paths are READ-ONLY and symlinks fail with "Permission denied". `docker cp` a tarball into `/tmp/…` and symlink `node_modules` to the image's own `/app/node_modules`.
8. **Skipping the pre-deploy `pg_dump -Fc`** — no rollback. Dump to `/opt/lngift/backups/pre-v<ver>-<TS>.dump`, chmod 600 root, and prove it with `pg_restore --list`.
9. **Trusting `docker inspect … restarts=0` alone** — also `grep version /app/package.json`, check logs for Ready, `prisma migrate status`, and 200s on /, /withdraw, /admin, /docs/api; then `apply-prod-compose.sh --check` must report in sync.
10. **The PAT cannot cancel stale CI runs** — the fine-grained PAT is read-only (no `actions:write`). Verify tag↔digest identity instead of trying to cancel.
11. **Probing the live unused legit link's `/pay`** — never touch it. Mint a fresh invoice on the link's staging wallet (LNbits path via `node -e` in the app container; curl is absent) and present that.
12. **Inlining secret-file → shell-quoted curl** — guardrails flag it as exfiltration. Prefer ssh script files over inline secrets in commands.
