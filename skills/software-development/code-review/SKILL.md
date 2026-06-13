---
name: code-review
description: Guidelines for performing thorough code reviews with security and quality focus
version: 1.1.0
metadata:
  hermes:
    tags: [code-review, security, quality, PR-review, audit]
    trigger_conditions:
      - "code review"
      - "review this code"
      - "review this PR"
      - "audit code"
      - "security review"
      - "check code quality"
      - "review my changes"
      - "PR review"
      - "is this code safe"
      - "code audit"
      - "review the diff"
      - "check for vulnerabilities"
      - "code quality check"
---

# Code Review Skill

Use this skill when reviewing code changes, pull requests, or auditing existing code.

## When to Use

- A PR or diff needs security review for vulnerabilities
- Code quality audit is requested before merging changes
- Someone asks "is this safe" or "check for vulnerabilities"
- Reviewing someone else's code changes for correctness and maintainability
- Auditing legacy or third-party code for security anti-patterns
- Pre-commit review before pushing to a shared repository
- Checking for hardcoded secrets or credential leaks in new code

## Not For

- Writing new code or implementing features → use `writing-plans` or `subagent-driven-development`
- Debugging runtime errors or crashes → use `systematic-debugging`
- Testing existing code behavior → use `test-driven-development`
- Automated linting or formatting → use terminal linters (ruff, eslint, etc.)
- Performance profiling or optimization → use profiling tools, not code review
- Architecture design review → use `writing-plans` for design proposals

## Review Checklist

### 1. Security First
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation on all user-provided data
- [ ] SQL queries use parameterized statements (no string concatenation)
- [ ] File operations validate paths (no path traversal)
- [ ] Authentication/authorization checks present where needed

### 2. Error Handling
- [ ] All external calls (API, DB, file) have try/catch
- [ ] Errors are logged with context (but no sensitive data)
- [ ] User-facing errors are helpful but don't leak internals
- [ ] Resources are cleaned up in finally blocks or context managers

### 3. Code Quality
- [ ] Functions do one thing and are reasonably sized (<50 lines ideal)
- [ ] Variable names are descriptive (no single letters except loops)
- [ ] No commented-out code left behind
- [ ] Complex logic has explanatory comments
- [ ] No duplicate code (DRY principle)

### 4. Testing Considerations
- [ ] Edge cases handled (empty inputs, nulls, boundaries)
- [ ] Happy path and error paths both work
- [ ] New code has corresponding tests (if test suite exists)

## Review Response Format

When providing review feedback, structure it as:

```
## Summary
[1-2 sentence overall assessment]

## Critical Issues (Must Fix)
- Issue 1: [description + suggested fix]
- Issue 2: ...

## Suggestions (Nice to Have)
- Suggestion 1: [description]

## Questions
- [Any clarifying questions about intent]
```

## Common Patterns to Flag

### Python
```python
# Bad: SQL injection risk
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Good: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### JavaScript
```javascript
// Bad: XSS risk
element.innerHTML = userInput;

// Good: Safe text content
element.textContent = userInput;
```

## Pitfalls

1. **Reviewing without context — missing the "why"** — Code review without understanding the design intent leads to superficial comments about formatting while missing logic bugs. Recovery: read linked issues/PR descriptions and any design docs first; ask clarifying questions if intent is unclear.

2. **Flagging style issues that linters would catch** — Wasting review time on indentation, line length, or naming conventions that an automated formatter handles. Recovery: run the project's linter first (`ruff`, `eslint`, `clippy`); only flag style issues that the linter doesn't catch.

3. **Missing SQL injection in concatenated strings** — The #1 security bug: f-strings or string concatenation in SQL queries. Recovery: check every database call for parameterized queries; flag all string interpolation in SQL immediately.

4. **Trusting user input without validation** — Input from query params, form fields, file uploads, or API payloads must be validated. Recovery: check that every user-provided value has type checking, length limits, and sanitization before use.

5. **Reviewing too much code at once — attention fatigue** — PRs over 400 lines degrade review quality significantly. Bugs in the second half are missed. Recovery: if the PR is large, review in chunks; ask the author to split into smaller PRs next time.

6. **"Looks good to me" without running the code** — Static review misses runtime errors, broken imports, or missing dependencies. Recovery: check out the branch and run the code if possible; at minimum verify imports resolve and the test suite passes.

7. **Hardcoded secrets in plain sight** — API keys, tokens, or passwords embedded in source files. Recovery: search for patterns like `= "sk-`, `= "ghp_`, `: "eyJ` in the diff; flag immediately as critical.

8. **Mixing formatting changes with logic changes** — When a PR reformats code AND changes logic in the same commit, it's nearly impossible to review. Recovery: flag the PR for splitting; suggest the author re-submit formatting-only and logic-only commits separately.

9. **Error handling that swallows exceptions** — Bare `except:` (Python) or `catch(e) {}` (JS) that silently discards errors. Recovery: every catch block should log the error with context or re-raise; flag empty catch blocks as bugs.

10. **Resource leaks — unclosed files, connections, handles** — Forgetting `close()`, missing context managers, or not returning connections to pools. Recovery: check for `with` statements (Python) or `finally` cleanup blocks; flag manual `.close()` calls without error-path coverage.

11. **Assuming the happy path — no edge case handling** — Functions that only handle the expected input and crash on null/empty/wrong-type. Recovery: test with `null`, `""`, `[]`, `0`, and negative values mentally; flag functions without input guards.

12. **Review feedback that's all problems, no guidance** — Critique without suggesting fixes demoralizes authors and slows iteration. Recovery: for every flagged issue, include a one-line fix suggestion or pointer to the right approach.

## Tone Guidelines

- Be constructive, not critical
- Explain *why* something is an issue, not just *what*
- Offer solutions, not just problems
- Acknowledge good patterns you see
