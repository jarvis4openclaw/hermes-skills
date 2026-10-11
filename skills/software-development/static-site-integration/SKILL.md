---
name: static-site-integration
description: "Use when adding pages to an existing served site (redesign, /v2/, microsite) — read the SPA fallback and CSP before writing markup, or the new pages silently vanish in production."
version: 1.1.0
author: webrefactor
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [CSP, SPA-fallback, fonts, static-site, deploy, self-hosting]
    related_skills: [csp-static-site-build, web-fonts-self-hosting, web-ia-planning]
    trigger_conditions:
      - "add new pages to the existing site"
      - "build the v2 pages"
      - "the new pages work locally but not on the server"
      - "SPA fallback is serving the old index"
      - "new directory serves the old site"
      - "check the CSP before writing HTML"
      - "fonts break on deploy but work as a local file"
      - "microsite inside the existing server"
      - "the new page 404s or shows the old page"
      - "read the serving layer first"
      - "does the server rewrite extension-less paths"
      - "adding a subdirectory to a single-page app"
      - "standalone page under an SPA router"
---

# Static-Site Integration

Building a new page set (redesign, `/v2/`, microsite) into an existing served site without breaking the old one. The serving layer decides what the new HTML may do — enumerate it BEFORE writing markup, and verify against the real server, not local files.

## When to Use

- New pages (redesign, `/v2/`, microsite) must live **inside an already-served site** without disturbing the old one.
- A new page set **works locally but not when served** — wrong page loads, fonts fall back, scripts blocked.
- It is unclear how the server handles **extension-less paths** (SPA fallback rewriting).
- You must enumerate the **CSP directives** before deciding whether inline `<style>`/`<script>` or an external CDN is allowed.
- Brand font decisions hinge on whether `font-src` exists (or falls back to `default-src`).
- The old site has a **pathname router** and a second one under the new prefix would collide with it.
- Multiple agents are quoting server behaviour at each other and you need the repo to settle it.

## Not For

- **Planning the page set, sitemap and component inventory before any markup** → use `web-ia-planning` instead.
- **A static site built from scratch with its own CSP, where there is no legacy site to avoid breaking** → use `csp-static-site-build` instead.
- **Subsetting/self-hosting the webfont files themselves** (unicode-range surgery, woff2 generation) → use `web-fonts-self-hosting` instead.
- **Final pre-deploy verification of fonts, glyphs and CSP on a finished artifact** → use `design-delivery-verification` instead.
- **Designing print/paper output** → use `print-layout-design` instead.
- **Verifying that a QR code on the page actually decodes** → use `qr-code-verification` instead.
- **Art direction and visual design of the new pages** → use `web-redesign-art-direction` instead.

## Procedure

### 1. Ground truth from the repo, not the live URL
- If the deployed URL won't resolve (DNS_PROBE on internal/staging domains is normal — the host may be LAN-only), search the local disk for the site source before treating it as unreachable: `find ~ -maxdepth 3 -iname "*<site-name>*"`. README + server code + CSS answer "what color", "what flows", "what endpoints" far better than any screenshot, and they clear [TBC] items in build plans.
- Never trust a screenshot for an exact brand color (rendering skews hex). Grep the CSS and count frequency:
  `grep -roE '#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}\b' <public-dir> | awk -F: '{print $NF}' | sort | uniq -c | sort -rn`
  The most-used hex is the true "same color" the user means — not the canonical one they'd name.

### 2. Read the serving layer before writing HTML
Find the server (server.py / nginx / Caddy / Express static handler) and extract three things:
- **SPA fallback**: extension-less paths are typically rewritten to index.html. A new subdirectory must therefore link explicit `.html` paths (`/v2/create.html`), never bare `/v2/` — a dot-less directory name gets hijacked to the OLD index and the new pages silently vanish from the deployed site.
- **CSP header**: enumerate every directive; each one constrains the build:
  - `style-src 'unsafe-inline'` → inline `<style>` allowed (single-file reference heroes are safe).
  - `script-src 'self'` → NO inline `<script>`; any JS must be a bundled external file.
  - No `font-src` → falls back to `default-src 'self'` → Google Fonts CDN silently blocked on deploy. See `references/font-self-hosting.md`.
  - `img-src data:` → data-URI art fine.
- **Cache-Control**: versioned assets (`/assets/*`, bundle names) are often `immutable` — a stale bundle pins a broken build; HTML is usually `no-cache`.

Then verify against the REAL server: `curl -sI http://<host>/v2/...` and compare emitted headers to the source. Opening files locally applies no CSP, so a locally-fine page ships broken fonts/scripts.

### 3. Don't collide with the existing router
If the old site routes on `location.pathname`, do not add a second pathname router under the new prefix — the two intercept each other. Static multi-page with `.html` links is the safe shape under an SPA-fallback server.

### 4. Verify claims in the repo, not teammate summaries
In multi-agent rooms, re-read the server file before quoting directives or fallback behavior — one line of CSP text changes what the build may ship.

## Pitfalls

1. **Extension-less directory link → serves the old index (SPA fallback)** — always link explicit `.html` paths (`/v2/create.html`), never a bare `/v2/`.
2. **Local-file preview lies** — no CSP, no fallback; fonts and inline scripts look fine locally and break on deploy. Screenshots taken without the server will show the intended font while the deployed page silently falls back to Georgia/system-ui.
3. **Dropping latin-ext when self-hosting fonts silently breaks brand glyphs** (₿, ®, and other U+20AD–20C0-range marks) — keep both latin blocks; see `web-fonts-self-hosting`.
4. **Grep the deployed server's actual response headers too** — the running config may differ from the source file (`curl -sI http://<host>/v2/...`).
5. **Never trust a screenshot for an exact brand color** — rendering skews hex. Grep the CSS and count frequency; the most-used hex is the "same color" the user means.
6. **A dot-less directory name gets hijacked to the OLD index** — the new pages then silently vanish from the deployed site even though the files are present.
7. **`style-src 'unsafe-inline'` presence/absence flips whether single-file reference pages are safe** — check it per server; do not assume the previous project's CSP.
8. **`script-src 'self'` means no inline `<script>` at all** — every script must be a bundled external file; inline event handlers (`onclick=`) are blocked too.
9. **`immutable` cache headers pin a stale bundle** — versioned assets under `/assets/*` may serve the broken build long after a fix; bust the name, not the header.
10. **Do not add a second pathname router under the new prefix** — the old and new routers intercept each other; static multi-page with `.html` links is the safe shape under an SPA-fallback server.
11. **`DNS_PROBE` on an internal/staging domain is normal** — search the local disk for the site source (`find ~ -maxdepth 3 -iname "*<site-name>*"`) before declaring the site unreachable.
