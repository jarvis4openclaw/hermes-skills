# API Token Recovery After pmxcfs Wipe

## When This Happens
After a pmxcfs configuration database wipe (`/etc/pve` cleared), all users and API tokens defined in `user.cfg` are lost. The `api-rw@pam` user and its `moltbot` token must be recreated for resource reporting and any other API-based automation to work.

## Symptoms
- `curl` to Proxmox API returns `HTTP/1.1 401 Authentication failed!`
- `pveum user list` shows only `root@pam`
- `/etc/pve/user.cfg` is missing or empty
- Resource report script (`proxmox_detailed_report.py`) fails with `urllib.error.HTTPError: HTTP Error 401`

## Recovery Steps

### 1. Verify the problem
```bash
ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@192.168.100.23 \
  'pveum user list'
```
If `api-rw@pam` is missing, proceed.

### 2. Create the user
```bash
ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@192.168.100.23 \
  'pveum user add api-rw@pam'
```

### 3. Create the API token
```bash
ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@192.168.100.23 \
  'pveum user token add api-rw@pam moltbot --privsep 0'
```
This outputs the new token secret — copy the `value` field.

### 4. Assign permissions
```bash
ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@192.168.100.23 \
  'pveum acl modify / --roles PVEAuditor --users api-rw@pam && \
   pveum acl modify / --roles PVESysAdmin --users api-rw@pam'
```

### 5. Update local credentials
Replace `PROXMOX_TOKEN_SECRET` in `~/.proxmox-credentials` with the new secret:
```bash
# The file lives at ~/.proxmox-credentials
export PROXMOX_TOKEN_SECRET=<new-token-from-step-3>
```

### 6. Verify it works
```bash
source ~/.proxmox-credentials
curl -sk -H "Authorization: PVEAPIToken=$PROXMOX_TOKEN_ID=$PROXMOX_TOKEN_SECRET" \
  "$PROXMOX_HOST/api2/json/nodes/pve/status" | python3 -m json.tool | head -10
```
Should return node status JSON, not 401.

## Notes
- The token name `moltbot` is hardcoded in the credentials file as `api-rw@pam!moltbot`
- `--privsep 0` disables privilege separation so the token has full user permissions
- ACLs on `/` with `PVEAuditor` + `PVESysAdmin` give read+admin access to everything
- This procedure is also needed after any event that wipes `/etc/pve/user.cfg`
