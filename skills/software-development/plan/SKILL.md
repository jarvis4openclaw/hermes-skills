---
name: plan
description: "Plan mode: write markdown plan to .hermes/plans/, no exec."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow]
    related_skills: [writing-plans, subagent-driven-development]
    trigger_conditions:
      - "/plan"
      - "plan this out"
      - "write a plan for"
      - "create a plan"
      - "plan mode"
      - "don't execute yet"
      - "just plan"
      - "what's the plan for"
      - "how would you approach"
      - "design document for"
---

# Plan Mode

Use this skill when the user wants a plan instead of execution.

## Core behavior

For this turn, you are planning only.

- Do not implement code.
- Do not edit project files except the plan markdown file.
- Do not run mutating terminal commands, commit, push, or perform external actions.
- You may inspect the repo or other context with read-only commands/tools when needed.
- Your deliverable is a markdown plan saved inside the active workspace under `.hermes/plans/`.

## When to Use

- User explicitly says "plan this", "don't execute", "just plan", or uses `/plan`
- Before starting a complex multi-step implementation
- When the user wants to review the approach before any code is written
- When the task is ambiguous and needs scoping before execution

## Not For

- **Writing implementation plans with task breakdowns** → use `writing-plans` skill (produces detailed task-by-task plans with code)
- **Throwaway experiments** → use `spike` skill
- **Direct execution** — this skill produces a plan document only, no code runs
- **Quick questions** — if the user just wants a brief answer, don't create a full plan document

## Output requirements

Write a markdown plan that is concrete and actionable.

Include, when relevant:
- Goal
- Current context / assumptions
- Proposed approach
- Step-by-step plan
- Files likely to change
- Tests / validation
- Risks, tradeoffs, and open questions

If the task is code-related, include exact file paths, likely test targets, and verification steps.

## Save location

Save the plan with `write_file` under:
- `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

Treat that as relative to the active working directory / backend workspace. Hermes file tools are backend-aware, so using this relative path keeps the plan with the workspace on local, docker, ssh, modal, and daytona backends.

If the runtime provides a specific target path, use that exact path.
If not, create a sensible timestamped filename yourself under `.hermes/plans/`.

## Interaction style

- If the request is clear enough, write the plan directly.
- If no explicit instruction accompanies `/plan`, infer the task from the current conversation context.
- If it is genuinely underspecified, ask a brief clarifying question instead of guessing.
- After saving the plan, reply briefly with what you planned and the saved path.

## Pitfalls

- **Executing instead of planning** — this is a READ-ONLY mode. Do not run builds, tests, or mutating commands. Only read files and write the plan document.
- **Over-planning** — if the task is simple (single file, <10 lines), a plan is overkill. Just note the approach briefly.
- **Wrong save location** — always save to `.hermes/plans/` relative to the workspace root, not to an arbitrary path.
- **Missing timestamp** — always include a timestamp in the filename to avoid overwriting previous plans.
- **Confusing with writing-plans** — `writing-plans` produces detailed implementation plans with bite-sized tasks and complete code. This skill produces higher-level design/approach documents. Use the right one for the job.
- **Not asking when underspecified** — if the `/plan` command comes with no context and no recent conversation to infer from, ask what to plan rather than guessing.
