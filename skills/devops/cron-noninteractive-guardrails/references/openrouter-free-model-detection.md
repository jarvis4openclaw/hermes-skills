# OpenRouter Free Model Detection Pattern

## What it does
A cron-driven detector that monitors OpenRouter's free model API for changes — new models appearing or existing ones going paid (expired). Includes a dashboard tab for visualizing the data.

## Files
- Script: `~/.hermes/scripts/detect-new-free-models.py`
- Tracker: `~/.hermes/openrouter-free-models.json` (known models + expired history)
- Image generator: `~/.hermes/scripts/gen-model-table.py` (PIL table image)
- Cron job: `openrouter-free-model-detector` (daily at 10am CST)
- Dashboard page: `~/clawd/automation-dashboard/my-app/src/app/(dashboard)/free-models/page.tsx`
- Dashboard API: `~/clawd/automation-dashboard/my-app/src/app/api/openrouter-free-models/route.ts`

## Detection logic
1. Fetch all models from `https://openrouter.ai/api/v1/models` (via curl — see IPv6 pitfall)
2. Filter for "top-tier": frontier lab (deepseek/qwen/llama/gemma/nemotron/etc), ≥200k context, free pricing
3. Ping each model for latency via chat completions endpoint (1.5s delay between pings)
4. Compare against known models file
5. Output: `NEW_MODELS`, `EXPIRED_MODELS`, `NEW_AND_EXPIRED`, or `NO_CHANGE`

## Cron prompt behavior
- **New models** → notify user with details, ask if they want to add it (human-in-the-loop, never auto-add)
- **Expired models** → alert user that model is no longer free, warn to check config.yaml for references
- **No change** → silent exit

## Key design decisions
- Uses `curl` subprocess instead of Python `urllib` (IPv6 hang issue)
- Tracks `first_seen` and `expired_at` timestamps for full lifecycle visibility
- Only notifies on changes — no spam on no-change runs
- Human-in-the-loop for adding new models (user reviews before config change)
- Latency pinging integrated into the detection script itself

## OpenRouter API Notes

### No popularity/usage stats
The `/api/v1/models` endpoint does **not** include popularity rankings, usage stats, or weekly token counts. Sort by context length as the best proxy for "top tier".

### No latency data in models endpoint
The `/api/v1/models` endpoint does **not** include latency/performance stats. To measure latency, ping each model via chat completions:
```bash
curl -s -X POST https://openrouter.ai/api/v1/chat_completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"model/id","messages":[{"role":"user","content":"ok"}],"max_tokens":5}'
```
Measure wall-clock time. Add ~1.5s delay between pings to avoid rate limiting.

### Tool calling support
Check `supported_parameters` for `tools`/`tool_choice`. As of May 2026, all top-tier free frontier models support OpenAI-style tool/function calling.

### Reasoning support
Check for `reasoning`/`include_reasoning` in `supported_parameters`.

## Automation Dashboard — Adding a Tab

The dashboard is a Next.js app at `~/clawd/automation-dashboard/my-app/` running on port 2999.

### Pattern for adding a new tab:
1. **Nav item**: Add to `NAV_ITEMS` in `src/app/dashboard-layout.tsx` with `{ id, label, href, icon }`
2. **Page**: Create `src/app/(dashboard)/<name>/page.tsx` — fetches from `/api/<name>`
3. **API route**: Create `src/app/api/<name>/route.ts` — reads tracker JSON or live APIs
4. **Icons**: Use `lucide-react` icons (already a dependency)

### Data flow:
- Tracker JSON in `~/.hermes/` is the source of truth
- API route reads tracker and returns structured JSON
- Page fetches from API on mount and on refresh
- `next dev` auto-reloads when files change

### Page structure convention:
- Header with title, subtitle, last-updated timestamp, refresh button
- Summary cards row (grid-cols-4)
- Data table with alternating row colors
- Color-coded badges for latency/status
- Links to external resources
- Footer with legend and attribution

## PIL Table Image Generation

### Pattern
Use Pillow (`PIL`) for data table images:
- Dark background, color-coded latency (green/yellow/red/dim)
- Brown/warn background for N/A rows
- Ellipsis truncation for long text
- Dynamic date via `datetime.now().strftime('%B %Y')`

### Gotchas
- Font paths: try `/usr/share/fonts/truetype/dejavu/`, `/usr/share/fonts/TTF/`, `/usr/share/fonts/truetype/liberation/`
- Text truncation: use `textbbox()` to measure, shorten with ellipsis
- Import: `from PIL import Image, ImageDraw, ImageFont` (NOT `Image, Draw`)
- Save to `~/.hermes/` for easy reference

## Lightpanda Browser Backend

Headless browser in Zig, supported as Hermes browser backend.

### Installation (x86_64 Linux)
```bash
curl -fsSL -o ~/.local/bin/lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux
chmod +x ~/.local/bin/lightpanda
```

### Config
```yaml
browser:
  engine: lightpanda
```

### Behavior
- Handles core workflows (navigate, snapshot, click, type, scroll)
- Auto-falls back to Chrome for screenshots, PDF gen, etc.
- Instant startup, tiny memory footprint vs Chrome (~200MB)

## Adapting this pattern
To monitor a different API:
1. Replace fetch + filter logic in the script
2. Update tracker JSON schema
3. Update cron prompt for the new domain
4. Keep output prefix convention (`NEW_*/EXPIRED_*/NO_CHANGE`)
5. Add dashboard tab following the pattern above
