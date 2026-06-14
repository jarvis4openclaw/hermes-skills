---
name: ponytail-review
version: 1.1.0
description: >
  Code review focused exclusively on over-engineering. Finds what to delete:
  reinvented standard library, unneeded dependencies, speculative abstractions,
  dead flexibility. One line per finding: location, what to cut, what replaces
  it. Use when the user says "review for over-engineering", "what can we
  delete", "is this over-engineered", "simplify review", or invokes
  /ponytail-review. Complements correctness-focused review, this one only
  hunts complexity.
metadata:
  hermes:
    trigger_conditions:
      - "review for over-engineering"
      - "what can we delete"
      - "is this over-engineered"
      - "simplify review"
      - "/ponytail-review"
      - "ponytail review"
      - "find the bloat"
      - "what's unnecessary here"
      - "cut the fat"
      - "is this too complex"
      - "slim this down"
      - "delete dead code"
      - "remove abstractions"
---

Review diffs for unnecessary complexity. One line per finding: location, what
to cut, what replaces it. The diff's best outcome is getting shorter.

## When to Use

- User explicitly asks for an over-engineering review or complexity audit
- User says "what can we delete" or "is this over-engineered"
- After a feature ships and the team wants to simplify before the next sprint
- Reviewing a PR where the diff is large and you suspect bloat
- User invokes `/ponytail-review` or "simplify review"
- Comparing two implementations and the simpler one isn't obvious

## Not For

- **Security vulnerability review** → ponytail-review only hunts complexity; use `code-review` or `requesting-code-review` for security checks
- **Correctness bugs or logic errors** → this skill explicitly excludes correctness; a "yagni" finding that deletes a needed feature is out of scope
- **Performance profiling or optimization** → use benchmarking tools; ponytail-review doesn't measure, it only identifies structural bloat
- **Architecture design review (system-level, multi-service)** → this skill works on code diffs, not system diagrams; use `writing-plans` or `architecture-diagram` for design review
- **Accessibility or compliance auditing** → these are correctness concerns, not complexity; use `code-review` with an accessibility lens
- **Test coverage or test quality review** → ponytail-review doesn't evaluate tests; it may flag a smoke test as bloat (it shouldn't — see Boundaries)

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

Complexity only, correctness bugs, security holes, and performance go to a
normal review pass, not this one. A single smoke test or `assert`-based
self-check is the ponytail minimum, not bloat, never flag it for deletion.
Does not apply the fixes, only lists them.
"stop ponytail-review" or "normal mode": revert to verbose review style.

## Pitfalls

1. **Flagging a smoke test as bloat** — The Boundaries section says "a single smoke test or assert-based self-check is the ponytail minimum, not bloat." But in practice, reviewers see a `test_something()` function and tag it `delete:`. Fix: never flag a single assert-based self-check or `__main__` block for deletion. That's the ponytail minimum, not waste.

2. **YAGNI on a feature the user explicitly requested** — User says "add retry with exponential backoff" and the review says "yagni: retry wrapper, nothing replaces it." That's not YAGNI, that's ignoring a requirement. Fix: YAGNI applies to *unspecified* complexity. If the user asked for it, it's not speculative — even if you think it's overkill.

3. **Missing the `net:` score** — The format requires ending with `net: -N lines possible.` Skipping this makes the review feel incomplete and unactionable. Fix: always compute and report the net line reduction, even if it's 0 (report `Lean already. Ship.`).

4. **Reviewing without a diff** — If the user pastes a code block without a diff, the `L<line>:` format is meaningless. Fix: ask for a diff (`git diff` output) or file+line references before starting the review.

5. **Over-focusing on style over substance** — Flagging variable naming or formatting as "over-engineering" is out of scope. Fix: only flag structural complexity (abstractions, dependencies, dead code), not style preferences.

6. **Applying ponytail-review to test code** — Test code has different complexity tradeoffs; a test helper used by 10 test files is not "yagni: one caller." Fix: when reviewing test files, raise the abstraction threshold — only flag truly single-use test helpers.

7. **Not distinguishing "shrink" from "delete"** — `shrink:` means the same logic in fewer lines (e.g., `dict(zip(keys, values))` vs manual loop). `delete:` means the code is unnecessary. Using `delete:` for a `shrink:` case understates the value. Fix: use the correct tag; `shrink:` preserves behavior, `delete:` removes it.

8. **Reviewing generated/AI code without noting it** — If the diff is clearly AI-generated (boilerplate-heavy, over-abstracted), the review should note this context. Fix: prefix with "AI-generated code pattern detected — high bloat expected" to set expectations.
