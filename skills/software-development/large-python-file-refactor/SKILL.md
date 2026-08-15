---
name: large-python-file-refactor
description: Refactor large Python files via shared-module extraction. Use when a 2000+ line file (often a Lambda handler) needs bulk mechanical edits — extract functions to a shared module, rename symbols, or thread parameters across many call sites with a single in-memory script.
category: software-development
version: 1.1.0
metadata:
  hermes:
    tags: [refactor, python, lambda, shared-module, bulk-edit, dedup]
    trigger_conditions:
      - "refactor a 2000+ line python file"
      - "extract duplicated functions from two files"
      - "rewire callers to import from a shared module"
      - "remove a block of functions and replace with imports"
      - "rename a symbol across dozens of call sites"
      - "add a parameter and thread it through all call sites"
      - "monolithic lambda handler refactor"
      - "shared module extraction for python"
      - "bulk mechanical edit without patch tool"
---

# Large Python File Refactor

## When to Use

- You have a 2000+ line Python file (often an AWS Lambda handler or a monolithic
  module) and need to make a structural change that touches many call sites:

- Extract duplicated functions from two+ files into a shared module, then rewire
  both callers to import from it (the most common trigger).
- Remove a block of function/class definitions and replace them with imports.
- Rename a symbol across dozens of call sites.
- Add a parameter to a function and thread it through all call sites.

**Do NOT use the `patch` tool for this.** At 50+ call sites and 5000-line files,
patch calls are slow, fragile (fuzzy matching drifts), and you lose track of
state. Instead, write ONE Python script that reads the file, transforms it
in-memory, and writes it back. See `references/bulk-refactor-script-pattern.md`
for a reusable skeleton.

## Not For

- **A single surgical one-line fix or a handful of edits** (≤ ~10 call sites) → use the `patch` tool directly
- **Extraction where the duplicate analysis (AST dead-code proof, canonical-version reconciliation) is the main work** → use `shared-module-extraction`
- **Refactoring non-Python code** — this skill's three-pass script pattern and block detection are Python-specific
- **Deploying/terraform work after the refactor** (Lambda layer builds, env bootstrap) → use `terraform-aws-env-bootstrap` and `opc-algo`

## Core principle

> For edits touching >~10 call sites or spanning >~500 lines, prefer a single
> in-memory Python script over chained patch calls. Patch is for surgical,
> unique, one-or-few edits; scripts are for bulk, mechanical, repetitive edits.

## Workflow

1. **Read the full file as raw text with `terminal` + Python `open()`, NOT the
   `read_file` tool.** `read_file` injects `LINE|content` prefixes and truncates
   at ~100K chars per call — useless for in-memory processing. A one-liner
   `python3 -c "open(path).read()"` (or a script file) gives you clean bytes.
   See the read_file gotcha in Pitfalls.

2. **Map the work into three idempotent passes over the lines:**
   - **Pass A — alias / rename calls.** Replace `old_func(` → `new_func(` for
     every call site. Skip `def`/`class` lines in this pass (handle them in
     Pass C). This avoids mangling the very definitions you're about to remove.
   - **Pass B — parameter threading.** Apply a regex
     (`re.sub(r'_shared_func\(([^)]*)\)', add_param, line)`) to append a kwarg
     (`_config_secret=_config_secret`) to calls. Guard against double-adding by
     checking the kwarg isn't already present.
   - **Pass C — block removal.** Delete the `def`/`class` blocks you're
     extracting. See Block-aware removal below.

3. **Write the file back** with `open(path, 'w').write('\n'.join(lines))`.

4. **Verify** (do not skip — see Verification below):
   - `python3 -m py_compile <file>` — catches syntax errors.
   - Targeted regex checks that removed defs are gone and aliases are present.

## Block-aware function/class removal

Do NOT slice by line number — they shift as you edit. Detect blocks by
indentation instead:

- A block starts at a `def name(` or `class Name(` line at indent `N`.
- It ends at the first subsequent line whose indent `<= N` AND is a real
  statement (not blank, not a comment). Blank lines and comments belong to the
  block they follow.
- Optionally also swallow the single blank line *preceding* the def so you don't
  leave a double blank line. Do NOT swallow blank lines *after* the block — the
  next `find_block_end` already consumes the trailing blank as part of its
  boundary check.
- Use a `set` of removed indices so overlapping ranges (preceding-blank vs
  block-body) dedupe cleanly.

See `references/bulk-refactor-script-pattern.md` for the exact algorithm.

## Alias rewiring pattern (shared-module extraction)

When importing a shared function under an alias to avoid colliding with a
locally-removed name, the import looks like:

```python
import sys
sys.path.insert(0, '/var/task')   # Lambda unpacks ZIP to /var/task/
from shared.opc_shared import (
    get_secret_json as _shared_get_secret_json,
    get_config_value as _shared_get_config_value,
    normalize_symbol,          # non-aliased: same name, no call-site change
    submit_mleg_order_raw,     # non-aliased
    success_response,
    DecimalEncoder,
    validate_spx_spread as _shared_validate_spx_spread,
)
import shared.opc_shared as _opc_shared
```

Rule: **aliased imports require call-site rewrites** (`get_config_value(` →
`_shared_get_config_value(`); **non-aliased imports need none** (the name is
identical). After import, initialize shared module globals from the caller's
config so lazy singletons work:

```python
_opc_shared.ALPACA_KEY = ALPACA_KEY
_opc_shared.ALPACA_SECRET = ALPACA_SECRET
_opc_shared.prices_table = prices_table   # if the shared func needs it
```

**Keep caller-specific overrides.** If a function's behavior must stay local
(e.g. Entry's `validate_spx_spread` sends Discord alerts via `require_spx_symbol`,
while the shared version is bare), KEEP the local definition and do NOT import
the shared alias for it. The task spec will tell you which to keep — honor it
exactly; removing the wrong one changes alert/trading behavior.

## Parameter passing for shared functions

When a shared function needs context the caller has (e.g. a module-level
`_config_secret`), the shared signature should take it as an optional kwarg:

```python
# shared module
def get_config_value(secret_key, env_name=None, default=None, _config_secret=None):
    if _config_secret is not None:
        return _config_secret[secret_key]
    return os.environ.get(env_name, default) if env_name else default
```

Every caller call site then becomes
`_shared_get_config_value('key', 'ENV', 'default', _config_secret=_config_secret)`.
Apply this in Pass B so indirect callers (a kept helper that itself calls the
shared func) also get the param — but note: a *non-aliased* `get_positive_float_config`
call still routes through the shared module's internal `get_config_value`, which
will see `_config_secret=None` and fall back to env vars. That is a known
behavior tradeoff of the shared-module design; the task spec decides whether to
accept it ("no call-site changes needed" for non-aliased funcs).

## Verification

Run AFTER writing the file:

```bash
python3 -m py_compile <file> && echo SYNTAX_OK
```

Then a regex audit (in a script, after write-back):

- Confirm removed `^def name\(` are absent (`re.search(r'^def name\\(', text, re.M)`.
- Confirm aliases present: `'_shared_get_config_value(' in text`.
- Confirm `_config_secret=` present on every `_shared_get_config_value(` call.
- Confirm keep-overrides still defined (`require_spx_symbol`, local
  `validate_spx_spread`, etc.).
- Confirm `class DecimalEncoder` removed from the caller that now imports it.

## Pitfalls

1. **`read_file` line-number prefixes** — The `read_file` tool returns
   `LINENO|content` and truncates ~100K chars. For in-memory bulk edits, read with
   `terminal`: `python3 -c "open('/path').read()"` or a script file. Don't try to
   `split('|',1)` the read_file output back into clean source — it mangles
   content that legitimately contains `|`.
2. **Regex substring false-positive in verification** — A check for
   `get_config_value(` will MATCH `_shared_get_config_value(...` because the old
   name is a substring of the alias. To detect *un-aliased* raw calls, use a
   lookbehind that excludes the `_shared_` prefix and skip `def` lines:
   `re.finditer(r'(?<!_shared_)get_config_value\(', text)` then ignore spans that
   are `def get_config_value(`. A naive `func + '(' in line` scan reports hundreds
   of false errors — don't trust it; use the lookbehind.
3. **Lookbehind must be fixed-width** — `r'(?<!def |_shared_)'` raises
   `look-behind requires fixed-width pattern` because the alternatives differ in
   length. Use separate anchored checks instead (see Verification above).
4. **Don't remove the wrong override** — KEEP local versions the spec says to keep;
   only remove the exact `def` names listed. After removal, re-grep to prove the
   kept ones survived.
5. **Don't touch `lambda_handler`** — Constraint in these refactors: only extract
   the listed duplicated functions; never modify the handler or unrelated logic.
6. **Double blank lines** — If removal eats both the preceding and trailing blank
   lines, adjacent functions end up with a single blank line between them — which
   is fine. But if your block-end logic is wrong you can get `def` directly
   abutting the previous statement with no separator. Verify visually or with a
   regex for `\n\ndef` gaps.
7. **AST-based tests break when functions are extracted** — Tests that use
   `ast.parse()` + `exec()` to extract specific `FunctionDef` nodes by name
   from the Lambda source will fail with `NameError` after extraction — the
   functions are no longer `FunctionDef` nodes in the file, they're
   `ImportFrom` nodes. The test's `ast.parse` finds zero matching nodes, so
   the extracted `exec` namespace is missing those names. **Fix**: remove the
   extracted function names from the test's `FUNCTION_NAMES` set and provide
   them as inline stubs in the test's `exec` namespace. Since the shared
   functions are pure Python (no boto3/alpaca-py deps), copy the function
   bodies directly into the namespace dict. For functions with external deps
   (like `get_alpaca_client`), the tests don't extract those — they only
   extract the pure functions they actually call. Check which extracted
   functions appear in the test's `FUNCTION_NAMES` set before extraction
   and plan the stub provision.

8. **Shared-globals init ordering (import-time NameError)** — After wiring the
   caller to the shared module, the init block `_opc_shared.SPREAD_WIDTH = SPREAD_WIDTH`
   (or `_opc_shared.ALPACA_KEY = ALPACA_KEY`, etc.) MUST come AFTER the local
   definition it references. If it sits in the early config block and the local
   `SPREAD_WIDTH = get_positive_float_config(...)` is defined later in the file,
   the Lambda fails at import with `NameError: name 'SPREAD_WIDTH' is not defined`.
   The shared module has a safe default (`SPREAD_WIDTH = 1`) so the error only
   surfaces when the init line runs. Fix: remove the assignment from the early
   init block and place it immediately after the local definition. In Lambda,
   this is an INIT_START/init-phase failure (Runtime.Unknown), and the function
   returns 500 with the stack trace pointing at the module level — NOT a handler
   exception. Verify with `python3 -m py_compile` locally (passes) — the ordering
   bug only shows at import/execution time, so also grep that every name in the
   `_opc_shared.X = X` init block is defined ABOVE the init line.
9. **Line numbers shift as you edit** — Never slice blocks by line number from
   the original read; detect block boundaries by indentation in a single
   transform script (see Block-aware removal). Re-reading after each patch call
   is what makes the patch-tool approach slow and error-prone.
10. **Blank-line swallowing asymmetry** — Swallow the single blank line
    *preceding* a removed def, but NOT the one after (the next `find_block_end`
    consumes the trailing blank as part of its boundary). Doing the opposite
    leaves stray double-blank gaps or defs abutting prior statements.
11. **Subagent self-reports are not proof** — If the mechanical edits were
    delegated, re-verify yourself: `py_compile` every touched file, run the
    unit tests, and grep for the removed defs. A subagent claiming "done" can
    leave partial removals that compile but change behavior.

## References

- `references/bulk-refactor-script-pattern.md` — reusable script skeleton with
  the block-detection algorithm, the three-pass transform, and the verification
  regexes. Copy it, adapt `FUNCS_TO_REMOVE` / alias maps, run, verify.
