---
name: design-delivery-verification
description: Use when finalizing web design artifacts for deployment — verify CSP, self-hosted fonts, brand glyphs and real-server rendering before declaring a design done.
version: 1.1.0
tags: [design, css, fonts, csp, verification, deployment, html]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, css, fonts, csp, deploy, verification]
    related_skills: [web-redesign-art-direction, web-fonts-self-hosting, static-site-integration]
    trigger_conditions:
      - "is this design ready to deploy"
      - "final check before handoff"
      - "fonts broke after deploy"
      - "text looks fine but the deployed page lost its typography"
      - "verify the design on the real server"
      - "brand glyph not rendering"
      - "CSP is blocking my fonts"
      - "hand this design to the build agent"
      - "screenshot looked right but deployment looks wrong"
      - "self-host the fonts before shipping"
      - "check the CSP before choosing asset URLs"
      - "declare the design done"
      - "verify glyphs are in the subset"
---

# Design Delivery Verification

Verifies fonts, glyphs, CSP, and rendering before a design handoff. Rules for the final step of any web-design build: making sure what looked right in the local preview actually survives deployment. Load alongside the design skill that produced the artifact (e.g. `web-redesign-art-direction`, `frontend-taste`) before declaring a design done or handing it to a build step.

## When to Use

- A design looks correct in the local preview and you are about to **declare it done** or hand it to a build agent.
- Typography **silently fell apart on deploy** (system fonts, wrong weights) while the local file was fine.
- A **brand glyph or symbol** (₿, ✓, ®) is missing, invisible, or rendering in the wrong face.
- It is unclear whether an external font/style CDN is actually callable under the deployment **CSP**.
- Fonts must be **self-hosted** and you need the latin + latin-ext subsets kept intact.
- A symbol overlaps a same-colored decoration and you need to prove the cause (font vs. geometry).
- You need deploy-accurate handoff notes: which assets are self-hosted, which paths must stay siblings, what is pure-vector.

## Not For

- **Integrating new pages into an existing served site** (SPA fallback, router collisions, cache headers) → use `static-site-integration` instead.
- **Deciding how the site should look** — art direction, type scale, layout taste → use `web-redesign-art-direction` instead.
- **Planning the page set and section order before a build** → use `web-ia-planning` instead.
- **The mechanics of self-hosting a webfont** (subsetting, `@font-face` generation, unicode-range surgery) → use `web-fonts-self-hosting` instead.
- **Verifying a rendered QR code decodes** → use `qr-code-verification` instead.
- **Designing print/paper output** (fold maps, print CSS, ink cost) → use `print-layout-design` instead.
- **A design critique or visual-polish pass with no deployment involved** → use `frontend-taste` instead.

## Procedure

1. **Check the deployment CSP before choosing asset URLs.** Fetch the real server's response headers (`curl -sI`). If `font-src` is absent it falls back to `default-src`; `style-src 'self'` blocks external stylesheets like Google Fonts. External font/style CDNs behind such a CSP fail *silently* — text falls back to system fonts and the whole typography layer is lost.
2. **Self-host fonts when CSP is same-origin.** Download woff2 from the Google Fonts CSS2 API using a browser User-Agent (otherwise you get TTF). Keep both `latin` and `latin-ext` `@font-face` blocks per weight; drop cyrillic/vietnamese. Write a local `fonts.css` with the unicode-ranges preserved and relative `src` paths, and keep the fonts directory a sibling of the css so relative paths survive moves.
3. **Verify critical glyphs exist in the subset files.** A glyph can be listed in a `unicode-range` yet the subset file still be the wrong one — check with fontTools (`TTFont(f).getBestCmap()`), e.g. U+20BF (₿) lives in latin-ext, not latin. Confirm rendered output with `document.fonts` in the browser (`[...document.fonts].map(f => f.family + ':' + f.status)`).
4. **Inline brand-critical symbols as vector paths, not font glyphs.** For a logo mark or brand symbol inside an SVG illustration, extract the glyph outline from the font file (`fontTools` `SVGPathPen` on the glyph set) and embed it as an SVG `<path>` with an explicit transform. Font-glyph `<text>` in SVG can fail from subset gaps and renders inconsistently; paths render identically everywhere. Remember SVG font coordinates are y-up: scale by `fontSize/unitsPerEm` and negate y.
5. **Never overlap a mark with a same-colored decoration.** A symbol centered behind a same-color stripe/ribbon/background element is invisible — position brand marks in clear space. When a user reports a symbol "not rendering", first check its rendered bounding box (`getBoundingClientRect()`) and what element overlaps it before assuming a font failure.
6. **Verify served over HTTP, not `file://`.** CSP, relative paths, and font loading all behave differently served vs local. Serve (`python3 -m http.server`), then screenshot desktop AND mobile widths via the browser tool, and visually inspect the exact pixels of anything the user flagged. A local-file screenshot looking perfect proves nothing about deployment.
7. **Hand off with deploy-accurate notes.** Tell the consumer (build agent or user) which assets are self-hosted, which paths must keep their sibling relationship, and which elements are pure-vector (no font dependency).

## Pitfalls

1. **Screenshot tools sometimes hang on full-page capture or external font fetches** — use `captureBeyondViewport: false` and viewport-only clips, and retry once on timeout; retries usually succeed.
2. **Vision models misread screenshots** (describe the wrong element, claim a visible glyph is absent) — cross-check with DOM facts (computed styles, `document.fonts`, bounding boxes) before acting on a vision critique.
3. **A screenshot taken from `file://` proves nothing** — no CSP, no SPA fallback, different relative-path resolution. Always serve over HTTP before verifying.
4. **`font-src` absent means the fallback is `default-src`, not "fonts allowed"** — a self-same-origin `default-src` silently kills Google Fonts on deploy while working perfectly locally.
5. **`style-src 'self'` blocks external stylesheets outright** — the font never even gets requested; the page just falls back.
6. **Keeping only the `latin` subset drops brand glyphs** — U+20BF (₿) and similar marks live in `latin-ext`; keep both blocks per weight and drop only cyrillic/vietnamese.
7. **A glyph listed in a `unicode-range` can still be missing from the file** — verify with fontTools `TTFont(f).getBestCmap()`, not by reading the CSS.
8. **SVG `<text>` in a brand mark is fragile; convert to a `<path>`** — extract the glyph outline with `SVGPathPen` and remember SVG font coordinates are y-up (scale by `fontSize/unitsPerEm`, negate y).
9. **A mark behind a same-colored stripe is invisible, not broken** — check `getBoundingClientRect()` and the overlapping element before blaming fonts.
10. **`document.fonts` is the only proof a webfont actually loaded** — `[...document.fonts].map(f => f.family + ':' + f.status)`; a CSS `@font-face` rule loading nothing still reports nothing.
11. **`python3 -m http.server` serves the tree but applies no CSP** — for CSP-accurate verification, curl the real server's headers (`curl -sI`) and compare against the source config before signing off.
