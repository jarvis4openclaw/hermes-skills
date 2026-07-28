---
name: tanstack-start-setup
description: >-
  TanStack Start project setup, migration from Next.js, and common
  pitfalls. Covers the nitro() plugin conflict, custom server wrapper
  for production SSR, server route handler configuration, Vite plugin
  import paths, autoCodeSplitting issues, and production deployment.
type: craft
version: 1.1.0
triggers:
  - tanstack start
  - react-router
  - migrate from next.js
  - tanstack start server routes 404
  - createFileRoute server.handlers not working
  - TSRSplitComponent is not defined
  - nitro plugin breaks SSR
  - tanstack start outputs .output instead of dist
metadata:
  hermes:
    trigger_conditions:
      - "Set up TanStack Start project"
      - "Migrate from Next.js to TanStack Start"
      - "TanStack Start SSR not working"
      - "nitro plugin conflict TanStack Start"
      - "TanStack Start builds to .output instead of dist"
      - "TSRSplitComponent is not defined"
      - "TanStack Start server routes 404"
      - "createFileRoute server.handlers not working"
      - "TanStack Start custom server wrapper"
      - "TanStack Start production deployment"
      - "TanStack Router file routing convention"
      - "createServerFn usage"
      - "TanStack Start autoCodeSplitting error"
---

# TanStack Start Setup

TanStack Start is a full-stack React framework built on TanStack Router and Vite. It adds SSR, streaming, server functions, and REST API endpoints.

## When to Use

- **Building a new full-stack React application** — TanStack Start provides SSR, file-based routing, and server functions out of the box
- **Migrating from Next.js to a Vite-based stack** — If you want Vite's faster build times and more transparent configuration while keeping SSR and file-based routes
- **Projects requiring type-safe server-client RPC** — `createServerFn` gives end-to-end type safety without REST endpoint boilerplate
- **Dashboard or admin interfaces with API routes** — File-based API routes with `server.handlers` work alongside page routes in the same project
- **Need SSR with streaming** — TanStack Start supports streaming SSR out of the box for data-heavy pages
- **Projects where build output transparency matters** — Unlike Next.js's opaque `.next` folder, TanStack Start produces readable `dist/` output

## Not For

- **Simple static sites or SPAs** → use plain Vite + React Router (TanStack Router without the Start layer) instead — it's lighter and doesn't need SSR
- **Existing Next.js projects where migration cost outweighs benefits** → if the Next.js project works, the Vite build speed may not justify the rewrite. Consider incremental migration only.
- **Server-rendered apps that need edge runtime** → TanStack Start's custom server pattern works best on Node.js; if you need edge/worker deployment, consider Next.js or Remix instead
- **Projects that depend on Next.js proprietary features** → `next/image`, `next/head`, middleware, ISR, and app router patterns have no direct equivalent in TanStack Start
- **Large monorepos already on Next.js** → the migration cost across many apps/services may not be worth the build speed gain

## Key Architecture Difference from Next.js

TanStack Start is **not** Next.js. It uses:
- `createFileRoute` for both page routes and API routes (with `server.handlers`)
- `createServerFn` for type-safe RPC calls
- **`tanstackStart()`** for production SSR — this handles the server build internally (do NOT add a separate `nitro()` plugin)
- File-based routing with `.` as path separator: `api.health.ts` → `/api/health`

## Pitfalls

### 1. Do NOT add `nitro()` plugin alongside `tanstackStart()` (CRITICAL)

**This is a frequent migration trap.** Many older guides and earlier versions of TanStack Start used a separate `nitro()` Vite plugin from `nitro/vite`. In TanStack Start 1.168.x+, `tanstackStart()` handles the server build internally — adding `nitro()` on top **BREAKS** the build. Recovery: Remove `nitro()` from the plugins array and rebuild. If `.output/` directory persists, run `rm -rf dist .output node_modules/.nitro && npm run build`.

**Symptom:** The build succeeds but produces `.output/` with a bare SPA HTML shell:
```html
<!-- .output/server/_chunks/renderer-template.mjs -->
<!DOCTYPE html>
<html lang="en">
  <head><title>Automation Dashboard</title></head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>  <!-- WRONG: dev path in production -->
  </body>
</html>
```

The page HTML is a shell — no SSR-rendered content. API routes may return this HTML shell for any path (SPA fallback). The build also outputs to `.output/` instead of `dist/`.

**Root cause:** The `nitro()` plugin takes over the build pipeline and produces a Nitro preset output. The TanStack Start `renderer-template.mjs` becomes a plain HTML template with no React SSR rendering (`renderRouterToStream` is never called). The `.output/server/index.mjs` starts its own HTTP server on port 3000 (or `PORT` env var), serving only the SPA shell.

**Fix:** Remove `nitro()` from the plugins array. The correct config uses ONLY `tanstackStart()`:
```ts
// vite.config.ts — CORRECT (no nitro import)
import { defineConfig } from 'vite'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    TanStackRouterVite({
      target: 'react',
      autoCodeSplitting: true,
      routesDirectory: './src/routes',
      generatedRouteTree: './src/routeTree.gen.ts',
    }),
    tanstackStart(),   // handles SSR server build — NO nitro() needed
    viteReact(),
    tailwindcss(),
  ],
})
```

This produces `dist/server/server.js` (exports `{ default: { fetch(request) } }`) and `dist/client/assets/`. The server.js includes proper React SSR via `renderRouterToStream` from `@tanstack/react-router/ssr/server`.

**Production serving:** Since `dist/server/server.js` exports only a handler (not a server), a custom Node.js HTTP wrapper is needed. See Pitfall #5 below.

**How to verify the build is correct:**
```bash
# Check for SSR markers in the server bundle
grep -c "renderRouterToStream\|defineHandlerCallback" dist/server/server.js
# Should return >= 1

# Start the server and verify SSR content — HTML should contain rendered components
curl -s http://localhost:2999/ | head -20
# Should see real content: <aside class="sidebar">... not just <div id="root">
```

**Still seeing `.output/` after removing nitro()?** Clean all build artifacts:
```bash
rm -rf dist .output node_modules/.nitro && npm run build
```

### 2. autoCodeSplitting Causes TSRSplitComponent Error

Setting `autoCodeSplitting: true` on `TanStackRouterVite` produces a runtime error:
```
ReferenceError: TSRSplitComponent is not defined
```

**Fix:** Set `autoCodeSplitting: false` in the plugin options:

```ts
TanStackRouterVite({
  target: 'react',
  autoCodeSplitting: false,  // disable to avoid TSRSplitComponent error
  routesDirectory: './src/routes',
  generatedRouteTree: './src/routeTree.gen.ts',
}),
```

### 3. Wrong Vite React Plugin Import Path

The correct import is from `@vitejs/plugin-react`, NOT `@vitejs/plugin/react`:

```ts
// ✅ CORRECT
import viteReact from '@vitejs/plugin-react'

// ❌ WRONG — this path does not exist
import viteReact from '@vitejs/plugin/react'
```

### 4. Production Port: vite dev server vs custom wrapper

The `server: { port: 2999 }` config in `vite.config.ts` controls the **dev server** port only. For production with a custom `start-server.mjs` wrapper, the port is set directly in the wrapper's `httpServer.listen()` call. If using the Nitro built-in server (`.output/server/index.mjs` — see pitfall #1 about when this applies), the port comes from:

```js
process.env.NITRO_PORT ?? process.env.PORT ?? 3000
```

To run production on a specific port with a custom wrapper:
```js
// start-server.mjs
const PORT = 2999;
httpServer.listen(PORT, '0.0.0.0', () => { ... });
```

To run with Nitro built-in server (if applicable):
```bash
PORT=2999 node .output/server/index.mjs
```

**Do not rely on `server.port` in vite.config.ts for production.** Always set the port explicitly in your startup script or systemd service.

### 5. Custom Server Wrappers: Use with Caution

Custom Node.js HTTP server wrappers (e.g., `start-server.mjs` that imports `./dist/server/server.js`) can work but require careful implementation. The wrapper must:
- Correctly handle the Response object from `server.fetch(request)`
- Stream the response body using `response.body.getReader()`
- Set proper headers and status codes

**Working pattern** (from automation-dashboard):
```js
import { createServer } from 'node:http';
import serverModule from './dist/server/server.js';

const server = serverModule.default || serverModule;
const PORT = 2999;

const httpServer = createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
    const headers = new Headers();
    for (const [k, v] of Object.entries(req.headers)) {
      if (v) headers.set(k, Array.isArray(v) ? v.join(', ') : v);
    }
    const request = new Request(url, { method: req.method, headers });
    const response = await server.fetch(request);
    
    res.writeHead(response.status, Object.fromEntries(response.headers));
    if (response.body) {
      const reader = response.body.getReader();
      const pump = async () => {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          res.write(value);
        }
        res.end();
      };
      pump();
    } else {
      res.end();
    }
  } catch (err) {
    console.error('Server error:', err);
    res.writeHead(500);
    res.end(`Internal Server Error: ${err.message}`);
  }
});

httpServer.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
```

**When to use custom wrappers:**
- Need static file serving with custom caching rules
- Want health check warmup on startup
- Need custom logging or middleware

**When to use built-in Nitro server:**
- Simpler deployment (just `node .output/server/index.mjs`)
- Don't need custom static file handling
- Prefer the standard TanStack Start pattern

**Pitfall:** If API routes return HTML instead of JSON, or hang indefinitely, the wrapper may not be handling the Response body correctly. Check that `response.body.getReader()` is being called and the stream is properly piped to `res.write()`.

## Migrating from Next.js

### File Routing Convention

TanStack Router uses `.` for file-based routing, not directories:

| Next.js | TanStack Start |
|---------|---------------|
| `app/page.tsx` | `routes/index.tsx` |
| `app/api/health/route.ts` | `routes/api.health.ts` |
| `app/model-routing/page.tsx` | `routes/model-routing.tsx` |
| `app/agents/page.tsx` | `routes/agents.tsx` |

### API Routes

In Next.js, API routes use `export async function GET(req)`. In TanStack Start:

```ts
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/api/health')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        return Response.json({ status: 'ok' })
      },
    },
  },
})
```

### Layout/Shell

In TanStack Start, the root layout lives in `routes/__root.tsx`:

```tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'
import { Scripts } from '@tanstack/react-start'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <html>
      <body>
        <Outlet />
        <Scripts />
      </body>
    </html>
  )
}
```

### Data Fetching

Use `createServerFn` for server-only data operations instead of Next.js server components or `getServerSideProps`:

```tsx
import { createServerFn } from '@tanstack/react-start'
import { createFileRoute } from '@tanstack/react-router'

const getData = createServerFn({ method: 'GET' }).handler(async () => {
  return { message: 'Hello from server!' }
})

export const Route = createFileRoute('/data')({
  loader: () => getData(),
  component: DataPage,
})
```

## Verification Steps

After setup, verify all route types work:

1. **Build**: `npm run build` (should complete without errors, output to `dist/` not `.output/`)
2. **Verify build output**: Check that `dist/server/server.js` exists and contains SSR markers:
   ```bash
   grep -c "renderRouterToStream\|defineHandlerCallback" dist/server/server.js
   # Should return >= 1
   ```
3. **Start production**: Use a custom Node.js HTTP wrapper (see Pitfall #5):
   ```bash
   node start-server.mjs
   ```
   Or with systemd: `systemctl start automation-dashboard.service`
4. **Verify port**: `ss -tlnp | grep 2999` or `lsof -i :2999` — confirm the process is listening on the expected port
5. **Test page routes**: `curl http://localhost:2999/` (should return HTML with SSR-rendered content, not just `<div id="root">`)
6. **Test API routes**: `curl http://localhost:2999/api/health` (should return JSON, not HTML or `{"status":500,"unhandled":true,"message":"HTTPError"}`)
7. **Test SSR**: The page HTML should contain rendered components (e.g., `<aside class="sidebar">...`), not just a shell

**If you see SPA shell instead of SSR content:** You likely added `nitro()` to the plugins array. Remove it and rebuild (see Pitfall #1).

## References

- `@tanstack/react-start` docs (in `node_modules/@tanstack/start-client-core/skills/`)
- TanStack Router docs: [server-routes guide](https://tanstack.com/router/latest/docs/framework/react/guide/server-routes)
- `references/error-reference.md` — Specific error codes, stack traces, and fixes from real debugging sessions
