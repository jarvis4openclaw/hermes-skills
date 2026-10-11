---
name: web-ia-planning
description: Use when planning a site redesign, sitemap, or component map — turn a design spec and a real repo into a grounded IA plan (sitemap, section order, component inventory, data flow, build order) before any pixels.
version: 1.1.0
tags: [ia, sitemap, information-architecture, redesign, web, planning, component-inventory]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ia, sitemap, redesign, web, planning]
    related_skills: [csp-static-site-build, web-redesign-art-direction, static-site-integration]
    trigger_conditions:
      - "plan the site structure"
      - "sitemap for the redesign"
      - "information architecture"
      - "component map"
      - "what pages do we need"
      - "plan the redesign before building"
      - "section order for each page"
      - "site plan document"
      - "turn the design spec into a build order"
      - "copy outline for the new site"
      - "which components does this flow need"
      - "IA plan before pixels"
      - "plan the v2 site"
---

# Web IA / Site Planning

Produce structure before pixels: sitemap, section order, copy outline, component inventory, image slots, data flow, build order.

## When to Use

- A redesign, `/v2/`, or microsite is starting and nobody has written down the **page set and section order** yet.
- A design spec (JSON/markdown) or a marketing reference exists but the **real app flows** are not mapped to pages or components.
- You need a **component inventory** split into "spec components" vs "components the real flow requires" before a build agent starts.
- The site's domain will not resolve (internal/LAN/staging) and the plan risks filling the gap with invented endpoints or flows.
- A build order must be split into **UI-first and wiring phases**, or must end with an E2E/deploy-realism gate.
- Deployment constraints (CSP, SPA fallback, cache headers, deep links) have to be pinned down **before** the build order is fixed.
- Two agents are about to build the same site and you need one shared, citable source of ground truth.

## Not For

- **Building the pages once the plan exists** (CSP headers, `.html` links, font self-hosting, serving) → use `static-site-integration` instead.
- **Deciding how the site should look** — art direction, typography, layout taste → use `web-redesign-art-direction` instead.
- **A static site with a CSP to honour from scratch** (no existing site to integrate with) → use `csp-static-site-build` instead.
- **Final pre-deploy verification** of fonts, glyphs and CSP on a finished artifact → use `design-delivery-verification` instead.
- **Verifying a rendered QR code or print output** → use `qr-code-verification` instead.
- **Designing the print/paper version of an artifact** (fold maps, print CSS) → use `print-layout-design` instead.
- **Generic design critique or visual polish of an existing page** → use `frontend-taste` instead.

## Procedure

## Procedure

1. **Gather inputs before planning:** the design spec (JSON/markdown), any reference site (extract it live with web_extract), and screenshots (vision_analyze for layout structure). Batch these reads.
2. **Find the real source before marking anything unknown.** If the site's domain doesn't resolve (internal/DNS-blocked), do NOT treat functionality as a black box:
   - Search the workspace for the project name / domain (`search_files` on repo names, grep ARCHITECTURE/TOOLS docs).
   - Ask teammates / check for a local repo — a static site's source is usually on disk somewhere.
   - Read `server.py`/equivalent, `README.md`, and the main view/router JS yourself. Verify: inputs, endpoints (or absence thereof), external API allowlists (CSP `connect-src`), routing base-path behavior, exact brand color hexes from CSS.
3. **Only mark items [TBC] that are genuinely unresolvable**, and list them explicitly as open decisions with owners. Never invent endpoints, fields, or flows.
4. **Write the plan as a cached artifact** (e.g. `v2/site-plan.md`) with sections: ground-truth facts, sitemap, per-page section order table, copy outline with voice, component inventory (spec components + new ones the real flow requires), image slots with sizes, data-flow diagram, build order, open decisions for the user.
5. **Derive components from the actual flows, not the marketing reference.** A marketing-site template (e.g. Swan gifts) lacks app components — a real create/redeem flow adds things like ticket-result panels, status states, and warning callouts. Constraint-bearing copy (e.g. experimental-funds warnings) must keep its substance even when styling is reworked.
6. **Check deployment constraints before finalizing the build order — by running the server and curling headers, not by reading code alone:** server CSP (`script-src 'self'` → no inline scripts; `connect-src` → which external APIs are callable; **missing directives like `font-src` fall back to `default-src`**, which silently kills external fonts on deploy while working fine as a local file), SPA fallback rewriting extension-less paths (a bare `/v2/` can serve the OLD site — mandate explicit `.html` links), cache headers, and deep-link/fragment compatibility (`#code=…` share URLs must keep working across old and new versions).
7. **Split build order into UI-first and wiring phases** when flows involve crypto/payments, and end with an E2E test gate on a test network.
8. **End the build order with a deploy-realism check:** pages served through the real server (not `file://`), fonts confirmed loaded via `document.fonts`, special glyphs rendering in the right face, zero CSP console errors. A hero that only looks right opened as a local file has not been verified.

## Pitfalls

1. **Verify a teammate's summary against the repo before baking it into the plan** — secondhand facts drift (e.g. wrong color counts); the plan is only as grounded as its least-verified claim.
2. **A "static site with no backend" conclusion changes everything downstream** — plans that assume an API produce dead forms. Confirm from the server code, not from the domain's behavior.
3. **Preserving an old site while building `/v2/` means the new build must be base-path-aware** — it must not touch the root router or asset handling; see `static-site-integration`.
4. **One-line decisions that gate later work** (brand color canonization, tone of irreversibility warnings) belong in an explicit "open decisions" section addressed to the user, not buried in prose.
5. **Modules under a build root (e.g. `src/`) that get esbuild-bundled into the served tree cannot be linked from new static pages** — plan a second bundler entry that imports them, and note the bundle is prebuilt so deploys need no build tooling on the server.
6. **Special brand glyphs in text (₿, ✓-style marks) often live only in a font's latin-ext subset** — if fonts are self-hosted, require the covering subset and verify the glyph post-deploy, or convert the mark to an SVG path with no font dependency. See `web-fonts-self-hosting`.
7. **Reuse-by-bundling beats reimplementation for crypto/payment logic** — the existing module's smoke tests then cover exactly what the new pages import.
8. **"External API unreachable from the sandbox" is often an IPv6 problem in this environment** — force IPv4 (`curl -4`, `--resolve` with A records) before recording any E2E gate as blocked.
9. **A completed build in the working tree is not a deployment** — check for git remotes / untracked state before telling the user a URL is live, and record the actual ship step (e.g. rsync the served directory wholesale) in the plan.
10. **Do not let the marketing reference dictate the component inventory** — a template with no app flows will omit ticket-result panels, status states and warning callouts that the real flow requires.
11. **`[TBC]` is a debt, not a deliverable** — every `[TBC]` must appear in the open-decisions list with an owner; a plan that ships unresolved `[TBC]`s is not finished.
