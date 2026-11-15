---
name: github-issue-to-pr
description: "Carry a GitHub issue end to end to a tested, verified pull request with honest CI reporting — read the live thread, sweep for duplicates, validate the premise against current code and design intent, fix the whole bug class, prove the regression test bites, then shepherd CI from live evidence. Use when asked to fix an issue, implement a feature request, or take a bug from issue to green CI."
version: 1.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Issues, Coding, Pull-Requests, CI]
    related_skills: [github-issues, github-pr-workflow, github-code-review, github-auth, test-driven-development, requesting-code-review]
    trigger_conditions:
      - "fix issue #123 and open a PR"
      - "implement this GitHub feature request"
      - "take this bug from issue to green CI"
      - "address this issue and open a PR"
      - "work this issue"
      - "close issue #N with a PR"
      - "resolve this GitHub issue"
      - "turn this issue into a pull request"
      - "make the fix for issue #N"
      - "issue to PR"
      - "shepherd the PR to merge"
      - "check the CI on my PR"
      - "land this fix properly"
---

# GitHub Issue to Pull Request

Turn a GitHub issue into a tested, verified PR. This skill owns the end-to-end discipline — premise validation, duplicate sweeps, class-level fixes, and honest CI reporting; the sibling GitHub and development skills own their own mechanics.

## When to Use

- "Fix issue #123 and open a PR."
- "Implement this GitHub feature request."
- "Take this bug from issue to green CI."
- A bug report or feature request that must end in a reviewed, CI-verified pull request.
- You need the duplicate-PR sweep and premise validation done *before* any code is written.
- The fix touches more than one call site and the sibling sites must not be left broken.
- CI is red or flaky and someone must say honestly whether it is your diff or the baseline.

## Not For

- **Reviewing an existing pull request** → use `github-code-review` instead.
- **PR mechanics alone** (branch naming, commit convention, body shape) → use `github-pr-workflow` instead.
- **Filing, labelling or triaging issues** with no code change requested → use `github-issues` instead.
- **A delegated review lane on someone else's PR** → use `open-code-review-delegation` instead.
- **Answering a code question, or exploring a repo with no change requested** — just answer; no branch, no PR.
- **Establishing repo credentials or scopes** → use `github-auth` instead.
- **A multi-hour debugging campaign with no issue attached** → use the debugging skills (`debug-generated-code-errors`); come back here once the fix has an issue to land against.

## Procedure

### 1. Read the live issue — body AND full thread

Use `terminal` to run `gh issue view <N> --comments`. The body is a snapshot from filing time; the newest comments carry the live state: partial fixes already merged, new root-cause analyses, maintainer decisions, or questions directed at you that change the task. Also read repository instructions (`AGENTS.md`, contribution docs) with `read_file`. Done when the currently requested behavior, non-goals, and any unanswered thread questions are known.

### 2. Sweep for existing and duplicate work

Before writing anything, run `gh pr list --search "#<N>" --state all` plus at least two keyword/synonym variants of the symptom (`gh pr list --search "<subsystem> <symptom>" --state open`). Popular issues attract multiple independent fixes; building a duplicate wastes the work and the credit. Also check whether a recent commit already fixed it: `git log --oneline -20 -- <relevant files>`. Done when you know every open PR and recent commit touching this issue, or that none exist.

### 3. Validate the premise against current code — and against design intent

Reproduce the bug or demonstrate the missing behavior on the current default branch with a failing test or fixture, using `search_files` and `read_file` to trace the reported path. Then check the second question: is the "bug" actually deliberate design? Run `git log -p -S "<symbol>"` on the code the issue wants changed and read the original commit's intent — a missing link or restriction is often the feature. Challenge stale or flawed issue prose instead of implementing it blindly. Done when the root cause or feature gap is demonstrated in current code AND the change doesn't fight an intentional design.

### 4. Define acceptance and risk

List acceptance criteria, interfaces, migrations/state changes, compatibility, security/privacy, rollout, and rollback. Map every criterion to a test or explicit verification. Done when review has a finite contract.

### 5. Implement the smallest complete change — and fix the class

Work on an isolated branch or worktree, loading `systematic-debugging` or `test-driven-development` when the bug class calls for them. Add regression tests first, then implement. When the fix is in hand, `search_files` for the same bug shape at sibling call sites and fix the whole class in this PR — an incomplete fix that leaves known siblings broken is worse than none. Every changed line must trace to the issue; no drive-by cleanup. Done when targeted tests pass, the original failure no longer reproduces, and sibling sites are fixed or explicitly ruled out.

### 6. Prove the regression test bites (sabotage run)

Temporarily restore the old behavior of the exact function under test, run the new test, and confirm it FAILS; then restore the fix and confirm it passes. A regression test that passes with and without the fix proves nothing. Done when the test demonstrably fails on pre-fix code.

### 7. Run repository quality gates, then open the PR immediately

Run the formatter, lint, typecheck, and the repo's canonical test entrypoint on affected areas; use `requesting-code-review` on the diff. Then push and open the PR right away — the PR is what dispatches CI, and CI latency is the long pole; do not sit on finished work. Load `github-pr-workflow` for PR mechanics: conventional branch/commit, body linking the issue with problem, approach, tests, risk, and exclusions. Read the PR back and verify head SHA, base, title, and files. Done when the PR exists with the intended diff and CI is running.

### 8. Shepherd CI honestly and close the loop

Inspect live checks and failure logs via `gh pr checks` / `gh run view --log-failed`. Distinguish failures introduced by your diff from pre-existing baseline or infrastructure failures — reproduce on the default branch when unsure, and rerun once only for genuine infra flakes. Never say "green," "merged," or "released" without live evidence of that exact state. When the PR lands, comment on the issue with the PR link and a one-line explanation so the reporter gets a traceable resolution. Done when CI state, remaining blockers, and the issue thread all reflect reality.

## Pitfalls

1. **Coding before reading the issue thread** — The body is a snapshot from filing time; the newest
   comments carry partial fixes already merged, new root-cause analyses and maintainer decisions. Run
   `gh issue view <N> --comments` first, or you will implement a request that has already changed.

2. **Building a duplicate fix** — Popular issues attract several independent PRs. Run
   `gh pr list --search "#<N>" --state all` plus at least two keyword/synonym variants of the symptom,
   and `git log --oneline -20 -- <relevant files>`, before writing anything.

3. **"Fixing" behavior that the original commit shows is intentional design** — A missing link or a
   restriction is often the feature. Run `git log -p -S "<symbol>"` on the code the issue wants
   changed and read the intent; if it conflicts, challenge the issue prose instead of the design.

4. **Fixing a symptom at one call site while sibling sites keep the same bug** — Search for the same
   bug shape at sibling call sites and fix the whole class in this PR, or rule each sibling out
   explicitly in the PR body. A half-fix is worse than none.

5. **Shipping a regression test that also passes without the fix** — Do the sabotage run: temporarily
   restore the old behavior of the exact function under test, confirm the new test FAILS, then restore
   the fix and confirm it passes. Otherwise the test proves nothing.

6. **Claiming "green", "merged" or "released" without live evidence** — Read `gh pr checks` and
   `gh run view --log-failed`. Never restate the intended state; restate the observed one.

7. **Opening a PR with unrun tests or unrelated formatting churn** — Run the formatter, lint, typecheck
   and the repo's canonical test entrypoint on affected areas first. Every changed line must trace to
   the issue; no drive-by cleanup, no reformat sweeps.

8. **Sitting on finished work** — The PR is what dispatches CI and CI latency is the long pole. Push and
   open the PR as soon as the change is verified rather than polishing in a local branch.

9. **Treating a pre-existing baseline or infrastructure failure as yours** — Reproduce the failure on the
   default branch when unsure, distinguish your diff from the baseline, and rerun once only for genuine
   infra flakes. Blanket "flaky test" claims are not acceptable.

10. **Claiming the issue is delivered because a PR exists** — The issue is closed when the PR lands, and
    the reporter needs a traceable resolution. Comment on the issue with the PR link and a one-line
    explanation at that point.

11. **Working on the default branch directly** — Use an isolated branch or worktree, and load
    `systematic-debugging` or `test-driven-development` when the bug class calls for them. A dirty
    default branch makes the PR's diff unreadable and the revert ambiguous.

## Verification

- [ ] Full issue thread read; newest comment state reflected in the plan.
- [ ] Duplicate-PR sweep run with issue number + 2 keyword variants.
- [ ] Premise reproduced on current code; design intent checked via git history.
- [ ] Regression test proven to fail without the fix.
- [ ] Sibling call sites fixed or explicitly ruled out.
- [ ] Every changed line traces to the issue.
- [ ] CI state reported from live evidence only; issue commented with the PR link.
