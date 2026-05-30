# Proxmox SSL/Broken API Troubleshooting

## Symptom
- `nc -zv <host> 8006` says "open" but `curl -k https://<host>:8006/` hangs
- Python `urllib.request.urlopen` hangs indefinitely (ssl.SSLError: handshake timed out)
- Report scripts time out after 5+ minutes with no output

## Root Cause
`pveproxy` workers crash-loop because the node SSL certificate is missing:
```
/etc/pve/nodes/<node>/pve-ssl.pem' does not exist!
```

pveproxy journal shows on every worker restart:
```
/etc/pve/local/pve-ssl.key: failed to load local private key
(key_file or key) at /usr/share/perl5/PVE/APIServer/AnyEvent.pm line 2150.
```

The kernel accepts TCP connections (SYN/SYN-ACK complete) but no TLS handshake happens
because the application can't load its cert. This makes it look like a firewall issue.

## Diagnosis (run from a host with SSH access)
```bash
# 1. Check pveproxy status
ssh root@<host> "systemctl status pveproxy --no-pager -l | grep -A2 'failed\|error\|ERROR'"

# 2. Check if the cert file exists
ssh root@<host> "ls -la /etc/pve/nodes/*/pve-ssl.pem"

# 3. Check pvesh (CLI tool — bypasses HTTPS entirely)
ssh root@<host> "pvesh get /nodes"
# If this works but curl doesn't, SSL is definitely the issue
```

## Fix
```bash
# Regenerate node certificates
ssh root@<host> "pvecm updatecerts --force"

# Restart pveproxy
ssh root@<host> "systemctl restart pveproxy"

# Verify
curl -sk https://<host>:8006/api2/json/version
```

## Workaround (run report without fixing cert)
Use SSH + pvesh directly — pvesh connects to the local `pvedaemon` daemon
via Unix socket, bypassing HTTPS entirely. See the SSH fallback section in SKILL.md.
