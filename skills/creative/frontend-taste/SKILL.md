---
name: frontend-taste
description: Use for a beautiful site or to make a site look better. Curated component catalogue and design principles from premier modern UI registries (BeautifulUI, beUI, Rare UI, Transitions.dev, shadcn/ui, 21st.dev, EasyUI) for landing pages, dashboards, and agent interfaces.
version: 1.1.0
author: Jarvis
license: MIT
metadata:
  hermes:
    tags:
      - frontend
      - ui-design
      - components
      - animations
      - styling
    related_skills:
      - claude-design
      - sketch
      - popular-web-designs
      - unslop-ui
    trigger_conditions:
      - "make it look better"
      - "beautiful site"
      - "make this site beautiful"
      - "polish the UI"
      - "prettier dashboard"
      - "modern landing page"
      - "improve the design"
      - "make it prettier"
      - "UI inspiration"
      - "component ideas"
      - "make it look modern"
      - "premium look"
      - "design polish"
---

# frontend-taste

A curated design engine and component catalogue distilled from premier modern UI registries and design systems: **BeautifulUI**, **beUI**, **Rare UI**, **Transitions.dev**, **shadcn/ui**, **21st.dev**, and **EasyUI**.

## When to Use
- When the user asks for a **"beautiful site"** or **"make the site look better"**.
- When designing modern landing pages, agent dashboards, or SaaS interfaces that require polish, high aesthetic taste, and fluid micro-interactions.
- When seeking inspiration for component architecture (cards, docks, loaders, Bento grids, modals, drawers).
- When asked to polish an existing UI with micro-interactions, bento layouts, or modern primitives.

## Not For

- **Designing a full one-off HTML artifact from a brief** → use `claude-design` instead
- **Throwing together 2–3 throwaway HTML mockups for comparison** → use `sketch` instead
- **Copying a real design system's look (Stripe, Linear, Vercel)** → use `popular-web-designs` instead
- **Stripping AI-slop from prose (not UI)** → use `unslop-text` instead
- **Generating images/video with diffusion models** → use `comfyui` instead

---

## 1. Core Taste Principles & Visual Hierarchy

Modern, high-end web applications avoid generic AI slop by following distinct craftsmanship principles:

1. **Subtle Depth & Micro-Surfaces:**
   - Instead of flat boring boxes or aggressive box shadows, use semi-transparent borders (`border border-white/10` or `border-neutral-800`), backdrop blurs (`backdrop-blur-md bg-neutral-900/60`), and fine inner highlight gradients.
2. **Spring & Layout Continuity Motion:**
   - Interfaces feel tactile through physics-based spring animations (`framer-motion` / `motion/react`) rather than stiff ease curves.
   - Morphing views share layout IDs (`layoutId`) so cards smoothly expand into modals or detail drawers.
3. **Typography & Rhythm:**
   - Crisp tracking (`tracking-tight` for large headings, `tracking-normal` for body).
   - High-contrast text hierarchies with muted subheaders (`text-neutral-400` / `text-neutral-500`).
4. **Interactive Delight:**
   - Cursor-aware 3D card tilts, rolling digit tickers, glowing gradient borders on hover, dynamic island state transitions, and smooth origin-aware menus.

---

## 2. Component Catalogue by Design System Inspiration

### A. AI Interfaces & Modern Primitives (Inspiration: `beautifului.dev`)
Specialized patterns for generative AI applications, agents, and data-dense dashboards:
- **Pixel-grid / Shimmer Loaders:** Elapsed-time indicators (`0.0s`) with smooth shimmering bars.
- **Thinking / Trace Drawers:** Collapsible hierarchical execution trees (Reasoning, Searching, Tool Executions).
- **Streaming Text Cards:** Inline citation badges, real-time action pill attachments, and follow-up chips.
- **Approval Cards & Decision Gates:** Human-in-the-loop interactive prompts with accept/reject buttons and parameter tweaking.
- **Live Task Rows:** Progress states (running, paused, completed, stockout risk scores, draft indicators).
- **Context & Source Chunk Cards:** Retrieved chunks with MIME icons, token/character lengths, and metadata previews.
- **Diff Tables:** Interactive inline tabular comparisons highlighting additions and removals.
- **Command Prompt Bars:** Dynamic input composers supporting `@` source mentions, `/` slash commands, model pickers, and audio dictation buttons.
- **Scrubbable Insight Cards:** Metric overviews with sparklines and scrubbing hover tooltips.

### B. Fluid Motion & Dynamic Surfaces (Inspiration: `beui.dev`)
Components powered by spring physics and layout continuity:
- **Expandable Controls & Action Bars:** Compact icon docks that glide open into labeled pills on hover or focus.
- **Morphing Modals & Drawers:** Single-panel containers that smoothly animate height and crossfade content between multi-step views.
- **Animated Toast Stacks:** Swipeable stacked notifications with status-driven icon transitions.
- **Dynamic Island:** Floating pill widgets that morph into rich interactive activity cards.
- **3D Tilt Cards:** Perspective-tilt cards with cursor-tracked lighting glare.
- **Draggable Bottom Sheets:** Inertia-aware sheets with customizable snap points and glassmorphism.
- **Text & Number Animators:** Rolling slot digit tickers and staggered character scrambles.
- **Bloom Iris Menus:** Radial trigger buttons that blossom outwards into circular or grid action matrices.
- **Cross-Chain / Multi-Asset Swaps:** Currency converters with flip transitions and live rate morphing.

### C. Unique & Rare Standout Blocks (Inspiration: `rareui.com` & `easyui.site`)
Standout components that break repetitive layouts:
- **Fluid AI Orbs:** Shimmering, generative canvas/SVG spheres for assistant states.
- **Folder Tabs & Binders:** Tactile layered tabs resembling real folder organizers.
- **Gravity & Physics Typography:** Playful falling or colliding headline letters.
- **Proximity & Bounce Sidebars:** Navigation drawers that react to cursor proximity.
- **Interactive Duration Pickers & Segmented Dials:** Precision circular and horizontal scrubbers.
- **Interactive Feedback Bars:** Micro-reaction drawers and celebratory confetti triggers.

### D. Micro-Interactions & State Transitions (Inspiration: `transitions.dev`)
Delightful state shifts for everyday UI:
- **Origin-Aware Dropdown Menus:** Popups that scale out directly from the click origin vector.
- **Digit Flips & Tickers:** Numbers that roll vertically like odometer wheels during counter increments.
- **Button Status Morph:** Buttons transitioning seamlessly between `Idle` → `Loading Spinner` → `Drawn SVG Checkmark` → `Success`.
- **Gooey Plus Menus:** SVG gooey-filtered buttons that divide into secondary action bubbles.
- **Distance-Falloff Avatar Stacks:** Avatars that lift and separate when hovered.
- **Liquid File Drops:** Drop zones that morph organically when dragging files over them.
- **Masked Gradient Text Sweeps:** Subtle shimmer lights traveling across key typography.
- **Error Shake Feedback:** Cubic-bezier horizontal shakes on invalid inputs.

### E. Standard Foundations & Radix Primitives (Inspiration: `ui.shadcn.com`)
Clean, accessible standard primitives:
- **Accessible Base Primitives:** Dialogs, Popovers, Accordions, Tabs, Tooltips, Dropdown Menus, Context Menus, and Sheets.
- **Input Suites:** OTP Input matrices, Tag Comboboxes, Date Range Pickers, and Sliders.
- **Data Grids:** Paginated, sortable data tables with column toggling and row selection filters.
- **Card Grids & Stat Cards:** Consistent padding, muted badges, and clear typography.

### F. Modern Hero Blocks & Creative Shaders (Inspiration: `21st.dev` / Aceternity / Magic UI)
Showcase marketing surfaces:
- **Animated Heroes:** Radial glow backdrops, interactive particle canvas fields, and spotlight beams.
- **Bento Grids:** Asymmetrical feature grids with mixed content (charts, live previews, code snippets).
- **Glassmorphic Navigation Bars:** Floating sticky navbars with blur backdrops and active pill indicators.
- **Marquee & Infinite Card Carousels:** Seamlessly looping client logo walls and testimonial cards.

---

## 3. Implementation Blueprint for "Make It Look Better"

When asked to polish or build a site:

```
[1. Structural Canvas & Palette]
  - Neutral dark base (e.g., bg-neutral-950, text-neutral-100) or clean crisp light base.
  - Subtle borders (border-white/10 or border-neutral-200).
  - Ambient glowing gradients in hero / focal areas.

[2. Bento Layout Composition]
  - Break uniform lists into an asymmetrical Bento grid (span-1, span-2, span-3).
  - Add interactive hover state (scale-102, border glow, cursor-following glare).

[3. Micro-Interactions]
  - Button press effects (active:scale-95 transition-transform).
  - Tab indicators with animated sliding pills.
  - Number counters with ticker animations.

[4. Live Preview Verification]
  - Render directly in Hermes desktop using ::preview{file="..."} or open_preview.
```

---

## Pitfalls

1. **Vague briefs produce generic "AI slop" gradients** — a request like "make it beautiful" without direction defaults to purple-blue gradients and glassmorphism. Always pin the palette, the target brand feel, and the primary interaction before choosing components.
2. **Copying a full design system wholesale is wrong** — `popular-web-designs` exists for that. Use this skill for taste principles + component ideas; over-applying every animation makes the UI noisy, not premium.
3. **Micro-interactions without performance budget hurt** — heavy spring physics, 3D tilts, and canvas orbs on low-end hardware degrade the experience. Check the device; prefer CSS transforms and `will-change` for the critical path.
4. **`layoutId` morphing requires matching component trees** — if the card and modal don't share the same structure (same key position, same parent), the morph breaks into a jarring crossfade. Keep the shared layout wrapper.
5. **Dark-first palettes hide on light themes** — `bg-neutral-950` + `border-white/10` assumes dark mode. When the user's site is light, flip to `bg-neutral-50` + `border-neutral-200` and re-check contrast (WCAG AA).
6. **Accessible primitives get replaced by pretty ones** — Radix/shadcn base components (dialog, popover, tabs) handle focus trap, ARIA, and keyboard nav. Swapping in a custom animation-only version breaks screen readers; keep the base primitive and layer motion on top.
7. **Live preview verification is the deliverable, not the code dump** — render with `::preview{file="..."}` or `open_preview` and iterate on the actual look; describing components without rendering invites drift.
8. **Ticker/counter animations overflow small containers** — rolling digit tickers and number scramblers need fixed-width monospace slots; without them the layout shifts on every tick. Reserve them for stat rows, not body text.
9. **Bento grids break on narrow viewports** — an asymmetric span-1/span-2/span-3 grid collapses badly below ~768px. Define a mobile fallback (single column) before shipping.
10. **Don't restyle working code for the sake of taste** — if the user asks to "make it look better," first confirm the target (hero? whole page? brand direction) and keep the existing functional structure; a full visual rewrite risks regressions for marginal gain.
