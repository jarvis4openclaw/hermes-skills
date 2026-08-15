---
name: opc-algo
description: Deploy/maintain Wahid's OPC-Algo delta-spreads SPY options bot on AWS us-west-2 (simulated broker). Use when deploying, invoking, or troubleshooting the opc-wahid Lambdas, Terraform envs/wahid, or the opc-wahid-secret.
version: 1.1.0
author: Jarvis
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [opc-algo, trading, terraform, aws, lambda, simulation]
    trigger_conditions:
      - "deploy OPC-Algo"
      - "OPC trading bot"
      - "wahid environment"
      - "simulation mode"
      - "fractalphive OPC"
      - "opc-wahid entry"
      - "opc-wahid exit"
      - "delta-spreads SPY bot"
      - "opc-wahid-secret"
      - "BROKER_MODE simulated"
---

# OPC-Algo Meta-Skill

Wahid's own version of the OPC-Algo automated delta-spreads options trading
bot. Deployed to **Wahid's own AWS account (112900452411, us-west-2)** as his
personal dev environment, separate from boss Fractalphive's account.

## Source Code Location

The repo (git) lives at:
- Local: `/tmp/algo/code/OPC-Agentic/` (may be temporary — re-clone from GitHub if gone)
- GitHub: `fractalphive/OPC-Agentic`, branch `code-review-cleanup-bugfixes` (PR #1)
- The original boss repo is `fractalphive/OPC` (different repo)

## Key Facts

- **AWS account**: 112900452411, region us-west-2, root creds in `/tmp/aws-creds.env`
- **Terraform state bucket**: `opc-wahid-terraform-state-112900452411`
- **Terraform env**: `opc-terraform/envs/wahid/` (Wahid's environment segment)
- **Environment name**: `wahid` (added to all 6 module validations)
- **BROKER_MODE**: `simulated` on both Lambdas (no real Alpaca account yet)
- **Entry window**: 11:30 AM - 1:30 PM Central (confirmed correct)
- **GitHub PR**: https://github.com/fractalphive/OPC-Agentic/pull/1 (2 commits)
- **Discord webhook**: real URL in `/tmp/secrets.env` + `opc-wahid-secret` in AWS

## Architecture Summary

Two AWS Lambda functions (Entry + Exit) + shared module + simulation module:
- `opc-code/Lambdas/OPC-SPY-Entry.py` — entry logic (trend parse, option chain, order placement)
- `opc-code/Lambdas/OPC-SPY-Exit.py` — exit logic (stop loss, PT, timed exit, orphan reconciliation)
- `opc-code/shared/opc_shared.py` — 17 shared functions + DecimalEncoder (extracted from both)
- `opc-code/shared/simulation.py` — fake Alpaca clients for broker-less testing

Infrastructure (Terraform):
- `opc-terraform/modules/{lambda,lambda-layer,eventbridge,dynamodb,iam,secrets}/`
- `opc-terraform/envs/wahid/` — Wahid's env (backend, main, outputs, variables, versions)

## When to Use

- User asks to deploy, redeploy, or troubleshoot the OPC-Algo bot on **Wahid's** AWS environment (`112900452411`, us-west-2)
- User mentions OPC-Algo, delta-spreads SPY bot, `opc-wahid-*` Lambda functions, or the `wahid` Terraform environment
- Lambda invocations fail (500s, `Runtime.Unknown`, Discord 405) and the fix may involve secrets, layers, or packaging
- Terraform plan/apply for `opc-terraform/envs/wahid/` needs a run or a state/backend check
- Simulated-broker testing (entry/exit flows without a real Alpaca account)
- Reviewing the code-review-cleanup-bugfixes branch or PR #1 state

## Not For

- **General AWS/Terraform env bootstrapping** (fresh account, S3 backend, module validation fixes) → use `terraform-aws-env-bootstrap`
- **Extracting shared modules / deduplicating Lambda code** → use `shared-module-extraction` and `large-python-file-refactor`
- **Generic Proxmox or homelab operations** → use the relevant `proxmox-*` skills
- **Trading strategy design or Pine Script** — OPC-Algo's strategy lives in TradingView; this skill covers the AWS bot deployment only

## What Was Done (Session 2026-08-14)

### Phase 1 — Code review & critical fixes
- TRADING_ENABLED kill switch now universal (was missing in 4 Exit paths + 1 Entry path)
- 4 bare `except:` → `except Exception:`
- 635 lines dead code removed (9 dead functions)

### Phase 2 — Shared module extraction
- Created `opc-code/shared/opc_shared.py` (17 functions + DecimalEncoder)
- Both Lambdas import from it; Terraform packages it in the ZIP
- Fixed SPREAD_WIDTH init-ordering bug (referenced before definition in both files)

### Phase 3 — Wahid's own deployment
- Built Terraform backend (S3 bucket + DynamoDB lock table) in Wahid's account
- Created `opc-terraform/envs/wahid/` mirroring dev
- Extended module env validations to accept "wahid"
- Fixed IAM module hardcoded us-east-2 → region-agnostic
- Built Lambda Layer (alpaca-py 0.43.2 + pytz + holidays + requests for python3.11)
- Applied: 25 resources created
- Populated consolidated secret (`opc-wahid-secret`) with 21 config keys

### Phase 4 — Simulation mode
- `opc-code/shared/simulation.py` — fake Alpaca clients (account/positions/orders/chain/quotes)
- `get_alpaca_client()`/`get_option_client()` return sim clients when `BROKER_MODE=simulated`
- Verified: market_open_alert → 200; check_pending_orders → 200; DEW_TREND day-check works
- Discord webhook connected (real URL in secret); verified with 204 + no Lambda error

## Secret Schema (opc-wahid-secret, 21 keys)

```
api_key, api_secret, alpaca_base_url,
cash_per_spread=5000, spread_width=1,
close_order_max_retries=12, close_order_refresh_working_orders=true,
close_order_cancel_wait_seconds=1,
max_entry_attempts=4, entry_days_allowed=0,1, trading_symbols=SPY,
market_open, confirm_trend, pre_entry_alert, entry_placed, entry_filled,
exit_alert, market_close, errors, reports, price_alert  (all Discord webhooks)
```

## Deployment Workflow (for Wahid's env)

```bash
cd /tmp/algo/code/OPC-Agentic/opc-terraform/envs/wahid
set -a; source /tmp/aws-creds.env; set +a
terraform init -reconfigure
terraform plan
terraform apply -auto-approve
```

## Testing Workflow

```bash
# Unit tests (local)
cd /tmp/algo/code/OPC-Agentic
python3 -m unittest opc-code.tests.test_entry_pnl opc-code.tests.test_entry_market_open_positions -v

# Invoke Entry (market open alert)
aws lambda invoke --function-name opc-wahid-entry --region us-west-2 \
  --cli-binary-format raw-in-base64-out \
  --payload '{"action":"market_open_alert","symbol":"SPY","timestamp":"14 AUG 2026 08:30"}' \
  /tmp/response.json

# Invoke Exit (check pending orders)
aws lambda invoke --function-name opc-wahid-exit --region us-west-2 \
  --cli-binary-format raw-in-base64-out \
  --payload '{"source":"aws.events","detail-type":"Check Pending Orders"}' \
  /tmp/response.json

# Check logs
aws logs tail /aws/lambda/opc-wahid-entry --region us-west-2 --since 10m
```

## Pitfalls

1. **SPREAD_WIDTH ordering**: `_opc_shared.SPREAD_WIDTH = SPREAD_WIDTH` must come
   AFTER `SPREAD_WIDTH = get_positive_float_config(...)` in both Lambdas.
2. **Secret cache on warm containers**: Updating the secret does NOT refresh a
   warm Lambda container. Force a cold start (update description/config) before
   testing webhook changes.
3. **Discord 405**: means the Lambda is using a stale/placeholder webhook URL.
   Cold-start the Lambda and retest.
4. **Layer build**: `holidays` package needs its dist-info intact — never strip
   `*.dist-info` (ISSUE-009 pitfall). Verify `importlib.metadata.version('holidays')`
   after building.
5. **Lambda ZIP packaging**: Both `opc_shared.py` AND `simulation.py` must be in
   the `shared/` dir of the ZIP, plus `shared/__init__.py`.
6. **aws CLI payload**: use `--cli-binary-format raw-in-base64-out --payload file://...`
   for JSON payloads.
7. **No real Alpaca account yet**: Broker keys are placeholders; simulation client
   is used. When a real account is created, put keys in the secret and flip
   `BROKER_MODE` to anything except "simulated".
8. **Temp files vanish** — `/tmp/algo/code/OPC-Agentic/` and `/tmp/aws-creds.env`
   are ephemeral. If the repo is gone, re-clone from GitHub
   (`fractalphive/OPC-Agentic`, branch `code-review-cleanup-bugfixes`); if creds
   are gone, regenerate from AWS rather than hunting transcripts.
9. **Terraform state drift** — After any manual `aws` change (bucket, secret,
   table), run `terraform plan` in `opc-terraform/envs/wahid/` before assuming
   the world matches the code. Manual changes silently desync state.
10. **Entry window is Central Time** — the 11:30 AM–1:30 PM window is CT, not
    UTC. When validating EventBridge schedules or logs, convert timestamps or
    you will misjudge whether a run fired on time.
11. **Warm-container log reuse** — when checking logs after a fix, confirm a
    fresh `START RequestId` + `Init Duration` (cold) appears, otherwise you may
    be reading stale container output that still shows the old error.

## What's Next (Open Items)

- Force a full simulated entry (Monday timestamp) to see chain → fill → trade record
- Replace placeholder Alpaca keys when account created
- Watch PR #1 CI checks complete
- Boss's PR (#1) review and merge
- Consider cleanup: remove `.terraform.lock.hcl` from envs/wahid if not wanted in git
