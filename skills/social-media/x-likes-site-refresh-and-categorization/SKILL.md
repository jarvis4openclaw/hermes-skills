---
name: x-likes-site-refresh-and-categorization
description: Refresh X likes data and safely update category filters/buttons for the X Likes static site
category: social-media
---

# X Likes Site: Refresh + Category Expansion

## When to use
- User asks to pull a fresh X likes copy
- User wants new filter categories/buttons added to the X Likes site
- You need to regenerate `/home/wahid/clawd/x-bookmarks/web/index.html`

## Environment
- Repo path: `/home/wahid/clawd/x-bookmarks/`
- Generator: `/home/wahid/clawd/x-bookmarks/web/generate_bird_html.py`
- Update script: `/home/wahid/clawd/scripts/xbookmarks-update-bird.sh`
- Output HTML: `/home/wahid/clawd/x-bookmarks/web/index.html`

## Workflow
1. Inspect current generator/filter logic:
   - Confirm `categorize()` and filter button/category generation in `generate_bird_html.py`.
2. Centralize category config before editing logic:
   - Add `CATEGORY_CONFIG` (id -> label/icon)
   - Add `CATEGORY_KEYWORDS` (id -> keyword list)
   - Add `CATEGORY_ORDER` (button/display order)
3. Keep required categories if requested:
   - Preserve `all`, `bitcoin`, `tech`
   - Add requested categories (e.g., `ai`, `health`) + optional extras.
4. Wire config into both Python and JS categorization:
   - Python `categorize(tweet)` must map to same IDs used in HTML.
   - In embedded JS `categorize(tweet)`, mirror the same category IDs to keep filtering consistent.
5. Regenerate data + page using the canonical script:
   - Run: `/home/wahid/clawd/scripts/xbookmarks-update-bird.sh`
6. Validate output:
   - Confirm `data-category="..."` buttons in `index.html`
   - Confirm matching `id="category-..."` sections exist
   - Run `python3 -m py_compile /home/wahid/clawd/x-bookmarks/web/generate_bird_html.py`

## Fast verification commands
- `search_files(pattern='data-category="', target='content', path='/home/wahid/clawd/x-bookmarks/web/index.html')`
- `search_files(pattern='category-', target='content', path='/home/wahid/clawd/x-bookmarks/web/index.html')`
- `terminal(command='python3 -m py_compile /home/wahid/clawd/x-bookmarks/web/generate_bird_html.py')`

## Pitfalls
- **`bird` is not on PATH in cron/non-interactive shells** — use `npx bird` instead of bare `bird`. The binary is installed globally via npx but not symlinked to PATH.
- **`brv` is not on PATH in cron shells** — use full path `/home/wahid/.brv-cli/bin/brv` and always append `2>/dev/null || true` so a missing brv never aborts the update.
- **Cron job target `./xbookmarks-update` must exist** — the canonical script lives at `/home/wahid/clawd/scripts/xbookmarks-update-bird.sh`; create a thin wrapper at `/home/wahid/clawd/x-bookmarks/xbookmarks-update` if cron points there.
- Keep category IDs stable across Python + JS + HTML (`all`, `bitcoin`, etc.).
- Do not manually edit generated `index.html` first; edit generator and regenerate.
- If odd placeholder-like text appears while reading file snippets, trust compile + regeneration + output checks over partial snippet artifacts.
- If search appears “dead” (typing does nothing), check `renderTweets(tweets)` first: it must render from the filtered `tweets` argument, not `allTweets`.
- In `filterTweets()`, use null-safe text access (`(tweet.text || '')`) and include author fields when useful (`tweet.author?.name`, `tweet.author?.username`) to avoid silent failures and improve matching.

## Server recovery (if site spins/unresponsive)
1. Check listener + process:
   - `ss -ltnp | grep 3456`
   - `pgrep -af "python3 server.py"`
2. Restart cleanly:
   - `cd /home/wahid/clawd/x-bookmarks/web`
   - `pkill -f "python3 server.py" || true`
   - `nohup python3 server.py >/tmp/xlikes-server.log 2>&1 &`
3. Verify with keepalive script (canonical health check):
   - `/home/wahid/clawd/scripts/xlikes-keepalive.sh`
4. Inspect logs if still bad:
   - `tail -n 80 /tmp/xlikes-server.log`

## Done criteria
- Fresh likes import succeeded
- New requested buttons visible in generated HTML
- Category sections render and filter IDs match button IDs
- Generator compiles successfully
- Server passes keepalive health check