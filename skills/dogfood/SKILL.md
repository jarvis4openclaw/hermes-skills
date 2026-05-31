---
name: dogfood
description: "Exploratory QA of web apps: find bugs, evidence, reports."
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: [plan, spike, claude-design]
    trigger_conditions:
      - "test this web app"
      - "dogfood"
      - "qa testing"
      - "find bugs in"
      - "check this site for issues"
      - "exploratory testing"
      - "web app QA"
      - "screenshot and report bugs"
      - "audit this website"
      - "browser testing"
      - "check for broken links"
      - "verify this page"
      - "systematic web testing"
---

# Dogfood: Systematic Web Application QA Testing

## Overview

This skill guides you through systematic exploratory QA testing of web applications using the browser toolset. You will navigate the application, interact with elements, capture evidence of issues, and produce a structured bug report.

## When to Use

- User says "test this web app" or "find bugs in this site"
- User wants a systematic audit of a website or web app before launch
- User asks for "QA testing" or "exploratory testing"
- User wants screenshots and a report of issues found
- User says "check this for broken links" or "verify this page"
- User needs a pre-release sanity check on a new feature or page
- User says "dogfood" explicitly
- User wants to compare expected vs actual behavior across a site

## Not For

- **Unit testing or API endpoint testing** → use a testing framework (pytest, jest) instead
- **Load or performance testing** → use dedicated tools (k6, artillery, lighthouse CI)
- **Security penetration testing** → use specialized security tools or skills
- **Accessibility audit (WCAG compliance scoring)** → use axe-core, lighthouse accessibility, or a dedicated a11y tool
- **Testing mobile-native apps** → this skill is browser-based only
- **Automated regression test suite creation** → use Playwright, Cypress, or Selenium
- **Design critique or visual design review** → use `claude-design` or `sketch` instead

## Prerequisites

- Browser toolset must be available (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`, `browser_back`, `browser_press`)
- A target URL and testing scope from the user

## Inputs

The user provides:
1. **Target URL** — the entry point for testing
2. **Scope** — what areas/features to focus on (or "full site" for comprehensive testing)
3. **Output directory** (optional) — where to save screenshots and the report (default: `./dogfood-output`)

## Workflow

Follow this 5-phase systematic workflow:

### Phase 1: Plan

1. Create the output directory structure:
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
2. Identify the testing scope based on user input.
3. Build a rough sitemap by planning which pages and features to test:
   - Landing/home page
   - Navigation links (header, footer, sidebar)
   - Key user flows (sign up, login, search, checkout, etc.)
   - Forms and interactive elements
   - Edge cases (empty states, error pages, 404s)

### Phase 2: Explore

For each page or feature in your plan:

1. **Navigate** to the page:
   ```
   browser_navigate(url="https://example.com/page")
   ```

2. **Take a snapshot** to understand the DOM structure:
   ```
   browser_snapshot()
   ```

3. **Check the console** for JavaScript errors:
   ```
   browser_console(clear=true)
   ```
   Do this after every navigation and after every significant interaction. Silent JS errors are high-value findings.

4. **Take an annotated screenshot** to visually assess the page and identify interactive elements:
   ```
   browser_vision(question="Describe the page layout, identify any visual issues, broken elements, or accessibility concerns", annotate=true)
   ```
   The `annotate=true` flag overlays numbered `[N]` labels on interactive elements. Each `[N]` maps to ref `@eN` for subsequent browser commands.

5. **Test interactive elements** systematically:
   - Click buttons and links: `browser_click(ref="@eN")`
   - Fill forms: `browser_type(ref="@eN", text="test input")`
   - Test keyboard navigation: `browser_press(key="Tab")`, `browser_press(key="Enter")`
   - Scroll through content: `browser_scroll(direction="down")`
   - Test form validation with invalid inputs
   - Test empty submissions

6. **After each interaction**, check for:
   - Console errors: `browser_console()`
   - Visual changes: `browser_vision(question="What changed after the interaction?")`
   - Expected vs actual behavior

### Phase 3: Collect Evidence

For every issue found:

1. **Take a screenshot** showing the issue:
   ```
   browser_vision(question="Capture and describe the issue visible on this page", annotate=false)
   ```
   Save the `screenshot_path` from the response — you will reference it in the report.

2. **Record the details**:
   - URL where the issue occurs
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Console errors (if any)
   - Screenshot path

3. **Classify the issue** using the issue taxonomy (see `references/issue-taxonomy.md`):
   - Severity: Critical / High / Medium / Low
   - Category: Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge issues that are the same bug manifesting in different places.
3. Assign final severity and category to each issue.
4. Sort by severity (Critical first, then High, Medium, Low).
5. Count issues by severity and category for the executive summary.

### Phase 5: Report

Generate the final report using the template at `templates/dogfood-report-template.md`.

The report must include:
1. **Executive summary** with total issue count, breakdown by severity, and testing scope
2. **Per-issue sections** with:
   - Issue number and title
   - Severity and category badges
   - URL where observed
   - Description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshot references (use `MEDIA:<screenshot_path>` for inline images)
   - Console errors if relevant
3. **Summary table** of all issues
4. **Testing notes** — what was tested, what was not, any blockers

Save the report to `{output_dir}/report.md`.

## Tools Reference

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Go to a URL |
| `browser_snapshot` | Get DOM text snapshot (accessibility tree) |
| `browser_click` | Click an element by ref (`@eN`) or text |
| `browser_type` | Type into an input field |
| `browser_scroll` | Scroll up/down on the page |
| `browser_back` | Go back in browser history |
| `browser_press` | Press a keyboard key |
| `browser_vision` | Screenshot + AI analysis; use `annotate=true` for element labels |
| `browser_console` | Get JS console output and errors |

## Pitfalls

1. **Testing without a defined scope** — "Full site" sounds comprehensive but leads to shallow coverage. Define 3–5 critical user flows and test those deeply rather than clicking every link shallowly.

2. **Skipping `browser_console` after navigation** — Silent JS errors are among the highest-value findings. They don't block the UI but indicate broken functionality. Always run `browser_console(clear=true)` after every `browser_navigate` and after form submissions.

3. **Using `browser_click` without a snapshot first** — `browser_click` requires a ref like `@e5`. If the page changed since the last snapshot, the ref may point to a different element or fail. Always call `browser_snapshot` immediately before `browser_click`.

4. **Not verifying screenshots were saved** — `browser_vision` returns a `screenshot_path`, but it may fail if the filesystem is full or the path is invalid. Confirm the file exists with `terminal(command="ls -la <screenshot_path>")` before referencing it in the report.

5. **Reporting the same bug in multiple places as separate issues** — A broken navigation link that appears on every page is one issue, not N issues. De-duplicate in Phase 4. Check the URL and root cause before filing.

6. **Testing only the happy path** — Empty form submissions, invalid emails, very long text, special characters, and rapid clicks catch real bugs. Don't just test "valid input works" — test "invalid input is handled gracefully."

7. **Forgetting to scroll** — Content below the fold often has rendering issues (overlapping elements, broken images, layout shifts). Use `browser_scroll(direction="down")` repeatedly until you reach the bottom of the page.

8. **Misclassifying severity** — A misspelled word is Low. A broken checkout button is Critical. A console error on a marketing page is Medium. Use the definitions in `references/issue-taxonomy.md` consistently.

9. **Writing a report without screenshots** — "The button is broken" is weak evidence. "The button is broken — see `MEDIA:<screenshot_path>`" is strong evidence. Every issue should have a screenshot.

10. **Not checking `browser_vision` annotations against snapshot refs** — When `annotate=true`, `browser_vision` returns `[N]` labels that map to `@eN`. But the vision tool may label elements differently than the snapshot. If you plan to click after a vision call, re-run `browser_snapshot` to get the current refs.

11. **Stopping after finding one bug** — The goal is systematic coverage, not "find one issue and stop." Continue through the full sitemap even after finding bugs. Multiple issues in the same area often share a root cause.

12. **Running on production sites with write operations** — This skill is for testing, not for interacting with live production data. Don't submit real forms, create real accounts, or make real purchases during a dogfood session. Use staging environments or test data.
