---
name: health-ingest
description: Health data ingestion pipeline — HTTP server for JSON intake + DuckDB analytics storage
version: 1.1.0
metadata:
  hermes:
    tags: [health, ingest, duckdb, analytics, apple-health, jsonl]
    trigger_conditions:
      - "health ingest"
      - "health data ingestion"
      - "ingest health data"
      - "Apple Health export"
      - "health JSONL"
      - "health duckdb"
      - "restart health ingest"
      - "health ingest service"
      - "check health data"
      - "import health records"
      - "health analytics"
      - "duckdb health"
      - "health pipeline"
---

# Health Ingest Pipeline

Two-part pipeline: (1) HTTP server that accepts health JSON POSTs and writes JSONL, (2) DuckDB ingestion for analytics.

## When to Use

- Receiving health data POSTs from iOS Shortcuts, wearables, or automation scripts
- Troubleshooting the health ingest server (port 8889) or systemd service
- Running the DuckDB ingestion script to load JSONL files into analytics tables
- Querying ingested health data in DuckDB for trends, reports, or dashboards
- Setting up or modifying the health ingest cron schedule
- Verifying data integrity (SHA-256 dedup, schema validation, file counts)
- Adding support for new health data types or Apple Health export fields
- Managing the `health-ingest.service` systemd user unit (start, stop, restart, logs)

## Not For

- General health data visualization or dashboards → use `automation-dashboard-update` or a BI tool instead
- Sending health data to external APIs (Apple HealthKit, Google Fit) → this is an intake pipeline, not an export
- Running the DuckDB CLI for ad-hoc queries outside the ingestion context → use `terminal` with `duckdb` directly
- HIPAA compliance or PHI security auditing → this is a personal pipeline, not a healthcare system
- Debugging network connectivity to the server from remote devices → use `curl` or network diagnostics directly
- Creating or editing the `ingest_apple_health.py` script beyond the paths documented here → see `references/apple-health-duckdb-ingest.md`

## Part 1: HTTP Ingest Server

A 110-line Python stdlib server on port 8889. Accepts POST to `/` with JSON body:

```json
{
    "type": "Heart Rate",
    "dates": ["2019-12-16 08:24:36", "2019-12-16 08:26:39"],
    "values": ["74", "72"]
}
```

Validates schema, saves raw JSON to `data/raw/`, converts to JSONL records in `data/processed/`, returns 201.

### Files
- `ingest.py` — main server (see `references/ingest.py`)
- `test_ingest.py` — smoke test (see `references/test_ingest.py`)
- `health-ingest.service` — systemd user unit (see `references/health-ingest.service`)

### Canonical paths
- Project root: `/home/wahid/health-ingest/`
- Server: `/home/wahid/health-ingest/ingest.py`
- Data: `/home/wahid/health-ingest/data/raw/` and `data/processed/`
- Service: `~/.config/systemd/user/health-ingest.service`

### Managing the service
```bash
systemctl --user status health-ingest
systemctl --user restart health-ingest
journalctl --user -u health-ingest -f
```

### JSONL output format (one record per line, LLM-friendly)
```jsonl
{"type":"Heart Rate","date":"2019-12-16 08:24:36","value":"74"}
{"type":"Heart Rate","date":"2019-12-16 08:26:39","value":"72"}
```

## Part 2: DuckDB Analytics Ingestion

After JSONL files accumulate in `data/processed/`, the ingestion script loads them into DuckDB for querying.

### Built pipeline (June 12, 2026)
- **Script:** `/home/wahid/health-ingest/ingest_apple_health.py`
- **Venv:** `/home/wahid/health-ingest/.venv/` (DuckDB installed, isolates from system Python)
- **DB:** `/home/wahid/health-ingest/data/health.duckdb`
- **Intended schedule:** Friday 1am (`0 1 * * 5`) — not yet created
- See `references/apple-health-duckdb-ingest.md` for the full spec

### Running manually
```bash
source /home/wahid/health-ingest/.venv/bin/activate
python /home/wahid/health-ingest/ingest_apple_health.py           # deletes source files after import
python /home/wahid/health-ingest/ingest_apple_health.py --keep-files  # keep source files
```

### Schema
- `apple_health_records` — normalized observations (metric_type, observed_at UTC, value_raw, value_num)
- `ingest_files` — file-level metadata (sha256, rows_inserted, skipped, deleted)
- Idempotent: files matched by SHA-256 are skipped on re-run

## Pitfalls

1. **Health data is sensitive** — Never print raw records in HTTP responses or log output. Recovery: verify response payloads with `curl -s http://localhost:8889/ | python3 -c "import sys; sys.exit('records' in sys.stdin.read())"` before exposing externally.

2. **JSONL files must be valid JSON per line** — Pretty-printed JSON or multi-line records break DuckDB ingestion with `Invalid Input Error`. Recovery: validate with `python3 -c "import json; [json.loads(l) for l in open('data/processed/YOUR_FILE.jsonl')]"`.

3. **Server binds to 0.0.0.0:8889 by default** — This exposes the endpoint to the LAN. If only local access is needed, bind to `127.0.0.1` in `ingest.py`. Recovery: check current bind with `ss -tlnp | grep 8889`.

4. **`loginctl enable-linger wahid` is required** — Without linger enabled, the user systemd service stops when the session ends. Recovery: `sudo loginctl enable-linger wahid` once; verify with `loginctl show-user wahid --property=Linger`.

5. **DuckDB venv must be activated before running the ingest script** — Running `python ingest_apple_health.py` without activating the venv fails with `ModuleNotFoundError: No module named 'duckdb'`. Recovery: `source /home/wahid/health-ingest/.venv/bin/activate` first.

6. **Missing `data/` subdirectories cause silent failures** — The server expects `data/raw/` and `data/processed/` to exist. If they don't, the server starts but POSTs fail silently. Recovery: `mkdir -p /home/wahid/health-ingest/data/{raw,processed}`.

7. **Schema drift between health data types** — Apple Health exports different fields for different metrics (Heart Rate has `value`, Blood Pressure has `systolic`/`diastolic`). Lossy normalization drops fields. Recovery: use a raw JSON column (`value_raw`) plus extracted common fields; see the `ingest_apple_health.py` implementation.

8. **Duplicate ingestion by SHA-256 dependency** — The idempotent check relies on SHA-256 hashes. If the source file is re-exported with different whitespace or ordering, the hash changes and it's ingested again. Recovery: verify with `python3 -c "import hashlib,json,sys; d=json.load(open(sys.argv[1])); print(hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest())"` to check canonical hash.

9. **Port 8889 conflict with other services** — Port 8889 may be used by Jupyter, development servers, or other local tools. Recovery: `ss -tlnp | grep 8889` to check before starting; change the port in `ingest.py` and `health-ingest.service` if needed.

10. **Systemd journal rotation can hide old logs** — `journalctl --user -u health-ingest` defaults to the current boot. Recovery: use `journalctl --user -u health-ingest --since "2 days ago"` to see older entries, or check `/home/wahid/health-ingest/data/` for the canonical source of truth.
