---
name: nextjs-rename-chunkloaderror-recovery
description: Recover Next.js/Turbopack apps after mass rename operations cause stale chunk references (ChunkLoadError / Cannot find module for old chunk names).
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nextjs, turbopack, chunkloaderror, rename, cache, recovery]
    related_skills: [systematic-debugging, maintain-personal-web-app]
    trigger_conditions:
      - "ChunkLoadError"
      - "chunk load error"
      - "Cannot find module chunk"
      - "stale chunk"
      - "rename broke the app"
      - "rename recovery"
      - "turbopack cache"
      - "Next.js build cache"
      - "app 404 after rename"
      - "renamed project won't start"
      - "stale build artifacts"
      - "rebuild after rename"
      - ".next cache clear"
---

# Next.js Rename Chunk Recovery

Use when a renamed app (paths/labels) fails with errors like:
- `ChunkLoadError`
- `Cannot find module ... mission-control_* ...`
- stale `.next/server/chunks/*` references to old names

## When to Use

- App throws `ChunkLoadError` or `Cannot find module` for chunk filenames after a rename
- Mass rename operation (project directory, app label, route names) just completed
- `.next/` or `.turbo/` cache references old chunk filenames that no longer exist
- App starts but specific pages 404 or load blank after a rename
- Consolidating or removing dashboard routes and old chunks persist
- Next.js/Turbopack dev server won't start after project restructuring
- Rename combined with feature removal — need full cleanup pass
- Verifying that stale build artifacts are completely purged

## Not For

- General Next.js build errors (unrelated to renames) → use `systematic-debugging` first
- Static site deployment failures → use `static-site-deploy-verify`
- App crashes from missing dependencies (not chunk references) → run `npm install` and check `package.json`
- Cloud deployment issues (Vercel, Cloudflare) → use `cloudflare-pages-deploy` or Vercel CLI
- TypeScript compilation errors after rename → fix imports first, then run this recovery
- Port conflicts or process management (not rename-related) → use `ss -tlnp` and `pkill` directly
- Fresh project scaffolding or initial setup → this skill assumes an existing codebase with build caches

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

## Pitfalls

1. **Broad rename operations inside generated directories corrupt the build** — Running `sed`/`find -exec rename` inside `.next`, `node_modules`, `dist`, or `build` dirs creates broken references. Recovery: always exclude generated dirs from batch rename operations.

2. **Backup source trees under project root compile into the build** — Directories like `src.backup-*` under the app root are compiled by Next.js/Turbopack even though they're not imported. If they reference deleted imports, the build fails. Recovery: move backup trees outside the project root before building.

3. **`EADDRINUSE` after restart — kill before retry** — If the port is occupied by a stale process, restart loops fail silently. Recovery: identify and kill the process (`lsof -ti :<port> | xargs kill`) before starting.

4. **IPv6 edge cases with `localhost` causing false negatives** — `curl http://localhost:3000` may resolve to IPv6 `::1` while the server binds only IPv4 `0.0.0.0`. Recovery: use `127.0.0.1` explicitly for health checks.

5. **Build fails on imports from deleted components but source still exists in backup** — After removing a page and its imports, the build may still reference the old import because a stale copy exists in `src.backup-*`. Recovery: `rm -rf src.backup-*` or relocate outside the project root.

6. **Removed routes return stale 200 after restart** — The route directory was deleted but Next.js cached the route map. Recovery: delete `.next/` and `.turbo/` before rebuilding; verify removed routes return 404.

7. **API route rename leaves dangling fetch callers** — Renaming `/api/usage-trends` to `/api/token-usage` without updating all `fetch('/api/usage-trends')` callers in components causes silent 404s. Recovery: search for the old endpoint string across `src/` before deleting the old route.

8. **Widget/CTA text referencing deleted pages remains in UI** — After removing a page (e.g., `/issues`), status cards may still say "Click to view issues." Recovery: update all UI text references to removed routes in the same change set.

9. **Port changes in rename operations must be propagated everywhere** — When changing app ports as part of a rename, update: `package.json` scripts, restart scripts, keepalive scripts, health-check scripts, and any documentation referencing the port. Missing one causes silent failures.

10. **Architecture docs stale after route/API cleanup** — After removing routes, APIs, and DB tables, the project's architecture docs may still reference deleted endpoints. Recovery: update TOOLS.md, API lists, and schema docs in the same commit.

11. **Turbopack dev server caches across port changes** — If you change the port but Turbopack has a stale dev session on the old port, the new port may appear free but the dev server binds to the old port. Recovery: `pkill -f "next dev"` before restarting on a new port.

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
