---
name: automation-dashboard-update
version: 1.1.0
description: Update the Automation Dashboard at http://192.168.100.52:2999 — edit source files, rebuild, and restart. Use when asked to add/remove sidebar nav items, change pages, update components, or redeploy the dashboard.
metadata:
  hermes:
    tags: [automation-dashboard, next.js, deploy, sidebar, nav, clawd]
    trigger_conditions:
      - "update dashboard"
      - "add sidebar item"
      - "new page on the dashboard"
      - "redeploy the dashboard"
      - "restart automation dashboard"
      - "change nav in dashboard"
      - "edit dashboard page"
      - "dashboard component"
      - "dashboard is not showing"
      - "dashboard 404"
      - "dashboard build failed"
      - "fix dashboard"
      - "dashboard stack"
---

# Automation Dashboard Update

The Automation Dashboard is a Next.js app running at **http://192.168.100.52:2999** (dev mode, port 2999).

## When to Use

- Adding, removing, or renaming sidebar navigation items in the dashboard
- Creating new pages or routes inside the dashboard app
- Editing React/TypeScript components, layout files, or global styles
- Rebuilding the dashboard after source changes
- Restarting the dev server when it's stale, crashed, or port-locked
- Verifying a dashboard change rendered correctly in the browser
- Updating a dashboard component that shows dynamic data from SQLite
- Diagnosing dashboard startup failures or TypeScript build errors
- Adding systemd services for dashboard-adjacent tools

## Not For

- Deploying to a remote host or cloud provider (Vercel, Cloudflare Pages) → use `cloudflare-pages-deploy` or `cloudflare-pages-static-site` instead
- Static site verification or "changes not showing after push" → use `static-site-deploy-verify`
- Model catalog management for the OpenRouter free-models page → use `openrouter-model-management`
- Next.js app issues after mass file renames (ChunkLoadError) → use `nextjs-rename-chunkloaderror-recovery`
- Production deployment with CI/CD, Docker, or build pipelines → this skill covers the local dev server only
- Writing general-purpose Next.js applications from scratch → this skill assumes the existing dashboard codebase

## Key Paths

| What | Path |
|------|------|
| App root | `/home/wahid/clawd/automation-dashboard/my-app` |
| Sidebar nav | `src/app/dashboard-layout.tsx` |
| Main page | `src/app/(dashboard)/page.tsx` |
| Token dashboard | `src/app/(dashboard)/token-dashboard/page.tsx` |
| Free models page | `src/app/(dashboard)/free-models/page.tsx` |
| Agents page | `src/app/agents/page.tsx` |
| Layout | `src/app/layout.tsx` |
| Global CSS | `src/app/globals.css` |
| Restart script | `/home/wahid/clawd/restart-automation-dashboard.sh` |
| DB (SQLite) | `/home/wahid/clawd/automation-dashboard/data/automation-dashboard.db` |
| Activity log | `/home/wahid/clawd/logs/automation-dashboard-activity.log` |

## Stack

- **Next.js 16** (Turbopack, dev mode)
- **TypeScript / React** (`.tsx`)
- **Tailwind CSS** (utility classes)
- **lucide-react** (icons)
- **SQLite** (via `src/lib/db.ts`)

## Full Update Workflow

### 1. Edit Source

Use `patch` (preferred) or `write_file` for targeted edits.

**Sidebar nav items** live in `dashboard-layout.tsx` as the `NAV_ITEMS` array (line ~15):

```typescript
const NAV_ITEMS: { id: string; label: string; href: string; icon: ComponentType<{ className?: string }>; external?: boolean }[] = [
  { id: 'dashboard', label: 'Dashboard', href: '/', icon: LayoutDashboard },
  // ... add/remove items here
];
```

For **internal** routes, use `href: '/relative-path'` with Next.js `Link`.
For **external** links, add `external: true` — the component renders `<a target="_blank">` instead of `<Link>`.

Icons are imported from `lucide-react` at the top of the file. Add new imports as needed.

### 2. Rebuild

Always run a build after edits — dev mode serves from cache and may not reflect changes immediately:

```bash
cd /home/wahid/clawd/automation-dashboard/my-app && npm run build
```

Build takes ~5–15s. Check exit code — if non-zero, read the TypeScript error and fix before proceeding.

### 3. Restart Server

The dashboard runs as a background dev server on port **2999**. Kill and restart:

```bash
# Kill existing
kill $(lsof -t -i:2999) 2>/dev/null
sleep 2

# Start fresh (background)
cd /home/wahid/clawd/automation-dashboard/my-app
nohup npm run dev -- -p 2999 > /dev/null 2>&1 &
sleep 5

# Verify
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:2999/
```

Or use the restart script:
```bash
bash /home/wahid/clawd/restart-automation-dashboard.sh
```

### 4. Verify

```bash
# HTTP check
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:2999/

# Check for expected content in rendered HTML
curl -s http://127.0.0.1:2999/ | grep -i "your-new-content"
```

## Adding a New Sidebar Nav Item

1. Add icon import to `dashboard-layout.tsx` (e.g., `Brain`)
2. Add entry to `NAV_ITEMS` array
3. Rebuild + restart
4. Verify link appears in rendered HTML

### Example: Add a "Logs" nav item

```typescript
// In the import block, add:
Brain, // already imported — add your icon

// In NAV_ITEMS, add:
{ id: 'logs', label: 'Logs', href: '/logs', icon: ScrollText },
```

Then create the page at `src/app/(dashboard)/logs/page.tsx`.

## Adding a New Page

1. Create directory under `src/app/(dashboard)/<page-name>/`
2. Create `page.tsx` with a default export component
3. Add the route to `NAV_ITEMS` in `dashboard-layout.tsx`
4. Rebuild + restart

## Systemd Services for Dashboard Tools

### General Pattern: Creating a Systemd Service for a Local Tool

When asked to create a systemd service for auto-start on boot:

1. **Do NOT use `write_file` to `/etc/systemd/system/`** — Hermes blocks writes to sensitive system paths. Instead, provide the commands for the user to run.
2. **Do NOT create user-level services** (`~/.config/systemd/user/`) unless explicitly asked. Boss prefers system-level services.
3. **Check if linger is enabled** for the user (`loginctl show-user <user> --property=Linger`) — this determines whether user-level services can start at boot without login.

**Template for a system-level systemd service:**

```bash
sudo tee /etc/systemd/system/<service-name>.service > /dev/null << 'EOF'
[Unit]
Description=<Service Description>
After=network.target

[Service]
Type=simple
User=<username>
ExecStart=<full command with args>
Restart=on-failure
RestartSec=5
Environment=HOME=/home/<username>

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now <service-name>
```

**Always verify after starting:**
```bash
sudo systemctl status <service-name> --no-pager
ss -tlnp | grep <port>
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/
```

### Known Services

| Service | Port | Description |
|---------|------|-------------|
| mnemosyne-dashboard | 8765 | Mnemosyne memory dashboard |
| hermes-dashboard | 9119 | Hermes Agent web dashboard |

#### Mnemosyne Dashboard Service

The mnemosyne dashboard runs as a **system-level** systemd service at `/etc/systemd/system/mnemosyne-dashboard.service`:

```bash
# Check status
sudo systemctl status mnemosyne-dashboard

# Restart
sudo systemctl restart mnemosyne-dashboard

# Stop
sudo systemctl stop mnemosyne-dashboard
```

The user-level service (`~/.config/systemd/user/mnemosyne-dashboard.service`) should remain **disabled** to avoid conflicts.

#### Hermes Dashboard Service

The Hermes dashboard runs as a **system-level** systemd service at `/etc/systemd/system/hermes-dashboard.service`:

```bash
# Check status
sudo systemctl status hermes-dashboard

# Restart
sudo systemctl restart hermes-dashboard

# Stop
sudo systemctl stop hermes-dashboard
```

Service file content:
```ini
[Unit]
Description=Hermes Agent Dashboard
After=network.target

[Service]
Type=simple
User=wahid
ExecStart=/usr/local/bin/hermes dashboard --host 0.0.0.0 --port 9119 --insecure --no-open
Restart=on-failure
RestartSec=5
Environment=HOME=/home/wahid

[Install]
WantedBy=multi-user.target
```

## Pitfalls

1. **`as const` breaks optional fields on NAV_ITEMS** — Using `as const` infers literal types and rejects the optional `external` field on items that don't have it. Always use an explicit type annotation instead. Recovery: remove `as const` and add the explicit type annotation.

2. **Build before restart is mandatory** — Dev mode with Turbopack is fast but stale `.next` cache can serve old code after file edits. Always run `npm run build` before restarting. Recovery: if you see stale content, stop the server, delete `.next/`, rebuild, and restart.

3. **Port 2999 must be specified explicitly** — The default Next.js dev port is 3000, but this dashboard uses 2999. Forgetting `-p 2999` starts the server on the wrong port and curl checks fail. Recovery: check which port the process bound with `lsof -i :3000` or `lsof -i :2999`.

4. **Shell `&` in foreground terminal() hangs** — Using shell backgrounding (`&`) inside a foreground `terminal()` call causes the terminal tool to wait forever. Use `terminal(background=true)` or `nohup ... &` with explicit redirect. Recovery: if the command is stuck, cancel it and rerun with `nohup`.

5. **write_file to /etc/systemd/system/ is blocked** — Hermes has a security guard against writing to system-level systemd paths. Recovery: provide the `sudo tee` command pattern for the user to run, or use a user-level service path (`~/.config/systemd/user/`) only when explicitly requested.

6. **Port conflict kills the dashboard silently** — If another process is on 2999, the Next.js dev server may fail to start without a visible error. Recovery: always run `kill $(lsof -t -i:2999)` before starting the dashboard.

7. **Missing `external: true` renders external links as internal** — Links to external dashboards (e.g., Mnemosyne at `:8765`) will 404 if treated as Next.js internal routes. Recovery: verify the link uses `<a>` not `<Link>` by checking that `external: true` is present.

8. **User-level systemd services need linger enabled** — If you create a user-level systemd service (`~/.config/systemd/user/`) and the user isn't logged in, the service won't start at boot. Recovery: check `loginctl show-user <user> --property=Linger`; if `no`, enable it with `sudo loginctl enable-linger <user>`.

9. **DB file path is relative to the project root** — `src/lib/db.ts` resolves the SQLite database path relative to the project root. If the server starts from a different working directory, the DB path breaks and the app throws. Recovery: always start the server from `/home/wahid/clawd/automation-dashboard/my-app`.

10. **Activity logger writes to a separate log file** — Dashboard activity is written to `/home/wahid/clawd/logs/automation-dashboard-activity.log`, not stdout. If you're looking for error traces, check that file. Recovery: `tail -50 /home/wahid/clawd/logs/automation-dashboard-activity.log`.

11. **TypeScript strictness on NAV_ITEMS requires explicit type** — Adding a new field to one item requires updating the type annotation for ALL items. The array is typed as a whole, not per-element. Recovery: if you get a type error, check the `NAV_ITEMS` type annotation at the top of the file.

12. **Turbopack caching hides source changes** — Even after a rebuild, Turbopack can cache aggressively. If `curl` shows old content but you confirmed the source file is updated, the cache is stale. Recovery: stop the server, remove `.next/`, and restart.

## Related Skills

- **openrouter-model-management** — Managing the OpenRouter model catalog, free model list, and `resolve_alias` sort logic. The Free Models page on the dashboard reads from the tracker JSON that the cron job populates.

## File Structure Reference

```
my-app/src/
├── app/
│   ├── layout.tsx              # Root layout (html/body)
│   ├── globals.css             # Tailwind + global styles
│   ├── dashboard-layout.tsx    # Sidebar + main content wrapper
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Dashboard group layout
│   │   ├── page.tsx            # Main dashboard page
│   │   ├── token-dashboard/page.tsx
│   │   └── free-models/page.tsx
│   ├── agents/page.tsx
│   └── api/                    # API routes (activities, health, cron, etc.)
├── components/
│   ├── DashboardHeader.tsx
│   ├── StatsOverview.tsx
│   ├── ActivityFeed.tsx
│   ├── HealthOverview.tsx
│   ├── ModelCosts.tsx
│   └── ui/                     # shadcn-style primitives (badge, card, button)
└── lib/
    ├── db.ts                   # SQLite access
    ├── activity-logger.ts
    ├── openclaw.ts
    └── utils.ts
```
