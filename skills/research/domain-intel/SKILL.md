---
name: domain-intel
description: Passive domain reconnaissance using Python stdlib. Subdomain discovery, SSL certificate inspection, WHOIS lookups, DNS records, domain availability checks, and bulk multi-domain analysis. No API keys required.
version: 1.1.0
metadata:
  hermes:
    tags: [domain, reconnaissance, osint, whois, ssl, dns, subdomains]
    trigger_conditions:
      - "find subdomains"
      - "domain intel"
      - "domain intelligence"
      - "SSL certificate"
      - "WHOIS lookup"
      - "domain reconnaissance"
      - "DNS records"
      - "check domain availability"
      - "passive OSINT"
      - "crt.sh subdomains"
      - "domain info"
      - "bulk domain analysis"
      - "certificate expiry"
---

# Domain Intelligence — Passive OSINT

Passive domain reconnaissance using only Python stdlib.
**Zero dependencies. Zero API keys. Works on Linux, macOS, and Windows.**

## When to Use

- Discovering subdomains of a domain via Certificate Transparency logs (crt.sh)
- Checking SSL/TLS certificate expiry, issuer, cipher suites, and SANs
- Performing WHOIS lookups for registration info, registrar, and dates
- Resolving DNS records (A, AAAA, MX, NS, TXT, CNAME)
- Checking domain availability via passive signals (DNS + WHOIS + SSL)
- Running bulk analysis on multiple domains in parallel
- Infrastructure reconnaissance without API keys or paid services
- Investigating the TLS surface of a domain before migrations or security reviews

## Not For

- General research about what a company/domain does → use `web_search` or `web_extract` instead
- Getting the actual content of a webpage → use `web_extract` or `browser_navigate`
- Simple HTTP reachability checks → use `terminal` with `curl -I`
- Website reputation or safety checks → use `web_search` for context
- Active scanning, port scanning, or vulnerability testing → this skill is passive only
- Finding email addresses, social media profiles, or employee info → use `web_search` or `exa-web-search-free`
- Real-time domain monitoring or alerting → this is a one-shot tool, not a monitoring system

## Helper script

This skill includes `scripts/domain_intel.py` — a complete CLI tool for all domain intelligence operations.

```bash
# Subdomain discovery via Certificate Transparency logs
python3 SKILL_DIR/scripts/domain_intel.py subdomains example.com

# SSL certificate inspection (expiry, cipher, SANs, issuer)
python3 SKILL_DIR/scripts/domain_intel.py ssl example.com

# WHOIS lookup (registrar, dates, name servers — 100+ TLDs)
python3 SKILL_DIR/scripts/domain_intel.py whois example.com

# DNS records (A, AAAA, MX, NS, TXT, CNAME)
python3 SKILL_DIR/scripts/domain_intel.py dns example.com

# Domain availability check (passive: DNS + WHOIS + SSL signals)
python3 SKILL_DIR/scripts/domain_intel.py available coolstartup.io

# Bulk analysis — multiple domains, multiple checks in parallel
python3 SKILL_DIR/scripts/domain_intel.py bulk example.com github.com google.com
python3 SKILL_DIR/scripts/domain_intel.py bulk example.com github.com --checks ssl,dns
```

`SKILL_DIR` is the directory containing this SKILL.md file. All output is structured JSON.

## Available commands

| Command | What it does | Data source |
|---------|-------------|-------------|
| `subdomains` | Find subdomains from certificate logs | crt.sh (HTTPS) |
| `ssl` | Inspect TLS certificate details | Direct TCP:443 to target |
| `whois` | Registration info, registrar, dates | WHOIS servers (TCP:43) |
| `dns` | A, AAAA, MX, NS, TXT, CNAME records | System DNS + Google DoH |
| `available` | Check if domain is registered | DNS + WHOIS + SSL signals |
| `bulk` | Run multiple checks on multiple domains | All of the above |

## When to use this vs built-in tools

- **Use this skill** for infrastructure questions: subdomains, SSL certs, WHOIS, DNS records, availability
- **Use `web_search`** for general research about what a domain/company does
- **Use `web_extract`** to get the actual content of a webpage
- **Use `terminal` with `curl -I`** for a simple "is this URL reachable" check

| Task | Better tool | Why |
|------|-------------|-----|
| "What does example.com do?" | `web_extract` | Gets page content, not DNS/WHOIS data |
| "Find info about a company" | `web_search` | General research, not domain-specific |
| "Is this website safe?" | `web_search` | Reputation checks need web context |
| "Check if a URL is reachable" | `terminal` with `curl -I` | Simple HTTP check |
| "Find subdomains of X" | **This skill** | Only passive source for this |
| "When does the SSL cert expire?" | **This skill** | Built-in tools can't inspect TLS |
| "Who registered this domain?" | **This skill** | WHOIS data not in web search |
| "Is coolstartup.io available?" | **This skill** | Passive availability via DNS+WHOIS+SSL |

## Platform compatibility

Pure Python stdlib (`socket`, `ssl`, `urllib`, `json`, `concurrent.futures`).
Works identically on Linux, macOS, and Windows with no dependencies.

- **crt.sh queries** use HTTPS (port 443) — works behind most firewalls
- **WHOIS queries** use TCP port 43 — may be blocked on restrictive networks
- **DNS queries** use Google DoH (HTTPS) for MX/NS/TXT — firewall-friendly
- **SSL checks** connect to the target on port 443 — the only "active" operation

## Data sources

All queries are **passive** — no port scanning, no vulnerability testing:

- **crt.sh** — Certificate Transparency logs (subdomain discovery, HTTPS only)
- **WHOIS servers** — Direct TCP to 100+ authoritative TLD registrars
- **Google DNS-over-HTTPS** — MX, NS, TXT, CNAME resolution (firewall-friendly)
- **System DNS** — A/AAAA record resolution
- **SSL check** is the only "active" operation (TCP connection to target:443)

## Pitfalls

1. **WHOIS over TCP port 43 blocked by firewalls** — Many corporate and strict home networks block outbound TCP 43. WHOIS lookups will hang or timeout. Recovery: use `web_search` with `site:who.is` or a web-based WHOIS as fallback.

2. **crt.sh rate limiting on popular domains** — Domains with thousands of certificates (google.com, github.com) can return truncated results or time out. Recovery: re-run with a longer timeout or accept partial results.

3. **SSL certificate chains with incomplete intermediates** — The `ssl` command reads the leaf certificate only. If the chain is needed (for trust path validation), connect with `openssl s_client -showcerts` instead. Recovery: note to the user that only the leaf cert was inspected.

4. **WHOIS data redacted for GDPR** — Most European TLDs (.eu, .de, .fr) and newer gTLDs redact registrant info. The output will show "REDACTED FOR PRIVACY" — this is expected, not a failure. Recovery: tell the user GDPR redaction is the norm.

5. **DNS resolution may differ by resolver** — System DNS (A/AAAA) uses `/etc/resolv.conf`, while MX/NS/TXT use Google DoH. Different resolvers can return different results. Recovery: note the resolver source when reporting to the user.

6. **Domain availability check is heuristic, not authoritative** — The `available` command uses 3 passive signals. A domain may appear available but actually be registered (or vice versa). Recovery: for authoritative results, use a registrar API or `whois` directly on the TLD's registry server.

7. **SSL connection to port 443 may trigger IDS/IPS** — Connecting to port 443 on a target domain is technically active (not passive). On monitored networks, this may trigger alerts. Recovery: warn the user if they're on a sensitive network.

8. **crt.sh uses HTTPS to crt.sh — works behind most firewalls** — Unlike WHOIS (TCP:43), crt.sh queries are standard HTTPS and rarely blocked. If they fail, it's most likely a DNS or general connectivity issue. Recovery: check `curl -s https://crt.sh` reachability.

9. **Bulk analysis is sequential by default** — Running `bulk` on 20+ domains can take 30-60 seconds. Recovery: use `--checks dns` for a faster subset, or run separate bulk calls for different check types.

10. **Script path uses `SKILL_DIR` variable** — The instructions reference `SKILL_DIR/scripts/domain_intel.py` but the actual path is `~/.hermes/skills/research/domain-intel/scripts/domain_intel.py`. Recovery: use the full path if `SKILL_DIR` isn't set in your shell.

---

*Contributed by [@FurkanL0](https://github.com/FurkanL0)*
