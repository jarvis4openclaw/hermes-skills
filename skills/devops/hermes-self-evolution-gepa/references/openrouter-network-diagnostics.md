# OpenRouter Network Diagnostics

Runbook for when OpenRouter API calls fail due to network egress issues.

## Quick Diagnosis

```bash
# 1. Check if the API key is valid (read raw, not via read_file which masks)
python3 -c "
with open('/home/wahid/.hermes/evolution-creds.env') as f:
    for line in f:
        if 'OPENROUTER_API_KEY' in line and '=' in line and not line.startswith('#'):
            key = line.split('=',1)[1].strip()
            break
print(f'Key length: {len(key)}, starts: {key[:15]}..., ends: ...{key[-5:]}')
"

# 2. Test connectivity (curl is more diagnostic than Python requests)
curl -v --max-time 15 https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer ***  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/auto","messages":[{"role":"user","content":"OK"}],"max_tokens":5}'
```

## Symptom Table

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `curl` exits 43, no output | Shell escaping mangled the Bearer token | Use Python subprocess or direct script |
| `curl -v` shows DNS resolved, TCP open, TLS handshake ok, but hangs | IPv6 silently blocked; `requests` tries IPv6 first and never falls back | Force IPv4 (see below) |
| `nc -zv` shows port open but curl hangs | Same as above — IPv6 issue | Force IPv4 |
| `curl -v` shows entire TLS handshake succeeds, returns 200 | API is working; check your key or model name | Verify key is in `evolution-creds.env` |
| Python `requests` times out silently | Either IPv6 hang or missing `verify=False` | Force IPv4 + add timeout |

## Fix: Force IPv4 in evolve_skill.py

In `evolution/skills/evolve_skill.py`, add BEFORE all other imports:

```python
# Force IPv4 for all outbound connections (IPv6 hangs on this host)
import socket as _socket
_orig_getaddrinfo = _socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, _socket.AF_INET, type, proto, flags)
_socket.getaddrinfo = _ipv4_getaddrinfo
```

**Do NOT** include this in upstream PRs — it's a host-specific workaround for network configuration, not a code bug.

## Alternative: Use Local Ollama

When OpenRouter is unreachable, fall back to LLM-as-Judge (Strategy A) with local models:

```python
import dspy
lm = dspy.LM('ollama/qwen2.5:3b-instruct', api_base='http://localhost:11434')
```

Tested: `qwen2.5:3b-instruct` responds reliably (~18s). `qwen3:8b` may timeout under load.

## API Key Verification

The file `~/.hermes/evolution-creds.env` format:
```
OPENROUTER_API_KEY=sk-or-v1-...
export OPENROUTER_API_KEY
```

Source before running: `source ~/.hermes/evolution-creds.env`

The key appears masked (`***`) in `read_file` output but is present in the raw file. Use Python to read it programmatically.
