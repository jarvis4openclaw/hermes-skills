---
name: print-layout-design
description: Use when designing HTML/CSS that must print correctly — greeting cards, foldable sheets, printable tickets. Covers fold maps, @media print, ink cost and QR size for paper.
version: 1.1.0
author: Hermes Agent
license: MIT
tags: [design, print, css, qr, greeting-card, media-print]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [print, css, fold, greeting-card, qr, media-print]
    related_skills: [qr-code-verification, bitcoin-business-card, web-fonts-self-hosting]
    trigger_conditions:
      - "greeting card layout"
      - "printable card"
      - "fold map"
      - "quarter fold"
      - "media print CSS"
      - "design for printing"
      - "the printed output has blank pages"
      - "QR code not scanning from paper"
      - "card back text landed on the wrong side"
      - "print layout for a business card"
      - "how big should the QR code be when printed"
      - "print-only DOM"
      - "printable ticket layout"
---

# Print Layout Design

Designing HTML/CSS that must come out of a real printer correctly — greeting
cards, foldable sheets, printable tickets. Screen-verified is not
print-verified; the failure modes are different (CSP, ink cost, fold
geometry, QR scannability) and mostly invisible until paper comes out.

## When to Use

- Building an artifact that ends up **on paper**: greeting card, foldable sheet, printable ticket, business card.
- The output must survive a **physical fold** and the panel map is not written down yet.
- A **QR code** has to scan from paper with a phone camera, not just render on screen.
- The print must be **exactly one page** and blank sheets are appearing.
- Sensitive values (keys, codes, recovery material) must be **absent from the printed DOM** entirely.
- The HTML is served under a **CSP** and must still print with the right fonts and glyphs.
- You need a programmatic pre-flight (overlap assertions, emulated print) before handing the physical test to the user.

## Not For

- **Verifying that a rendered QR code actually decodes** (decoder runs, density maths, scannability proof) → use `qr-code-verification` instead.
- **Self-hosting the webfonts** used by the print artifact → use `web-fonts-self-hosting` instead.
- **General web/app visual design** with no paper output → use `frontend-taste` or `web-redesign-art-direction` instead.
- **Integrating new pages into an existing served site** (CSP, SPA fallback) → use `static-site-integration` instead.
- **The final pre-deploy design verification of a web artifact** → use `design-delivery-verification` instead.
- **Planning the page set / IA of a site** → use `web-ia-planning` instead.
- **Generating the artwork itself** (illustration, pixel art) with no print constraints → use `creative-ideation` or `sketch` instead.

## Workflow

1. **Lock the physical format first** — sheet size (`@page { size: letter; margin: 0 }`),
   fold pattern, quadrant/panel map. Write the panel map as a table in the spec
   before any CSS; fold geometry errors are the #1 print bug and cheap to fix on paper,
   expensive after ink.
2. **Spec content zones per panel** — strict vertical stacks in normal flow, fixed
   gaps, no absolute positioning except single pinned items (a footer URL).
3. **Build a print-only DOM subtree** for anything that must not leak screen
   content (see secrets rule below).
4. **Verify programmatically, not by eye** — then get a real print test.

## Always-on rules

- **`@media print` hides the app, not greys it.** `visibility:hidden` leaves
  elements in layout flow — the body still measures N pages tall and the
  printer emits blank sheets. Use `display:none` on the specific non-print
  containers so the document collapses to exactly one page.
- **Secrets never enter the print DOM.** Anything sensitive (keys, codes,
  recovery material) must be absent from the print subtree's markup entirely —
  not `display:none`d, not masked. A print-only sibling node (e.g.
  `#print-card` next to the ticket, never a child) makes selector accidents
  structurally impossible. Verify by grepping the rendered subtree for the
  secret strings: expect zero.
- **QR codes: size for the worst camera, not the screen.** Home-print floor
  is ~68mm for a dense URL payload; ~34mm looks fine on screen and fails
  phone scans off paper. Pure `#000` modules on `#fff` (colored QRs die to
  inkjet dithering), error-correction `M` (H smudges at print size), quiet
  zone ≥4mm, `image-rendering:pixelated` on the canvas.
- **QR libraries set inline canvas styles.** The `qrcode` npm package writes
  `style="width:Npx;height:Npx"` inline, which beats stylesheet `width:100%` —
  the canvas renders at full intrinsic size and overflows its tile onto
  neighboring content. Override with `width:100%!important;height:100%!important`
  inside a fixed-size tile.
- **Overlap assertions are code, not vibes.** Measure
  `getBoundingClientRect()` of every stacked element and assert
  `prev.bottom < next.top` for each adjacent pair. Vision models and eyes
  miss slow bleeds; rects don't.
- **Paper is not the screen background.** A "white" panel must be `#FFFFFF`,
  not a near-white token like `#FFFDF9` — printers render #FFF as "no ink"
  and near-whites as a visible cream wash. Full-bleed color fronts are ink
  waste; expect users to ask for white-front designs with one spot of color.
- **Fold lines:** dashed `1.5px` guides at exact panel midpoints,
  color light enough to ignore after folding (`#B9AE9E`-class), verified
  with `getBoundingClientRect` against the expected inch offset.

## Quarter-fold map (8.5×11, 2×2 of 4.25×5.5in)

The map that survived a real physical fold test — all panels upright,
**no 180° rotations** (rotated bottom rows are the classic quarter-fold bug;
they land the back text at the wrong edge):

| Sheet quadrant | Card face | Content |
|---|---|---|
| Top-left | FRONT | white panel, hero mark, title |
| Top-right | BACK | near-empty; footer item (e.g. URL) pinned with `justify-content:flex-end` |
| Bottom-left | inside-left | empty |
| Bottom-right | inside-right | main stack (caption → QR → amount → message → date) |

Fold-line check that caught a real bug: if the user reports the back text
landed on the physical top, the rows are swapped — move front to a top
quadrant and re-map diagonally, don't add rotations.

## Verification

- Emulate print: CDP `Emulation.setEmulatedMedia` (media `print`) +
  `Page.captureScreenshot`, or `Page.printToPDF` → PNG. Screenshot the full
  sheet and check: panel map, fold lines on midpoints, no overlaps, no
  rotated content, one page only.
- `document.fonts.size` / `instanceof SVGElement` checks catch two silent
  killers: CSP-blocked webfonts falling back (self-host woff2 + `@font-face`
  when the server CSP has no `font-src` — it falls back to `default-src 'self'`;
  keep latin + latin-ext subsets, currency/symbol glyphs like ₿ live in
  latin-ext) and `document.createElement` producing HTML-namespace nodes that
  never paint inside `<svg>` (use `createElementNS`).
- The final gate is always a physical print + phone scan. CSS cannot prove
  what a printer does to a quiet zone; say so and hand that test to the user.

## Pitfalls

1. **Don't trust a vision model's read of near-empty panels** — it calls a lone bottom-pinned element "centered". Trust the CSS rule and the measured rect.
2. **Don't spec colored strokes/outlines to fix contrast against a colored ground without reconsidering when the ground changes** — a cream stroke that saved an orange-on-orange box is dead weight on a white front.
3. **Long user messages need a hard clamp** (char cap + line clamp + ellipsis) in the print node, or a long greeting collides with the pinned footer.
4. **`visibility:hidden` leaves elements in layout flow** — the body still measures N pages tall and the printer emits blank sheets. Use `display:none` on the specific non-print containers.
5. **A "white" panel must be `#FFFFFF`, not a near-white token** (`#FFFDF9`) — printers render #FFF as "no ink" and near-whites as a visible cream wash.
6. **Colored QR modules die to inkjet dithering** — pure `#000` on `#fff`, error-correction `M` (H smudges at print size), quiet zone ≥4 mm, `image-rendering:pixelated`.
7. **The `qrcode` npm package writes inline `style="width:Npx;height:Npx"`** which beats a stylesheet `width:100%` — override with `width:100%!important;height:100%!important` inside a fixed-size tile.
8. **Rotated bottom rows are the classic quarter-fold bug** — they land the back text at the wrong edge. Re-map diagonally; never add a 180° rotation to fix it.
9. **`document.createElement` inside `<svg>` produces HTML-namespace nodes that never paint** — use `createElementNS` for SVG elements.
10. **Region/currency glyphs (₿) live in the font's latin-ext subset** — if the server CSP has no `font-src` it falls back to `default-src 'self'` and self-hosted woff2 must keep both subsets.
11. **CSS cannot prove what a printer does to a quiet zone** — the final gate is always a physical print plus a phone scan; say so and hand that test to the user rather than declaring the artifact verified.
