# Self-hosting fonts under strict CSP

## Why

CSP with no `font-src` falls back to `default-src` (usually `'self'`), so a Google Fonts `<link>` AND the woff2 files both get blocked on deploy. Local-file previews and pre-deploy screenshots show no CSP and will look correct while the deployed page silently falls back to Georgia/system-ui/monospace — the typography that defines the look is gone.

## Fetch the right woff2 URLs

Hit the CSS2 API with a **browser User-Agent** (else it returns TTF), keeping `display=swap`:

```bash
curl -s -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" \
  "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500&display=swap"
```

The response has one `@font-face` block per subset (latin, latin-ext, vietnamese, cyrillic, …). Extract each `src: url(...)` woff2, download into the site's `assets/fonts/`, and rewrite the URLs to relative paths. Drop only the far subsets (vietnamese/cyrillic) if saving bytes.

## The subset trap (brand glyphs)

Per-glyph coverage differs per subset, and the FIRST block (latin) is not enough. Example: `₿` (U+20BF) is covered only by the latin-ext range (`U+20AD-20C0`), not latin. Self-hosting just the latin block makes ₿ silently fall back to the system font while every Latin letter renders correctly — easy to miss.

**Rule:** keep BOTH latin and latin-ext `@font-face` blocks per weight, and include a brand-glyph render check in the post-build screenshot.

## Variable fonts

Variable families (e.g. Fraunces with the `opsz` axis) return one woff2 whose URL encodes the requested axis ranges. Preserve the URL exactly as the API emitted it — hand-retyping a simpler URL drops the axes and weight/optical sizing renders off.

## Verification

1. Build, then serve from the REAL server (CSP active).
2. Screenshot and confirm (a) the family actually applied, (b) brand glyphs render in-family — not just Latin letters.
3. `curl -sI` the font URL and confirm HTTP 200 from `'self'` (no CDN redirect).
