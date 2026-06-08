---
name: architecture-diagram
description: "Dark-themed SVG architecture/cloud/infra diagrams as HTML."
version: 1.1.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [concept-diagrams, excalidraw]
    trigger_conditions:
      - "architecture diagram"
      - "system architecture"
      - "cloud infrastructure diagram"
      - "microservice diagram"
      - "deployment diagram"
      - "network diagram"
      - "AWS architecture"
      - "backend architecture"
      - "infrastructure diagram"
      - "service topology"
      - "database architecture diagram"
      - "tech stack diagram"
      - "dark theme diagram"
---

# Architecture Diagram Skill

Generate professional, dark-themed technical architecture diagrams as standalone HTML files with inline SVG graphics. No external tools, no API keys, no rendering libraries — just write the HTML file and open it in a browser.

## When to Use

- Visualizing software system architecture (frontend / backend / database layers)
- Documenting cloud infrastructure (VPC, regions, subnets, managed services)
- Mapping microservice or service-mesh topology
- Creating database + API maps or deployment diagrams
- Generating quick architecture diagrams for documentation or presentations
- Producing dark-themed tech visuals that look professional out of the box
- Needing a self-contained HTML file with no dependencies (offline-capable)

## Not For

- **Hand-drawn whiteboard style** → use `excalidraw` instead
- **Scientific diagrams (physics, chemistry, biology)** → use `matplotlib` or `manim` instead
- **Physical objects, hardware, anatomy** → use `architecture-diagram` only for tech-infra; use `excalidraw` or `sketch` for non-tech subjects
- **Animated explainers or interactive diagrams** → use `manim-video` or `p5js` instead
- **Floor plans, narrative journeys, educational visuals** → use `excalidraw` or `sketch` instead
- **Flowcharts or process diagrams** → use `excalidraw` or `mermaid` (via terminal) instead
- **Light-themed or white-background corporate diagrams** → this skill is dark-themed by design; use `excalidraw` for light themes

## Scope

**Best suited for:**
- Software system architecture (frontend / backend / database layers)
- Cloud infrastructure (VPC, regions, subnets, managed services)
- Microservice / service-mesh topology
- Database + API map, deployment diagrams
- Anything with a tech-infra subject that fits a dark, grid-backed aesthetic

**Look elsewhere first for:**
- Physics, chemistry, math, biology, or other scientific subjects
- Physical objects (vehicles, hardware, anatomy, cross-sections)
- Floor plans, narrative journeys, educational / textbook-style visuals
- Hand-drawn whiteboard sketches (consider `excalidraw`)
- Animated explainers (consider an animation skill)

If a more specialized skill is available for the subject, prefer that. If none fits, this skill can also serve as a general SVG diagram fallback — the output will just carry the dark tech aesthetic described below.

Based on [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT).

## Workflow

1. User describes their system architecture (components, connections, technologies)
2. Generate the HTML file following the design system below
3. Save with `write_file` to a `.html` file (e.g. `~/architecture-diagram.html`)
4. User opens in any browser — works offline, no dependencies

### Output Location

Save diagrams to a user-specified path, or default to the current working directory:
```
./[project-name]-architecture.html
```

### Preview

After saving, suggest the user open it:
```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## Design System & Visual Language

### Color Palette (Semantic Mapping)

Use specific `rgba` fills and hex strokes to categorize components:

| Component Type | Fill (rgba) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **Backend** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **Database** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/Cloud** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **Security** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **External** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

### Typography & Background
- **Font:** JetBrains Mono (Monospace), loaded from Google Fonts
- **Sizes:** 12px (Names), 9px (Sublabels), 8px (Annotations), 7px (Tiny labels)
- **Background:** Slate-950 (`#020617`) with a subtle 40px grid pattern

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

## Technical Implementation Details

### Component Rendering
Components are rounded rectangles (`rx="6"`) with 1.5px strokes. To prevent arrows from showing through semi-transparent fills, use a **double-rect masking technique**:
1. Draw an opaque background rect (`#0f172a`)
2. Draw the semi-transparent styled rect on top

### Connection Rules
- **Z-Order:** Draw arrows *early* in the SVG (after the grid) so they render behind component boxes
- **Arrowheads:** Defined via SVG markers
- **Security Flows:** Use dashed lines in rose color (`#fb7185`)
- **Boundaries:**
  - *Security Groups:* Dashed (`4,4`), rose color
  - *Regions:* Large dashed (`8,4`), amber color, `rx="12"`

### Spacing & Layout Logic
- **Standard Height:** 60px (Services); 80-120px (Large components)
- **Vertical Gap:** Minimum 40px between components
- **Message Buses:** Must be placed *in the gap* between services, not overlapping them
- **Legend Placement:** **CRITICAL.** Must be placed outside all boundary boxes. Calculate the lowest Y-coordinate of all boundaries and place the legend at least 20px below it.

## Document Structure

The generated HTML file follows a four-part layout:
1. **Header:** Title with a pulsing dot indicator and subtitle
2. **Main SVG:** The diagram contained within a rounded border card
3. **Summary Cards:** A grid of three cards below the diagram for high-level details
4. **Footer:** Minimal metadata

### Info Card Pattern
```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

## Output Requirements
- **Single File:** One self-contained `.html` file
- **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts)
- **No JavaScript:** Use pure CSS for any animations (like pulsing dots)
- **Compatibility:** Must render correctly in any modern web browser

## Pitfalls

1. **Arrows showing through semi-transparent component boxes** — SVG arrows render on top of elements drawn earlier. Fix by drawing all arrows BEFORE the component rectangles (early in SVG, after the grid). Use the double-rect masking technique: draw an opaque `#0f172a` background rect first, then the semi-transparent styled rect on top.

2. **Legend overlaps boundary boxes** — The legend must be placed below all region/security group boundaries. Calculate `max_y = max(boundary.y + boundary.height for all boundaries)` and place the legend at `max_y + 20`. Test by visually inspecting the output — if the legend is inside a boundary, it's in the wrong place.

3. **Component labels overflow the box width** — JetBrains Mono at 12px renders ~10-12 characters per 60px of box width. For long component names (e.g., "Kubernetes API Server"), use a wider box (160-200px) or split the label across two lines using SVG `<tspan>` elements.

4. **Message bus overlaps services instead of sitting between them** — Message buses must be placed in the vertical gap between service rows. Calculate: `bus_y = service_bottom + (next_service_top - service_bottom - bus_height) / 2`. If the gap is too small (<40px), increase the vertical spacing between components.

5. **Google Fonts fails to load offline** — The diagram references JetBrains Mono from Google Fonts CDN. If the user opens the file without internet, the font won't load and the browser falls back to default monospace. For fully offline use, embed the font as a base64 data URL in the CSS `@font-face` declaration (adds ~200KB).

6. **Security group boundaries clip component labels** — If a security group boundary is too tight around components, the labels may be cut off. Add 20-30px padding inside security groups: `security_group_rect = (min_x - 20, min_y - 20, max_x - min_x + 40, max_y - min_y + 40)`.

7. **Region boundaries overlap with component labels** — Region boundaries are large dashed rectangles. If they're drawn after components, they may cover labels. Draw region boundaries BEFORE all components (after the grid and arrows) in the SVG z-order.

8. **Arrowhead markers don't render** — SVG `<marker>` elements must be defined inside a `<defs>` block and referenced by ID. If the marker ID doesn't match the `marker-end="url(#arrowhead)"` attribute, the arrowhead won't appear. Verify the marker definition and the reference match exactly.

9. **Wrong color mapping for component type** — Components must use the exact `rgba` fill and hex stroke from the color palette table. Using a slightly different color breaks the visual language and makes the diagram harder to read. Double-check the table before generating.

10. **Diagram too wide for the browser viewport** — The SVG viewBox should be set to match the actual content dimensions. If the diagram is wider than ~1200px, consider a vertical layout instead of horizontal, or reduce the spacing between components. Set `viewBox="0 0 <width> <height>"` on the SVG element.

11. **Multiple HTML files overwrite each other** — If the user generates multiple diagrams, they may accidentally overwrite the previous file. Always use a descriptive filename: `./<project-name>-architecture.html` or append a timestamp: `./diagram-$(date +%s).html`.

12. **Template.html not loaded when needed** — Complex diagrams benefit from the full template. Load it with `skill_view(name="architecture-diagram", file_path="templates/template.html")` before generating. The template contains working examples of every component type, arrow style, and boundary — use it as structural reference.

## Template Reference

Load the full HTML template for the exact structure, CSS, and SVG component examples:

```
skill_view(name="architecture-diagram", file_path="templates/template.html")
```

The template contains working examples of every component type (frontend, backend, database, cloud, security), arrow styles (standard, dashed, curved), security groups, region boundaries, and the legend — use it as your structural reference when generating diagrams.