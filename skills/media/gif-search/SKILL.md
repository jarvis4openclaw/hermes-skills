---
name: gif-search
description: "Search/download GIFs from Tenor via curl + jq."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [TENOR_API_KEY]
  commands: [curl, jq]
metadata:
  hermes:
    tags: [GIF, Media, Search, Tenor, API]
    trigger_conditions:
      - "search for a gif"
      - "find a reaction gif"
      - "download a gif"
      - "send a gif"
      - "tenor gif"
      - "gif search"
      - "search tenor"
      - "get me a gif"
      - "look up gif"
      - "animated gif"
      - "gif of"
      - "reaction gif"
      - "find gif"
---

# GIF Search (Tenor API)

Search and download GIFs directly via the Tenor API using curl. No extra tools needed.

## When to Use

- Searching for reaction GIFs to spice up conversation
- Finding a specific GIF by keyword (celebration, thumbs up, etc.)
- Downloading a GIF file for local use or sharing
- Getting GIF metadata (title, dimensions, format variants)
- Embedding GIF URLs in markdown content or chat messages
- Sending lightweight `tinygif` previews in bandwidth-constrained channels
- Batch-search-and-pick workflows where you want multiple options

## Not For

- **MP4/video clips** → use `youtube-content` or `gif-search` (Tenor returns MP4s too but for dedicated video search, use other tools)
- **Creating/GIF generation** → use `stable-diffusion-image-generation` or `comfyui` instead
- **Local GIF library management** → use filesystem tools, not API search
- **Animated stickers** → Tenor sticker API is a separate endpoint; not covered here
- **Copyright-sensitive contexts** → Tenor returns user-uploaded content; verify licensing before commercial use
- **GIF editing/manipulation** → use image processing tools, not this skill

## Pitfalls

1. **TENOR_API_KEY not set in environment** — curl returns HTTP 401 with empty results. Fix: set `TENOR_API_KEY=your_key` in `${HERMES_HOME:-~/.hermes}/.env`. Verify with `curl -s "https://tenor.googleapis.com/v2/search?q=test&limit=1&key=$TENOR_API_KEY"`.

2. **API key in wrong format (Google Cloud Console vs. Tenor direct)** — Google Cloud Tenor keys work but require billing-enabled project (free tier exists). Direct Tenor v2 keys are simpler. If `curl` returns HTTP 403, check key source at https://developers.google.com/tenor/guides/quickstart.

3. **jq parsing fails on empty results** — `jq -r '.results[0].media_formats.gif.url'` returns `null` when no results match. Fix: always check result count first: `jq '.results | length'`.

4. **Spaces not URL-encoded in query** — `curl "https://tenor.googleapis.com/v2/search?q=thumbs up&..."` breaks because spaces aren't valid in URLs. Fix: replace spaces with `+`: `q=thumbs+up`. For special chars, use `printf` percent-encoding.

5. **GIF download URL returns redirect** — `curl -sL` handles 3xx redirects; plain `curl` without `-L` downloads an empty file. Always use `-L` flag when downloading.

6. **Rate limiting (10 requests/second free tier)** — Tenor free tier has per-second caps. Bulk downloads hit this fast. Fix: add `sleep 0.2` between requests in loops. For production, use Google Cloud billing for higher quotas.

7. **tinygif vs. gif tradeoff in messaging** — `tinygif` URLs are ~90% smaller but lower resolution. For messaging platforms with file size limits (Telegram 50MB, Discord 8MB), use `tinygif`. For full-quality sharing, use `gif` format.

8. **Content filter too restrictive** — Default `contentfilter` varies; `off` returns unfiltered content while `high` may exclude common reactions. If getting zero results for innocuous queries, try `contentfilter=off`.

9. **API key exposed in command history** — Curl commands with `&key=$TENOR_API_KEY` log the resolved key in shell history. Fix: use `--header` approach or read key from env inside a script rather than on the CLI.

10. **GIF URLs expire or go stale** — Tenor GIF URLs are stable for months but not permanent. For long-lived references, download and host locally.

11. **locale mismatch returns region-specific content** — Searching `q=football` with `locale=en_US` returns American football; with `locale=en_GB` returns soccer. Specify locale explicitly when region matters.

## Setup

Set your Tenor API key in your environment (add to `${HERMES_HOME:-~/.hermes}/.env`):

```bash
TENOR_API_KEY=your_key_here
```

Get a free API key at https://developers.google.com/tenor/guides/quickstart — the Google Cloud Console Tenor API key is free and has generous rate limits.

## Prerequisites

- `curl` and `jq` (both standard on macOS/Linux)
- `TENOR_API_KEY` environment variable

## Search for GIFs

```bash
# Search and get GIF URLs
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.gif.url'

# Get smaller/preview versions
curl -s "https://tenor.googleapis.com/v2/search?q=nice+work&limit=3&key=${TENOR_API_KEY}" | jq -r '.results[].media_formats.tinygif.url'
```

## Download a GIF

```bash
# Search and download the top result
URL=$(curl -s "https://tenor.googleapis.com/v2/search?q=celebration&limit=1&key=${TENOR_API_KEY}" | jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif
```

## Get Full Metadata

```bash
curl -s "https://tenor.googleapis.com/v2/search?q=cat&limit=3&key=${TENOR_API_KEY}" | jq '.results[] | {title: .title, url: .media_formats.gif.url, preview: .media_formats.tinygif.url, dimensions: .media_formats.gif.dims}'
```

## API Parameters

| Parameter | Description |
|-----------|-------------|
| `q` | Search query (URL-encode spaces as `+`) |
| `limit` | Max results (1-50, default 20) |
| `key` | API key (from `$TENOR_API_KEY` env var) |
| `media_filter` | Filter formats: `gif`, `tinygif`, `mp4`, `tinymp4`, `webm` |
| `contentfilter` | Safety: `off`, `low`, `medium`, `high` |
| `locale` | Language: `en_US`, `es`, `fr`, etc. |

## Available Media Formats

Each result has multiple formats under `.media_formats`:

| Format | Use case |
|--------|----------|
| `gif` | Full quality GIF |
| `tinygif` | Small preview GIF |
| `mp4` | Video version (smaller file size) |
| `tinymp4` | Small preview video |
| `webm` | WebM video |
| `nanogif` | Tiny thumbnail |

## Notes

- URL-encode the query: spaces as `+`, special chars as `%XX`
- For sending in chat, `tinygif` URLs are lighter weight
- GIF URLs can be used directly in markdown: `![alt](url)`
