---
name: bitcoin-fits-site
description: Update the Bitcoin FITS Calculator site (bitcoin-fits.onrender.com) — edit code, add features, deploy.
category: devops
version: 1.1.0
metadata:
  hermes:
    tags: [bitcoin, fits, calculator, cloudflare-pages, deploy, devops]
    trigger_conditions:
      - "update the bitcoin fits site"
      - "bitcoin fits calculator"
      - "fits.wahid.my"
      - "bitcoin-fire-calc"
      - "deploy bitcoin fits"
      - "fix bitcoin calculator"
      - "Cloudflare Pages bitcoin"
      - "FITS calculator bug"
      - "donate button / QR bitcoin fits"
      - "fits calculator share URL"
      - "True Market Mean API"
---

# Bitcoin FITS Calculator Site

**Live URL:** https://fits.wahid.my/ (Cloudflare Pages)
**Pages.dev URL:** https://bitcoin-fits.pages.dev/
**Legacy URL (Render — shutting down):** https://bitcoin-fits.onrender.com/
**GitHub:** `jarvis4openclaw/bitcoin-fits` (public)
**Branch:** `main`
**Local path:** `/home/wahid/bitcoin-fire-calc/`
**Cloudflare Pages project:** `bitcoin-fits`
**Custom domain:** `fits.wahid.my` (CNAME → `bitcoin-fits.pages.dev`, proxied)

## When to Use

- Updating the Bitcoin FITS calculator — editing the calculator JS, adding a model, fixing a form/validation bug, or changing the donate setup.
- Deploying the static site to Cloudflare Pages (auto-deploy via git push, or manual wrangler).
- Troubleshooting the running site (500 errors, broken share URLs, modal/UI glitches, missing assets).
- Working with the Flask legacy version while it is still on Render.

## Not For

- The Lightning Wallets Comparison site (a different calculator with its own repo/skill) → use `update-lightning-wallets-site` instead.
- Generic Flask app patterns (validation, tooltips, jQuery gotchas) that appear here → use `flask-web-app-patterns` instead.
- Cloudflare Pages deployment mechanics in general → use `cloudflare-pages-deploy` / `cloudflare-pages-static-site` instead.
- Bitcoin investment advice or price analysis — this skill is only about running the site.

## Stack

The site has TWO versions:

### Static version (`dist/` — PRIMARY, free hosting)
- Pure client-side HTML/CSS/JS — no server, no Python
- `dist/index.html` — standalone HTML (no Jinja2)
- `dist/assets/js/calculator.js` — CAGR data, projection math, Plotly chart generation, TMM API fetch, all ported from `app.py`
- `dist/assets/js/scripts.js` — Form handling, URL params, theme toggle, share, model tiles, donate modal
- `dist/assets/css/styles.css` — Full CSS (copied from Flask version)
- `dist/assets/donate-qr.png`, `dist/assets/favicon.png` — Static assets
- Deploying to **Cloudflare Pages** (free) — see `cloudflare-pages-deploy` skill
- All calculation runs in the browser; True Market Mean API called client-side with 1hr cache
- Asset paths changed from `/static/...` to `/assets/...`

### Flask version (legacy, still on Render — to be shut down)
- Python Flask + Plotly 6.5, Bootstrap 4 + Font Awesome frontend
- Runs under systemd: `bitcoin-fire-calc.service` (user)
- Keepalive: `/home/wahid/clawd/scripts/bitcoin-fits-keepalive.sh` (every 5 min cron)
- Deployed via gunicorn on Render, `render.yaml` at project root
- **Render is being replaced by Cloudflare Pages to eliminate overage charges**

## File Map

### Static version (`dist/`)

| File | Purpose |
|------|---------|
| `dist/index.html` | Standalone HTML — sidebar form, results container (JS-populated), modals, donate FAB |
| `dist/assets/js/calculator.js` | CAGR data tables, `calculateProjections()`, `runCalculation()`, `fetchTrueMarketMean()`, Plotly chart data builders |
| `dist/assets/js/scripts.js` | Form submit → `runCalculation()` → `renderResults()`, URL param pre-population + auto-calculate, theme toggle, share button, model tile selection, advanced CAGR, fixed withdrawal toggles, donate modal |
| `dist/assets/css/styles.css` | CSS variables for dark/light themes, tile grid, summary cards, starting-point banner, tooltips, donate modal, responsive |
| `dist/assets/donate-qr.png` | BOLT 12 QR code (downloaded from Render site) |
| `dist/assets/favicon.png` | 32×32 orange circle PNG (generated — original was 404 on both Render and local) |

### Flask version (legacy)

| File | Purpose |
|------|---------|
| `app.py` | Flask routes, CAGR data, projection logic, Plotly chart generation, custom CAGR models, summary stats, starting point info |
| `templates/index.html` | Jinja2 template — sidebar form, results (server-rendered), modals |
| `static/css/styles.css` | Same CSS as static version |
| `static/js/scripts.js` | Client-side JS for Flask version (theme, share, tiles, URL pre-pop — no calculation) |
| `requirements.txt` | Flask, Plotly, gunicorn |

## Donate Setup

Same BOLT 12 offer and QR as Lightning Wallets Comparison:
- Offer: `lno1pg8hgmeqwpshjsrhv95xjepwd4u3vggzz220lavkujt662gze403jee7jqsf20vsvfwk3s3wjx6353wqxtfs`
- Lightning Address: `pay@wahid.my`
- QR: `static/donate-qr.png` (copied from LWC project)
- CSS color scheme: `#ff8000` (matches site's existing orange theme)

## Deploy Workflow (Static Version — PRIMARY)

### Auto-deploy (Cloudflare native Git integration)
1. Edit files in `/home/wahid/bitcoin-fire-calc/dist/`
2. `cd /home/wahid/bitcoin-fire-calc && git add -A && git commit -m "message" && git push origin main`
3. Cloudflare Pages auto-deploys from `main` branch — build output directory: `dist`, no build command
4. Verify: `curl -s https://fits.wahid.my/ | grep -c "Calculate"` (should return 2)

### Manual deploy (wrangler CLI — for testing/quick fixes)
```bash
source ~/.hermes/.env
export CLOUDFLARE_API_TOKEN=$CLOUDFLARE_PAGES_API_KEY
export CLOUDFLARE_ACCOUNT_ID=$CLOUDFLARE_ACCOUNTID
cd /home/wahid/bitcoin-fire-calc/dist
npx wrangler pages deploy . --project-name=bitcoin-fits
```

### Note
- Render service has been deleted — no more overage charges ($0/month hosting)
- No `.github/workflows/` file needed — Cloudflare native Git integration handles auto-deploy
- GitHub token lacks `workflow` scope, so GitHub Actions files can't be pushed without `gh auth refresh -h github.com -s workflow`

## Deploy Workflow (Legacy Flask Version — being shut down)

1. Edit files in `/home/wahid/bitcoin-fire-calc/`
2. `cd /home/wahid/bitcoin-fire-calc && git add -A && git commit -m "message" && git push origin main`
3. Render auto-deploys from render.yaml — `autoDeploy: true` on branch `main`
4. Verify: `curl -s https://bitcoin-fits.onrender.com/ | grep -c "donate-btn"` (should return 1)

## Restart After Local Changes

```bash
systemctl --user restart bitcoin-fire-calc.service
```

## Verify Local

```bash
curl -s http://localhost:3457/ | grep -c "donate-btn"  # should return 1
curl -s http://localhost:3457/static/donate-qr.png -o /dev/null -w "%{http_code}\n"  # should return 200
```

## Port Configuration

- Local: 3457
- Health check: `curl -s http://localhost:3457/`

## Pitfalls

### Navigation / scope

1. **Render is deprecated — always verify the live URL after deploy** — The live site is `https://fits.wahid.my/` (Cloudflare Pages), NOT `bitcoin-fits.onrender.com` (shutting down). After any deploy, verify against the Cloudflare URL: `curl -s https://fits.wahid.my/ | grep -c "Calculate"` (expect 2). The Render URL will spin down and is not the source of truth.
2. **`step="1000"` on a general number input is a validation trap** — `min="1" step="1000"` means the browser only accepts 1, 1001, 2001… and silently blocks other whole numbers. Use `min="1"` alone for any whole-number field. Reserve `step` for currency-style stepping and never combine it with a general `min` unless intended.
3. **`safe_float(default=1.0)` hides missing data** — For required fields, default to `0.0` so server-side validation catches empty submissions. A `1.0` default makes empty forms silently pass as 1 BTC.
4. **Hidden fields with validation attributes block the entire form** — A hidden field (inside `display:none`) with `min`/`max`/`step`/`required` triggers "An invalid form control with name='...' is not focusable" in the console and silently prevents submission. Remove `required`/`min`/`max` from conditionally-hidden fields and let server-side validation handle them — or add `novalidate` to the `<form>`.
5. **Browser automation `form.submit()` vs click** — The browser_click tool does NOT trigger native HTML5 form submission (no submit event). If Calculate appears broken in browser tests, use `document.querySelector('form').submit()` in the console to verify the POST path works. This is a tooling limitation, not a site bug.
6. **jQuery `.val()` on `<select>` returns an array-like object** — `$(elem).val() === "yes ($)"` is ALWAYS false even when the value matches. Wrap with `String($(elem).val())` before string comparison. This is the #1 gotcha in the Flask form handlers.

### Layout / UI

7. **Tooltips clip at container boundaries with `bottom: 100%`** — Use `top: calc(100% + 6px); left: 0` (below element, left-aligned) instead. Long tooltip text needs `white-space: normal; width: max-content; max-width: 280px` or it goes off-screen.
8. **Fixed header covers modals on mobile** — `.header-bar` is `position: fixed; z-index: 1100`; Bootstrap modals default to `z-index: 1050`, so the modal close "×" hides behind the theme toggle. Override `.modal { z-index: 1150 !important; }`. Always check fixed elements against modal z-index when adding floating controls.
9. **Model tile selection state after POST** — After a POST, no tile is checked if Advanced mode was used. The Share button must fall back: `document.querySelector('input[name="model_number"]:checked') || document.querySelector('input[name="model_number"][value="6"]')`. Always query the DOM for `:checked`; never trust `form_data.model` alone.

### Calculation / data

10. **True Market Mean API is rate-limited** — BGeometrics free tier is 10 req/hr, 15 req/day. The 1-hour cache is mandatory; removing it will 429 the site.
11. **Asset paths differ between versions** — Flask serves from `/static/...`, static version from `/assets/...`. When copying code between versions, update ALL `src`/`href` attributes or assets 404.
12. **favicon was a 404** — Both Render and local Flask returned 404 for `/static/favicon.png`. Generated a 32×32 orange circle PNG. If the asset is missing again, regenerate rather than hunting for the original.

### Deploy

13. **Cloudflare auto-deploy only on git push to `main`** — The build output directory is `dist`, no build command. Manual wrangler deploys bypass the git history — prefer git push for auditable deploys. GitHub token lacks `workflow` scope, so GitHub Actions files can't be pushed without `gh auth refresh -h github.com -s workflow`.
14. **Local verification port is 3457** — `curl -s http://localhost:3457/ | grep -c "donate-btn"` should return 1. The local Flask service is `bitcoin-fire-calc.service` (user systemd).

## Recent Fixes (2026-06-10, Wave 5)

### 500 Error on Empty Bitcoin Stack
- Root cause: `safe_float(default=1.0)` meant empty submissions silently got 1.0 instead of triggering validation
- Fix: Changed default to 0.0 so `bitcoin_stack <= 0` catches it correctly
- Also moved to repo proper: `jarvis4openclaw/bitcoin-fire-calc` (public, branch `master`)

### Withdrawal Amount Number Input Bug
- Root cause: `navigator.clipboard.writeText()` requires HTTPS — fails silently on LAN
- Fix: Check `window.isSecureContext`, use `document.execCommand('copy')` fallback on non-secure contexts

### Horizontal Scrollbar on Sidebar
- Root cause: Child elements exceeding container width without CSS containment
- Fix: `box-sizing: border-box` + `max-width: 100%` on all sidebar children, `min-width: 0` on flex tiles

### Page Title Removed
- Removed `<title>Bitcoin FITS Calculator</title>` from `<head>` — no visible heading anywhere

### Regression Test (10 checks)
- Updated `tests/regression.sh` to include empty bitcoinstack, withdrawal_usd validation, default value checks

## Recent Fixes (2026-06-10, Wave 7)

### Calculate Button POST Blocked by Hidden Field Validation
- Root cause: `withdrawal_percentage` has `min="0.1"` but `value="0"` by default. When "Yes ($)" is selected, the field is hidden via CSS (`display: none`) but still in the form. Browser tries to validate it, can't focus the hidden field, blocks entire form submission with console error: "An invalid form control with name='withdrawal_percentage' is not focusable"
- Fix: Added `novalidate` attribute to form tag — disables HTML5 validation entirely, relies on server-side validation which already handles all checks
- Code: `<form method="POST" action="/" novalidate>`
- Lesson: When forms have conditionally-hidden fields with validation constraints, use `novalidate` + server-side validation. HTML5 validation can't show error messages for hidden fields and will silently block submission.

### Withdrawal Amount Validation Simplified
- Boss preference: Withdrawal Amount should accept ANY whole number > 0, no min/max constraints
- Current: `min="1" step="1"` (correct)
- Server-side: validates `withdrawal_usd <= 0` for "yes ($)" mode
- Lesson: Don't add artificial min/max constraints. Only rule: > 0.

### Model Cards Layout (3 Per Row)
- Boss preference: Show 3 cards per row for each model family (CAGR-based gets 3 cards, Power Law-based gets 3 cards)
- Current: `.model-tile` uses `flex: 1 1 30%` — fits 3 tiles per row
- Was: `flex: 1 1 45%` (2 per row) — changed to 30% for 3-tile layout

## Recent Fixes (2026-06-10, Wave 6)

### Model Tile CSS Regression
- Root cause: Uncommitted changes accidentally deleted the entire `.model-tile:hover`, `.model-tile.active`, `.model-tile .model-radio`, `.model-tile .model-tile-label/name/rate` rule block — tiles lost hover effect, active state (orange border + bg), radio button hiding, and label/name/rate typography
- Fix: Restored all 6 rule blocks after `.model-tile` base rule
- Lesson: When editing styles.css, the model tile section is fragile — always verify hover/active/radio rules exist after any change

### Hidden Required Field Blocks Form POST
- Root cause: Added `required` attribute to `withdrawal_percentage` input, but this field is hidden via CSS (`display: none`) when "Yes ($)" is selected — HTML5 validation still runs on hidden required fields, silently blocking form submission with no visible error
- Fix: Removed `required` from `withdrawal_percentage` (server-side validation already enforces > 0 for "Yes (%)")
- Lesson: Never add `required` to conditionally-hidden form fields — use server-side validation instead

## Recent Fixes (2026-06-09, Wave 4)

### 500 Error on Empty Form Fields
- HTML forms submit empty strings for unfilled fields, causing `float("")` / `int("")` ValueError
- Added `safe_float()` and `safe_int()` helpers that handle empty/missing/invalid inputs gracefully
- Extended validation to cover all critical fields: Bitcoin Stack, Your Age, Withdrawal Start Year, Withdrawal Amount/Percentage
- Empty form now shows a validation error instead of crashing with 500

### Removed Results Title
- The `<h3>Projection Results</h3>` heading is now removed entirely — the summary banner is enough

### Withdrawal Amount Validation
- Server-side: `withdrawal_usd <= 0` for "yes ($)", `withdrawal_percentage <= 0` for "yes (%)"
- Client-side: `min="1" required` on withdrawal_usd, `min="0.1"` on withdrawal_percentage

### Regression Test Suite (9 tests)
- Updated `scripts/regression.sh` — 9 automated checks including empty form 500 protection

## Recent Fixes (2026-06-09, Wave 3)

### Share Button HTTP Fallback
- `navigator.clipboard.writeText()` requires HTTPS — fails silently on HTTP (local dev, LAN)
- Added `fallbackCopy()` using textarea + `document.execCommand('copy')` as fallback
- Works on all browsers including local HTTP and LAN addresses
- Called from `.catch()` after modern clipboard API attempt

### Sidebar Horizontal Scrollbar Fix
- Long tooltip wrappers / form labels caused horizontal overflow in 300px sidebar
- Added `overflow-x: hidden` to `.sidebar` CSS rule
- Prevents layout shift and scrollbar noise

### Client-Side Validation (HTML5)
- Added `min="1" required` to Withdrawal Amount input (prevents 0 submission)
- Added `min="0.1"` to Withdrawal Percentage input (prevents 0% submission)
- `required` attribute triggers browser validation before form POST
- Server-side validation still enforced as defense-in-depth

### Regression Test Suite
- Created `scripts/regression.sh` (skill support file) with 9 automated checks:
  1. GET / returns 200
  2. Empty state has no Welcome heading
  3. POST with defaults returns 200 (no 500)
  4. Advanced collapse POST doesn't error on empty custom CAGR
  5. Withdrawal Amount = 0 shows validation error
  6. Starting point banner renders
  7. Default Fixed = "yes ($)", Taxes = 15 on GET
- Run after any local change: `bash tests/regression.sh` (copied to project) or `bash /home/wahid/.hermes/skills/devops/bitcoin-fits-site/scripts/regression.sh`
- All 9 tests pass as of 2026-06-09
- See `scripts/regression.sh` in this skill's directory

## Recent Fixes (2026-06-09, Wave 2)

### Tooltip Bottom-Positioning (No Clipping)
- Changed ALL tooltips from `bottom: calc(100% + 6px)` to `top: calc(100% + 6px); left: 0` — appears below trigger element, no clipping at top/left
- Removed `letter-spacing: 0.06em` from `.model-section-label` so "CAGR-based" and "Power Law–based" display normally
- Updated Your Age tooltip text to "Used to calculate calendar years"
- See `flask-web-app-patterns` skill → references/tooltip-css-pattern.md

### Server-Side Validation
- Added validation in POST handler: `withdrawal_usd > 0` for "yes ($)", `withdrawal_percentage > 0` for "yes (%)"
- On validation failure: re-renders with red `alert-danger` banner and preserved `form_data`
- Error message passed via `error` template variable
- See `flask-web-app-patterns` skill → references/flask-form-pattern.md

### Default Values Changed
- Fixed Withdrawal: default = "yes ($)" (was "no (Variable)")
- Taxes on Withdrawal: default = 15% (was 0%)
- Updated in both GET `form_data` defaults (app.py line ~203) and template fallback logic

### Empty State Cleanup
- Removed `<h3>Bitcoin FITS Calculator</h3>` from empty state entirely
- Empty state now: lead paragraph + Important Notes — no heading

### Starting Point Modal Updates
- Added Chart Inspect link alongside Checkonchain: `https://chartinspect.com/charts/true-market-mean` (with "requires sign-up" note)
- True Market Mean value in modal is now dynamically fetched (no longer hardcoded $64,934 in modal body)

### True Market Mean API Integration
- **New**: `get_true_market_mean()` fetches from BGeometrics API `https://api.bitcoin-data.com/v1/true-market-mean?size=1`
- **Cached at module load** (`BASE_PRICE_1_4 = get_true_market_mean()`) and refreshed per POST for display
- **1-hour TTL cache** — respects BGeometrics free tier limit (10 req/hr)
- **Graceful fallback** to hardcoded $64,934 if API fails
- **Current live value**: $78,579.17 (as of June 9, 2026) vs old hardcoded $64,934
- **Site no longer needs redeploy** when True Market Mean changes
- Requires `requests` Python package (added to imports)

## Recent Fixes (2026-06-09, Wave 1)

### Tooltip Wrapping & Positioning
- Added `max-width: 240px; white-space: normal; width: max-content; text-align: left; line-height: 1.4` to `.fits-tooltip-text`
- Long tooltips now wrap instead of going off-screen
- Added `title` attributes to model section labels and Your Age tooltip for native browser fallback

### Share Button Robustness
- Fixed `modelChecked` undefined bug: when Advanced mode is active, no tile is checked
- Added fallback: `params.set("model", modelChecked || "6")`
- Added safe empty-string fallbacks for all params: `val() || ""`

### Starting Point Banner + Modal
- New `starting_point` dict computed in backend with model-aware base price
- Banner shows: `Starting point: $X = Y BTC × $Z` with model-family-specific explanation
- "Learn more" link opens StartingPointModal with full bitcoincompounding.com explanation
- Modal covers: True Market Mean anchor, Power Law anchors, why CAGR, two model families

### FITS Acronym & Section Labels
- FITS now uses `.fits-acronym` with dashed orange underline (`border-bottom: 1px dashed var(--accent)`) — same font/color as surrounding text, no hover tooltip
- Removed `text-transform: uppercase` from `.model-section-label` so "CAGR-based" and "Power Law–based" display normally

### Important Notes Update
- Volatility note now mentions "CAGR (Compound Annual Growth Rate) **or Power Law**" and "modeled starting point value" instead of spot price

## Static Conversion (2026-07-02)

See `references/2026-07-02-static-conversion.md` for full details on the Flask → client-side JS conversion.

- Converted entire Flask app to pure static site in `dist/` directory
- All Python calculation logic ported to JS — CAGR tables, projections, Plotly chart data, TMM API
- jQuery `.val()` on `<select>` returns array-like object, not string — must wrap with `String()` (see pitfalls)
- Deploying to Cloudflare Pages (free) to replace Render (paid overages)
- Local test: `cd dist && python3 -m http.server 8099`