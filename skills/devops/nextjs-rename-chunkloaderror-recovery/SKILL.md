---
name: nextjs-rename-chunkloaderror-recovery
description: Recover Next.js/Turbopack apps after mass rename operations cause stale chunk references (ChunkLoadError / Cannot find module for old chunk names).
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nextjs, turbopack, chunkloaderror, rename, cache, recovery]
    related_skills: [systematic-debugging, maintain-personal-web-app]
---

# Next.js Rename Chunk Recovery

Use when a renamed app (paths/labels) fails with errors like:
- `ChunkLoadError`
- `Cannot find module ... mission-control_* ...`
- stale `.next/server/chunks/*` references to old names

## Root Cause Pattern
Mass renames can leave stale Turbopack/Next build artifacts pointing at old chunk filenames. Runtime then requests non-existent chunks.

## Recovery Steps
1) Stop active Next processes for the app ports.
- `pkill -f "next dev -p <port>" || true`
- `pkill -f "next start -p <port>" || true`

2) Remove build caches in the app root.
- `rm -rf .next .turbo`

3) Rebuild and restart.
- Dev mode: `npm run dev -- -p <port>`
- Prod mode: `npm run build && npm run start`

4) Verify health and pages.
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/`
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/api/health`
- Check key routes (e.g. `/tasks`) return 200.

5) Confirm old chunk names are gone from rendered output/logs.
- Search fetched HTML/logs for old token (e.g. `mission-control_my-app`).

## Guardrails
- Never run broad rename operations inside generated dirs: `.next`, `node_modules`, `dist`, `build`.
- Never include backup source trees (e.g. `src.backup-*`) under app root during cleanup; Next TypeScript/build can still compile them and fail on deleted imports.
- If `EADDRINUSE` appears, identify/kill the process already listening instead of retry loops.
- Prefer `127.0.0.1` over `localhost` for checks to avoid IPv6 edge cases.

## Rename + Feature Removal Combo (common follow-up)
If you remove pages/components after a rename recovery:
1) Re-run `npm run build` immediately after deletions.
2) If build fails on references from legacy backup folders (`src.backup-*`), remove or relocate those folders outside the project root.
3) Verify removed routes return `404` (not stale `200`) after restart.
4) Run a frontend→API contract sweep after deletions:
   - Search for remaining `fetch('/api/...')` calls in pages/components.
   - Confirm each endpoint still exists under `src/app/api`.
   - Fix or remove dangling calls (common example: `/tasks` page still calling `/api/tasks/pending` after API cleanup).
5) If port changes are part of the same task, update all of these together:
   - app scripts (`package.json` dev/start)
   - restart scripts
   - keepalive scripts
   - health-check scripts
   - docs that reference URLs/ports

6) If consolidating/removing dashboard routes (ex: merge `/health` into `/` and delete `/issues`):
   - Move reusable UI into a shared component first (ex: `HealthOverview`) and render it on the surviving page.
   - Remove deleted route directories under `src/app/(dashboard)/...` so Next route map drops them.
   - Remove nav/sidebar links and any `router.push('/deleted-route')` calls.
   - Reword status cards/widgets that referenced deleted pages (don’t leave dead CTA text like “Click to view …”).
   - If you rename an API route during cleanup (ex: `/api/usage-trends` -> `/api/token-usage`), update all fetch callers before deleting the old route.
   - Verify expected behavior explicitly: surviving routes `200`, removed routes `404`.

7) For a true zero-dead-code pass after route/API removals:
   - Delete unused API routes and helper modules (ex: `/api/issues`, `issue-reporter.ts`) once no callers remain.
   - Remove corresponding DB schema/functions/types from `src/lib/db.ts` (don’t keep orphaned tables/queries just in case).
   - Update dashboard tiles/cards so removed concepts disappear from UI (ex: remove “Open Issues” tile, add replacement tile).
   - Run content search for deleted endpoint strings (e.g. `/api/issues`) across `src/` before final build.
   - Update architecture/docs to match reality (key routes, API list, schema) in the same change set.

## Fast Triage Checklist
- [ ] Process conflict fixed (`ss -tlnp` / `lsof -i`)
- [ ] `.next` and `.turbo` cleared
- [ ] Restart successful
- [ ] `/`, key route(s), and `/api/health` return 200
- [ ] No old-name chunk references remain
