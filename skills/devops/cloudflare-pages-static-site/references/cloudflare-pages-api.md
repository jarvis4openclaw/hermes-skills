# Cloudflare Pages API Reference

Session-tested curl commands for managing Cloudflare Pages projects.

## Auth
```bash
TOKEN=$(grep CLOUDFLARE_PAGES_API_KEY ~/.hermes/.env | cut -d= -f2)
ACCT=239c7bfe059be16a29cfe3bd2e769bfe
ZONE=9f14d36bc1f3e3dbb73f154609ac81b0  # wahid.my
```

## Project Management

### Create project
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"<project>","production_branch":"main"}'
```

### Delete project
```bash
curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>" \
  -H "Authorization: Bearer $TOKEN"
```

### Get project details (check production_branch)
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Deployments

### Trigger deployment for a branch
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"branch":"main"}' | python3 -m json.tool
```

### List deployments
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>/deployments?per_page=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Custom Domains

### Add domain to project
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>/domains" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"subdomain.example.com"}' | python3 -m json.tool
```

### Remove domain from project
```bash
curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>/domains/<domain>" \
  -H "Authorization: Bearer $TOKEN"
```

### Check domain status
```bash
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>/domains/<domain>" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)['result']
print(f'Status: {d[\"status\"]} | Verify: {d[\"verification_data\"][\"status\"]} | SSL: {d[\"validation_data\"][\"status\"]}')
"
```

## DNS (Zone API)

### List CNAME records
```bash
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records?type=CNAME&name=subdomain.example.com" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Update CNAME target
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records/<record_id>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"<project>.pages.dev"}' | python3 -m json.tool
```

## Wrangler CLI

### Deploy current directory
```bash
CLOUDFLARE_API_TOKEN=$TOKEN CLOUDFLARE_ACCOUNT_ID=$ACCT \
  npx wrangler pages deploy . --project-name=<project>
```

### Create project via wrangler
```bash
CLOUDFLARE_API_TOKEN=$TOKEN CLOUDFLARE_ACCOUNT_ID=$ACCT \
  npx wrangler pages project create <project> --production-branch=main
```

## Fix: Production Branch Mismatch

If deployments succeed but production URL shows stale content:

```bash
# 1. Check current production branch
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import json,sys
print(json.load(sys.stdin)['result']['production_branch'])
"

# 2. Update to match repo branch
curl -s -X PATCH "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"production_branch":"main"}'

# 3. Trigger new deployment
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCT/pages/projects/<project>/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"branch":"main"}'
```
