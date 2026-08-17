---
name: update-lightning-wallets-site
description: Update the Lightning Wallets Comparison site (wallets.wahid.my) — edit tables, add columns, update wallet data, deploy.
category: devops
version: 1.1.0
metadata:
  hermes:
    tags: [lightning-wallets, cloudflare-pages, static-site, wallets, bitcoin, deploy]
    trigger_conditions:
      - "update lightning wallets site"
      - "add wallet to wallets.wahid.my"
      - "add a column to the wallet comparison"
      - "edit wallet data table"
      - "deploy lightning wallets site"
      - "change the donate button on wallets site"
      - "update wallets.json"
      - "wallet comparison new field"
      - "lightning wallet feature flag"
      - "Cloudflare Pages wallet site"
---

# Lightning Wallets Comparison Site

**Live URL:** https://wallets.wahid.my
**Local path:** `/home/wahid/clawd/lightning-wallets-comparison/`
**Repo:** `https://github.com/jarvis4openclaw/lightning-wallets-comparison` (branch: `main`)
**Hosting:** Cloudflare Pages (project: `lightning-wallets-site`, Git-connected, auto-deploys on push to `main`)
**Production branch:** `main` (was `master` — fixed on 2026-05-24)

## File Structure

| File | Purpose |
|------|---------|
| `index.html` | Page structure, header, tables, footer, donate modal |
| `app.js` | Column definitions, rendering, filtering, sorting, donate modal JS |
| `style.css` | Full dark theme, table styles, donate modal/FAB styles |
| `wallets.json` | Wallet data — 2 categories: `openSource[]` and `freemium[]` |
| `donate-qr.png` | BOLT 12 offer QR code (reusable) |

## When to Use
- User asks to edit the Lightning Wallets Comparison site (wallets.wahid.my): add/remove a wallet, change wallet data, add a comparison column, or tweak the donate flow.
- The task touches `wallets.json`, `app.js` column definitions, or the site's `index.html` table structure.
- Any deploy of this specific Cloudflare Pages project (`lightning-wallets-site`).

## Not For
- Deploying a *different* static site on Cloudflare Pages → use `cloudflare-pages-static-site` instead.
- Editing the Bitcoin FITS Calculator (a separate project) → use `bitcoin-fits-site` instead.
- General Cloudflare DNS/zone management → use `caddy-proxy-management` or direct Cloudflare API work.
- Building a new wallet-comparison feature from scratch → treat this skill as the deploy/update playbook only.

## Edit + Deploy Workflow

1. Edit files in `/home/wahid/clawd/lightning-wallets-comparison/`
2. `git add -A && git commit -m "message" && git push origin main`
3. Cloudflare Pages auto-deploys (~30s)
4. Verify with: `curl -s https://<hash>.lightning-wallets-site.pages.dev | grep <expected>`
5. Custom domain `wallets.wahid.my` may have CDN cache lag (~15min). Use hash URL for immediate verification.

## Wallet Data Schema

Each wallet entry in `wallets.json`:
```json
{
  "name": "Bankify",
  "link": "https://website",
  "repo": "https://github.com/user/repo",
  "fees": "Free",
  "selfHostable": true,
  "nonCustodial": "No",
  "lnAddress": false,
  "liquid": false,
  "autoWithdraw": false,
  "nwc": false,
  "ecash": false,
  "customMint": false,
  "multipleMints": false
}
```

- `nonCustodial`: "Yes" | "No" | "Both" | "Optional"
- `lnAddress`: `bool` or string (e.g. "10 (limited)", "∞")
- All other boolean values: `true` | `false`

## Adding a New Column

Three places to touch:

### 1. `wallets.json` — Add field to every wallet
Use a Python script to add the field before `autoWithdraw`:

```python
import json
with open('wallets.json') as f:
    data = json.load(f)
for cat in ['openSource', 'freemium']:
    for w in data[cat]:
        w['newcolumn'] = False  # default
# Insert at specific position
items = list(w.items())
keys = [k for k, v in items]
insert_at = keys.index('autoWithdraw')
new_items = items[:insert_at] + [('newcolumn', w['newcolumn'])] + items[insert_at:]
```

### 2. `app.js` — Add column definition
In the `columns` array, add before autoWithdraw:
```js
{ key: 'newcolumn', label: 'Label', type: 'bool' },
```

### 3. `app.js` — Add filter (optional, for booleans)
- Add `newcolumn: null` to `state.filters` object
- Add to `renderFilters()` filter list
- Add to `handleFilter()` toggle condition: `|| key === 'newcolumn'`

### 4. `index.html` — Update colspan
Increment colspan in both no-results rows (currently `colspan="12"`).

## Donate Setup

- **BOLT 12 offer:** `lno1pg8hgmeqwpshjsrhv95xjepwd4u3vggzz220lavkujt662gze403jee7jqsf20vsvfwk3s3wjx6353wqxtfs` (reusable, no expiry)
- **Lightning Address:** `pay@wahid.my`
- **QR image:** `donate-qr.png` (generated with Python qrcode, white on dark `#121216` bg)

### Donate Button: Portable Pattern

The donate FAB + modal (CSS classes, HTML structure, JS logic) is a self-contained pattern that can be dropped into any web project. Replicated to Bitcoin FITS Calculator on 2026-06-08. See the `bitcoin-fits-site` skill for that project's full details.

1. **CSS** — Append the `.donate-fab`, `.donate-modal-*`, `.donate-copy-btn`, `@keyframes donatePulse`, and responsive block. Match the project's existing color scheme (orange `#ff8000` for Bitcoin FITS, `#f7931a` for LWC).
2. **HTML** — Drop the `<button id="donate-btn">` and `<div id="donate-modal">` blocks BEFORE the `<script>` tag (script must load after DOM elements exist).
3. **JS** — Append the `initDonateModal()` IIFE. Uses vanilla JS (no jQuery dependency needed).
4. **Asset** — Copy `donate-qr.png` into the project's static directory.
5. **Verify** — `curl -s http://localhost:<port>/ | grep -c "donate-btn"` should return 1.

## Pitfalls

1. **Production branch is `main` not `master`** — verified in Cloudflare Pages settings. Pushing to `master` will NOT deploy. Confirm the branch before pushing.
2. **CDN cache on custom domain can serve stale HTML** — the hash URL (`<hash>.lightning-wallets-site.pages.dev`) is always fresh. Verify with the hash URL, then wait ~15 min for the custom domain, or hard-refresh.
3. **URL encoding in JS** — use `encodeURIComponent()` for dynamic URLs; raw user input breaks links.
4. **colspan must match total column count** — currently 12. Adding a column without bumping colspan breaks table rendering.
5. **`wallets.json` is served client-side** — keep it compact and valid JSON. One trailing comma breaks the whole site.
6. **Don't forget to update the `state.filters` object** when adding filterable columns — filters silently no-op for unregistered keys.
7. **The `columns` array, filters, and colspan are three separate places** — a new column touches all three; missing one produces a partial render that looks fine in dev.
8. **Donate QR is BOLT 12 and reusable** — don't regenerate it; copy `donate-qr.png` and reuse the offer string.
9. **Git push succeeds but site doesn't change** — check Cloudflare Pages deployment status; a failed build (invalid JSON) silently keeps the old deployment.
10. **Auto-deploy only triggers on `main`** — commits to feature branches deploy to preview URLs only; don't rely on them for production checks.
