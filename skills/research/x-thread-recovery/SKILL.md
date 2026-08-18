---
name: x-thread-recovery
description: Recover full X thread text when login-walled or root-only.
version: 1.1.0
metadata:
  hermes:
    tags: [x, twitter, threads, extraction, recovery, playwright, wayback, xurl, repurposing]
    trigger_conditions:
      - "extract full thread from X"
      - "recover thread content"
      - "build e-book from X threads"
      - "thread of threads"
      - "login wall on X thread"
      - "root only / can't see replies"
      - "x.com only shows the root tweet"
      - "scrape an X thread for an ebook"
      - "thread extraction returned a stub"
      - "capture polluted with the wrong profile page"
      - "Wayback snapshot of an X status"
      - "reconstruct a self-reply chain from the timeline API"
      - "EstateRanger style thread batch"
---

# X Thread Recovery

Recover the complete text of X/Twitter self-reply threads when the visible page is login-walled, renders only the root post, or returns the wrong page entirely. Validated on a 34-thread recovery job (EstateRanger) for e-book repurposing.

## When to use
- User wants full thread text for an e-book / guide / archive and X blocks unauthenticated reads.
- A "thread of threads" index post lists many roots that each need extraction.
- An earlier extraction missed content (stubs, polluted pages) and you need the real chains.
- A batch job (e.g. EstateRanger, X-likes refactor) needs consistent CHAIN/STUB/POLLUTED/MISSING classification.

## Not For
- **Downloading a single tweet's metadata or media** (no chain needed) → use `fxtwitter` API or the `xurl` skill directly, not this ladder.
- **Full user timeline analytics** (following, engagement stats) → use the `xurl` skill and its v2 API endpoints.
- **Monitored cross-posting between platforms** → use `nostrx`, not thread recovery.
- **Extracting a thread that is fully visible and not login-walled** → plain `web_extract` on the status URL is enough; skip the ladder.
- **Video/audio content inside a thread** → use `social-video-transcription` / `social-media-transcription` instead.

## Tool ladder (validated, in order)
1. **web_extract on the x.com URL** — free, no setup, works for many threads (X renders server-side text for guests). Returns the full chain for some threads, root-only for others. Batch it and classify results.
2. **Playwright headless Chromium** — the reliable general path; renders the guest conversation fully for most threads:
   - Setup: `python3 -m venv venv && ./venv/bin/pip install playwright && ./venv/bin/python -m playwright install chromium`
   - Launch: `chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"])`
   - Navigate to the status URL, wait ~4s, scroll ~12×1500px steps with ~1s pauses to trigger lazy rendering.
   - Grab `document.body.innerText`. The `article[data-testid="tweet"]` selector often returns 0 on the JS shell, but innerText still contains the whole chain — don't gate on the article count.
3. **fxtwitter API** — `api.fxtwitter.com/{user}/status/{id}` — single tweet + account metadata ONLY (no chain). Use to confirm root text, account joined/verified/description, reply counts.
4. **X API v2 via xurl** — reconstruct threads from the user timeline:
   - Get user id: `xurl user @handle` → `data.id`.
   - Pull timeline paginated: `/2/users/{id}/tweets?max_results=100&tweet.fields=created_at,conversation_id,referenced_tweets&exclude=retweets`, advance with `pagination_token`.
   - Rebuild each thread: all tweets sharing `conversation_id`, where a reply's `referenced_tweets` (type `replied_to`) parent is itself in that conversation (self-reply chain). Exclude replies whose parent is outside the conversation.
   - **Field gotcha**: `in_reply_to_id` is NOT a valid `tweet.fields` value (API rejects it) — use `referenced_tweets` + `conversation_id`.
   - **Window limit**: the v2 user timeline caps around the ~3,200 most recent tweets (~3 months for a busy account). Pre-2022 threads are NOT reachable this way.
5. **Wayback Machine** — `web.archive.org/cdx/search/cdx?url={twitter.com|x.com}/user/status/{id}&output=json&limit=20&filter=statuscode:200`. Flaky (503s) — retry ×3 per host, query BOTH hosts, sleep between calls. Pre-X-redesign snapshots (2021–2022) can contain full server-side thread HTML. Some threads have NO snapshots at all — don't keep hammering.
6. **Authenticated fallback (bird with cookies)** — for threads with no mirrors and outside the API window, only `bird` (auth_token/ct0 env) or manual paste works. State this plainly and ask the user; never fabricate missing content.

## Dead ends (do not burn time)
- **Nitter instances**: most are dead, 403, or an Anubis bot-challenge page. Probe one quickly, then move on.
- **ThreadReaderApp**: pages are boilerplate-only (thread content loads client-side) — web_extract returns no thread text.
- **Raw curl of x.com**: returns a JS shell with no `__INITIAL_STATE__`/`full_text` payload — useless unauthenticated.
- **v2 search with `conversation_id:`**: returns 0 results; xurl has no replies subcommand, so search cannot reconstruct chains.

## Pitfalls
1. **The pollution pitfall (expensive — verify every capture)** — For some threads, x.com serves the user's PROFILE page (with their pinned "thread of threads" / index) instead of the requested conversation. The extraction looks successful but is the wrong content entirely. Detection: count distinct `/user/status/{id}` IDs in a capture — if it includes the master/pinned thread root plus many other thread roots, it is polluted. In the reference job, 5 of 34 captures were silently polluted this way and looked like 30+ post "threads" that were actually the index rail. Classify EVERY capture as CHAIN / STUB (root only) / POLLUTED / MISSING, then re-route STUB + POLLUTED through the ladder. Never trust a raw char count or post count as proof of correctness.
2. **Root-vs-reply parse trap** — Root tweets carry the timestamp AFTER the body; reply tweets carry the date BEFORE the body. A naive splitter mislabels root bodies as dates. Split replies on the header pattern (`<Author>\n@handle\n<date>\n<body>`), and handle the root post specially.
3. **Nitter is a time sink** — most instances are dead, 403, or an Anubis bot-challenge page. Probe one quickly, then move on. Do not burn multiple attempts.
4. **ThreadReaderApp returns boilerplate only** — thread content loads client-side; `web_extract` returns no thread text. Skip it.
5. **Raw curl of x.com is useless unauthenticated** — returns a JS shell with no `__INITIAL_STATE__`/`full_text` payload. Don't bother.
6. **v2 search with `conversation_id:` returns 0 results** — xurl has no replies subcommand, so search cannot reconstruct chains. Use the timeline rebuild path instead.
7. **`in_reply_to_id` is NOT a valid `tweet.fields` value** — the API rejects it. Use `referenced_tweets` + `conversation_id` (see ladder step 4).
8. **v2 timeline window caps at ~3,200 tweets** — roughly 3 months for a busy account. Pre-2022 threads are NOT reachable this way; route them to Wayback or ask for bird cookies.
9. **Wayback 503s and empty CDX results are normal** — retry ×3 per host, query BOTH `twitter.com` and `x.com`, sleep between calls. Some threads have NO snapshots at all — don't keep hammering; move to the authenticated fallback.
10. **Never fabricate missing content** — when a thread has no mirrors and is outside the API window, only `bird` (auth_token/ct0 env) or manual paste works. State this plainly and ask the user. Do NOT invent posts to fill the gap.
11. **Playwright article-count gating is a false negative** — `article[data-testid="tweet"]` often returns 0 on the JS shell, but `document.body.innerText` still contains the whole chain. Do not gate success on the article count.
12. **Engagement-metric noise lines** — pure-number lines (like/retweet/view counts) pollute post bodies. Strip them before assembling e-book content.

## Workflow for a thread-of-threads job
1. web_extract the index URL → enumerate all root tweet IDs + titles.
2. Batch web_extract each root; classify captures (CHAIN/STUB/POLLUTED/MISSING).
3. Playwright-batch the STUBs; then Wayback CDX the remaining missing.
4. For anything still missing, check the v2 timeline window; if the thread predates it, request bird cookies or manual paste.
5. Strip engagement-metric noise lines (pure numbers / like-retweet-view counts) from post bodies.

## Support files
- `references/x-estateranger-recovery.md` — the 34-thread EstateRanger job: per-thread route results, script shapes, timeline stats, recovery counts.
