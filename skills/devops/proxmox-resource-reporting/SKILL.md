---
name: proxmox-resource-reporting
description: Generate detailed resource reports from Proxmox VE cluster including node status, VMs, LXC containers, and storage utilization
category: devops
version: 1.1.0
metadata:
  hermes:
    trigger_conditions:
      - "generate a Proxmox resource report"
      - "Proxmox node / VM / LXC / storage status"
      - "run proxmox_detailed_report.py"
      - "Proxmox API token auth / PVEAPIToken"
      - "Proxmox report email not sending"
      - "pvesh fallback / API down report"
      - "Proxmox storage usage / VM CPU report"
---

# Proxmox Resource Reporting Skill

## When to Use
Use this skill when you need to generate detailed resource reports from a Proxmox VE cluster, including node status, VMs, LXC containers, and storage utilization. Particularly useful for monitoring homelab or production Proxmox environments.

## Not For

- **Live Proxmox administration (VMs/CTs, users, ACLs, snapshots)** → use `proxmox` or `proxmox-host-management` instead — this skill only *reports*.
- **Host-level cron/systemd maintenance on the PVE box** → use `proxmox-host-management` instead (its cron jobs, systemd services, and SSH lifecycle belong there).
- **Resource reports across non-Proxmox servers** → use `server-health` instead.
- **Managing StartOS / Start9 nodes** → use `startos` instead; this skill is Proxmox-specific.
- **Interactive cluster dashboards / long-polling monitoring** → use `pulse-proxmox-monitor` (REST dashboard) instead of one-shot reports.

## Quick Start
The primary report script is at `/home/wahid/clawd/scripts/proxmox_detailed_report.py`. Run it directly:

```bash
cd /home/wahid/clawd && \
  source /home/wahid/clawd/venv/bin/activate && \
  source ~/.proxmox-credentials && \
  python3 scripts/proxmox_detailed_report.py
```

> **⚠️ Venv path**: The clawd venv is at `/home/wahid/clawd/venv/` — NOT `.venv`. If `source .venv/bin/activate` fails, use the absolute path above.

The script generates an HTML email report and delivers it via AgentMail. See the Email Delivery section below for the recipient address.

### Python Dependencies
The script requires the `agentmail` Python package installed in the clawd venv:
```bash
/home/wahid/clawd/venv/bin/pip install agentmail
```
If you see `ModuleNotFoundError: No module named 'agentmail'`, install it with the command above. The venv is minimal (only pip by default), so dependencies must be installed explicitly.

## Prerequisites
- Access to Proxmox VE API (typically port 8006)
- Valid API token with appropriate permissions
- Python 3.x with urllib and json modules
- ~/.proxmox-credentials file with:
  - PROXMOX_HOST=https://your-proxmox-host:8006
  - PROXMOX_TOKEN_ID=your-token-id@pam!your-token-name
  - PROXMOX_TOKEN_SECRET=your-token-secret
  - AGENTMAIL_API_KEY=your-agentmail-key (for email delivery)

## Approach
Proxmox API token authentication uses a non-standard format: `PVEAPIToken=TOKEN_ID=TOKEN_SECRET` (note the double equals, not colon). This is a common point of failure.

## Steps

### 1. Verify Credentials Format
Check your ~/.proxmox-credentials file:
```bash
cat ~/.proxmox-credentials
```
Should contain:
```
export PROXMOX_HOST=https://host:8006
export PROXMOX_TOKEN_ID=api-rw@pam!token-name
export PROXMOX_TOKEN_SECRET=your-secret-uuid
export AGENTMAIL_API_KEY=your-agentmail-key
```

### 2. Test API Connectivity
Use this Python snippet to verify token format:
```python
import os
import urllib.request
import json
import ssl
import socket

# CRITICAL: Set socket timeout or API hangs on broken pveproxy
socket.setdefaulttimeout(10)

# Load credentials
with open(os.path.expanduser('~/.proxmox-credentials'), 'r') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            if 'export' in line:
                line = line.strip()
                if line.startswith('export '):
                    line = line[7:]
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"')

host = os.environ["PROXMOX_HOST"]
token_id = os.environ["PROXMOX_TOKEN_ID"]
token_secret = os.environ["PROXMOX_TOKEN_SECRET"]
auth = f"PVEAPIToken={token_id}={token_secret}"  # NOTE: Double equals

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api_call(endpoint):
    url = f"{host}/api2/json{endpoint}"
    req = urllib.request.Request(url, headers={"Authorization": auth})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
        return json.loads(response.read())["data"]

# Test with version endpoint (usually works)
try:
    version = api_call("/version")
    print(f"Proxmox Version: {version}")
except Exception as e:
    print(f"Auth failed: {e}")
```

### 3. Generate Resource Report

**Primary: API-based (when pveproxy is healthy)**
Use the working script approach:
1. Fetch node status: `/nodes/pve/status`
2. Fetch VMs: `/nodes/pve/qemu`
3. Fetch LXC containers: `/nodes/pve/lxc`
4. Fetch storage: `/nodes/pve/storage`
5. Format output with clear sections and warnings

**Fallback: SSH-based via pvesh (when API/SSL is broken)**
When the HTTPS API is unreachable (SSL cert missing, pveproxy down), fall back to SSH:
```bash
# Test connectivity first — pvesh returns instantly, doesn't hang
ssh -o StrictHostKeyChecking=no root@<host> "pvesh get /cluster/resources --output-format json"

# Fetch all data in one call: /cluster/resources includes nodes, VMs, containers, storage, and networks
ssh root@<host> "pvesh get /cluster/resources --output-format json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data:
    print(f\"{item.get('type','?'):10} | {item.get('id','?'):30} | {item.get('status','?')}\")
"
```
Key `pvesh` endpoints mirror the API:
- `/cluster/resources` — everything (nodes, VMs, containers, storage, networks) in one call
- `/nodes/<node>/status` — node-level CPU/memory/uptime
- `/nodes/<node>/qemu`, `/nodes/<node>/lxc` — VMs/containers (empty when none exist)
- `/nodes/<node>/storage` — storage pools

The `--output-format json` flag is required for machine-readable output; default pvesh output is a human-readable table.

### 4. Recover Lost Credentials (After pmxcfs Wipe)
If the API call returns `401 Authentication failed!` even with the correct token format, the user/token may have been wiped. After a pmxcfs wipe, `/etc/pve/user.cfg` is recreated empty — the `api-rw@pam` user and its `moltbot` token disappear. Follow the full recovery in the `proxmox-host-management` skill: `references/api-token-recovery.md`. Quick version:

```bash
# SSH in and recreate
ssh root@<host> 'pveum user add api-rw@pam'
ssh root@<host> 'pveum user token add api-rw@pam moltbot --privsep 0'
# → copy the new token secret
ssh root@<host> 'pveum acl modify / --roles PVEAuditor --users api-rw@pam && pveum acl modify / --roles PVESysAdmin --users api-rw@pam'
# Then update PROXMOX_TOKEN_SECRET in ~/.proxmox-credentials
```

### 5. Email Delivery
Reports are sent via AgentMail. The recipient must be a valid, deliverable email address. The script currently sends to `onewahid@gmail.com` (do NOT change to `onewahid@live.com` — that domain bounces).

**Config location:** Inside `proxmox_detailed_report.py`, the `to` parameter is set explicitly. If the recipient ever needs to change, patch the script directly.

### 6. Key Warnings to Watch For
- **Broken API/WebUI**: Check if pveproxy is healthy BEFORE running API scripts. A missing `pve-ssl.pem` causes indefinite hang. See `references/ssl-troubleshooting.md`.
- Storage pools >80% usage
- VMs with sustained high CPU usage (>80%)
- Memory usage >85% on node
- Any stopped critical services
- Backup storage status
- **Container disk over-allocation**: LXC root disk showing >100% usage (e.g., 8.37/4GB = 209%). This means the container is using more disk than its allocated size — investigate bind-mounts, filesystem quotas, or potential reporting bugs. Not always a real issue (bind mounts can inflate the number), but worth verifying.

## Pitfalls
1. **Token Format**: Using `PVEAPIToken=ID:SECRET` instead of `PVEAPIToken=ID=SECRET` — the double-equals is the single most common auth failure. When a 401 appears, check this first.
2. **SSL Verification**: Self-signed certs require disabling verification (`ssl.CERT_NONE`); with verification enabled, `urllib` raises `SSL: CERTIFICATE_VERIFY_FAILED` immediately.
3. **Endpoint Paths**: Always use `/api2/json/` prefix — omitting it 404s or returns the HTML web UI instead of JSON.
4. **Response Format**: Data is in `["data"]` field of JSON response — forgetting the `["data"]` unwrap yields `NoneType` errors downstream.
5. **Numeric Comparisons**: Load averages may be strings, not floats — cast before comparing or `TypeError: '>' not supported` in the warning logic.
6. ✋ **API Hang from Broken pveproxy**: When the Proxmox SSL cert is missing (`/etc/pve/nodes/<node>/pve-ssl.pem` does not exist), pveproxy workers crash-loop. HTTPS connections to port 8006 accept at TCP level but hang indefinitely during SSL handshake. `urllib.request.urlopen` with no explicit timeout will block forever (default socket timeout is None). Always set `socket.setdefaulttimeout(10)` or pass `timeout=10` to `urlopen`. The script `proxmox_detailed_report.py` at `/home/wahid/clawd/scripts/` is affected — it has no timeout. Diagnose by checking pveproxy status via SSH: `systemctl status pveproxy`. See `references/ssl-troubleshooting.md` for full diagnostic flow.
7. **Silent API failures in cron**: When running under cron, a hung API call silently blocks the job until the scheduler timeout. Always verify API health before running the full report — a quick `pvesh get /cluster/resources` via SSH catches this in seconds.
8. **Bounced email recipient**: `onewahid@live.com` bounces permanently. Never use it. The correct email is `onewahid@gmail.com`. If the script's `to=` field ever gets changed to the live.com address, the report will fail with `MessageRejectedError: Recipient(s) blocked: onewahid@live.com (bounced)`.
9. **Stale credentials after pmxcfs wipe**: A 401 on a token that used to work means the user.cfg was wiped. Recreate the user and token via SSH (see Recovery section above); don't waste time troubleshooting the token format.
10. **Editing the report script's f-string HTML**: `proxmox_detailed_report.py` mixes large f-string HTML blocks with Python control flow. The `patch` tool struggles when (a) duplicate HTML structures exist in both VM and LXC sections, (b) f-string interpolation `{variable}` looks like patch syntax, and (c) indentation from the file's original formatting gets mangled. **Strategy**: read the file fresh after each failed patch attempt to verify actual state; include enough unique surrounding context (variable names like `cpu_cores` vs `disk_alloc_gb`) to disambiguate; and **NEVER use `replace_all=true`** on this file — the same HTML table patterns (`</td></tr></table>`, `{progress_bar_html(...)}`, `</tr></table>`) appear in the VM, LXC, External Mounts, AND Storage sections, so `replace_all` will silently corrupt sections you didn't intend to touch. When many changes are needed at once, consider writing a preview HTML file with mock data first (see Workflow below), getting approval, then making targeted patches — or use `write_file` to rewrite the entire script in one shot after reading the full file.
11. **NEVER use `replace_all=true` on this script**: On 2026-07-02, using `replace_all=true` to fix a duplicate `html += '''` string in the VM section also replaced matching strings in the LXC section, External Mounts section, Storage Summary header, and Node Overview closing tags — destroying the entire file. The script is NOT in a git repo, so there was no recovery. **Always back up the file** (`cp script script.bak`) before making structural patches. If you need to change the same pattern in multiple sections, make each patch with unique context — never `replace_all`.
12. **HTML table structure validation**: When editing the report HTML, ensure all `<table>` tags are properly nested and closed. A common failure mode is mismatched `</td></tr></table>` sequences that cause content to "break out of the frame" — appearing outside the intended container. After making structural changes, verify the HTML by checking that each VM/LXC card has matching open/close tags. The preview workflow (step 1 above) helps catch these issues before they reach production.
13. **File corruption recovery**: On 2026-07-02, the script was corrupted by aggressive `patch` operations with `replace_all=true`. Recovery required manually rewriting the entire file with `write_file`. If you encounter a corrupted script (syntax errors, broken HTML structure, missing sections), the fastest recovery is to read the full file, identify the corruption pattern, and use `write_file` to restore a working version. Always maintain a `.bak` copy before major edits.
14. **No QEMU Guest Agent note in report**: The yellow "Disk usage statistics require QEMU Guest Agent" note was intentionally removed from the report. Do not re-add it — the user found it took up unnecessary space. Disk info for VMs without guest agent simply shows allocated size without a note.
15. **Venv path confusion**: The clawd venv is `/home/wahid/clawd/venv/` — NOT `.venv`. If `source .venv/bin/activate` fails, use the absolute path; a bare `python3` outside the venv will raise `ModuleNotFoundError: No module named 'agentmail'`.
16. **`~/.proxmox-credentials` not sourced**: The report script reads credentials from env vars; running it without `source ~/.proxmox-credentials` first yields `KeyError: 'PROXMOX_HOST'`. Always source the file in the same shell invocation.

## Workflow: Preview Before Committing Report Changes
When the user requests layout/format changes to the report:
1. Generate a standalone preview HTML file (e.g. `/home/wahid/proxmox-report-preview.html`) with mock data showing the proposed changes.
2. Let the user open it in a browser and approve.
3. **Back up the real script before patching**: `cp /home/wahid/clawd/scripts/proxmox_detailed_report.py /home/wahid/clawd/scripts/proxmox_detailed_report.py.bak`
4. Only then patch the real script (`/home/wahid/clawd/scripts/proxmox_detailed_report.py`). Make each `patch` call with enough unique surrounding context to match only the intended section — **never use `replace_all=true`** (see pitfall #11).
5. For large multi-section rewrites, prefer `write_file` (after reading the full file) over many fragile `patch` calls.
6. The External Mount Points Summary and Storage Summary sections should be preserved unless the user explicitly asks to change them.

## Verification
After generating report, verify:
- All expected VMs/containers are listed with correct status
- Storage percentages look reasonable
- Timestamp is current
- No authentication errors in output

## Report HTML Layout

The report is an HTML email with these sections (in order):
1. **Header** — title + timestamp + node name
2. **Node Overview** — version, uptime, CPU model, 3 stat cards (Load, RAM %, Disk %), summary line
3. **Virtual Machines (QEMU)** — one card per VM (no QEMU Guest Agent note)
4. **LXC Containers** — one card per container
5. **External Mount Points Summary** — all bind mounts across containers (if any exist)
6. **Storage Summary** — one card per active storage pool with usage bar
7. **Footer** — "Generated by Jarvis"

### VM/LXC Card Layout (compact, as of 2026-07-01)
- **Stopped** VMs/LXCs: compact one-liner — just `VM/CT {id}: {name}` + STOPPED badge. No CPU/RAM/DISK shown.
- **Running** VMs/LXCs: header row (name + RUNNING badge), then a single row with 3 equal-width cards: CPU, RAM, Disk/Root Disk. Value font is 12-13px (small), labels 9-10px. Progress bars 6px height.
- VMs with QEMU Guest Agent: filesystem breakdown still shown below the resource row (only when running).
- LXCs with bind mounts: mount points shown below the resource row.
- Padding is tight (12-15px outer, 4-8px inner) to keep the report compact.

See `references/report-layout.md` for detailed HTML structure and the preview workflow.

## Maintenance
- Update scripts if Proxmox API changes
- Monitor for authentication token expiration
- Adjust warning thresholds based on your environment