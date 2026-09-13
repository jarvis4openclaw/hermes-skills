---
name: slowbooks-dev
description: "Use when developing or QA-testing the SlowBooks codebase."
version: 1.1.0
metadata:
  hermes:
    tags: [slowbooks, development, fastapi, ai-provider, pr, github, qa, pytest]
    related_skills: [slowbooks-api, github, ssh-file-deploy]
    trigger_conditions:
      - "slowbooks"
      - "SlowBooks Pro"
      - "develop slowbooks"
      - "slowbooks service"
      - "CT 120 slowbooks"
      - "slowbooks pytest"
      - "add an AI provider to slowbooks"
      - "slowbooks AI Insights"
      - "slowbooks PR"
      - "slowbooks fork workflow"
      - "slowbooks exit 137 / OOM"
      - "chunked QA runner"
      - "slowbooks codebase layout"
---

# SlowBooks Pro — codebase development & contribution

Development/contribution workflow for the SlowBooks Pro 2026 codebase (VonHoltenCodes/SlowBooks-Pro-2026), complementing the API-operation skill.

## When to Use

- You are about to change code in the SlowBooks Pro 2026 codebase (`VonHoltenCodes/SlowBooks-Pro-2026`) on CT 120.
- You need the codebase layout, service wiring, or venv/systemd facts before editing — which process runs, which interpreter to use, whether a restart is needed.
- You are adding or fixing an **AI Insights provider** (`PROVIDERS` dict, `build_request()`/`parse_response()`, `settings` keys, `settings.js` dropdown).
- You are preparing a **fork + PR** to upstream and need the required PR-template section headings.
- You are running the **full pytest suite** on the 1 GB CT and need the chunked pattern so it does not OOM.
- You hit **`git` "dubious ownership"** on the CT because SSH runs as `root` while the repo is owned by `wahid`.
- You are diagnosing a slowbooks service symptom in `journalctl -u slowbooks` after a file edit.

## Not For

- **Operating the running SlowBooks service via its HTTP API** (settings, analytics endpoints, payload shapes) → use `slowbooks-api` instead
- **Moving files onto or off the CT** over SSH/scp with verification → use `ssh-file-deploy` instead
- **Generic GitHub PR mechanics** (review workflow, `gh` CLI auth, merge policy) → use `github` instead
- **Surveying an unfamiliar repo's structure without touching it** → use `codebase-inspection` instead
- **Requesting or giving a code review on the diff** → use `requesting-code-review` instead
- **Deploying a finished app to a proxy-fronted host** → use `self-hosted-app-deployment` instead

## Codebase layout & services

- Lives on CT 120 (192.168.100.50) at `/home/wahid/SlowBooks-Pro-2026`, owned by user `wahid`, run as systemd `slowbooks.service` with `.venv/bin/python run.py`.
- **The service auto-reloads on file changes** — `run.py` runs uvicorn with WatchFiles. Editing a `.py`/`.js` file on disk triggers an automatic reload; check `journalctl -u slowbooks --since '1 hour ago'` for `WatchFiles detected changes ... Reloading...`. No manual restart needed for code edits.
- **Git on the CT as root trips "dubious ownership"** — the repo is owned by `wahid` but SSH runs as root. Fix once: `git config --global --add safe.directory /home/wahid/SlowBooks-Pro-2026`.
- **Use the project venv, not system python**: `.venv/bin/python` has httpx/fastapi/sqlalchemy. Dev/test tools (pytest, black, ruff) come from `requirements-dev.txt` — install with `.venv/bin/pip install -r requirements-dev.txt` if missing.

## AI Insights provider architecture

- Providers live in `app/services/ai_service.py` as a `PROVIDERS` dict of `ProviderSpec` (key, label, default_model, wire_format `openai|anthropic|gemini`, docs_url, free_tier_hint, model_choices, needs_account_id/needs_worker_url/needs_endpoint_url flags).
- `build_request()` constructs the httpx payload per provider; `parse_response()` normalizes the text. **OpenAI-compat providers share a parse branch** — if you add a new OpenAI-compat provider, it MUST be added to that tuple or responses parse to empty and raise `empty response`.
- `validate_worker_url()` is the SSRF guard reused for any user-supplied URL: HTTPS-only, blocks private/loopback/link-local/multicast/reserved, no embedded creds, DNS-rebinding recheck.
- Config lives in the `settings` table under well-known keys (`ai_provider`, `ai_model`, `ai_api_key` Fernet-encrypted, `ai_worker_url`, `ai_endpoint_url`), wired through `app/routes/analytics.py` (`AIConfigUpdate` schema, `_require_provider_extras`, read/write plumbing, 4 call sites).
- UI: `app/static/js/settings.js` renders the provider dropdown from `cfg.providers`, reveals conditional fields via `needs_*` flags, saves through `collectPayload()`.

## Contributing (fork + PR)

- Upstream: VonHoltenCodes/SlowBooks-Pro-2026, `main` protected, code-owner review by @VonHoltenCodes. CI = black/ruff/pytest/CodeQL; must be green before merge.
- Fork workflow: `git remote add fork https://github.com/<you>/SlowBooks-Pro-2026.git && git push -u fork feat/my-topic`, then PR via compare URL or `gh pr create --head <you>:branch`.
- PR template wants: Summary, Changes (bullet list user/developer-visible), Test plan, Screenshots, Security implications, Database changes, Documentation updates, Related issues.
- **PR body template with those exact section headings lives at `references/pr-body-template.md`.**

## QA verification on CT 120 — full suite on a 1 GB box (validated 2026-09-06)

CT 120 has only **1 GB RAM**. Running the whole pytest suite in ONE process OOM-kills it (exit 137, resource ceiling — NOT a test failure). Observed twice: full run died at ~91%, and a run excluding heavy OCR/desktop/upload modules died at ~52%. The suite is ~1881 tests across ~103 `tests/test_*.py` files.

**Working pattern — chunk the suite by file, one process per chunk:**

1. Create a detached worktree at the commit under QA (do NOT touch the live `/home/wahid/SlowBooks-Pro-2026` service checkout):
   `git -C /home/wahid/SlowBooks-Pro-2026 worktree add /home/wahid/qa-<tag> <sha>`
2. Run `scripts/chunked-qa-runner.sh` (8 files per chunk; each chunk is a fresh python process so RSS stays under the ceiling). Copy it to the CT, launch as user `wahid` via `su` + `nohup`, log to `/home/wahid/qa-chunked.log`.
3. Aggregate: sum the per-chunk `N passed` lines; a green run shows `AGGREGATE_RESULT exit=0`, `FAILED_CHUNKS:` empty, `RUNNER_DONE`, and 13/13 `chunk N exit=0` lines. 2026-09-06 validated result: **1881 passed, 0 failed** at head `e3fa2d8` in ~3 min wall.
4. Record the outcome in Mnemosyne before reporting.

Chunk sizing: 8 files kept peak RSS around 400/1024 MB. Larger chunks risk the OOM; smaller chunks just add overhead. Memory check between chunks: `free -m` available should stay well above zero.

**Remote launch approvals:** compound remote commands (`scp … && ssh … 'nohup bash script &'`) hit the interactive approval gate even in a live Telegram session — the first attempt timed out BLOCKED, and only succeeded after the user explicitly approved. Treat a compound remote launch as needing explicit user go-ahead; never blind-retry a blocked one. A single short read-only `ssh` probe passes without approval.

**Git on the CT as root trips "dubious ownership"** for worktrees too — the repo is owned by `wahid`, SSH runs as root. Fix per worktree: `git config --global --add safe.directory /home/wahid/qa-<tag>` (run as the wahid user via `su -s /bin/bash wahid -c '…'`), then `git rev-parse --short HEAD` to confirm the worktree is at the expected commit.

## Pitfalls

1. **Running `python3` instead of the project venv** — system python lacks httpx/fastapi/sqlalchemy, so imports fail in confusing ways. Always `.venv/bin/python`. Dev tools come from `.venv/bin/pip install -r requirements-dev.txt`.
2. **`git` "dubious ownership" on the CT** — the repo is owned by `wahid` but SSH runs as `root`. Fix once with `git config --global --add safe.directory /home/wahid/SlowBooks-Pro-2026`; repeat per worktree for `qa-<tag>` dirs (run as `wahid` via `su -s /bin/bash wahid -c '...'`).
3. **Full pytest run OOM-kills CT 120 (exit 137)** — 1 GB RAM cannot host ~1881 tests in one process. Chunk by file (8 files per chunk, fresh process each) via `scripts/chunked-qa-runner.sh`; peak RSS stayed ~400/1024 MB at that size.
4. **Reading exit 137 as a test failure** — 137 is the OOM killer, not a red test. Confirm with a memory check (`free -m`); a run dying at 91% or 52% is the ceiling, not a regression.
5. **Running QA inside the live service checkout** — use a detached worktree at the commit under QA (`git worktree add /home/wahid/qa-<tag> <sha>`). Editing the live tree triggers WatchFiles reloads mid-run.
6. **Assuming a manual restart is needed after a code edit** — `run.py` runs uvicorn with WatchFiles and auto-reloads. Check `journalctl -u slowbooks --since '1 hour ago'` for `WatchFiles detected changes ... Reloading...` before restarting anything.
7. **Adding an OpenAI-compat provider without wiring the shared parse branch** — OpenAI-compatible providers share one branch in `parse_response()`; a new one not added to that tuple parses to empty and raises `empty response`.
8. **Trusting a provider URL without `validate_worker_url()`** — every user-supplied URL must go through the SSRF guard (HTTPS-only; blocks private/loopback/link-local/multicast/reserved; no embedded creds; DNS-rebinding recheck). Do not hand-roll a lighter check.
9. **Forgetting the four call sites when adding a settings key** — a new config key is only live once wired through `app/routes/analytics.py` (`AIConfigUpdate`, `_require_provider_extras`, read/write plumbing, 4 call sites). Skipping one yields a silently unsaved value.
10. **Blind-retrying a blocked compound remote launch** — `scp … && ssh … 'nohup bash script &'` hits the interactive approval gate. It needs explicit user go-ahead; a single short read-only `ssh` probe passes without approval. Never auto-retry a BLOCKED one.
11. **Launching the runner as root** — start it as user `wahid` (`su` + `nohup`) and log to `/home/wahid/qa-chunked.log`, or file ownership and safe.directory errors cascade.
12. **Calling a QA run green without the aggregate signature** — a valid pass shows `AGGREGATE_RESULT exit=0`, an empty `FAILED_CHUNKS:`, `RUNNER_DONE`, and 13/13 `chunk N exit=0` lines. Also record the outcome in Mnemosyne before reporting the result.

## References

- `references/pr-body-template.md` — exact PR section headings for upstream submissions.
- `references/qa-restamp-2026-09-06.md` — full session detail behind the chunked-QA pattern.
- `scripts/chunked-qa-runner.sh` — 8-files-per-chunk pytest runner for the 1 GB CT.
