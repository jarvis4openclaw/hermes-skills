---
name: web-fonts-self-hosting
description: Self-host web fonts so type survives a strict CSP or an offline deploy — woff2 subset capture, latin-ext glyphs, and verifying real rendering instead of a file:// preview.
version: 1.1.0
tags: [fonts, typography, csp, woff2, web-design, deploy]
metadata:
  hermes:
    category: creative
    related_skills: [web-quality-audit, csp-static-site-build, static-site-integration, frontend-taste]
    trigger_conditions:
      - "self-host fonts"
      - "self hosting web fonts"
      - "Google Fonts not loading"
      - "font falls back to a system font"
      - "strict CSP blocks fonts"
      - "font-src CSP directive"
      - "woff2 subset download"
      - "latin-ext unicode-range"
      - "custom font missing in production"
      - "fonts look right locally but wrong deployed"
      - "offline font deploy"
      - "variable font font-weight range"
      - "glyph missing from the font (bitcoin sign, arrows, ligatures)"
      - "next/font before Next 13"
---

# Web Fonts: Self-Hosting for Strict CSP / Offline Deploys

Use when a page with custom typefaces will be served under a restrictive Content-Security-Policy (or anywhere Google Fonts can't be trusted to load). Goal: fonts render identically in dev and production, no silent fallback.

## When to Use

- A page must render a custom typeface under a restrictive CSP (`style-src 'self'`, no `fonts.gstatic.com` in `font-src`)
- The deployed page falls back to system fonts while a local `file://` preview looks perfect
- An offline / bundled / LAN-only deploy (StartOS, static export, air-gapped box) needs the font files in-tree
- A brand-critical glyph (₿, an arrow, a ligature) renders as tofu or a system substitute in production
- Migrating off Google Fonts for privacy, perf, or supply-chain reasons
- You are about to judge typography and must first know whether you are looking at the real face or a fallback
- A Next.js 12 (pre-`next/font`) project needs the `@font-face` + preload wiring that 13+ does for you

## Not For

- Auditing contrast, a11y, focus states or CSS tokens across a built page → use `web-quality-audit` instead
- Serving the whole site under a CSP (headers, hashes, SPA fallback) → use `csp-static-site-build` instead
- The deploy host, vhost or header wiring itself → use `caddy-proxy-management` instead
- Choosing the typeface, palette or art direction in the first place → use `frontend-taste` (with `popular-web-designs`) instead
- Headless browser verification of a rendered page (CDP/Playwright harness) → use `gui-app-headless-testing` instead
- The printable companion of a card or comp (fold, trim, QR density) → use `print-layout-design` instead
- Verifying a QR code decodes and is camera-scannable → use `qr-code-verification` instead

## Why Google Fonts silently breaks

- `style-src 'self'` blocks the `fonts.googleapis.com` stylesheet `<link>`.
- Missing `font-src` falls back to `default-src` (usually `'self'`), blocking `fonts.gstatic.com` woff2 downloads.
- The failure is **silent**: local `file://` previews look perfect, the deployed page falls back to system fonts. Never validate typography from a local-file preview — serve over HTTP with the real CSP before judging.

## Self-hosting recipe

1. Fetch the CSS2 API with a browser User-Agent so it returns woff2:
   `curl -s -A "Mozilla/5.0 ... Chrome/120 ..." "https://fonts.googleapis.com/css2?family=<Family>:wght@...&display=swap"`
2. The response is one `@font-face` block per subset (latin, latin-ext, vietnamese, cyrillic…) with its own URL and `unicode-range`.
3. Download woff2s for the subsets you need (usually **latin + latin-ext**; drop vietnamese/cyrillic unless the content needs them) into `assets/fonts/`.
4. Write a local `fonts.css` reproducing those blocks with relative `src: url('assets/fonts/<file>.woff2')`, keeping `font-display: swap` and the original `unicode-range` values (they enable per-subset lazy loading).
5. Verify served over HTTP, not file://:
   - `document.fonts` shows every face `loaded`
   - `getComputedStyle(el).fontFamily` resolves to the custom face
   - visually check the exotic glyphs the design depends on (see pitfalls)

## Pitfalls

1. **Per-weight files are often one variable font in disguise.** Before writing a `@font-face` block
  per weight, hash the files: if `Fraunces-500/600/700-latin.woff2` are byte-identical, it is a single
  variable file and the correct declaration is **one block per subset** (latin / latin-ext) carrying
  `font-weight: 100 900` — declare the range and the browser instances the axis. Confirm with fontTools
  `fvar` rather than assuming, and check the **default instance**, which can differ from the filename:
  Public Sans's file reports `usWeightClass 100` ("Thin") while serving a 100–900 `wght` axis.
2. **`document.fonts.check('16px "X"')` is not an existence test.** It returns **true** for a family
  that is declared nowhere, and **false** for a declared face the page has not needed yet — lazy
  subset loading is correct, not a failure. To assert real availability, read `[...document.fonts]`
  statuses and force a subset with `document.fonts.load('16px "X"', 'łř')` (a character outside
  U+0000-00FF reaches the latin-ext face). Expect a normal page to have loaded only the faces its
  text needs; assert that none are `error`, not that all are `loaded`.
3. **No `next/font` before Next 13.** On Next 12 the whole mechanism is self-hosted `@font-face` plus a
  `<link rel="stylesheet">` in `_document`/`_app`. Add
  `<link rel="preload" as="font" type="font/woff2" crossOrigin="anonymous">` for the body face or it
  is fetched after first paint and the text reflows; the `crossOrigin` attribute is required because
  fonts are always requested in anonymous CORS mode.
4. **Exotic glyphs live in latin-ext, not latin.** Currency/special symbols like ₿ (U+20BF) are covered only by the latin-ext `unicode-range` (`U+20AD-20C0`). Self-hosting just the latin block — the easy mistake — makes the glyph silently fall back to a system face. Keep latin-ext for any face rendering such glyphs; verify with `0x20BF in TTFont(f).getBestCmap()` (fontTools).
5. **Brand-critical marks: inline a vector path, not a font glyph.** Extract the outline with fontTools and embed as SVG `<path>` — zero font dependency, immune to subset loading, pixel-identical everywhere:
  ```python
  from fontTools.ttLib import TTFont
  from fontTools.pens.svgPathPen import SVGPathPen
  f = TTFont('font.woff2'); gs = f.getGlyphSet()
  cmap = f.getBestCmap()
  pen = SVGPathPen(gs); gs[cmap[0x20BF]].draw(pen); d = pen.getCommands()
  ```
  Wrap with `translate(cx cy) scale(S -S) translate(-centerX -centerY)` — font units are y-up, SVG y-down, hence the negative scale.
6. **Variable fonts (e.g. Fraunces `opsz`)**: confirm the captured woff2 URL carries the requested axis ranges or optical sizing/weights render off.
7. **Relative paths**: `fonts.css` and `assets/fonts/` must keep their sibling relationship after any move into a deploy tree — re-check post-restructure.
8. **Same-color camouflage**: a glyph centered over a same-hue graphic element (e.g. an orange ₿ behind an orange ribbon stripe) is invisible even when rendering correctly. When a user reports a missing mark, check overlap/contrast before assuming a font failure — `getBoundingClientRect()` on the element tells you if it rendered and where.

9. **A 404'd woff2 degrades silently inside the `src` list.** If the local URL is wrong, the browser walks to the next `src` entry — or the system stack — while the declaration still reads correct. Check the *status* of every face in `document.fonts` (an `error` entry is the real signal) rather than trusting the CSS.
10. **Preloading the wrong face costs more than not preloading.** A `preload` on a face the first viewport never uses (display face, latin-ext-only face) delays the one that does. Preload only the body face, at most two files, and keep `crossOrigin="anonymous"` — fonts are always requested CORS-anonymous.
11. **A subset fetched from the Google CDN is cut at request time.** Re-requesting the CSS2 URL later can return different subset URLs and `unicode-range` values, so glyph coverage changes under a rebuild nobody edited. Commit the downloaded woff2 binaries *and* the generated `fonts.css` to the repo.

## Verification checklist before shipping

- [ ] Page served over HTTP with production CSP, not file://
- [ ] All faces `loaded` in `document.fonts`
- [ ] Exotic glyphs (₿, arrows, ligatures) visually correct
- [ ] Zero CSP console errors
