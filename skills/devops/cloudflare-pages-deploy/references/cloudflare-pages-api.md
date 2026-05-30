# Cloudflare Pages API Reference

Base URL: `https://api.cloudflare.com/client/v4`

All requests require:
```
Authorization: Bearer <token>
Content-Type: application/json
```

## Authentication

- Token scope needed: `Account.Cloudflare Pages:Edit`
- Create tokens at: https://dash.cloudflare.com/profile/api-tokens
- Account ID is visible in dashboard sidebar and URL

## Endpoints

### Create Project

```
POST /accounts/:account_id/pages/projects
Body: { "name": "my-project", "production_branch": "main" }
```

### Get Project

```
GET /accounts/:account_id/pages/projects/:project_name
```

### Delete Project

```
DELETE /accounts/:account_id/pages/projects/:project_name
```

### Get Deployments

```
GET /accounts/:account_id/pages/projects/:project_name/deployments
```

### Add Custom Domain

```
POST /accounts/:account_id/pages/projects/:project_name/domains
Body: { "name": "sub.example.com" }
```

Response includes:
- `status`: "initializing" → "pending" → "active"
- `verification_data.status`: "pending" → "active"
- `validation_data.status`: "initializing" → "pending" → "active"
- `validation_data.method`: "http" (HTTP challenge)
- `certificate_authority`: "google" or "lets_encrypt"
- `zone_tag`: Cloudflare zone ID (present for same-account zones)

### Get Domain Status

```
GET /accounts/:account_id/pages/projects/:project_name/domains/:domain_name
```

### List Custom Domains

```
GET /accounts/:account_id/pages/projects/:project_name/domains
```

### Delete Custom Domain

```
DELETE /accounts/:account_id/pages/projects/:project_name/domains/:domain_name
```

## DNS Setup for Custom Domains

For same-account zones (zone_tag present in domain response), Cloudflare should auto-create the CNAME record. The required record:

| Type  | Name        | Target                     | Proxy |
|-------|-------------|----------------------------|-------|
| CNAME | `<sub>`     | `<project>.pages.dev`      | ON    |

If auto-provisioning stalls, manually create this record via Cloudflare DNS dashboard or the DNS API (`Zone.DNS:Edit` permission required — separate from Pages:Edit).

## Wrangler CLI Equivalents

| API | wrangler equivalent |
|-----|---------------------|
| Create project | `wrangler pages project create <name>` |
| Deploy assets | `wrangler pages deploy <dir> --project-name=<name>` |
| List deployments | `wrangler pages deployment list --project-name=<name>` |
| Custom domain | Dashboard only (no wrangler subcommand) |
