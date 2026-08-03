---
name: pattern-reference-workflow
description: Handle "do it like X" requests by examining recent examples before proceeding. Use when the user references a pattern from recent work, says "like you did for X", "like the other recent Y", or asks to follow an established format.
version: 1.1.0
metadata:
  hermes:
    tags: [workflow, pattern-matching, user-correction]
    trigger_conditions:
      - "do it like X"
      - "like you did for X"
      - "like you did before"
      - "like the other recent X posts"
      - "same format as the last one"
      - "follow the pattern from"
      - "use the same structure as"
      - "replicate the format of"
      - "the way you did for [specific example]"
      - "like the recent X"
      - "reference the last X"
      - "match the previous format"
      - "copy the structure of the last X"
---

# Pattern Reference Workflow

When the user says "do it like X" or "like you did for Y", they're referencing a pattern from recent work. Don't guess the format — examine recent examples first.

## When to Use

- The user references a pattern from recent work ("like you did for X", "like the other recent Y")
- The user asks to follow an established format ("same format as the last one")
- You must create a database entry, page, post, or file that matches a prior artifact's structure
- A user says "the way you did for [specific example]" and you're tempted to reconstruct from memory
- Cross-session work where the pattern may have evolved since you last saw it

## Not For

- **The user gives a fully explicit spec** — no reference to prior work → use the spec directly, no pattern hunt needed.
- **The reference is to a sibling skill's behavior** (e.g. "review like ponytail") → use \`ponytail-review\` instead.
- **Fresh one-off tasks with no prior artifact** — there is nothing to examine; guessing a "standard" format is acceptable and expected.
- **The user references a documented process in a skill** (e.g. "do it like the health report") → load that skill (\`weekly-health-report\`) instead of mining sessions.
- **Format changes the user explicitly declares** ("this time make it different") — follow the new instruction, not the old pattern.

## Workflow

1. **Identify the reference**: What specific example is the user pointing to?
   - "like you did for PDFs / Gumroad"
   - "like the other recent X posts"
   - "same format as the last one"

2. **Examine recent examples**: Look at the actual recent work to understand the exact format
   - Check database entries, files, or outputs from recent sessions (`session_search` on the referenced topic)
   - Note the specific properties, structure, and format used
   - Don't assume you remember — verify against actual examples
   - Prefer 2–3 instances over a single one: one example can be an outlier

3. **Apply the pattern**: Replicate the exact format from the examples
   - Match all properties and fields
   - Follow the same structure
   - Use the same naming conventions
   - Preserve relations/links the example shows (e.g. a Buckets relation to a parent database)

## Example

User: "Save these prompts to Notion like you did for the other recent X posts"

Wrong approach:
- Guess that it should be a Notion page
- Create a child page under the Pepper bucket
- Forget to set specific properties

Right approach:
- Check recent Notion entries (PDFs / Gumroad, Faceless YouTube Shorts, etc.)
- See they're database entries in the Ideas database
- Note they link to Pepper via Buckets relation
- Note they set the Source URL property
- Replicate this exact format

## Pitfalls

1. **Guessing the format instead of checking** — you might remember wrong, or the format might have evolved. Recovery: always `session_search` the referenced topic or inspect the actual artifact before writing.
2. **Applying a generic pattern when a specific one exists** — "database entry" is generic, but the exact database, properties, and relations matter. Recovery: locate the exact database/collection the prior examples used and replicate its schema.
3. **Not verifying against recent examples** — always check 2-3 recent instances to confirm the pattern. Recovery: if you can't find examples, say so instead of inventing a format.
4. **Copying the pattern but missing relations/links** — the prior entries linked to a parent (e.g. Buckets relation); a replica without the link is silently wrong. Recovery: enumerate the example's full property set, including relation fields.
5. **Assuming the pattern hasn't changed** — a format from months ago may differ from last week's. Recovery: use the most recent examples, not the first one you remember.
6. **Over-applying the pattern** — when the user's new item differs (different category, different destination), force-fitting the old shape breaks it. Recovery: adapt fields that don't apply; note the deviation to the user.
7. **Confusing "like X" with "review X"** — "review it like you did for Y" asks for a review approach, not artifact replication. Recovery: check what the user wants produced before mining formats.

## When This Applies

This pattern applies whenever the user references recent work:
- "Format it like the last email you wrote"
- "Use the same structure as that report"
- "Follow the pattern from yesterday's analysis"
- "Do it the way you did for [specific example]"

Always examine the referenced examples before proceeding.
