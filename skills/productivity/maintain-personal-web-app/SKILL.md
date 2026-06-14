---
name: maintain-personal-web-app
description: Maintain personal web applications with reliable timestamp updates
version: 1.0.0
category: productivity
metadata:
  hermes:
    trigger_conditions:
      - "update my web app"
      - "fix the website timestamp"
      - "personal web app"
      - "Flask Bootstrap app"
      - "maintain web application"
      - "tooltip not working"
      - "Bootstrap modal"
      - "share button broken"
      - "theme toggle"
      - "dark mode CSS"
      - "form values not persisting"
      - "Jinja2 template"
      - "CSS custom properties theming"
---

# Maintain Personal Web Application (Flask/Bootstrap)

## When to Use This Skill
When you have a personal web application built with **Flask + Bootstrap** that:
- Renders dynamic data via Jinja2 templates
- Uses Bootstrap components (modals, tooltips, alerts, cards, forms)
- Has interactive JavaScript (share URLs, theme toggles, dynamic form sections)
- Uses CSS custom properties for dark/light theming
- Handles form submissions (POST) and reflects submitted values back

## Not For

- **Full redesigns or new app builds** → use `flask-web-app-patterns` for architecture, then apply this skill for maintenance patterns
- **Publishing or hosting** → use `render-deploy` or `cloudflare-pages-static-site` instead
- **Adding authentication or user management** → this skill covers UI/UX patterns, not backend auth
- **Performance optimization or caching** → this skill covers correctness, not speed
- **Replacing the entire frontend framework** → this skill's patterns assume Flask + Bootstrap + Jinja2. A React/Vue migration needs a different approach.
- **Database schema changes** → this skill covers template context and form handling, not ORM/schema work
- **CI/CD pipeline setup** → use `github-pr-workflow` or deployment skills instead

## Problem
Personal web apps accumulate ad-hoc fixes: tooltips clip off-screen, share buttons lose state after POST, modals don't bind correctly, theme variables aren't respected, form values don't persist after submission.

## Solution
Apply consistent patterns across the stack: backend data → template context → CSS variables → Bootstrap components → JavaScript enhancements.

## Steps
1. **Identify the workflow**: Locate your data fetch/update script and HTML generation script
2. **Find the timestamp file**: Look for a file that stores the last update time (often .last_updated, timestamp, etc.)
3. **Modify update script**: Add a step to write current timestamp to the timestamp file *before* calling HTML generation
4. **Verify HTML generation**: Ensure your HTML generation script reads from the timestamp file
5. **Test the fix**: Run the update script and verify the timestamp appears correctly on the webpage
6. **Document the process**: Create/maintain documentation explaining the update workflow
7. **Clean up**: Remove or archive unused files to reduce clutter
8. **Version control**: Set up Git repository with appropriate .gitignore rules

## Flask + Bootstrap Patterns

### Backend → Template Context
```python
# In Flask route, compute derived data and pass to template
starting_point = {
    'price': f'${base_price:,.0f}',
    'total': f'${starting_total:,.0f}',
    'btc': f'{bitcoin_stack}',
    'model_family': model_family,  # 'cagr' or 'power_law'
    'base_price_label': base_price_label,
}
return render_template('index.html', 
                     results=results,
                     summary=summary,
                     starting_point=starting_point,  # NEW: derived context
                     form_data=form_data)
```

### Tooltip Positioning (CSS Custom Properties)
```css
/* Reposition tooltips BELOW trigger (was above, clipped at top) */
.fits-tooltip .fits-tooltip-text {
  top: calc(100% + 6px);  /* was bottom: calc(100% + 6px) */
  left: 50%;
  transform: translateX(-50%);
  white-space: normal;    /* wrap long text */
  max-width: 240px;
  width: max-content;
  line-height: 1.4;
}
.fits-tooltip .fits-tooltip-text::after {
  bottom: 100%;           /* arrow points up */
  border-color: transparent transparent var(--accent) transparent;
}
```

### Acronym Styling (replaces ? tooltip for short terms)
```html
<span class="fits-acronym" title="Full expansion">FITS</span>
```
```css
.fits-acronym {
  border-bottom: 1px dashed var(--accent);
  text-decoration: none;
  cursor: help;
  font-weight: 700;
  color: inherit;
}
```

### Bootstrap Modal Binding
```html
<!-- Trigger -->
<a href="#" data-toggle="modal" data-target="#startingPointModal">Learn more.</a>

<!-- Modal (must exist in DOM) -->
<div class="modal fade" id="startingPointModal" tabindex="-1" role="dialog">
  <div class="modal-dialog modal-lg" role="document">
    <div class="modal-content">...</div>
  </div>
</div>
```

### Share Button — Handle POST State
```javascript
// After POST, tiles may be hidden (Advanced mode) → no :checked radio
var modelChecked = $("input[name='model_number']:checked").val();
params.set("model", modelChecked || "6");  // fallback to default

// Guard all optional values
params.set("cagr", $("#custom_cagr_fixed").val() || "");
```

### Theme Variables
```css
:root {
  --bg: #020817;
  --bg-sidebar: #0f172a;
  --bg-card: #1e293b;
  --text: #f8fafc;
  --accent: #ff8000;
}
body.light {
  --bg: #f8fafc;
  --bg-sidebar: #ffffff;
  --bg-card: #f1f5f9;
  --text: #0f172a;
}
```
Use `var(--accent)` everywhere for consistent theming.

### Form Value Persistence After POST
```html
<!-- In template, echo back submitted values -->
<input ... value="{% if form_data %}{{ form_data.age }}{% else %}35{% endif %}">
<select ...>
  <option value="6" {% if form_data and form_data.model == '6' %}selected{% endif %}>Model 6</option>
</select>
```

## Verification
- Check that timestamp file updates after each run
- Verify webpage shows updated timestamp
- Confirm data freshness matches timestamp
- Test multiple update cycles

## Maintenance
- Schedule regular updates via cron or similar
- Monitor for failures in timestamp updates
- Keep documentation current with any workflow changes
- Periodically clean up unused files

## Pitfalls

1. **Timestamp doesn't update after data refresh** — Check script execution order: the timestamp file must be written BEFORE HTML generation runs. Verify file permissions with `ls -la`; the update script needs write access. The timestamp and data fetch must be in the same script execution.
2. **Webpage shows old timestamp despite new data** — HTML generation reads from a different timestamp file than what the update script writes. Verify both scripts point to the same path. Grep for the timestamp filename across all scripts.
3. **Tooltip clips at top of viewport** — Default Bootstrap tooltip positioning puts the popup above the trigger element. Reposition to `top: calc(100% + 6px)` and set `white-space: normal; max-width: 240px` for long text wrapping.
4. **Share button URL loses form values after POST** — After a POST request, previously checked radio buttons may be unchecked. Add fallback defaults in JavaScript: `.val() || "default"` for every parameter. Guard all optional values before building the share URL.
5. **Bootstrap modal doesn't open** — Three checks: (a) `data-target="#id"` attribute on the trigger matches the modal's `id`, (b) Bootstrap JS is loaded in the page (check DevTools Console for errors), (c) the modal HTML is in the DOM, not conditionally rendered or removed after POST.
6. **Theme toggle doesn't respect CSS variables** — Both `:root` and `body.light` must define the same set of CSS custom properties. Missing a variable in one theme means it inherits the other theme's value. Always use `var(--property)` everywhere — never hardcode color values.
7. **Form values clear after submission** — Flask templates don't automatically persist form data. In every `<input>`, `<select>`, and `<textarea>`, add conditional default values: `value="{% if form_data %}{{ form_data.field }}{% else %}default{% endif %}"`.

## Troubleshooting (Quick Reference)
- If timestamp doesn't update: check script execution order and file permissions
- If webpage shows old timestamp: verify HTML generation reads correct file
- If data doesn't match timestamp: check that data fetch and timestamp update are in same script execution
- **Tooltip clips at top**: Reposition to `top: calc(100% + 6px)` with wrapping
- **Share button loses model after POST**: Add fallback `|| "6"` for unchecked tiles
- **Modal doesn't open**: Verify `data-target="#id"` matches modal `id`, Bootstrap JS loaded