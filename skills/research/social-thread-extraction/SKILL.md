---
name: social-thread-extraction
description: "Extract numbered/counted X/Twitter threads (self-reply chains) via cross-platform mirrors when X blocks unauthenticated access. Use when collecting prompt lists, tip threads, or numbered guides from X posts for Pepper's idea pipeline."
version: 1.1.0
metadata:
  hermes:
    tags: [x, twitter, threads, extraction, mirrors, research, social-media]
    trigger_conditions:
      - "extract thread from X"
      - "get all the prompts from this post"
      - "copy this thread"
      - "save this X thread"
      - "collect prompts from"
      - "unroll this twitter thread"
      - "pull the replies from this tweet"
      - "I can't read the replies on X"
      - "grab the whole thread"
      - "find a mirror of this tweet"
      - "number the items in this post"
      - "archive this thread"
      - "get the full list from this X post"
---

# Social Thread Extraction

Extract numbered/counted X/Twitter threads (self-reply chains) via cross-platform mirrors when X blocks unauthenticated access.

## When to Use

- A root X/Twitter post promises "N items/things/prompts" and the reply chain is behind a login wall
- You have a tweet URL and need the full numbered thread as text for downstream processing
- You are collecting prompt lists, tips, or numbered guides for the idea pipeline
- `web_extract` on the tweet URL returned only the root post and you need the rest
- You have `bird` and user-supplied cookies and want the authoritative, complete extraction
- You need to reconcile an extraction against the author's promised item count before presenting it
- A user asks "did I get all of them?" about a scraped thread
- You need to decide up front whether mirror-hunting is even worth trying for a given thread

## Not For

- **Extracting the *video* content of a post (transcript/captions)** → use `social-video-transcription` instead
- **Downloading the media file itself** → use `social-video-download` instead
- **Storing the extracted ideas into Notion** → use `notion-idea-entry` instead
- **General web/网页 research where X is not the source** → use `duckduckgo-search` or `exa-web-search-free` instead
- **X API v2 work using app-level auth only (`xurl` read/search)** → use the `xurl` reference directly; `xurl` cannot fetch reply chains
- **Triage of an email inbox** → use `email-inbox-triage` instead
- **Building a dashboard or site from the collected content** → use `frontend-taste`/`static-site-integration` instead

## The Problem

X/Twitter thread authors post numbered lists (e.g., "Here are 18 prompts to dominate YouTube:") as self-reply chains. The root post is visible to unauthenticated readers, but the reply chain is behind a login wall.

## Mirror Discovery Strategy

1. **Extract the root post** via `web_extract` on the X URL — this almost always works even without auth, and gives you the exact phrasing + promised item count (e.g., "18 prompts") + author handle for searching.

2. **Search for unique phrases** from the root post across other platforms:
   ```
   web_search '"BREAKING: Claude can now build your YouTube channel" "18 prompts"'
   web_search 'site:facebook.com "18 prompts to dominate YouTube"'
   web_search 'site:threads.net "Claude" "YouTube" "prompts" "monetized"'
   ```

3. **Extract mirror pages** with `web_extract`. Productivity ranking:
   - **Facebook** (highest): repost pages post the thread as the main post, then post each numbered item as a self-comment. Comments are visible without login and extract well via web_extract.
   - **Threads**: shows the main post but hides replies behind login — less useful than Facebook for getting the full thread.
   - **ThreadReaderApp**: `threadreaderapp.com/thread/TWEET_ID` — works when the thread has been unrolled, but often 404s for recent threads.
   - **Reddit / Medium / blog reposts**: sometimes contain the full list.

4. **Parse the extracted content**: Facebook comment threads come through `web_extract` as text with numbered items separated by comment metadata (timestamps, reaction counts, inline SVG reactions). Parse for the pattern `N. The Name` followed by the prompt text.

5. **Reconcile counts**: the root post promised N items. If the mirror only has M < N, **flag the gap** explicitly to the user and state how many items are missing. Do NOT silently present a partial extraction as complete.

## Two thread types — know which one you're dealing with

Before attempting extraction, determine the thread type:

1. **Self-reply thread**: the author posts numbered items as self-replies (e.g., "Here are 18 prompts..." → 18 self-reply tweets). Mirror strategy works well — reposters on Facebook/Threads/ThreadReaderApp often unroll the full chain.

2. **Community reply thread**: the author posts one root tweet asking followers to contribute ideas in replies (e.g., "Drop your best Christmas gift ideas below!"). The valuable content is in hundreds of replies from DIFFERENT users. Mirrors almost NEVER exist for these — no one reposts 366 random users' replies. The only reliable extraction path is authenticated API access (bird CLI with cookies). If bird is not available and no mirror exists, tell the user you cannot extract community replies without auth — do not burn time searching for mirrors that won't exist.

## Bird CLI — the authenticated fallback

When the user provides X cookies, `bird` can fetch the full thread:
```bash
export AUTH_TOKEN=<user_provided>
export CT0=<user_provided>
bird read TWEET_ID --plain           # root post
bird replies TWEET_ID --all --plain  # full reply chain
bird replies TWEET_ID --json         # structured output for parsing
```

The user gets `auth_token` and `ct0` from browser DevTools → Application/Storage → Cookies → x.com. Never ask the user to paste these in chat — have them set them as env vars in their shell.

## xurl — what it CAN and CANNOT do

`xurl` is an X API v2 CLI. It is useful for reading individual posts and searching, but it **does NOT have a `replies` subcommand** — there is no way to fetch a conversation's reply chain with xurl. Its relevant subcommands:
- `xurl read TWEET_ID` — fetch a single post with metrics (works with app-level auth)
- `xurl search "QUERY" -n 100` — keyword search (does NOT support `to:username` for reply discovery; the X v2 search API returns 0 results for this pattern)
- `xurl posts USERNAME` — list a user's recent posts

If `bird` is absent and the thread is a community reply thread, xurl will NOT save you. Fall back to asking the user for cookies (bird) or manual copy-paste.

## Verify tool availability before following a skill's workflow

Always check if the CLI tool a skill depends on is actually installed before committing to its workflow. Run `which bird` / `which xurl` immediately. If bird is absent, check whether the thread is self-reply (mirrors may work) or community reply (mirrors won't — only bird with auth or manual extraction will). Skip directly to the appropriate strategy instead of trying alternative frontends or browser workarounds.

## Pitfalls

1. **Mirror count mismatch** — reposters add/remove items or stop partway through, sometimes deliberately to drive traffic to their own PDF/product. Cross-reference the original promised count before presenting anything as complete.
2. **Facebook SVG noise** — extracted content contains inline SVG reactions as long base64 strings. Filter them out during parsing or they pollute every numbered item.
3. **ThreadReaderApp lag** — recent threads (last few days) often aren't unrolled yet; it 404s. Don't rely on it for fresh posts, and don't retry it more than once.
4. **Claiming completeness without auth** — without bird cookies you can verify the root post but cannot guarantee every reply. Say so explicitly rather than presenting a mirror scrape as the whole thread.
5. **Assuming `xurl` can fetch replies** — it has no `replies` subcommand. `search` also returns 0 results for `to:username` reply discovery. Even with auth, `xurl` cannot reconstruct a reply chain.
6. **Community reply threads have no mirrors** — when the root post asks followers to contribute (not a self-reply chain), nobody reposts hundreds of strangers' replies. Detect the thread type first and skip mirror-hunting entirely for these.
7. **Viral template reuse** — common templates are reposted by many accounts with different counts (6, 7, 8, 10, 18). Match the EXACT count from the user's source URL, never from a repost you happened to find.
8. **Using the login-walled X frontend or scraping it** — unauthenticated `X.com/i/status` views and third-party frontends are unreliable and often return only the root. Go straight to mirrors (self-reply) or bird (community).
9. **Asking the user to paste cookies into chat** — cookies are credentials. Have them export `AUTH_TOKEN`/`CT0` in their own shell; never request or echo the values.
10. **Silently truncating a partial result** — if the mirror yielded M of N items, state the gap and which items are missing. A partial list presented as complete is worse than a clear failure.
11. **Not writing the extraction down** — a successful full-thread extraction is worth persisting (numbered list + source URL + author + item count) so it isn't re-scraped next session. Record the count you verified.
12. **Ordering drift across mirror pages** — Facebook self-comments sometimes render out of order. Sort by the explicit `N.` prefix, and flag any duplicate or missing index instead of trusting page order.

## Related skills

- `notion-idea-entry` — store extracted ideas in Notion under the Pepper bucket
- `social-video-transcription` — extract content from video posts (X/YouTube)
- `xurl` — X API CLI (useful for `read` and `search`, but does NOT have a `replies` subcommand — cannot fetch reply chains)

## Reference files

- `references/x-thread-mirror-extraction.md` — session-specific extraction details for the @premtechAI "18 prompts" thread (post 2074009701994639672)