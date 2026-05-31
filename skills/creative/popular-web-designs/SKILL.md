---
name: popular-web-designs
description: 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS.
version: 1.1.0
author: Hermes Agent + Teknium (design systems sourced from VoltAgent/awesome-design-md)
license: MIT
tags: [design, css, html, ui, web-development, design-systems, templates]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, css, html, ui, web-development, design-systems, templates]
    related_skills: [claude-design, design-md, sketch, architecture-diagram]
    trigger_conditions:
      - "build a page that looks like"
      - "make it look like stripe"
      - "design like linear"
      - "vercel style"
      - "create a UI"
      - "web design"
      - "landing page"
      - "dashboard design"
      - "website styled like"
      - "design system template"
      - "clone the look of"
      - "match the style of"
      - "design tokens for"
---

# Popular Web Designs

54 real-world design systems ready for use when generating HTML/CSS. Each template captures a
site's complete visual language: color palette, typography hierarchy, component styles, spacing
system, shadows, responsive behavior, and practical agent prompts with exact CSS values.

## When to Use

- User asks to build a page that looks like Stripe, Linear, Vercel, or any of the 54 cataloged sites
- User wants a design system's visual language applied to a new page or prototype
- User needs a starting point for a landing page, dashboard, or marketing site with a specific aesthetic
- User says "make it look professional" and you need a concrete visual reference
- User is comparing design directions and needs tokens for different styles
- User wants to prototype a UI that matches a known brand's design language
- User asks for CSS custom properties, font stacks, or shadow values from a specific design system
- User needs a quick theme for a throwaway page but wants it to look polished

## Not For

- **The design *process* (scoping a brief, producing variants, verifying artifacts)** → use `claude-design` instead
- **Formal DESIGN.md token spec files (not rendered HTML)** → use `design-md` instead
- **Throwaway HTML mockups with variant comparison** → use `sketch` instead
- **Architecture diagrams or infrastructure visuals** → use `architecture-diagram` instead
- **Hand-drawn style wireframes or flowcharts** → use `excalidraw` instead
- **Interactive p5.js generative art or shaders** → use `p5js` instead
- **Pixel-art or retro game aesthetic** → use `pixel-art` instead

## Related design skills

- **`claude-design`** — use for the design *process and taste* (scoping a brief,
  producing variants, verifying a local HTML artifact, avoiding AI-design slop).
  Pair it with this skill when the user wants a thoughtfully-designed page styled
  after a known brand: `claude-design` drives the workflow, this skill supplies
  the visual vocabulary.
- **`design-md`** — use when the deliverable is a formal DESIGN.md token spec
  file, not a rendered artifact.

## How to Use

1. Pick a design from the catalog below
2. Load it: `skill_view(name="popular-web-designs", file_path="templates/<site>.md")`
3. Use the design tokens and component specs when generating HTML
4. Pair with the `generative-widgets` skill to serve the result via cloudflared tunnel

Each template includes a **Hermes Implementation Notes** block at the top with:
- CDN font substitute and Google Fonts `<link>` tag (ready to paste)
- CSS font-family stacks for primary and monospace
- Reminders to use `write_file` for HTML creation and `browser_vision` for verification

## HTML Generation Pattern

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <!-- Paste the Google Fonts <link> from the template's Hermes notes -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style>
    /* Apply the template's color palette as CSS custom properties */
    :root {
      --color-bg: #ffffff;
      --color-text: #171717;
      --color-accent: #533afd;
      /* ... more from template Section 2 */
    }
    /* Apply typography from template Section 3 */
    body {
      font-family: 'Inter', system-ui, sans-serif;
      color: var(--color-text);
      background: var(--color-bg);
    }
    /* Apply component styles from template Section 4 */
    /* Apply layout from template Section 5 */
    /* Apply shadows from template Section 6 */
  </style>
</head>
<body>
  <!-- Build using component specs from the template -->
</body>
</html>
```

Write the file with `write_file`, serve with the `generative-widgets` workflow (cloudflared tunnel),
and verify the result with `browser_vision` to confirm visual accuracy.

## Font Substitution Reference

Most sites use proprietary fonts unavailable via CDN. Each template maps to a Google Fonts
substitute that preserves the design's character. Common mappings:

| Proprietary Font | CDN Substitute | Character |
|---|---|---|
| Geist / Geist Sans | Geist (on Google Fonts) | Geometric, compressed tracking |
| Geist Mono | Geist Mono (on Google Fonts) | Clean monospace, ligatures |
| sohne-var (Stripe) | Source Sans 3 | Light weight elegance |
| Berkeley Mono | JetBrains Mono | Technical monospace |
| Airbnb Cereal VF | DM Sans | Rounded, friendly geometric |
| Circular (Spotify) | DM Sans | Geometric, warm |
| figmaSans | Inter | Clean humanist |
| Pin Sans (Pinterest) | DM Sans | Friendly, rounded |
| NVIDIA-EMEA | Inter (or Arial system) | Industrial, clean |
| CoinbaseDisplay/Sans | DM Sans | Geometric, trustworthy |
| UberMove | DM Sans | Bold, tight |
| HashiCorp Sans | Inter | Enterprise, neutral |
| waldenburgNormal (Sanity) | Space Grotesk | Geometric, slightly condensed |
| IBM Plex Sans/Mono | IBM Plex Sans/Mono | Available on Google Fonts |
| Rubik (Sentry) | Rubik | Available on Google Fonts |

When a template's CDN font matches the original (Inter, IBM Plex, Rubik, Geist), no
substitution loss occurs. When a substitute is used (DM Sans for Circular, Source Sans 3
for sohne-var), follow the template's weight, size, and letter-spacing values closely —
those carry more visual identity than the specific font face.

## Design Catalog

### AI & Machine Learning

| Template | Site | Style |
|---|---|---|
| `claude.md` | Anthropic Claude | Warm terracotta accent, clean editorial layout |
| `cohere.md` | Cohere | Vibrant gradients, data-rich dashboard aesthetic |
| `elevenlabs.md` | ElevenLabs | Dark cinematic UI, audio-waveform aesthetics |
| `minimax.md` | Minimax | Bold dark interface with neon accents |
| `mistral.ai.md` | Mistral AI | French-engineered minimalism, purple-toned |
| `ollama.md` | Ollama | Terminal-first, monochrome simplicity |
| `opencode.ai.md` | OpenCode AI | Developer-centric dark theme, full monospace |
| `replicate.md` | Replicate | Clean white canvas, code-forward |
| `runwayml.md` | RunwayML | Cinematic dark UI, media-rich layout |
| `together.ai.md` | Together AI | Technical, blueprint-style design |
| `voltagent.md` | VoltAgent | Void-black canvas, emerald accent, terminal-native |
| `x.ai.md` | xAI | Stark monochrome, futuristic minimalism, full monospace |

### Developer Tools & Platforms

| Template | Site | Style |
|---|---|---|
| `cursor.md` | Cursor | Sleek dark interface, gradient accents |
| `expo.md` | Expo | Dark theme, tight letter-spacing, code-centric |
| `linear.app.md` | Linear | Ultra-minimal dark-mode, precise, purple accent |
| `lovable.md` | Lovable | Playful gradients, friendly dev aesthetic |
| `mintlify.md` | Mintlify | Clean, green-accented, reading-optimized |
| `posthog.md` | PostHog | Playful branding, developer-friendly dark UI |
| `raycast.md` | Raycast | Sleek dark chrome, vibrant gradient accents |
| `resend.md` | Resend | Minimal dark theme, monospace accents |
| `sentry.md` | Sentry | Dark dashboard, data-dense, pink-purple accent |
| `supabase.md` | Supabase | Dark emerald theme, code-first developer tool |
| `superhuman.md` | Superhuman | Premium dark UI, keyboard-first, purple glow |
| `vercel.md` | Vercel | Black and white precision, Geist font system |
| `warp.md` | Warp | Dark IDE-like interface, block-based command UI |
| `zapier.md` | Zapier | Warm orange, friendly illustration-driven |

### Infrastructure & Cloud

| Template | Site | Style |
|---|---|---|
| `clickhouse.md` | ClickHouse | Yellow-accented, technical documentation style |
| `composio.md` | Composio | Modern dark with colorful integration icons |
| `hashicorp.md` | HashiCorp | Enterprise-clean, black and white |
| `mongodb.md` | MongoDB | Green leaf branding, developer documentation focus |
| `sanity.md` | Sanity | Red accent, content-first editorial layout |
| `stripe.md` | Stripe | Signature purple gradients, weight-300 elegance |

### Design & Productivity

| Template | Site | Style |
|---|---|---|
| `airtable.md` | Airtable | Colorful, friendly, structured data aesthetic |
| `cal.md` | Cal.com | Clean neutral UI, developer-oriented simplicity |
| `clay.md` | Clay | Organic shapes, soft gradients, art-directed layout |
| `figma.md` | Figma | Vibrant multi-color, playful yet professional |
| `framer.md` | Framer | Bold black and blue, motion-first, design-forward |
| `intercom.md` | Intercom | Friendly blue palette, conversational UI patterns |
| `miro.md` | Miro | Bright yellow accent, infinite canvas aesthetic |
| `notion.md` | Notion | Warm minimalism, serif headings, soft surfaces |
| `pinterest.md` | Pinterest | Red accent, masonry grid, image-first layout |
| `webflow.md` | Webflow | Blue-accented, polished marketing site aesthetic |

### Fintech & Crypto

| Template | Site | Style |
|---|---|---|
| `coinbase.md` | Coinbase | Clean blue identity, trust-focused, institutional feel |
| `kraken.md` | Kraken | Purple-accented dark UI, data-dense dashboards |
| `revolut.md` | Revolut | Sleek dark interface, gradient cards, fintech precision |
| `wise.md` | Wise | Bright green accent, friendly and clear |

### Enterprise & Consumer

| Template | Site | Style |
|---|---|---|
| `airbnb.md` | Airbnb | Warm coral accent, photography-driven, rounded UI |
| `apple.md` | Apple | Premium white space, SF Pro, cinematic imagery |
| `bmw.md` | BMW | Dark premium surfaces, precise engineering aesthetic |
| `ibm.md` | IBM | Carbon design system, structured blue palette |
| `nvidia.md` | NVIDIA | Green-black energy, technical power aesthetic |
| `spacex.md` | SpaceX | Stark black and white, full-bleed imagery, futuristic |
| `spotify.md` | Spotify | Vibrant green on dark, bold type, album-art-driven |
| `uber.md` | Uber | Bold black and white, tight type, urban energy |

## Choosing a Design

Match the design to the content:

- **Developer tools / dashboards:** Linear, Vercel, Supabase, Raycast, Sentry
- **Documentation / content sites:** Mintlify, Notion, Sanity, MongoDB
- **Marketing / landing pages:** Stripe, Framer, Apple, SpaceX
- **Dark mode UIs:** Linear, Cursor, ElevenLabs, Warp, Superhuman
- **Light / clean UIs:** Vercel, Stripe, Notion, Cal.com, Replicate
- **Playful / friendly:** PostHog, Figma, Lovable, Zapier, Miro
- **Premium / luxury:** Apple, BMW, Stripe, Superhuman, Revolut
- **Data-dense / dashboards:** Sentry, Kraken, Cohere, ClickHouse
- **Monospace / terminal aesthetic:** Ollama, OpenCode, x.ai, VoltAgent

## Pitfalls

1. **Forgetting to load the template file** — The SKILL.md only contains the catalog; the actual design tokens are in `templates/<site>.md`. Always call `skill_view(name="popular-web-designs", file_path="templates/<site>.md")` after picking a design. Without it, you're guessing at colors and spacing.

2. **Pasting Google Fonts `<link>` inside `<style>` tags** — The `<link>` tag must go in `<head>`, not inside a `<style>` block. Browsers silently ignore `<link>` inside `<style>`, so the font won't load and the page falls back to system fonts with no error message. Use `browser_vision` after rendering to catch this.

3. **Using proprietary font names in `font-family` without the CDN `<link>`** — Templates map proprietary fonts (e.g., "Geist Sans", "sohne-var") to CDN substitutes. If you use the proprietary name without loading the substitute font, the browser falls back to a generic sans-serif. Always include the Google Fonts `<link>` from the template's Hermes notes.

4. **Mixing design tokens from two different templates** — Each template is a self-contained system. Combining Stripe's purple gradient with Linear's spacing system produces visual incoherence. Pick one template and commit to it for the entire page.

5. **Skipping `browser_vision` verification** — CSS custom properties, font loading, and layout all fail silently. A page that looks correct in source code may be broken in the browser. Always navigate to the file and call `browser_vision(question="Does this page render correctly? Any layout issues or unstyled elements?")`.

6. **Using `skill_view` to load a template that doesn't exist** — The catalog lists 54 templates, but confirm the exact filename with `search_files(pattern="<site>.md", target="files", path="~/.hermes/skills/creative/popular-web-designs/templates")` before loading. Template filenames may differ from catalog names (e.g., `linear.app.md` vs `linear.md`).

7. **Overwriting the template tokens with your own guesses** — The template provides exact hex colors, font weights, spacing values, and shadow specs. Substituting "close enough" values defeats the purpose. Use the template values verbatim.

8. **Applying a dark-mode template to a light-mode page without adjusting** — Templates like Linear and ElevenLabs assume dark backgrounds. If the user wants a light page, pick a light-mode template (Vercel, Notion, Stripe) instead of inverting a dark one.

9. **Treating a design template as a full component library** — Templates provide visual language (colors, type, spacing, shadows), not pre-built React/Vue components. You still need to write the HTML structure; the template tells you how it should look.

10. **Loading `skill_view` for every page in a multi-page site** — Load the template once and store the tokens. Re-loading for every page wastes tool calls and slows down generation.

11. **Ignoring the template's responsive breakpoint guidance** — Many templates specify how spacing and typography change at different viewport sizes. Skipping this produces desktop-only designs that break on mobile.

12. **Pairing this skill with `generative-widgets` but forgetting the tunnel step** — If you serve via cloudflared tunnel, the tunnel URL must be accessible. After `write_file` and tunnel start, verify the live URL with `browser_navigate(url="<tunnel-url>")` — not just the local `file://` path.
