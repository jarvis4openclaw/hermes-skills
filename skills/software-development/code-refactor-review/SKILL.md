---
name: code-refactor-review
description: Structured code review framework focused on reuse, composition, consistency, and slop detection. Based on Sahaj's (jnsahaj) review methodology.
category: software-development
version: 1.1.0
metadata:
  hermes:
    tags: [code-review, refactor, reuse, composition, slop]
    trigger_conditions:
      - "Review code changes for reuse and composition"
      - "Check for over-engineering or slop in a diff"
      - "Refactor review following Sahaj's methodology"
      - "Audit a PR for codebase consistency"
      - "Find unnecessary abstractions or utils junk drawers"
      - "Decide clean / mostly clean / needs cleanup verdict"
      - "Review React or Next.js changes for quality"
      - "Ask what to delete in a refactor"
---

# Code Refactor Review Skill

Review code changes the way Sahaj usually asks for review: go deep on reuse, composition, codebase consistency, and anything that reads like slop.

## First Pass

```bash
git diff
git diff HEAD
```

## Review Lenses

### 1. Reuse Existing Code
- Check if new code duplicates existing functionality in the codebase
- Look for existing utilities, hooks, components that could be used instead
- Prefer composition over creating new abstractions

### 2. Codebase Consistency
- Follow existing patterns in `lib/` and similar directories
- Match naming conventions, file structure, import styles
- Use the same libraries and patterns already established

### 3. Composition and Boundaries
- Components should do one thing well
- Clear separation of concerns (data fetching, UI, business logic)
- Avoid premature abstraction — let patterns emerge

### 4. Slop Detection
Flag and, when asked to fix, remove:
- Unnecessary `useMemo` / `useCallback` (React's compiler often handles this)
- Over-engineered abstractions with single callers
- "Utils" / "helpers" / "shared" dumping grounds
- Dead code, commented-out blocks, console.logs

### 5. React / Next.js Quality
- Server components by default, client components only when needed
- Proper streaming / suspense boundaries
- No unnecessary client-side hydration
- Correct cache headers and revalidation strategies

### 6. Minimality
- Less code > more code
- Delete rather than add when possible
- Each line should justify its existence

## Output Format

Start with a verdict:
- `clean` — no issues found
- `mostly clean` — minor nits, no structural problems
- `needs cleanup` — structural issues, reuse violations, or slop detected

Then list findings by priority (high → low). For each finding include:
- File and line reference
- What the issue is
- Why it matters (reuse/consistency/slop/minimality)
- Suggested fix (or "remove" if slop)

## Red Flags (Investigate Immediately)

- `utils/` — often becomes a junk drawer
- `helpers/` — same
- `shared/` — vague ownership, unclear boundaries
- `index.ts` re-exports — hides true dependency graph

## Rules

- `if` the user asked for review only → do not edit files, only report
- `if` the user asked to fix it → make changes directly and summarize what changed
- Always prefer existing codebase patterns over "best practices" from outside
- When in doubt, delete the abstraction and inline until it hurts

## When to Use
- Reviewing a diff, PR, or refactor for reuse, composition, consistency, and slop.
- A second pass before merge that hunts for dead code, junk-drawer utils, and over-engineering.
- React/Next.js-specific quality checks (server components, streaming, cache headers).
- When the user says "review like Sahaj would" / "refactor review".

## Not For
- **Pre-commit security/quality gates with auto-fix** → use `requesting-code-review` (security scan + auto-fix).
- **Reviewing over-engineering ONLY (what to delete)** → use `ponytail-review` (one line per finding).
- **Correctness-focused debugging of test failures / production bugs** → use `systematic-debugging`.
- **Post-hoc review of changes since a fixed point in a branch** → use `github-code-review` / `review`.

## Pitfalls
1. **Editing files when the user asked for review only** — Respect the review/fix distinction. Report-only mode must never mutate the tree.
2. **Skipping the verdict line** — Start every review with `clean` / `mostly clean` / `needs cleanup`; a findings list without a verdict is unfinishable for the user.
3. **Missing the slop pass** — `useMemo`/`useCallback` that the React compiler handles, single-caller abstractions, commented-out blocks, and console.logs are the highest-value deletions; flag them explicitly.
4. **Letting `utils/` and `helpers/` slide** — They're junk-drawer red flags. Investigate them immediately rather than treating them as a normal pattern.
5. **Prescribing external "best practices" over codebase conventions** — The codebase's existing patterns win, even when a library doc suggests otherwise.
6. **Reviewing without diff context** — Always start from `git diff` / `git diff HEAD`; reviewing from memory or a single file misses the actual change scope.
7. **Not prioritizing findings** — List findings high → low with file/line references, why it matters, and a concrete suggested fix (or "remove").
8. **Ignoring hydration/streaming issues in Next.js** — Server components by default, client components only when needed; missing Suspense boundaries and wrong cache headers are structural problems, not nits.