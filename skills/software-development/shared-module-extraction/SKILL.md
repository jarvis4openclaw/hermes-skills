---
name: shared-module-extraction
description: Extract duplicated functions into a shared module. Use when two+ Python files (typically Lambda handlers) share duplicated or diverged functions and you must prove dead code via AST, reconcile to one canonical version, and wire a shared module with Lambda packaging.
category: software-development
version: 1.1.0
metadata:
  hermes:
    tags: [refactor, shared-module, deduplication, lambda, python, ast, dead-code]
    trigger_conditions:
      - "extract duplicated functions into a shared module"
      - "deduplicate code between two lambda handlers"
      - "refactor monolithic python file"
      - "remove dead code safely"
      - "two files have the same functions that diverged"
      - "shared module for lambda"
      - "AST dead-code proof"
      - "reconcile diverged function copies"
      - "canonical version of duplicated functions"
---

# Shared Module Extraction

Safely extract duplicated functions from monolithic Python files (especially
Lambda handlers) into a shared module. Covers dead-code verification via AST,
canonical-version reconciliation for diverged copies, subagent delegation for
mechanical edits, the AST-based-test breakage pattern, and Lambda packaging.

## When to Use
- Two Lambda/handler files share duplicated functions (8+ identical + diverged)
- User asks to "proceed with shared module extraction"
- Monolithic 3-6k-line Python files with 90-120 top-level functions
- Dead-code removal where you must PROVE a function is unreferenced before deleting

## Not For

- **The bulk mechanical rewire of many call sites** (three-pass script transform, alias rewiring) → use `large-python-file-refactor`
- **Day-to-day OPC-Algo operations or deployments** → use `opc-algo`
- **Bootstrapping a fresh AWS env/account** (S3 backend, module validation, Lambda Layer builds) → use `terraform-aws-env-bootstrap`
- **Refactoring without duplicate analysis** — if you're not proving dead code or reconciling diverged copies, a simpler refactor skill applies

## 1. Prove dead code with AST, not grep alone
Use `ast.parse` + `ast.walk` to:
- Count references per function (`len(re.findall(r'\b'+name+r'\b', content))` — 1 occurrence = only the def line = likely dead)
- Find duplicate definitions across files (`Counter(all_funcs)`); `ast.dump` equality distinguishes IDENTICAL vs DIVERGED copies
- Detect string-based dispatch: check for `getattr(`, `globals()['name']`, `eval(`, `exec(` — many calls are object-attribute access, not dynamic dispatch
- Cross-file check: a function may be "dead" in one file but called from the other — always search BOTH files

Only remove after verifying: no call site, no string dispatch, no getattr/globals() reference, no cross-file call.

## 2. Reconcile diverged copies to ONE canonical version
When the same function exists in both files with different bodies:
- **normalize/parse functions**: the version handling MORE input shapes wins (e.g. enum-like strings, exchange prefixes, bare numeric timeframes)
- **error-propagation**: the version that re-raises/logs wins over the one that swallows
- **raw HTTP fallbacks**: the version with more complete response object wins
- **stateful clients** (`get_alpaca_client`): identical except docstrings — pick either
- A function that calls a file-specific helper (e.g. sends Discord alerts) is NOT shared — keep it local, put only the pure logic in the shared module
- If a function is dead in BOTH files or dead in one and duplicated in the other, DELETE rather than share

## 3. Shared module shape
- `opc-code/shared/__init__.py` — package marker
- `opc-code/shared/opc_shared.py` — the functions + any shared class (e.g. DecimalEncoder)
- Module-level globals pattern for stateful deps: shared module declares `ALPACA_KEY = None`, `prices_table = None`, `_alpaca_client = None`; the CALLING file sets `_opc_shared.ALPACA_KEY = ALPACA_KEY` etc. after its own config init
- Aliased imports for stateful/context-dependent functions: `from shared.opc_shared import get_config_value as _shared_get_config_value` — then replace all call sites with the alias, passing the caller's local context (`_config_secret`)

## 4. Lambda packaging (Terraform archive_file)
The `archive_file` data source must add the shared module:
```hcl
source {
  content  = file("${path.module}/../../../opc-code/shared/opc_shared.py")
  filename = "shared/opc_shared.py"
}
source {
  content  = ""
  filename = "shared/__init__.py"
}
```
Verify the relative path with `realpath --relative-to=.` from the module dir — it is often 3 levels up, not 2.

In the Lambda source, the import must be discoverable at runtime:
```python
import sys
sys.path.insert(0, '/var/task')   # Lambda unpacks ZIP here
from shared.opc_shared import (...)
```

## 5. AST-based tests WILL break — fix the extraction
If tests extract functions from the Lambda source via `ast.parse` + `exec` into a namespace of fakes (a common pattern to avoid importing boto3/alpaca-py), extracting functions to the shared module breaks them with `NameError: name 'parse_occ_symbol' is not defined`.

Fix: remove the extracted names from the test's `FUNCTION_NAMES` set, and provide the pure-Python implementations directly in the test's `exec` namespace (copy the shared function body into a stub). The test cannot import the shared module because it depends on Lambda-layer packages.

## 6. Subagent delegation for the mechanical edits
For 15+ function removals across 2 large files, delegate the mechanical work with a precise prompt:
- List EXACT functions to remove per file
- List which to KEEP (file-specific wrappers like validate_spx_spread with Discord alerts)
- Specify the import block, globals init block, and alias call-site replacements verbatim
- Constrain: no logic changes, don't touch lambda_handler, no new backups, run py_compile after
- Verify the subagent's result yourself afterward (compile + tests) — subagent self-reports are not proof

## 7. Verification checklist
- `python3 -m py_compile` on all touched files
- Existing unit tests still pass (after fixing AST extraction per step 5)
- Bundle/CI verification scripts still pass
- `git diff --check` for whitespace
- Before/after line counts: expect the shared module to be smaller than the sum of deletions

## Pitfalls
1. **Deleting without cross-file check** — a function "dead" in one file may be called from the other — search BOTH.
2. **String dispatch false confidence** — `getattr(`, `globals()`, `eval()` in a file doesn't mean a specific function is dispatched dynamically — check the actual argument.
3. **Sharing a file-specific function** — if a function calls a Discord/alert helper only one file has, keep it local.
4. **Forgetting `data.aws_region.current`** (adjacent Terraform fix) — see terraform-aws-env-bootstrap skill.
5. **Partial patch left orphaned body** — when deleting a large function, a failed replace leaves the body indented under the next def — always re-read the full extent before patching, and py_compile after.
6. **Test namespace drift** — after extraction, AST tests silently lose access to shared helpers — run them, don't assume.
7. **`find_skill`-style name mismatch in automation** — if a script/CLI tries to locate this skill by a category-prefixed name (e.g. `software-development/shared-module-extraction`), it may fail; the canonical short name is `shared-module-extraction`. Use the short form.
8. **Reference path drift** — skills that point at `references/...` files must keep the referenced file in-tree. If you move or delete a reference (e.g. `bulk-refactor-script-pattern.md`), the skill silently loses a loadable file — check `skill_view` linked_files after edits.
