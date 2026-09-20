---
name: web-quality-audit
description: "Quality audit of a built site — compute WCAG contrast, check a11y semantics and CSS tokens, and prove JS/bundle findings against the shipped artifact rather than the source."
version: 1.1.0
author: webrefactor
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [a11y, contrast, wcag, semantic-html, css-tokens, esbuild, code-quality]
    related_skills: [static-site-integration, csp-static-site-build, web-fonts-self-hosting, requesting-code-review, code-review]
    trigger_conditions:
      - "audit the site"
      - "web quality audit"
      - "check contrast on the page"
      - "WCAG ratio"
      - "a11y audit"
      - "accessibility check"
      - "is this site accessible"
      - "css token drift"
      - "hardcoded hex instead of tokens"
      - "dead js selectors"
      - "esbuild bundle missing feature"
      - "inline styles dropped by CSP"
      - "heading order / aria-current check"
      - "site looks broken after the build"
---

# Web Quality Audit

The quality pass on a built site: tokens, contrast, focus states, semantics, JS hygiene. Prove every finding with a measurement (computed ratio, DOM geometry, grep of the built artifact) — never an eyeball claim.

Serving-layer constraints (SPA fallback, CSP, font self-hosting) are checked in `static-site-integration`; assume those passed and audit the page set itself.

## When to Use

- A site has been built and needs its quality pass: contrast, a11y semantics, token hygiene, JS/bundle truth
- A user says the page "looks off", is unreadable, or has an invisible section, and you need measurements rather than opinions
- A CSP was tightened (`style-src 'self'`) and layout/styling regressed in a way that reads as a CSS bug
- A feature works in `src/` but is missing in the deployed bundle (dynamic imports, tree-shaking)
- Reviewing someone else's built artifact before it ships, or verifying a builder's "it renders fine" claim
- Planning a batch of fixes your human will apply in one round and wanting the findings grouped by class

## Not For

- Serving-layer constraints — CSP headers, SPA fallback, hashes, font self-hosting → use `static-site-integration` or `csp-static-site-build` instead
- Auditing the typography pipeline itself (subset capture, `@font-face`, missing glyphs) → use `web-fonts-self-hosting` instead
- A general code review of source changes rather than built output → use `code-review` instead
- Headless browser harness work (CDP/Playwright capture, geometry probes) → use `gui-app-headless-testing` instead
- Design decisions — palette, type scale, art direction → use `frontend-taste` instead
- Verifying a QR code's density and camera-scannability → use `qr-code-verification` instead
- Deploying the site or checking whether it is live → use `static-site-deploy-verify` instead

## Procedure

1. **Inventory the page set.** `wc -l` the HTML/CSS/JS, then per page:
   - exactly one `<h1>`; no heading-level skips (h1→h3 is a skip); `<main>` present; `aria-label` on navs; `role="alert"` on status/error text.
   - `aria-current="page"` on the active nav link on EVERY page — it is typically only set on the page the builder tested.
   - zero inline `<script>` (CSP), and check every `style="..."` attribute against the "Inline styles under a strict CSP" rule below — under `style-src 'self'` they are not a style preference, they are dropped.
2. **Contrast:** compute WCAG ratios for EVERY token-on-background pair, including alpha-blended rgba text (blend it over its background first — alpha text on a colored band usually fails at ~.7 alpha). Run `scripts/contrast-wcag.py` per pair. Thresholds: small text 4.5:1, large text (≥24px, or ≥19px bold) 3:1. Brand-orange-on-cream and brand-color-as-text both fail regularly. Decorative oversized numerals that fail should be `aria-hidden`, not recolored.
3. **Token hygiene:** confirm colors/type/spacing all flow from `:root` variables (`grep -c 'var(--' per css file`); flag hardcoded hex in pages that should be tokens.
4. **JS dead-code check:** cross-check every selector string in the JS against the HTML. Before flagging an ID as dead, check it is not injected at runtime (`createElement`, an `el()` helper) — dynamic UI creates nodes the HTML never contains.
5. **Bundle verification:** the built artifact is the truth, not the source. See `references/bundle-verification.md` — dynamic imports that tree-shake out of an esbuild bundle break features at runtime while the source looks correct.
6. **Layout/clipping bugs:** serve locally (`python3 -m http.server <port> --directory public`), open in a browser, and verify geometry with `getBoundingClientRect()` comparisons (content edge vs overlay edge) — works even when screenshots cannot be captured. `overflow:hidden` + absolutely-positioned decorations (ribbons, bows, halos) overlay corner content silently; the fix is clearance (`margin-right`) + `white-space:nowrap` on the content, verified by measured clearance.
7. **Deploy-state claims:** before telling anyone a site is or isn't live, check `git remote -v` and `git status` in the repo. No remote or uncommitted files = the build exists only locally; debugging a "why can't I see it" against a never-pushed tree wastes the room.

## Inline styles under a strict CSP are DROPPED, not sanitised

When the served CSP is `style-src 'self'` (no `'unsafe-inline'`), a `style="..."`
attribute is **discarded by the browser**. The element renders unstyled — it does not
throw, log a visible error, or degrade gracefully — so it reads as a layout bug rather
than a policy violation, and it is easy to "fix" in the wrong place.

What to convert, and what to leave alone:

| Source | Blocked? | Action |
|---|---|---|
| `style="..."` in shipped HTML | yes | move the declaration into a class |
| `setAttribute('style', ...)` / `el({style: '...'})` from JS | yes | same |
| `<style>` block | yes | move to a stylesheet (or hash it) |
| `el.style.width = ...`, `el.style.cssText = ...` (CSSOM) | **no** | leave it |

That last row is why this is a small job and not a rewrite: `style-src` constrains how
stylesheets and style *attributes* are applied; the CSSOM API is explicitly out of
scope. Check the distinction before touching working code.

Name each utility after the property it sets (`.mt-64`, `.w-full`, `.optional-note`) so
the call site still reads clearly, and **do not add `!important`**: an inline style
outranked every stylesheet rule, and a class deliberately should not — page rules
beating a utility is the point. Then verify by measurement, not by grepping the
markup:

1. `grep -rn 'style="' ` over the shipped HTML and `grep -rn 'style:' ` over the
   built bundles — both must be zero.
2. Install a violation listener **before** the bundle runs, then clear the cache and
   load every page (a cached stylesheet hides a regression):
   `cdp('Page.addScriptToEvaluateOnNewDocument', source: "window.__v=[];document.addEventListener('securitypolicyviolation',e=>window.__v.push(e.violatedDirective)) ")`
   then read `window.__v` per page. Expect zero — a `style-src-attr` entry means a
   style attribute survived.
3. Assert **computed-style parity** for each converted element (the value the inline
   style used to carry). Zero violations only proves nothing was blocked; it does not
   prove the new class actually applies.

## Pitfalls

1. **A strict CSP turns inline styles into a silent layout bug, not an error.** Under `style-src 'self'` a `style="..."` attribute is dropped, so the symptom is "this block lost its spacing" — usually misdiagnosed as a CSS specificity problem and patched in the wrong place. Convert, then measure computed styles; and remember the CSSOM (`el.style.x = …`) is unaffected, so only attributes and `<style>` blocks need work.
2. **Dynamic imports vanish from esbuild bundles.** An entry that eagerly imports a page module tree-shakes that page's dynamic `import('x')` calls when the loader cannot prove they run; grep the BUILT file for every runtime dependency string (`jsqr`, `qrcode`, ...) — `grep` in source proves nothing.
3. **Missing selector ≠ dead code.** Verify dynamic injection before flagging; a false "dead" report sends the builder chasing code that is live.
4. **Screenshots are the weakest evidence.** CDP screenshot capture can time out, fail silently, or not exist in a sandbox; DOM geometry measurements from a real render are deterministic and sufficient. Pair them when you can get both.
5. **Contrast claims must be computed.** "Looks low" is not a ratio; always run the math, and include the alpha-blended case.
6. **`.reveal`-style scroll animations hide content without JS.** `opacity:0` start state leaves content permanently invisible if the bundle fails; gate the hidden state behind a `js` class added on `<html>` so no-JS users still see it.
7. **One-page a11y fixes are never one-page.** `aria-current`, focus-visible, and token fixes land on every page in the set — audit all pages, then batch the report so the builder fixes the class in one round.

8. **The built artifact is the audit target, not `src/`.** A grep or a ratio computed against source files proves nothing about what ships. Quote the file you actually measured (`public/`, `dist/`, the served response) — an audit that cites `src/` cannot distinguish a stale build from a real regression.
9. **Serve with the production headers or the audit proves nothing.** Auditing over a bare `python3 -m http.server` (no `style-src`, no `font-src`) hides exactly the failures this pass exists to catch. Diff the *served* headers first, then audit under them.
10. **A ratio that ignores compositing is not a measurement.** Text over a gradient, image or alpha band must be sampled at the composited pixel; a token pair that passes on paper (4.5:1 nominal) routinely fails over a hero image. Blend alpha and sample the real background before scoring.
11. **Group findings by class, with file + selector for each.** A flat list of "issues" sends the builder back into the same hunt; batch by token / CSP / a11y / bundle and state the exact location so every fix lands in one round.

## Support files

- `scripts/contrast-wcag.py` — WCAG ratio for solid or alpha-blended token pairs; run per pair during the contrast pass.
- `references/bundle-verification.md` — verifying an esbuild output bundle: tree-shaken dynamic imports, expected-dep grep list, stale-bundle pinning.
