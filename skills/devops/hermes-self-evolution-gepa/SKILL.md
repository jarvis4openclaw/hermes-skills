---
name: hermes-self-evolution-gepa
description: >
  Run GEPA (Genetic Evolution of Prompt Artifacts) skill optimization cycles on Hermes skills.
  Use when asked to improve skills, run self-evolution, optimize prompts, or audit skill quality.
  The pipeline lives at ~/hermes-agent-self-evolution. DSPy 3.1.3 is installed in its .venv.
version: 1.5.3
metadata:
  hermes:
    tags: [self-evolution, GEPA, DSPy, skills, optimization]
    trigger_conditions:
      - "Run a GEPA / self-evolution cycle"
      - "Optimize skills / audit skill quality"
      - "Improve skill reliability"
---

# Hermes Self-Evolution — GEPA Pipeline

## Environment

- **Repo:** `~/hermes-agent-self-evolution` (NousResearch/hermes-agent-self-evolution on GitHub)
- **Venv:** `/home/wahid/hermes-agent-self-evolution/.venv/bin/python`
- **DSPy version:** 3.1.3 (confirmed installed)
- **Skills source:** `~/.hermes/hermes-agent/` (NousResearch/hermes-agent)
- **Remote:** `https://github.com/NousResearch/hermes-agent-self-evolution.git`

## CLI Usage

```bash
# Dry run — validate setup without API calls
cd ~/hermes-agent-self-evolution && \
/home/wahid/hermes-agent-self-evolution/.venv/bin/python -m evolution.skills.evolve_skill \
  --skill <skill-name> \
  --dry-run

# Full optimization run
/home/wahid/hermes-agent-self-evolution/.venv/bin/python -m evolution.skills.evolve_skill \
  --skill github-pr-workflow \
  --iterations 5 \
  --optimizer-model anthropic/claude-haiku-3-5 \
  --eval-model anthropic/claude-haiku-3-5 \
  --eval-source synthetic
```

**CLI options:**
- `--skill` — skill name (short form, e.g. `github-pr-workflow` — matched by `find_skill()`)
- `--iterations` — GEPA iterations (default: 10; use 5 for fast cycles)
- `--eval-source` — `synthetic` | `golden` | `sessiondb`
- `--optimizer-model` / `--eval-model` — litellm model string
- `--run-tests` — gate on pytest suite (slow, opt-in)
- `--dry-run` — validate without API calls

## Fast Path: Early Exit (Do This First)

Before any expensive work, check if the last cycle already covered this ground:

```python
# 1. Find the most recent self-evolution session
session_search(query="self-evolution cycle", limit=3, sort="newest")

# 2. If the most recent one concluded with [SILENT] (or "No safe improvement found")
#    AND no CLI/user sessions exist since then:
session_search(source="cli", limit=5, sort="newest")

# 3. AND no error/correction sessions exist since then:
session_search(query="error failed correction", limit=5, sort="newest")
```

**If ALL true:** emit `[SILENT]` immediately. Do NOT read SKILLS.md, do NOT run session searches, do NOT load skills. The last cycle already did this work.

**Conditions for early exit:**
- Most recent self-evolution cycle was within the last 24h
- It concluded with `[SILENT]` or "No safe improvement found"
- Zero CLI/user sessions since that cycle
- Zero error/correction sessions since that cycle
- No new skills added since last cycle

This saves 4–6 API calls per redundant cycle. When skills are mature and no user activity is happening, the fast path should trigger 90%+ of the time.

## Step-by-Step Optimization Cycle

Run ONLY if the Fast Path above did NOT trigger.

1. **Select targets** — pick 5 skills. Two heuristics, in priority order:
   - **Delta-driven (preferred):** Find skills modified since the last GEPA cycle. Use `git log --name-only --since="<last-cycle-date>" -- skills/` in the hermes-agent repo first (catches genuine commits). Supplement with `find ~/.hermes/skills/ -name SKILL.md -newer <last-cycle-commit-timestamp-file>` for live-path-only skills. Of the candidates, select the 5 with highest delta potential (missing trigger_conditions + no When to Use + no Not For + <3 pitfalls). This catches skills that changed outside the GEPA pipeline and may have regressed or were never optimized.

   **⚠️ Do NOT use the cycle report file's mtime as the `-newer` reference.** The cycle writes skill files BEFORE the report, so `find -newer <report>` always returns the skills the cycle itself just wrote — false positives. Instead, create a timestamp file at the start of each cycle: `touch /tmp/gepa-cycle-N-start`. Use that as the `-newer` reference. See pitfall #14.
   - **Fallback — word-count-driven:** If no skills were modified since last cycle, pick by word count + trigger frequency. Highest delta potential = missing Pitfalls sections + vague descriptions.
2. **Check API key** — if masked, use LLM-as-Judge fallback (Strategy A: direct parent execution)
3. **Run optimization** — for each skill: read, score baseline, write evolved SKILL.md to live path
4. **Sync to repo** — `cp` evolved files from `~/.hermes/skills/` to `~/.hermes/hermes-agent/skills/`. If the target directory doesn't exist in the repo, create it with `mkdir -p` first. If the file is new (didn't exist in the repo), it will appear as an untracked file — stage it with `git add` before generating patches.
5. **Generate patches** — `git diff` in hermes-agent repo
6. **Write report + metrics** — in `~/hermes-agent-self-evolution/reports/`
7. **Commit both repos** — skill changes in hermes-agent, patches+report in self-evolution
8. **Attempt push** — try `git push` to self-evolution repo; if 403, log branch name in report

## GEPA Scoring Dimensions (0–10 each)

| Dimension | What it measures |
|-----------|----------------|
| `trigger_clarity` | How precisely the `description:` field disambiguates from sibling skills |
| `step_completeness` | Steps numbered, actionable, with exact copy-pasteable commands |
| `pitfall_coverage` | Common failure modes documented |
| `command_accuracy` | Shell commands correct and runnable |
| `reuse_potential` | Generalizes well, no hardcoded personal paths |

## Fallback: LLM-as-Judge (when API unavailable)

When live GEPA fails (API key not accessible), use one of two fallback strategies:

### Strategy A: Direct Parent Execution (PREFERRED)

For 5 skills, the most reliable approach is to write evolved content directly in the parent session:
1. Read each source SKILL.md
2. Score 5 dimensions (0–10)
3. Write evolved SKILL.md with trigger_conditions, When to Use, Not For, and Pitfalls
4. Sync to both paths, generate patches, commit

This avoids subagent timeout risk entirely and is faster for batches of ≤5 skills.

#### The 4-Gap Template (Apply to Every Skill)

When using LLM-as-Judge, the highest-leverage additions are these four standard gaps — proven across 14 cycles to deliver +12–17 points per skill:

| Gap | Where | What | Expected delta |
|-----|-------|------|---------------|
| `trigger_conditions` | YAML frontmatter | 13 phrase-match triggers under `metadata.hermes.trigger_conditions` | +3–4 trigger_clarity |
| `When to Use` | Body (after intro) | 6–8 concrete bullet points of use cases | +2–3 step_completeness |
| `Not For` | Body (after When to Use) | 5–7 entries disambiguating from sibling skills, each with `→ use \`skill-name\` instead` | +2–3 trigger_clarity |
| `Pitfalls` | Body (before References) | 10–12 numbered failure modes, each with bold title, em-dash explanation, and recovery action | +7–9 pitfall_coverage |

**Pitfall format:**
```
1. **Title** — Explanation of what goes wrong. Recovery action. Specific values/fixes.
```

**Trigger format:**
```yaml
trigger_conditions:
  - "phrase the user might say"
  - "another trigger phrase"
```

**When writing Not For entries:** Always reference the actual sibling skill name (check `skills_list`). Each entry must name a real alternative, not a vague category. Pattern: `**Situation** → use \`actual-skill-name\` instead`

**When replacing existing tables:** If the skill already has a "Common Issues" / "Tips" / "Gotchas" table, convert it to numbered pitfalls. Tables signal that pitfalls were an afterthought — numbered items signal they're first-class content.

**Version bump:** Increment patch version (1.0.0 → 1.1.0) for these structural additions. If the skill has no version field, add `version: 1.0.0`.

### Strategy B: Subagent Delegation (use only if parent context is full)

If the parent session context is too large to hold all skill content, delegate to subagents in parallel batches:

- **≤3 skills:** single subagent
- **4–5 skills:** split into 2 parallel tasks (e.g. 3+2) using `delegate_task(tasks=[...])`
- **6+ skills:** 3 parallel tasks of ~2 each

⚠️ **Subagent timeout risk:** Subagents may time out at 600s when asked to read + score + write evolved content for 2+ large skills. If 2 of 3 subagents time out (as observed in cycle 5), fall back to Strategy A for the remaining skills.

Each subagent prompt must:
1. Score 5 dimensions (0–10): `trigger_clarity`, `step_completeness`, `pitfall_coverage`, `command_accuracy`, `reuse_potential`
2. Write a fully evolved SKILL.md with Pitfalls section (5–7 failure modes), trigger_conditions in YAML, When to Use / Not For
3. **Write evolved content directly to the target SKILL.md path** — do NOT write to intermediate JSON files in arbitrary directories
4. Return **JSON only** (parseable) — no markdown wrapper, no preamble

```
goal: "Perform GEPA-style LLM-as-Judge scoring on skills X, Y, Z.
Read full SKILL.md for each from these paths: ...
Score 5 dimensions 0-10. Write fully optimized versions with Pitfalls.
Write evolved SKILL.md directly to the target path for each skill.
Output format: JSON {skill_name: {baseline_scores, evolved_scores, changes_summary}}
IMPORTANT: Output ONLY the JSON. No preamble, No markdown wrapper."
toolsets: ["terminal", "file"]
```

After subagents return (or time out), apply any missing evolved content directly, then sync and commit.

## GitHub Auth (Push to NousResearch)

⚠️ **Known blocker as of 2026-04-10:** All 3 available accounts lack push access:
- `friday-openclaw[bot]` — token invalid (gh auth shows failed)
- `jarvis4openclaw` — 403 on NousResearch org
- `wahidsaleemi` — 403 on NousResearch org

**Fix needed:** Grant push access to one of the above accounts. Until then, commit locally and report the branch name.

```bash
# Switch accounts
gh auth switch --user jarvis4openclaw
gh auth token  # verify

# Push once access is granted
cd ~/hermes-agent-self-evolution
GH_TOKEN=$(gh auth token) git push -u origin <branch>

# Create PR
gh pr create --title "feat: GEPA cycle N — skill optimization" \
  --body "..." --base main
```

## API Key Pitfall in Cron

`~/.hermes/.env` API keys may be **masked** (credential-manager-backed). Diagnose:
```bash
python3 -c "
with open('/home/wahid/.hermes/.env') as f:
    for l in f:
        if 'ANTHROPIC_API_KEY' in l:
            val = l.split('=',1)[1].strip()
            print(f'len={len(val)}, masked={\"***\" in val or len(val) < 20}')
"
```

If masked: store a plaintext service key in `~/.hermes/evolution-creds.env` and source it before running.

## Output Locations

- **Reports:** `~/hermes-agent-self-evolution/reports/gepa_cycle_N_report.md`
- **Metrics JSON:** `~/hermes-agent-self-evolution/reports/gepa_cycle_N_metrics.json`
- **Datasets:** `~/hermes-agent-self-evolution/datasets/skills/<skill-name>/`

## Pitfalls

1. **API key not plaintext in cron** — see section above. Live GEPA needs plaintext key. Fallback to LLM-as-Judge subagent.
2. **Skill name matching** — use the short skill name (e.g. `github-pr-workflow`), not the full path. `find_skill()` searches recursively under `~/.hermes/hermes-agent/skills/`.
3. **`--no-run-tests` doesn't exist** — the flag is `--run-tests` (boolean flag, default off). Don't pass `--no-run-tests`.
4. **Two separate skills directories** — `~/.hermes/hermes-agent/skills/` and `~/.hermes/skills/` have **different inodes** (confirmed cycle 3, 2026-04-12). They are NOT symlinked. The running agent reads from `~/.hermes/skills/` (live path). Always write evolved SKILL.md to the live path first, then sync to the repo path for version control. Pattern:
   ```bash
   # Write to live path first
   write_file(~/.hermes/skills/<path>/SKILL.md, evolved_content)
   # Then sync to repo
   cp ~/.hermes/skills/<path>/SKILL.md ~/.hermes/hermes-agent/skills/<path>/SKILL.md
   ```
5. **NousResearch org push access** — no currently valid account has push rights. Commit locally and surface to Boss with branch name.
6. **Subagent timeout on large content** — Subagents tasked with reading + scoring + writing evolved SKILL.md for 2+ large skills may time out at 600s. If subagents time out, complete the work directly in the parent session. See "Fallback: LLM-as-Judge" section for Strategy A (preferred) vs Strategy B.
7. **Patch generation ordering** — Patches must be generated AFTER syncing evolved content to the repo path. If patches are generated before syncing, they will be empty (0 lines). Always: write live → sync to repo → `git diff` → generate patch.
8. **Stale branch in self-evolution repo** — The self-evolution repo may be checked out to a branch from a previous cycle (e.g. `gepa/phase1-skill-optimization-cycle-3`). Commits made while on the wrong branch will NOT be on the intended cycle-N branch. Always run `git checkout main && git checkout -b gepa/phase1-skill-optimization-cycle-N` BEFORE committing. If you already committed to the wrong branch, use `git cherry-pick` to move the commit to the correct branch.
9. **Skill exists in live path but not in repo path** — Some skills in `~/.hermes/skills/` may not have a corresponding file in `~/.hermes/hermes-agent/skills/`. Before running `cp` to sync, check if the repo target path exists. If the parent directory doesn't exist, create it with `mkdir -p` first. If the file doesn't exist at all in the repo, it will show as a new file in `git diff` — stage it with `git add` before committing. Check with: `test -f ~/.hermes/hermes-agent/skills/<path>/SKILL.md || echo "NEW_FILE"`.
10. **Recursive self-inspection loops** — When browsing recent sessions with `session_search()` or `lcm_load_session()`, the current session may appear in the results. Loading your own session recursively wastes API calls and can spiral. **Guard:** always exclude the current `session_id` from investigation, or rely on `session_search(query=...)` with bookends instead of loading full session transcripts.

11. **Redundant cycles burning API calls** — When the cron runs hourly but nothing has changed since the last cycle, doing full session searches + SKILLS.md reads every time is wasteful. Always run the **Fast Path** check first. If it triggers, emit `[SILENT]` in one step.

12. **Gitignore silently hides skill files** — Some skill directories are listed in `.gitignore` (confirmed: `agent-browser/` at line 35 of hermes-agent's `.gitignore`). When a skill is gitignored, `git diff HEAD -- path` returns 0 lines, `git status` doesn't show the file, and `git ls-files` returns nothing — the file is invisible to git. **Detection:** `git check-ignore -v skills/<path>/SKILL.md` returns the ignore rule if it's gitignored. **Recovery for patches:** use `diff -u /dev/null <path> | tail -n +3` to generate a full-file patch for gitignored files. **Recovery for commits:** gitignored files can't be committed to the hermes-agent repo — note this in the report and track the patch in the self-evolution repo only. The evolved content still lives in `~/.hermes/skills/` (live path) where the running agent reads from it.

13. **`git add -A` in self-evolution repo catches stray files** — The self-evolution repo working directory may accumulate test scripts, scratch files, or debugging artifacts from previous cycles. Running `git add -A` stages these alongside your intentional changes. **Prevention:** before committing in the self-evolution repo, always run `git status --short` and verify only the expected files are staged. Remove strays with `git reset HEAD -- <file>` and `git checkout -- <file>`. Better: use `git add reports/ patches/` to add only the relevant directories instead of `git add -A`.

14. **`find -newer` on the last cycle's report file is a false-positive trap** — The delta-driven heuristic originally used `find ~/.hermes/skills/ -name SKILL.md -newer <last-cycle-report>`. This fails because the cycle writes skill files BEFORE the report — so every skill the cycle evolved shows up as "modified since." **Fix:** at the start of each cycle, `touch /tmp/gepa-cycle-N-start` and use THAT as the `-newer` reference. **Secondary check:** always validate candidates with `git log --name-only --since="<date>" -- skills/` in the hermes-agent repo to confirm which skills had genuine commits (not just cycle writes). The `find` approach catches live-path-only skills that don't exist in the repo; the `git log` approach catches repo-tracked skills with real human commits. Use both.

15. **`execute_code` doesn't expose all Hermes tools** — `session_search`, `memory`, `lcm_grep`, and other Hermes-native tools are NOT importable via `from hermes_tools import ...`. The `execute_code` sandbox only exposes `web_search`, `web_extract`, `read_file`, `write_file`, `search_files`, `patch`, and `terminal`. For programmatic session browsing or memory operations, use direct tool calls instead of `execute_code`. This blocked Cycle 14's attempt at batch `session_search` inside a Python script.

## When to Emit [SILENT]

The self-evolution cron cycle should emit `[SILENT]` (suppress delivery) when **all** of the following are true:

1. **No new session errors** — keyword search for `error failure retry` returns no sessions from the last 24h with undiagnosed issues.
2. **All active skills are current** — skills with "do NOT re-update" or "Adoption Status: awaiting manual action" markers are at their documented version; no version drift.
3. **No user correction in recent sessions** — keyword search for `user correction preference mistake wrong` returns no results.
4. **No new recurring pattern** — the same failure mode hasn't appeared in 2+ sessions since the last evolution that addressed it.

If any condition fails, produce a focused report on that one item. If all pass, emit `[SILENT]` — do not invent an improvement just to have output.

**Anti-pattern to avoid:** Producing a minor report ("No safe improvement found — top blocker: X") when X has been documented for a week and requires only manual operator action. That's noise, not signal. Emit `[SILENT]` instead.

## Manual LLM-as-Judge Cycle (No CLI)

When writing evolved skill content directly (without the CLI pipeline), the repo convention is:

1. **Write evolved SKILL.md** directly to `~/.hermes/skills/<category>/<skill>/SKILL.md` (the live path)
2. **Sync to repo path:** `cp ~/.hermes/skills/<path>/SKILL.md ~/.hermes/hermes-agent/skills/<path>/SKILL.md`. If the target directory doesn't exist in the repo, create it with `mkdir -p` first.
3. **Generate patch files** from the hermes-agent repo. First check if the skill is gitignored: `git check-ignore -v skills/<path>/SKILL.md`. If not ignored AND tracked in HEAD: `git diff HEAD -- skills/<path>/SKILL.md > ~/hermes-agent-self-evolution/patches/<skill>/gepa-cycle-N.patch`. For new files (not in HEAD): stage with `git add skills/<path>/SKILL.md`, then `git diff --cached -- skills/<path>/SKILL.md > ~/hermes-agent-self-evolution/patches/<skill>/gepa-cycle-N.patch`. **Do NOT use `git diff HEAD` for new files** — even after staging, HEAD has no reference to compare against and the diff will be empty. `--cached` compares the staging area against HEAD, which correctly captures additions. For gitignored files: `diff -u /dev/null skills/<path>/SKILL.md | tail -n +3 > ~/hermes-agent-self-evolution/patches/<skill>/gepa-cycle-N.patch`. Gitignored files can't be committed to the hermes-agent repo — track them in the self-evolution repo only.
4. **Create mkdir** for each `patches/<skill>/` dir before writing
5. **Write report** to `~/hermes-agent-self-evolution/reports/gepa_cycle_N_report.md`
6. **Write metrics** to `~/hermes-agent-self-evolution/reports/gepa_cycle_N_metrics.json`
7. **Commit all** (patches + report + metrics) in the self-evolution repo
8. **Commit skill changes** in the hermes-agent repo

The self-evolution repo does NOT track skill files directly — only diffs (patches) and reports. The live skill changes happen in `~/.hermes/skills/` which is the path the running agent actually reads from.
9. **Skill exists in live path but not in repo path** — Some skills in `~/.hermes/skills/` may not have a corresponding file in `~/.hermes/hermes-agent/skills/`. Before running `cp` to sync, check if the repo target path exists. If the parent directory doesn't exist, create it with `mkdir -p` first. If the file doesn't exist at all in the repo, it will show as a new file in `git diff` — stage it with `git add` before committing. Check with: `test -f ~/.hermes/hermes-agent/skills/<path>/SKILL.md || echo "NEW_FILE"`.
