---
name: ponytail-review
description: >
  Code review focused exclusively on over-engineering. Finds what to delete:
  reinvented standard library, unneeded dependencies, speculative abstractions,
  dead flexibility. One line per finding: location, what to cut, what replaces
  it. Use when the user says "review for over-engineering", "what can we
  delete", "is this over-engineered", "simplify review", or invokes
  /ponytail-review. Complements correctness-focused review, this one only
  hunts complexity.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Code-Review, Complexity, Refactoring, Minimalism]
    trigger_conditions:
      - "review for over-engineering"
      - "what can we delete"
      - "is this over-engineered"
      - "simplify review"
      - "/ponytail-review"
      - "review code for complexity"
      - "hunt complexity"
      - "find over-engineering"
      - "code simplification review"
---

# Ponytail Review

Review diffs for unnecessary complexity. One line per finding: location, what
to cut, what replaces it. The diff's best outcome is getting shorter.

## When to Use

Use when performing code reviews focused exclusively on reducing unnecessary complexity and bloat:
- Reviewing PRs or commits for over-engineering and speculative abstractions
- Hunting for reinvented standard library functions or duplicate dependencies
- Simplifying complex implementations before merging
- Auditing legacy codebases for dead flexibility and unused code layers

## Not For

- **Correctness bugs and security holes** — route to standard code review (`github-code-review`) instead; this skill hunts complexity only.
- **Performance tuning or profiling** — use specialized benchmarking tools; complexity reduction is structural, not micro-optimized.
- **Applying fixes automatically** — this skill lists findings, it does not modify the code.
- **Enforcing style guidelines** — linting and formatting belong to automated linters, not complexity reviews.

## Format

`L<line>: <tag> <what>. <replacement>.`, or `<file>:L<line>: ...` for
multi-file diffs.

Tags:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## Examples

❌ "This EmailValidator class might be more complex than necessary, have you
considered whether all these validation rules are needed at this stage?"

✅ `L12-38: stdlib: 27-line validator class. "@" in email, 1 line, real validation is the confirmation mail.`

✅ `L4: native: moment.js imported for one format call. Intl.DateTimeFormat, 0 deps.`

✅ `repo.py:L88: yagni: AbstractRepository with one implementation. Inline it until a second one exists.`

✅ `L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.`

✅ `L30-44: shrink: manual loop builds dict. dict(zip(keys, values)), 1 line.`

## Scoring

End with the only metric that matters: `net: -<N> lines possible.`

If there is nothing to cut, say `Lean already. Ship.` and stop.

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass, not this one. A single smoke test or `assert`-based
self-check is the ponytail minimum, not bloat, never flag it for deletion.
Does not apply the fixes, only lists them.
"stop ponytail-review" or "normal mode": revert to verbose review style.

## Pitfalls

1. **Confusing correctness bugs with complexity** — Flagging a logic error or security vulnerability under `yagni` or `delete` leads to breaking changes. Recovery: route correctness issues to standard code review and restrict findings to architectural/code bloat.
2. **Flagging smoke tests as dead code** — Mistaking a single smoke test or `assert`-based self-check for unneeded flexibility and recommending its removal. Recovery: preserve minimal smoke tests and self-checks as required safety baselines.
3. **Proposing automated code modifications** — Attempting to rewrite or patch the code directly during a ponytail review instead of providing the required one-line summaries. Recovery: list findings strictly in the format `L<line>: <tag> <what>. <replacement>.` and leave implementation to the developer.
4. **Inventing custom tags outside the defined set** — Using non-standard tags like `bloat:`, `refactor:`, or `clean:` which break review parsers. Recovery: stick strictly to the five defined tags (`delete:`, `stdlib:`, `native:`, `yagni:`, `shrink:`).
5. **Omitting the net savings metric** — Failing to conclude the review with the `net: -<N> lines possible` score or the required "Lean already. Ship." statement. Recovery: always compute and append the final line count metric.
