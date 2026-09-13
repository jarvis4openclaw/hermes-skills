---
name: web-redesign-art-direction
description: Use when acting as art director on a team site redesign.
version: 1.1.0
author: jarvis
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [design, art-direction, redesign, palette, typography, csp, multi-agent]
    category: creative
    related_skills: [frontend-taste, popular-web-designs, design-md, web-fonts-self-hosting, csp-static-site-build, web-quality-audit]
    trigger_conditions:
      - "art director"
      - "site redesign"
      - "design spec"
      - "redesign spec JSON"
      - "canonize the palette"
      - "brand color decision"
      - "reference hero"
      - "anti-references"
      - "no Inter, no purple"
      - "type system for the redesign"
      - "critique the hero"
      - "design tokens handoff"
      - "team redesign build"
---

# Web Redesign Art Direction

For multi-bot redesign builds where this role owns taste: spec first, reference hero second, critique loop last. Other roles build from the spec, so it must be concrete enough to implement without you.

## When to Use

- You are the **taste owner** on a multi-agent site redesign and other roles will build from your spec.
- You need to produce a **design spec as JSON** (brand adjectives, anti-references, named palette roles, 3-font type system, layout principles, component visual notes).
- You must **canonize a color palette with the user** before anyone scaffolds tokens.
- You need to build a **reference hero** as one self-contained HTML file that later becomes the token source of truth.
- You are choosing **font delivery** for a page that will be served under a strict CSP.
- You are **screenshotting and critiquing** a page at desktop (~1440px) and mobile (~390px) widths.
- You are running the **generic-test** against the spec's own anti-reference list before handoff.
- You are handing a finished hero to the build role and need the exact handoff payload.

## Not For

- **General UI/UX taste guidance while implementing components** → use `frontend-taste` instead
- **Browsing a library of reference site designs for inspiration** → use `popular-web-designs` instead
- **Writing the durable design-system doc / component spec** → use `design-md` instead
- **Producing the subsetted webfont files and `@font-face` CSS** → use `web-fonts-self-hosting` instead
- **Diagnosing which CSP directive blocks an asset** → use `csp-static-site-build` instead
- **Auditing a built site for contrast, a11y, and token violations** → use `web-quality-audit` instead
- **Verifying that delivered design assets are the ones actually shipped** → use `design-delivery-verification` instead
- **Laying out a printable document or brochure** → use `print-layout-design` instead

## Procedure

1. **Ground the spec in reality, not the brief.** Pull the current site's actual CSS colors and flows from the repo if one exists locally (check for a source dir near the workspace before concluding a site is unreachable — a DNS failure on a staging URL does not mean the code is gone).
2. **Write the design spec as JSON** with: brand adjectives, anti-references (explicit 'no' list — no Inter, no purple, no card grids, no generic gradient meshes), a canonized color palette with named roles (primary / hover / deep / soft / ink / paper), a 3-font type system (display serif + body sans + mono for hashes/addresses), layout principles, and a component list with *visual notes, not code*. Cache it to disk in the project's redesign directory — teammates read it from there.
3. **Canonize color with the user before anyone scaffolds tokens.** Present candidate hexes with one-line taste reasoning each; it is a one-line token change early and a repaint later. Do not assume a canonical brand color beats the site's existing color — this user rejected the default Bitcoin `#F7931A` aesthetic in favor of the site's own `#FF8000`.
4. **Build the reference hero as a single self-contained HTML file** with inline `<style>` only (no inline `<script>` — strict CSP `script-src 'self'` is common on static servers) and hand-drawn inline SVG illustration (CSP `img-src 'self' data:` covers it). Check the target server's CSP/caching/routing headers in the repo before choosing techniques.
5. **Screenshot and critique before handing off.** Verify at desktop (~1440px) and mobile (~390px) widths, then iterate CSS tokens and the hero only — not the whole page — until it passes.
6. **Generic-test the result against the spec's own anti-reference list** (no Inter, no purple, no card grid, asymmetric layout, one focal point). Do not accept a vision model's praise at face value — they flatter; re-check the actual pixels against the checklist yourself.

## Font delivery under CSP

- External font CDNs (Google Fonts `<link>`) break silently on strict-CSP hosts: absent `font-src` falls back to `default-src`, and the stylesheet itself is blocked by `style-src 'self'` — local `file://` previews render fine, so the breakage only shows on deploy. Check the server's CSP in the repo before choosing font delivery; when in doubt, self-host.
- Self-host recipe: fetch the CSS2 API with a browser User-Agent to get woff2 URLs, download the `latin` AND `latin-ext` blocks per weight (symbol glyphs like ₿ U+20BF live only in latin-ext's `U+20AD-20C0` range — latin-only falls back to system mono), write a local `fonts.css` preserving each block's `unicode-range` with relative `src: url('assets/fonts/...')` paths.
- Verify over HTTP (not file://): `[...document.fonts].every(f => f.status === 'loaded')`, then screenshot-check any special glyph. For variable fonts (e.g. Fraunces `opsz`), confirm the captured woff2 URLs carry the requested axis ranges or weights render wrong.

## Screenshot pitfalls

- The `capture_screenshot()` browser helper times out on some pages (its full-page capture hangs on pending font fetches). Fall back to raw CDP: `cdp('Page.captureScreenshot', format='png', captureBeyondViewport=False)`, base64-decode the `data` field, and write the PNG yourself.
- Do one emulation change + one capture per browser call; chaining `setDeviceMetricsOverride` + two captures in one call trips the IPC timeout.
- A vision model reporting 'header cut off' on a mobile shot is often just the capture viewport, not a layout bug — confirm against the DOM/sticky CSS before 'fixing' it.

## Handoff

Deliver: spec JSON path, hero HTML path, both screenshots, the canonized palette, and an explicit 'extend these tokens' note to the build role. The hero file is the reference implementation — its inline `:root` tokens become the team's `tokens.css`.

## Pitfalls

1. **Writing the spec from the brief instead of the real site** — pull the current site's actual CSS colors and flows from the repo first. A DNS failure on a staging URL does not mean the code is gone; look for a source dir near the workspace before declaring a site unreachable.
2. **Canonizing a brand color without the user** — present candidate hexes with one-line taste reasoning each. It is a one-line token change early and a full repaint later. This user rejected the default Bitcoin `#F7931A` aesthetic in favour of the site's own `#FF8000`.
3. **Assuming your "canonical" palette beats the site's existing color** — do not overwrite an existing brand color by default; ask, then canonize.
4. **Shipping the hero with inline `<script>`** — strict `script-src 'self'` is common on static servers and blocks it. Use inline `<style>` only, plus hand-drawn inline SVG (covered by `img-src 'self' data:`).
5. **Choosing a font CDN without checking the CSP** — external font links break silently on strict-CSP hosts because the missing `font-src` falls back to `default-src` and the stylesheet itself is blocked by `style-src 'self'`. `file://` previews render fine, so the breakage only appears on deploy.
6. **Subsetting to latin-only** — symbol glyphs such as ₿ (`U+20BF`) live only in latin-ext's `U+20AD-20C0` range; a latin-only subset falls back to system mono. Keep latin **+** latin-ext per weight.
7. **Verifying fonts over `file://`** — check `[...document.fonts].every(f => f.status === 'loaded')` over HTTP, then screenshot-check any special glyph.
8. **Variable fonts captured with the wrong axis range** — for something like Fraunces `opsz`, confirm the captured woff2 URLs carry the requested axis ranges/weights, or weights render wrong.
9. **Using `capture_screenshot()` on a page with pending font fetches** — the full-page capture hangs. Fall back to raw CDP: `cdp('Page.captureScreenshot', format='png', captureBeyondViewport=False)`, base64-decode the `data` field, and write the PNG yourself.
10. **Chaining one emulation change plus two captures in a single browser call** — this trips the IPC timeout. Do one emulation change and one capture per call.
11. **Trusting a vision model that reports "header cut off" on a mobile shot** — it is often just the capture viewport, not a layout bug. Confirm against the DOM/sticky CSS before "fixing" a non-issue.
12. **Accepting a vision model's praise at face value** — they flatter. Re-check the actual pixels against the spec's anti-reference list yourself.
13. **Iterating the whole page instead of tokens + hero** — adjust CSS tokens and the hero only until it passes; repainting everything drifts from the spec and burns the budget.
14. **Handing off without the reference implementation** — the build role needs the spec JSON path, hero HTML path, both screenshots, the canonized palette, and an explicit "extend these tokens" note. Without it the palette gets re-invented.
15. **Skipping the generic-test** — run the result against the spec's own anti-reference list (no Inter, no purple, no card grid, asymmetric layout, one focal point) before declaring the hero done.