---
name: blocked-page-recovery
description: "Recover blocked/paywalled/WAF'd pages via fallbacks."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Archives, Wayback, Paywall, WAF, Fallback]
    related_skills: [grounded-citations]
    trigger_conditions:
      - "page blocked by cloudflare"
      - "paywall bypass"
      - "403 forbidden article"
      - "429 rate limited page"
      - "wayback machine snapshot"
      - "archive.today recovery"
      - "recover deleted webpage"
      - "jina reader fallback"
      - "web cache google dead"
      - "get article behind waf"
      - "bot detection page"
      - "fetch blocked url"
      - "just a moment cloudflare"
---

# Blocked-Page Recovery

When a page won't fetch — 403/429, Cloudflare "Just a moment...", a paywall,
or a bot-detection interstitial — don't give up and don't loop on the same
URL. Third-party services often hold a **copy** of the page. Work down this
ladder, cheapest first.

## When to Use

- A page returns 403/429, Cloudflare "Just a moment...", or a bot-detection interstitial.
- A paywalled article needs a recoverable copy (archive services often have it).
- The user needs a deleted page's historical content (Wayback/CDX).
- `web_extract` fails but a third-party copy may exist.
- You need provenance (snapshot date) preserved when citing recovered content.

## Not For

- Normal web extraction of accessible pages → use `web_extract` directly.
- Live breaking-news/pricing data where a snapshot is not an answer → say the snapshot is context, not current truth.
- Bypassing login walls / authenticated paywalls (subscription-gated content) → that is unauthorized access; archives only cover publicly reachable copies.
- Sending credentials or cookies through generic proxy relays → never; see "Proxy relays: don't".

## The ladder

```
1. Wayback Machine  — archive.org "available" API  (snapshot + timestamp)
2. archive.today    — domain rotation: archive.ph → .md → .li → .is
3. Jina Reader      — only if JINA_API_KEY is set  (live server-side render)
4. API-first pivot  — look for /api/, /graphql, .json, or RSS on the same host
5. Real browser     — browser tool as the last, most expensive resort
```

Run it in one shot with the bundled script:

```bash
python3 scripts/recover_page.py "https://example.com/blocked-article" --json
```

The script tries each route in order, validates every body (see "Fake
successes" below), and prints the first genuine hit with its provenance.

## Provenance discipline (non-negotiable)

Every recovered copy carries a provenance you MUST preserve when citing:

| Route | Provenance | How to cite |
|-------|-----------|-------------|
| Wayback / archive.today | `snapshot` | Cite WITH the snapshot date: "as archived 2026-08-06". Never present a snapshot as the live page — it may be stale. |
| Jina Reader | `live` | Server-side re-render of the live page; cite normally. |
| Live fetch / browser | `live` | Cite normally. |

If the user needs *current* data (prices, availability, breaking news), a
snapshot is context, not an answer — say so explicitly and note its age.

## Manual routes

### 1. Wayback Machine (best provenance, try first)

```bash
# Discovery: returns closest snapshot URL + timestamp as JSON
curl -sL "https://archive.org/wayback/available?url={URL}"
# Then fetch archived_snapshots.closest.url
```

For enumerating many snapshots (or recovering deleted pages), the CDX index:

```bash
curl -sL "https://web.archive.org/cdx/search/cdx?url={URL}&output=json&limit=10"
```

CDX intermittently returns 503 under load — if it does, fall back to the
`available` API; don't retry-hammer it.

Works for: any publicly crawled URL. Fails for: robots-blocked sites,
never-crawled URLs, JS-only SPAs (snapshots don't render).

### 2. archive.today (paywalls, deleted content)

User-submitted archives — often has paywalled news articles Wayback lacks.
Rate-limits aggressively (429) and rotates domains, so iterate:

```bash
for d in archive.ph archive.md archive.li archive.is; do
  curl -sL --max-time 20 "https://$d/newest/{URL}" -o /tmp/page.html \
    -w "%{http_code}" && break
done
```

**Validate the body, not the status code** — a 429 still ships several KB of
rate-limit HTML that looks like a success to a size check alone.

### 3. Jina Reader (requires JINA_API_KEY)

`r.jina.ai` re-renders the live page in a real browser server-side and
returns markdown. Anonymous access is dead (401 → Turnstile); a key is
required:

```bash
curl -s -H "Authorization: Bearer $JINA_API_KEY" "https://r.jina.ai/{URL}"
```

Handles JS SPAs that archives can't. Skip this route entirely when the env
var is unset.

### 4. API-first pivot

WAFs protect the HTML surface far more aggressively than the data endpoints
behind it. After 2-3 blocked attempts on a site, stop fighting the HTML and
look for:

- `/api/...`, `/graphql`, or `.json` variants of the page URL
- An RSS/Atom feed (`/feed`, `/rss`, `<link rel="alternate">` in any copy
  you did recover)
- A sitemap (`/sitemap.xml`) revealing canonical URLs that may not be gated

## Fake successes — routes that LIE

These return HTTP 200 with a plausible body that is NOT the page. The script
rejects them automatically; reject them manually too:

- **Google Cache is dead** (since mid-2024). `webcache.googleusercontent.com`
  returns 200 + tens of KB, but it's a Google Search interstitial with a JS
  redirect, not a cache. Never use it.
- **AMP caches** (`*.cdn.ampproject.org`) mostly return a ~300-byte
  `<title>Redirecting</title>` meta-refresh stub pointing back at the
  original (blocked) URL. Treating that as success creates a fetch loop.
- **Rate-limit bodies**: archive.today 429 pages are multi-KB HTML. Check for
  the target's actual content (title words, expected strings), not just size.

Detection heuristics the script applies: body under a per-route byte floor;
meta-refresh/JS-redirect stubs whose target is the original host; interstitial
titles ("Just a moment", "Redirecting", "Google Search", "Attention Required").

## Proxy relays: don't

Generic "web proxy" relays are man-in-the-middle by construction. Never send
cookies or Authorization headers through one, and don't use them for anything
the user will rely on — provenance is unverifiable. Prefer archives, which at
least timestamp their copies.

## Pitfalls

1. **Never trust a 200 status alone** — Rate-limit pages (archive.today 429), Google Cache interstitials, and AMP redirect stubs all return 200 with multi-KB bodies. Validate the body for the target's actual content, not just size.

2. **Google Cache is dead (since mid-2024)** — `webcache.googleusercontent.com` returns 200 + tens of KB but it's a Search interstitial with a JS redirect. Never use it as a cache.

3. **AMP caches are redirect loops** — `*.cdn.ampproject.org` mostly returns a ~300-byte `<title>Redirecting</title>` meta-refresh stub pointing back at the blocked original. Treating that as success creates a fetch loop.

4. **CDX intermittently 503s under load** — If the CDX index errors, fall back to the `available` API. Don't retry-hammer the CDX endpoint.

5. **archive.today rate-limits aggressively and rotates domains** — Iterate `archive.ph` → `.md` → `.li` → `.is` with `--max-time`, and break on the first HTTP success. A 429 body still ships several KB of rate-limit HTML.

6. **A snapshot is context, not an answer** — For current data (prices, availability, breaking news), an archived copy may be stale. State its age and say it's a snapshot, not live truth.

7. **Preserve provenance when citing** — Cite Wayback/archive.today copies WITH the snapshot date ("as archived 2026-08-06"). Never present a snapshot as the live page.

8. **Jina Reader requires a key now** — Anonymous `r.jina.ai` access is dead (401 → Turnstile). If `JINA_API_KEY` is unset, skip the route entirely rather than failing repeatedly.

9. **Never send cookies/auth headers through proxy relays** — They are MITM by construction. Archives are the only acceptable fallback for sensitive or user-reliant content.

10. **After 2-3 blocked attempts, pivot to the API** — WAFs protect the HTML surface far more aggressively than `/api/`, `/graphql`, `.json`, RSS, or sitemaps on the same host. Stop fighting the HTML.
