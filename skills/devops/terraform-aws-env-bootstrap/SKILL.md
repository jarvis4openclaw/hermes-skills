---
name: terraform-aws-env-bootstrap
description: Bootstrap a new env/account from an existing Terraform repo. Use when deploying an existing Terraform project to a fresh AWS account, creating the S3 state backend + lock table, extending module env validations, or building a Lambda Layer.
category: devops
version: 1.1.0
metadata:
  hermes:
    tags: [terraform, aws, iac, bootstrap, lambda-layer, environment, backend]
    trigger_conditions:
      - "deploy this to a new AWS account"
      - "create the terraform backend"
      - "add a new environment to an existing terraform repo"
      - "deploy everything to my dev environment"
      - "stand up dev/test infrastructure"
      - "build a lambda layer"
      - "terraform s3 backend setup"
      - "new account bootstrap"
      - "terraform lock table"
      - "dynamodb lock table"
      - "lambda layer build python"
---

# Terraform AWS Environment Bootstrap

Stand up a new environment (dev/test/custom segment) from an existing Terraform
project — including a completely fresh AWS account. Covers S3 state backend
creation, module validation fixes, hardcoded-region remediation, Lambda Layer
builds, and plan/apply verification.

## When to Use
- Deploy an existing Terraform repo to a brand-new AWS account
- Add a new environment segment (e.g. `wahid`, `user1`) to an existing `envs/` structure
- Set up a Terraform S3 backend (state bucket + DynamoDB lock)
- Build a Lambda Layer for a Python serverless project
- User says "deploy everything to my dev environment" / "create the terraform backend"

See `references/opc-agentic-wahid-deployment.md` for a full worked example
(OPC-Algo → Wahid's account, 2026-08-14).

## Prerequisites
- AWS CLI (`aws --version`) and Terraform (`terraform version`) installed
- Credentials file (e.g. `/tmp/aws-creds.env`) with AWS_ACCOUNT_ID, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- `zip`/`unzip` installed for layer builds

## Not For

- **Day-to-day OPC-Algo bot operations** (invoking the deployed Lambdas, secret updates, log checks) → use `opc-algo`
- **Extracting duplicated Lambda functions into a shared module** (AST dead-code proof, canonical reconciliation) → use `shared-module-extraction` / `large-python-file-refactor`
- **Backup coverage decisions for Proxmox VMs/CTs** → use `proxmox-backup-coverage`
- **General Terraform plan/apply on an already-bootstrapped env** — this skill is for the bootstrap itself, not routine drift checks

## 1. Load and verify credentials
```bash
set -a; source /tmp/aws-creds.env; set +a
aws sts get-caller-identity   # confirms account + identity
```
- NEVER echo raw credentials. Redact output with `sed -E 's/(=.*)/=***REDACTED***/'`.
- Check account state first: `aws s3api list-buckets`, `aws dynamodb list-tables` — a fresh account returns empty.

## 2. Create the S3 state backend (once per account)
```bash
BUCKET="<project>-terraform-state-${AWS_ACCOUNT_ID}"
aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
  --create-bucket-configuration LocationConstraint="$AWS_REGION"
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$BUCKET" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration '{"BlockPublicAcls":true,"IgnorePublicAcls":true,"BlockPublicPolicy":true,"RestrictPublicBuckets":true}'
```
Lock table (only if backend uses DynamoDB locking; some repos use S3 native `use_lockfile = true` — check existing env's backend.tf):
```bash
aws dynamodb create-table --table-name <project>-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name <project>-terraform-locks
```

## 3. Survey the existing repo before writing new env files
- Read every module's `variables.tf`: environment validation lists (`contains(["dev","test","prod"], ...)`) must be extended for any new segment.
- Grep the whole tree for hardcoded regions — the classic is IAM CloudWatch log-group ARNs hardcoded to `us-east-2`. Fix with `data.aws_region.current.name` and ADD the `data "aws_region" "current" {}` block (easy to forget — plan fails otherwise).
- Read `envs/<working>/backend.tf` to copy the state bucket/key pattern.
- `dependency-layer.tf` may pin a layer ARN owned by ANOTHER account (e.g. `arn:aws:lambda:us-east-2:159625121587:...`). For a fresh account, instantiate `module.lambda_layer` instead of copying the pin.
- Note module outputs used by the env (`function_arn`, `function_url`, `layer_arn`, `all_table_arns`).

## 4. Extend module validation lists
Patch all modules (dynamodb, eventbridge, iam, lambda, lambda-layer, secrets):
`["dev", "test", "prod"]` → `["dev", "test", "prod", "<new-segment>"]`

## 5. Build the Lambda Layer (Python serverless)
See `references/lambda-layer-build-recipe.md` for the full recipe. Critical points:
- Install with `--platform manylinux2014_x86_64 --implementation cp --python-version 3.11 --abi cp311 --only-binary=:all:`.
- VERIFY `holidays` dist-info survived: `ls <target> | grep dist-info` and `importlib.metadata.version('holidays')` — holidays crashes at import without its metadata.
- Zip must have a top-level `python/` directory (required Lambda Layer structure).
- Verify zip contents with `zipfile` before applying.

## 6. Create the environment directory
Mirror the working env (e.g. dev): backend.tf, versions.tf, variables.tf (set `aws_assume_role_arn = ""` to use the current identity), main.tf, outputs.tf. In main.tf:
- Use the account's region.
- Point backend at the new bucket + `envs/<segment>/terraform.tfstate`.
- Wire `module.lambda_layer`'s `layer_arn` into the lambda modules (fresh account has no pre-published layer).
- Set TRADING_ENABLED and table-name env vars per function.

## 7. Plan, verify, apply
```bash
cd opc-terraform/envs/<segment>
terraform init -reconfigure
terraform plan          # expect N to add, 0 to change, 0 to destroy for a fresh env
terraform apply -auto-approve
```
- A fresh environment should show ONLY additions. Any change/destroy means wrong backend or reused state.
- After apply, verify: `aws secretsmanager list-secrets`, `aws lambda list-functions` (runtime + layer ARN), `aws lambda get-function` code URL.

## 8. Populate secrets out-of-band
Terraform owns the containers, never the values. Collect API keys/webhook URLs via a file (e.g. `/tmp/secrets.env`), NOT chat (transcripts leak). Then `aws secretsmanager put-secret-value` with a JSON of the config keys the handlers read — discover keys by grepping `get_config_value`/`_shared_get_config_value` calls in the Lambda source.

**Enumerate ALL config keys, not just the visible ones.** The Lambda reads config through several helper wrappers — grep for every wrapper family:
```bash
grep -oE "_shared_get_config_value\(\s*['\"][^'\"]+['\"]" opc-code/Lambdas/*.py
grep -oE "get_(positive_float|positive_int|non_negative_int|bool)_config\(\s*['\"][^'\"]+['\"]" opc-code/Lambdas/*.py
```
A missing key (e.g. `cash_per_spread`, `spread_width`, `close_order_max_retries`) crashes the Lambda at import with `ValueError: Missing required '<key>' field in the secret` — the stack trace names the exact missing key, so iterate: populate, redeploy, invoke, read the next missing key.

## 9. Lambda cold-start secret caching (test after secret updates)

Lambdas read Secrets Manager at **module import time** (`_config_secret = get_secret_json(...)` runs once per container). After you update a secret, a **warm container keeps the old value**. Symptoms:
- You updated the secret, invoked, and got an error that references the OLD value (e.g. Discord still 405 against the placeholder webhook URL).
- The log shows no fresh `INIT_START` (warm container reuse).

Fix: force a fresh container. Updating the function description (`aws lambda update-function-configuration --description "..."`) triggers a new config revision and cold start. Then re-invoke and check logs for a new `START RequestId` + `Init Duration` (cold) and the absence of the old error.
- Direct curl test of the webhook (`curl -X POST "$URL" -d '{"content":"test"}'` → HTTP 204) proves the URL itself is fine, isolating the problem to Lambda-side caching.
- The code logs Discord failures as warnings (`Discord alert failed: 405`) — the ABSENCE of that line after a cold start is the success signal.

## Broker-less simulation mode (testing without a broker account)

When the app is coupled to a broker API (Alpaca, etc.) and the user can't create an account yet, build a simulation layer instead of blocking:
- Create a `simulation.py` that mimics the EXACT client interfaces the handlers consume (`.get_account()`, `.get_all_positions()`, `.submit_order()`, `.get_option_chain()`, `.get_option_latest_quote()`) with in-memory state and immediate fills.
- Hook it in the shared client factory: `get_alpaca_client()` returns the sim client when `BROKER_MODE=simulated` (env var), else the real SDK client. All existing call sites keep working untouched.
- Package `simulation.py` into the Lambda ZIP (Terraform `archive_file` source block) and set `BROKER_MODE=simulated` + a `SIM_UNDERLYING_PRICE` env var on both functions.
- Populate the config secret with placeholder credentials — safe because the sim client never calls the real API.
- Verify: invoke handler actions (market_open_alert, check_pending_orders, DEW_TREND) and confirm clean 200s, `[SIM] Simulation mode enabled` in logs, correct strategy rejection (e.g. non-Monday entry rejected), and DynamoDB writes.

## Pitfalls
1. **Hardcoded region** — any `us-east-2` in module ARNs breaks non-Ohio accounts. Grep the whole tree before plan.
2. **Validation list rejection** — plan fails with "environment must be one of: dev, test, prod" if you miss a module.
3. **`data.aws_region.current` missing** — after switching ARNs to it, remember to declare the data source.
4. **Lock table mismatch** — if backend.tf uses `use_lockfile = true`, the DynamoDB lock table is unnecessary.
5. **Layer ownership** — repos may pin `dependency-layer.tf` to another account's ARN — for a fresh account, instantiate the module instead.
6. **Secrets in transcripts** — never paste Discord/Alpaca keys in chat; use a temp file the agent reads.
7. **Root credentials** — root works but has no IAM boundary — keep the env scoped and clean up when done.
8. **Missing config keys crash at import** — the Lambda reads secrets at module import; a missing key (e.g. `cash_per_spread`, `spread_width`) raises `ValueError: Missing required '<key>' field in the secret` before any handler runs. Enumerate ALL wrapper families (`_shared_get_config_value`, `get_positive_float_config`, `get_bool_config`, …) with the grep recipe in step 8 — never assume the visible calls are the full set.
9. **Warm-container secret caching** — after updating a secret, a warm container keeps the old value (Discord 405 against a stale webhook is the classic symptom). Force a cold start by updating the function description, then confirm a fresh `START RequestId` + `Init Duration` in the logs.
10. **Fresh env must show only additions** — a `terraform plan` with change/destroy on a fresh environment means the wrong backend or reused state. Stop and fix the backend before applying.
11. **Zip layer structure** — a Lambda Layer ZIP must have a top-level `python/` directory; a flat layout silently produces a layer with nothing on `sys.path`. Verify with `zipfile` before apply.
12. **`holidays` dist-info** — `holidays` crashes at import without its metadata; never strip `*.dist-info` during layer builds. Verify `importlib.metadata.version('holidays')` after building.
