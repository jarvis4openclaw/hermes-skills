---
name: update-lightning-wallets-site
description: Update the Lightning Wallets Comparison site (wallets.wahid.my) — edit tables, add columns, update wallet data, deploy.
category: devops
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

## Pitfalls

- Production branch is `main` not `master` — verified in Cloudflare Pages settings
- CDN cache on custom domain can serve stale HTML. Hash URL (`<hash>.lightning-wallets-site.pages.dev`) is always fresh.
- URL encoding in JS: use `encodeURIComponent()` for dynamic URLs
- colspan must match total column count (currently 12)
- `wallets.json` is served client-side — keep it compact
- Don't forget to update the `state.filters` object when adding filterable columns
