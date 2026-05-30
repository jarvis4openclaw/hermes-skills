---
name: proxmox-resource-reporting
description: Generate detailed resource reports from Proxmox VE cluster including node status, VMs, LXC containers, and storage utilization
category: devops
---

# Proxmox Resource Reporting Skill

## When to Use
Use this skill when you need to generate detailed resource reports from a Proxmox VE cluster, including node status, VMs, LXC containers, and storage utilization. Particularly useful for monitoring homelab or production Proxmox environments.

## Quick Start
The primary report script is at `/home/wahid/clawd/scripts/proxmox_detailed_report.py`. Run it directly:

```bash
cd /home/wahid/clawd && source .venv/bin/activate && \
  source ~/.proxmox-credentials && \
  python3 scripts/proxmox_detailed_report.py
```

The script generates an HTML email report and delivers it via AgentMail. See the Email Delivery section below for the recipient address.

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

## Common Pitfalls
1. **Token Format**: Using `PVEAPIToken=ID:SECRET` instead of `PVEAPIToken=ID=SECRET`
2. **SSL Verification**: Self-signed certs require disabling verification
3. **Endpoint Paths**: Always use `/api2/json/` prefix
4. **Response Format**: Data is in `["data"]` field of JSON response
5. **Numeric Comparisons**: Load averages may be strings, not floats
6. ✋ **API Hang from Broken pveproxy**: When the Proxmox SSL cert is missing (`/etc/pve/nodes/<node>/pve-ssl.pem` does not exist), pveproxy workers crash-loop. HTTPS connections to port 8006 accept at TCP level but hang indefinitely during SSL handshake. `urllib.request.urlopen` with no explicit timeout will block forever (default socket timeout is None). Always set `socket.setdefaulttimeout(10)` or pass `timeout=10` to `urlopen`. The script `proxmox_detailed_report.py` at `/home/wahid/clawd/scripts/` is affected — it has no timeout. Diagnose by checking pveproxy status via SSH: `systemctl status pveproxy`. See `references/ssl-troubleshooting.md` for full diagnostic flow.
7. **Silent API failures in cron**: When running under cron, a hung API call silently blocks the job until the scheduler timeout. Always verify API health before running the full report — a quick `pvesh get /cluster/resources` via SSH catches this in seconds.
8. **Bounced email recipient**: `onewahid@live.com` bounces permanently. Never use it. The correct email is `onewahid@gmail.com`. If the script's `to=` field ever gets changed to the live.com address, the report will fail with `MessageRejectedError: Recipient(s) blocked: onewahid@live.com (bounced)`.
9. **Stale credentials after pmxcfs wipe**: A 401 on a token that used to work means the user.cfg was wiped. Recreate the user and token via SSH (see Recovery section above); don't waste time troubleshooting the token format.

## Verification
After generating report, verify:
- All expected VMs/containers are listed with correct status
- Storage percentages look reasonable
- Timestamp is current
- No authentication errors in output

## Example Output Format
```
============================================================
PROXMOX NODE RESOURCE REPORT
============================================================
Timestamp: 2026-03-31 07:46:37

- NODE OVERVIEW -
[Node details]

- VMs (QEMU) -
[VM table]

- LXC Containers -
[Container table]

- STORAGE -
[Storage table]

============================================================
Report complete.
============================================================
```

## Maintenance
- Update scripts if Proxmox API changes
- Monitor for authentication token expiration
- Adjust warning thresholds based on your environment