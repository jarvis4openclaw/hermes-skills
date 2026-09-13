---
name: csp-static-site-build
description: Use when building static pages for a strict-CSP or SPA.
version: 1.1.0
author: jarvis
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [csp, static-site, fonts, spa, security-headers, frontend]
    category: web
    related_skills: [web-fonts-self-hosting, static-site-deploy-verify, web-redesign-art-direction, web-quality-audit]
    trigger_conditions:
      - "CSP"
      - "content security policy"
      - "strict-CSP static page"
      - "script-src 'self'"
      - "style-src 'self'"
      - "self-host fonts"
      - "font-src missing"
      - "SPA fallback server"
      - "static site inside an SPA"
      - "assets blocked in production but fine locally"
      - "brand font falls back to system-ui"
      - "inline SVG allowed by img-src"
      - "deploy a static page to a strict-CSP host"
---

# CSP-Safe Static Site Build

Rules for shipping a static front-end into a server that enforces a Content-Security-Policy or serves an existing SPA. These pitfalls only bite in production — a file opened locally (`file://`) has no CSP, so a screenshot that "looks right" proves nothing about the deployed page.

## When to Use

- You are adding a new static page to a host that serves a `Content-Security-Policy` header or an existing SPA shell.
- Fonts, scripts, or images render correctly from disk but break once deployed, and you need to know which directive is blocking them.
- You are choosing **font delivery** (self-host vs CDN) and need to know what survives a strict `font-src`/`style-src` policy.
- You must decide between inline `<script>`, bundled JS, and inline `<style>` under `script-src`/`style-src` restrictions.
- You are linking a new subdirectory on a **SPA-fallback** server and need the extension-explicit link rule.
- A new page needs modules that live **outside** the served root and must go through the existing bundler.
- You need proof a deployed page actually works — real browser, fonts confirmed loaded, async errors captured — not just a 200.

## Not For

- **Choosing the palette, type system, or art direction for a redesign** → use `web-redesign-art-direction` instead
- **Producing the actual subsetted woff2 files and `@font-face` CSS** → use `web-fonts-self-hosting` instead
- **Confirming a deploy reached the host (cache, headers, byte parity)** → use `static-site-deploy-verify` instead
- **Auditing contrast, a11y, tokens, or JS quality on a built site** → use `web-quality-audit` instead
- **Producing the design spec / component visual notes to build from** → use `design-md` instead
- **Fronting the site with a reverse proxy (Caddy / NPM)** → use `caddy-proxy-management` instead

## 1. Audit the real served headers first
Curl the actual server (or the deployed URL) and read the CSP; do not trust a locally-rendered screenshot. The CSP is set by the server, not by your HTML, so fonts/scripts/images that render fine from disk silently break once deployed.

```bash
curl -sS -D - -o /dev/null http://HOST:PORT/index.html | grep -i content-security-policy
```

## 2. Self-host fonts; external font links die silently
If the CSP is `style-src 'self' 'unsafe-inline'` with NO `font-src` directive, a Google Fonts `<link href="https://fonts.googleapis.com/...">` is blocked twice: the stylesheet URL violates `style-src 'self'`, and the font files themselves fall back to `default-src 'self'`. Result: brand fonts silently degrade to Georgia/system-ui/monospace with no console error worth chasing. Ship the `.woff2` files into your own assets dir and load them with a local `@font-face` (same-origin, allowed by `'self'`).

## 3. script-src 'self' bans inline and CDN scripts
No inline `<script>` blocks and no CDN `<script src>` under `script-src 'self'`. Bundle all JS into a local file. Inline `<style>` is fine when `style-src` includes `'unsafe-inline'`; an external `<link rel="stylesheet">` to a CDN is NOT (blocked by `'self'`).

## 4. img-src 'self' data: permits inline SVG and data URIs
Inline `<svg>` and `data:` URIs are allowed; remote images are blocked. Hand-built inline SVG is the safe choice for illustration and logos.

## 5. Never link extension-less paths into a SPA-fallback server
A static server that rewrites extension-less, non-file paths to `index.html` will serve the OLD app for a bare new-directory URL like `/v2/`. Use explicit file extensions (`/v2/index.html`, `/v2/create.html`) on every internal link and never link the bare directory.

## 6. Bundle modules outside the served root; don't copy-link them
If the project keeps source modules in a directory OUTSIDE the served public root (bundled by esbuild/webpack at build time into one IIFE), a new page cannot `import` them directly — the URL isn't reachable and the code isn't built. Add your own entry point to the existing bundler config so the logic compiles in. A static copy of the source file will not run. Reuse the original module via the new entry point, not a copy-paste of its source — a copy drifts and re-introduces bugs the original already fixed.

## 7. Self-hosted subsets: keep latin-ext for a non-latin brand glyph
When you self-host a webfont by subset (the standard way to trim size), a glyph outside the latin block — ₿ U+20BF, currency symbols, math symbols — silently falls back to system font if you only kept the latin file. Keep latin + latin-ext per weight (drop vietnamese/cyrillic), or render a one-off brand mark as an inline SVG vector path with zero font dependency (the robust choice for a logo/glyph; it can't fall back).

## 8. Verify in a real browser, not just curl
Curl proves headers and 200s; it doesn't prove fonts loaded or that bundled JS actually runs. Drive the served URL through browser_exec:
- Navigate and screenshot in SEPARATE calls — a CDP read issued during navigation can time out.
- Prefer raw `cdp("Page.captureScreenshot", format="png")` + base64-decode to a known absolute path over the `capture_screenshot()` helper, whose workspace-relative path is unreliable across calls.
- Before triggering an async action, install `window` `error` + `unhandledrejection` listeners that push into a readable array and read it back — a minified IIFE fails with no trace otherwise.
- `document.fonts.status === 'loaded'` is the real font check; a screenshot that "looks right" is not.

## Pitfalls

1. **Trusting a `file://` preview** — a locally opened file has no CSP, so the page renders perfectly and breaks on deploy. Audit the real served headers with `curl -sS -D - -o /dev/null <url>` before choosing any technique.
2. **Assuming your HTML can loosen the policy** — the CSP is set by the server. A `<meta http-equiv>` tag cannot relax a header-set policy; read the deployed response, not the template.
3. **External Google Fonts `<link>` degrading silently** — under `style-src 'self'` with no `font-src`, the stylesheet URL violates `style-src` AND the font files fall back to `default-src 'self'`. The symptom is Georgia/system-ui with no console error worth chasing. Self-host the `.woff2` and load it with a same-origin `@font-face`.
4. **Inline `<script>` under `script-src 'self'`** — blocked outright. Bundle all JS into a local file. Inline `<style>` survives only when `style-src` includes `'unsafe-inline'`.
5. **A CDN stylesheet treated as safe because `'unsafe-inline'` is present** — `'unsafe-inline'` covers inline style *text*, not cross-origin stylesheet URLs. A CDN `<link rel="stylesheet">` still needs that origin in `style-src`.
6. **Assuming remote images work** — `img-src 'self' data:` permits inline `<svg>` and `data:` URIs only. Hand-built inline SVG is the safe illustration/logo path.
7. **Linking the bare directory on a SPA-fallback server** — `/v2/` (extension-less, not a file) gets rewritten to the OLD app's `index.html`. Link explicit files: `/v2/index.html`, `/v2/create.html`.
8. **`import`ing a module that lives outside the served root** — the URL is unreachable and the code was never built. Add your own entry point to the existing esbuild/webpack config so the logic compiles in.
9. **Static-copying a source module instead of bundling it** — the copy does not run and drifts, re-introducing bugs the original already fixed. Reuse the original module through the new entry point.
10. **Subsetting to latin-only and losing the ₿ glyph** — `U+20BF` lives in latin-ext (`U+20AD-20C0`); keep latin **+** latin-ext per weight (drop vietnamese/cyrillic), or render the brand mark as an inline SVG path with zero font dependency.
11. **Chaining navigation and a read in one browser call** — a CDP read issued during navigation can time out. Navigate and screenshot in separate calls, and prefer raw `cdp("Page.captureScreenshot", format="png")` + base64-decode to a known absolute path over `capture_screenshot()`, whose workspace-relative path is unreliable across calls.
12. **Claiming a minified IIFE works with no evidence** — install `window` `error` + `unhandledrejection` listeners that push into a readable array *before* the async action, then read the array back. A minified bundle fails with no trace otherwise.
13. **Treating a screenshot that "looks right" as proof fonts loaded** — `document.fonts.status === 'loaded'` is the real check.
14. **Calling an unreachable external data source a code bug** — exercise the SAME imported functions via the repo's node smoke test and report it as "environment wall, not code bug" with curl-timeout-vs-working-endpoint evidence. Never leave a code path unexercised while claiming it works.

If the page's external data source is unreachable from the sandbox, exercise the SAME imported functions via the repo's node smoke test (or a throwaway node script) and report it as "environment wall, not code bug" with the curl-timeout-vs-working-endpoint evidence. Never leave a code path unexercised while claiming it works.
