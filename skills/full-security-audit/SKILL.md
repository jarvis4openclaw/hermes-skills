---
name: full-security-audit
description: "Run a full application-wide security audit end to end — Cloudflare's six phases, input-to-sink tracing, adversarial verification, repeated hunting waves — and deliver one standalone HTML report with severity, exact file:line, root cause and remediation patches. Use for an explicit audit or pen-test of an app, not for a one-off security question."
author: Hermes Agent
version: 1.1.0
license: MIT
platforms: [linux, macos, windows]
category: security
metadata:
  hermes:
    tags: [security, audit, vulnerability, pen-test, cloudflare, html, remediation]
    related_skills: [lightning-gift-app, web-quality-audit, github-code-review]
    trigger_conditions:
      - "security audit"
      - "full security audit"
      - "pen-test this codebase"
      - "find vulnerabilities in"
      - "security review report"
      - "audit this app for security"
      - "vulnerability assessment"
      - "run the cloudflare security audit"
      - "trace untrusted input to sinks"
      - "threat model this codebase"
      - "check this repo for security holes"
      - "produce a security findings report"
      - "security audit HTML report"
---
# Full Application Security Audit (HTML)

Runs Cloudflare's six-phase `security-audit-skill` methodology end to end — exhaustive input-to-sink tracing, auth/dependency/config review, adversarial verification, repeated hunting waves — and delivers one standalone HTML report with severity, exact file:line, root cause/attack vector, and concrete remediation patches.

## When to Use

Use for an explicit full application-wide audit or pen-test where the deliverable is an HTML report. Trigger phrases: "security audit", "full security audit", "pen-test this codebase", "find vulnerabilities in ...", "security review report".

## Not For

- **A quick security question or a single finding to triage** — answer it directly; the six-phase workflow and its artifacts are the wrong instrument. If the request could mean either, ask one focused question first.
- **A quality, performance or accessibility review of a front end** → use `web-quality-audit` instead.
- **Reviewing a pull request's diff for correctness** → use `github-code-review` or `open-code-review-delegation` instead.
- **A general SDLC or design review with no adversary model** → use `sdlc-review` instead.
- **Fixing the findings** — this skill's remediation loop runs only with explicit authorization to modify the target. Otherwise report and stop.
- **Auditing a running deployment you were not asked to audit** — never point the methodology at live third-party systems, real users, or paid APIs.
- **A build/deploy or homelab incident** → use the relevant `devops/*` skill; there is no attack boundary to trace.

## Non-negotiables

1. **The deliverable is HTML.** One standalone `.html` file, no external assets, inline CSS, readable in a browser and on print. JSON and Markdown are intermediate artifacts; the HTML report is what the user receives.
2. **Follow the Cloudflare methodology strictly.** Use `cloudflare/security-audit-skill` in **full-audit mode**: all six phases in order, the coverage ledger, `findings.json`, `report-schema.json`, and both validators. Do not invent a lighter process. If the repo cannot be fetched, follow the encoded fallback in `references/methodology-fallback.md` and say so in the report.
3. **Exhaustively trace untrusted input to execution sinks.** Every request parameter, header, cookie, body field, URL segment, webhook payload, file upload, environment value, and third-party response must be followed to its sink: SQL/ORM, shell, filesystem, HTML/DOM, template engine, log, outbound HTTP, crypto, wallet/RPC call. No "looks fine" without a trace.
4. **Inspect all auth and access controls.** Session/token issuance and revocation, role and ownership checks, tenant isolation, admin surfaces, CSRF, CORS, rate limits, 2FA/login flows, password reset, API keys, webhook signatures. For each, name the control and the bypass you tried.
5. **Inspect dependencies and configurations.** Lockfile advisories against the actual runtime (musl vs glibc, container base, build vs runtime deps), Docker/compose, reverse proxy, CSP/security headers, secrets handling, file permissions, CI/release configuration. A CVE that cannot execute in this deployment is a note, not a finding; say why.
6. **Verify every finding adversarially.** The agent that found a candidate must not be the one that confirms it. A fresh verifier tries to disprove it against source and bounded local evidence. Only verified records get severity.
7. **When you think you have found all vulnerabilities: you have not.** Run another hunting wave. Use coverage critics, re-read prior ledgers and findings, target gaps and changed source. Stop only when a clean coverage-critic pass finds no new units, or record `run_status: "incomplete"` with the exact reason. A single pass typically finds about half of what repeated passes find.
8. **Every reported vulnerability carries four fields:** (1) severity, (2) exact file and line location (`path/to/file.ext:123`), (3) root cause and attack vector (the boundary crossed, the principal, the preconditions, the concrete result), and (4) a concrete remediation patch (the invariant to enforce, the narrowest source change, and a regression test). Generic "sanitize inputs" advice is not a patch.

## Setup

1. Resolve and record: target repo root, repo name, source ref (commit + dirty state), output directory (outside the target by default), profile (`quick`/`standard`/`deep`; default `standard`), scope paths, and budget if set.
2. Obtain the methodology. Prefer an installed copy; otherwise `git clone https://github.com/cloudflare/security-audit-skill` into a scratch directory. Record the resolved commit SHA in `run-metadata.json`. Read `SKILL.md`, `RECONNAISSANCE.md`, `HUNTING.md`, `ATTACK-CLASSES.md`, `VALIDATION-AND-REPORTING.md`, and the domain companions that match the target. Run the validators with `node`.
3. Read prior runs first. If `coverage-ledger.json` or `findings.json` exist from earlier runs, read them before planning. Compare current source with prior records; carry forward only unchanged, still-valid `confirmed` records; create current revalidation units for changed source; never treat prior states as coverage of current work.
4. Write `run-metadata.json` before delegation. The parent owns all shared files; hunters and verifiers write only to their assigned `scratch/`; retained `artifacts/` are parent-promoted. Use the platform's delegation mechanism for isolated roles; if unavailable, run each role as a separate fresh process with no shared chat context and keep role isolation explicit in the artifacts.

## Workflow

Run the six phases in order. Do not stop mid-phase.

| Phase | What happens | Required output |
|---|---|---|
| 1. Reconnaissance | Map architecture, trust boundaries, input surfaces, build/run paths, prior evidence; seed deterministic coverage units. | `architecture.md`, `coverage-ledger.json`; run `validate-coverage-ledger.cjs` |
| 2. Coverage-led hunting | Assign isolated hunters per ledger unit. Each records checks and structured candidates. Run coverage critics after each wave; feed gaps into the next wave. Repeat until a clean critic pass or honest incomplete status. | candidate records; updated ledger |
| 3. Candidate validation | Deduplicate by fingerprint. Give every candidate to a fresh verifier that tries to disprove it. Verdicts: `confirmed`, `needs_validation`, `rejected`. | validated records |
| 4. Structured output | Write all records to `findings.json`; validate against `report-schema.json` with `validate-findings.cjs`; validate the coverage claim with `validate-coverage-ledger.cjs`. | valid `findings.json`, valid ledger |
| 5. Independent verification | Fresh agents verify final source claims. Material replacements get another independent verifier. Re-run the findings validator after every replacement. | verified records; validator pass |
| 6. HTML report | Derive the report from the verified records only. Write one standalone HTML file. Never let prose and JSON disagree. | the HTML deliverable |

## HTML report requirements

Use `references/html-report-template.md` as the structural and CSS baseline. At minimum the report contains:

- **Header/meta:** target, repo, commit/ref, dirty state, date, run ID, profile, scope, methodology commit, validator results.
- **Executive summary:** counts by severity and status; one-line scope/coverage statement; explicit statement of what was *not* covered.
- **Findings summary table:** ID, severity, status, title, file:line.
- **Per-finding cards** in severity order. Each card must show:
  - severity badge and status (`confirmed`, `needs_validation`, `rejected`);
  - exact `path/to/file.ext:line` (repo-relative; include the symbol/function);
  - root cause and attack vector: lower-trust principal, input, intended control, boundary crossed, affected resource, concrete result;
  - remediation patch: invariant, narrowest change, diff or code snippet, regression test;
  - evidence: source trace and bounded local reproduction; state clearly when no dynamic evidence was possible.
- **Needs-validation section:** no severity; the exact unresolved fact; the safe validation plan. Never inflate these into confirmed findings.
- **Rejected candidates:** what was disproved and why, so the next run does not repeat it.
- **Coverage ledger summary:** units planned/covered/deferred/out-of-scope, critic passes, prior-run carry-forward.
- **Remediation status dashboard** (only after fixes are applied): per-finding FIXED/KEPT/DEFERRED/CLOSED, commit SHA, verification evidence.
- **Audited surfaces confirmed clean (selected negatives):** short list of high-risk surfaces checked and found clean, with the check performed.

Rules for the HTML:

- Single file, no CDN fonts/scripts/images; inline CSS; semantic HTML; sufficient contrast; prints without loss.
- Escape all target-derived strings. A report about injection must not itself be injectable.
- Back up an existing report before overwriting: `cp report.html report.html.bak-$(date +%Y%m%d-%H%M%S)`.
- If the target lives in the wiki, save the final report under `~/wiki/projects/` with a descriptive name and update the wiki sync; keep the prior backup.
- State `run_status` and coverage honestly. An incomplete audit must say so at the top.

## Remediation loop (only when asked to fix)

After the audit report exists, and only with authorization to modify the target:

1. Create a branch. Apply the smallest effective patch for each accepted finding; do not batch unrelated refactors.
2. Run the project's tests and the specific regression test added for each finding. A fix without a failing-then-passing test is unverified.
3. Re-run the audit as a **scoped run** on the diff (Cloudflare scoped mode), plus targeted probes for each fixed finding. Record the commands and observed results.
4. Update the HTML report's remediation dashboard: per-finding status, commit SHA, evidence. Back up the prior HTML first.
5. Deploy only when the user authorizes it. After deployment, re-check the live behavior and record the result. If deployment is not authorized or not possible, say "fixed in source, not deployed" — never "fixed" without the distinction.
6. If a fix changes behavior in a way that invalidates a prior finding's evidence, re-open it rather than silently dropping it.

## Pitfalls

These started as a list of anti-patterns. Each entry now says what goes wrong **and** what to do
instead, because "don't do that" is not recoverable advice at 2am.

1. **Checklist deviation presented as a vulnerability** — A missing header, an absent hardening step,
   or a defense-in-depth gap with no reachable boundary violation is a note, not a finding. Name the
   boundary crossed and the principal who crosses it, or demote it; unproven findings devalue the
   real ones.

2. **Severity attached to a `needs_validation` record** — Treating "needs validation" as "low-confidence
   confirmed" invents a vulnerability the evidence does not support. Strip the severity, state the one
   exact unresolved fact, and give the safe validation plan.

3. **Claiming full coverage after one pass** — A single wave typically finds about half of what repeated
   waves find. Run another wave until a clean coverage-critic pass finds no new units, or record
   `run_status: "incomplete"` with the exact reason at the top of the report.

4. **Probing live or production systems when bounded local evidence suffices** — Never point the
   methodology at shared infrastructure, real users, or paid APIs to prove a point you can prove from
   source. If dynamic evidence is impossible, say so in the finding.

5. **Guessing deployment, proxy, browser or provider behavior that the source does not show** — Mark it
   `needs_validation` with the exact assumption. A guess written as fact becomes a false finding the
   moment someone checks it.

6. **Letting the finder verify its own finding** — Self-verification collapses the two roles and ships
   unverified candidates as confirmed. Every candidate goes to a fresh verifier that tries to disprove
   it; material replacements get another independent verifier.

7. **Letting prose and `findings.json` disagree** — Derive the HTML from the verified records only, and
   re-run `validate-findings.cjs` after any replacement. Two sources of truth means neither is trusted.

8. **Reporting a parser crash or self-impact as a cross-boundary vulnerability** — A crash inside the
   tooling, or an impact only on the reporter, is not a vulnerability of the target. Fix the tool, or
   record it as a tooling note outside the findings list.

9. **Generic remediation advice** — "Validate input" and "use parameterized queries" are not patches.
   Every confirmed finding carries the invariant to enforce, the narrowest source change, and a
   regression test.

10. **Overwriting the report without a backup** — Always `cp report.html
    report.html.bak-$(date +%Y%m%d-%H%M%S)` first. A lost report cannot be regenerated if the run's
    scratch has already been cleaned.

11. **Claiming a fix is deployed without checking the running system** — After an authorized fix,
    re-check live behavior and record the result, or say **"fixed in source, not deployed"**. The
    distinction is the difference between a report and a lie.

12. **Stopping because the first wave "feels complete"** — That feeling is the trigger for the next
    wave, not the end of the run. Re-read the prior ledgers, target the gaps and changed source, then
    launch the coverage critics again.

## Finish checklist

- [ ] Methodology repo commit recorded; six phases completed in order (or `incomplete` with reason).
- [ ] Coverage ledger validator passes; findings validator passes; counts reconcile.
- [ ] Every confirmed finding has severity, file:line, root cause/vector, remediation patch.
- [ ] Every `needs_validation` has no severity and an exact unresolved fact + safe plan.
- [ ] At least one post-clean critic pass confirmed no new units (or the gap is disclosed).
- [ ] HTML is standalone, escaped, backed up if replacing, and opens correctly.
- [ ] Report states what was not covered and whether fixes are deployed or source-only.
- [ ] Prior-run carry-forward and changed-source revalidation are explicit.

## References

- Methodology: https://github.com/cloudflare/security-audit-skill — `skills/security-audit/`
- Report template: `references/html-report-template.md`
- Fallback methodology summary: `references/methodology-fallback.md`
