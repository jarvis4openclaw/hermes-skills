---
name: sendblue-sms
description: "Send and receive iMessage/SMS texts via Sendblue CLI. Use when user wants to text, SMS, iMessage someone, or handle incoming messages."
tags: [sms, imessage, sendblue, messaging, contacts, webhooks]
version: 1.2.0
metadata:
  hermes:
    trigger_conditions:
      - "text someone"
      - "send a message to"
      - "iMessage"
      - "SMS"
      - "send text"
      - "incoming message"
      - "reply to text"
      - "sendblue"
      - "text Nicole"
      - "message Aamir"
      - "send iMessage"
      - "send SMS"
      - "check messages"
---

# Sendblue SMS/iMessage

Send and receive texts (iMessage) via the Sendblue CLI.

## When to Use

- User says "text [name]" or "send a message to [name]"
- Incoming iMessage/SMS webhook triggers an agent run
- User asks to reply to a text from a known contact
- User wants to send a group iMessage
- Checking account status or API key validity
- Setting up webhook-based incoming message handling
- Testing SMS delivery for a new integration

## Not For

- **Sending emails** → use `agentmail` or `outlook` skills instead
- **Posting to social media** → use `xitter` or `nostrx` skills for X/Twitter or Nostr
- **Phone calls** — Sendblue only handles text-based messaging (SMS/iMessage)
- **Large-scale SMS marketing** — the free plan has message limits; use a dedicated SMS marketing service
- **WhatsApp or Telegram messaging** — those need their own platform-specific integrations
- **Managing contacts** beyond a few entries — the CLI only syncs names from user's iPhone contacts; build your own mapping table for non-iCloud contacts

## Setup

- **CLI location:** `/home/wahid/.npm-global/bin/sendblue`
- **Shared number:** +1 (872) 296-4991
- **Plan:** Free API
- **Webhook registered:** `https://sendblue.wahidsaleemi.net/webhooks/sendblue-incoming` (type: receive) — see Incoming Messages below. SSL cert (Let's Encrypt, A-rated on SSL Labs) via NPM reverse proxy. Port forwarding configured on router.

## Contacts

| Name | Number | Notes |
|------|--------|-------|
| Wahid (Boss) | +1 (702) 576-8110 | Boss's own number |
| Nicole | +1 (714) 350-5472 | Boss's wife |
| Aamir | +1 (757) 679-4051 | |

## Sending Messages

### Send a message
```bash
/home/wahid/.npm-global/bin/sendblue send "<number>" "<message>"
```
- Number must be in E.164 format (e.g., `+171****5472`)
- Supports `--media <path>` for images/videos/files

### Send group message
```bash
/home/wahid/.npm-global/bin/sendblue send-group <args...>
```

### Send typing indicator
```bash
/home/wahid/.npm-global/bin/sendblue typing "<number>"
```

## Incoming Messages

Two approaches — **webhooks preferred** over polling.

### Option 1: Hermes Built-in Webhook Platform (Recommended) ★

Sendblue pushes incoming messages in real-time via HTTP POST. Hermes has a **native webhook platform** that receives these POSTs, triggers agent runs, and delivers responses to Telegram — no Express/Flask server needed.

**Architecture:**
```
Sendblue → NPM reverse proxy (sendblue.wahidsaleemi.net) → Hermes Gateway (port 8644) → Agent → Telegram
```

**Step 1: Enable webhook platform in Hermes**
```bash
hermes config set platforms.webhook.enabled true
hermes config set platforms.webhook.extra.host "0.0.0.0"
hermes config set platforms.webhook.extra.port 8644
hermes config set platforms.webhook.extra.secret "<generate-strong-secret>"
```

**Step 2: Restart gateway** (MUST be from a separate terminal, not inside the gateway process)
```bash
systemctl --user restart hermes-gateway
# Verify:
curl http://localhost:8644/health  # → {"status":"ok"}
```

**Step 3: Create Sendblue webhook subscription**
```bash
hermes webhook subscribe sendblue-incoming \
  --prompt "📋 Incoming iMessage from {from_number}: {content}
Service: {service} | Time: {date_sent}
Check USER.md contact list to identify sender.
If known contact (Nicole, Aamir), draft a helpful response and send via Sendblue CLI.
If unknown number, notify Boss via Telegram and ask for guidance." \
  --deliver telegram \
  --deliver-chat-id "<telegram-chat-id>" \
  --skills "sendblue-sms" \
  --description "Receive incoming iMessage/SMS from Sendblue"
```

**⚠️ Critical: Do NOT pass `--events`** — Sendblue payloads have no `event_type` or `type` field. The adapter defaults to `"unknown"`. If you pass `--events "receive"`, the POST is accepted (signature valid) but returns `{"status":"ignored","event":"unknown"}` and no agent run is triggered. The `hermes webhook subscribe` command creates the subscription with `events: ["receive"]` by default — you must edit `~/.hermes/webhook_subscriptions.json` afterward to set `"events": []` (empty array = accept all).

**Step 4: Configure reverse proxy in NPM**
- Domain: `sendblue.wahidsaleemi.net`
- Forward to: `<hermes-server-ip>:8644`
- Enable SSL (Let's Encrypt)

**NPM troubleshooting:** If you encounter nginx config errors, missing includes, or SSL cert creation failures, load the `nginx-proxy-manager-native` skill. It covers the dual-nginx architecture (OpenResty + system nginx), common config fixes, and the correct Let's Encrypt API schema.

**Step 5: Register webhook with Sendblue**
```bash
/home/wahid/.npm-global/bin/sendblue webhooks add \
  "https://sendblue.wahidsaleemi.net/webhooks/sendblue-incoming" \
  --type receive \
  --secret "<same-secret-as-hermes-subscription>"
```

**⚠️ Important:** The `--secret` you pass here must match the `secret` field in `~/.hermes/webhook_subscriptions.json`. Sendblue will send this secret in the `sb-signing-secret` header with every webhook POST. If they don't match, you'll get `"Invalid signature"` errors in the gateway logs.

**Step 6: Test end-to-end**
```bash
hermes webhook test sendblue-incoming \
  --payload '{"from_number":"+171****5472","content":"Test message","service":"iMessage","date_sent":"2026-06-29T20:00:00Z"}'
```

See `references/webhooks.md` for payload format, NPM config, and troubleshooting.

#### Sendblue Webhook Signing

Sendblue sends a custom `sb-signing-secret` header with each webhook request (plain secret comparison, similar to GitLab's `X-Gitlab-Token`). The Hermes webhook adapter was **patched on 2026-06-29** to recognize this header in `_validate_signature()` — see `references/webhook-adapter-patch.md` for details.

**Before the patch:** Every Sendblue POST was rejected with `"Invalid signature"` because the adapter only recognized `X-Hub-Signature-256`, `X-Gitlab-Token`, `X-Webhook-Signature`, and `svix-*` headers. The `sb-signing-secret` header was ignored.

**After the patch:** The adapter now checks for `sb-signing-secret` header and does a plain `hmac.compare_digest(sb_secret, secret)` comparison — same pattern as GitLab's token. The subscription's `secret` must match the value Sendblue sends in the `sb-signing-secret` header.

**Code change:** `~/.hermes/hermes-agent/gateway/platforms/webhook.py`, method `_validate_signature()`, added after the Svix block:
```python
# Sendblue: sb-signing-secret = <plain secret>
sb_secret = request.headers.get("sb-signing-secret", "")
if sb_secret:
    return hmac.compare_digest(sb_secret, secret)
```

**Gateway restart required:** The patched `webhook.py` only takes effect after `systemctl --user restart hermes-gateway` (from a separate terminal, not inside the gateway). The dynamic subscription file hot-reloads, but Python code changes do not.

**Current status (verified 2026-06-30):** The webhook endpoint at `https://sendblue.wahidsaleemi.net/webhooks/sendblue-incoming` is reachable and accepting POSTs. The `sendblue-incoming` subscription uses the global secret. The event filter is set to `events: []` (empty array = accept all) because Sendblue doesn't send an event field. Agent runs are triggering successfully — Boss receives Telegram notifications when SMS arrives.

#### Auto-Reply Rules (Boss's preference)
- **Known contacts (Nicole, Aamir):** Auto-draft and send a reply via Sendblue CLI
- **Unknown numbers:** Notify Boss via Telegram, do NOT auto-reply
- **No fallback polling** — trust webhooks 100%

#### Sendblue Webhook CLI Commands
```bash
# List
/home/wahid/.npm-global/bin/sendblue webhooks list

# Add a receive webhook
/home/wahid/.npm-global/bin/sendblue webhooks add <url> --type receive

# Remove
/home/wahid/.npm-global/bin/sendblue webhooks remove <url>
```

### Option 2: Polling via cron

```bash
/home/wahid/.npm-global/bin/sendblue messages --inbound --limit 10
```

Downsides: burns tokens on every poll, delayed by poll interval, re-processes old messages without dedup tracking.

The old OpenClaw setup used polling every 5 minutes with a dedup file at `/home/wahid/clawd/agents/friday/memory/sendblue-reported.json`. A poll script exists at `/home/wahid/clawd/scripts/sendblue-check.sh`.

**Use polling only as a fallback** behind webhooks.

## Other Commands

### View contacts
```bash
/home/wahid/.npm-global/bin/sendblue contacts
```
Note: contacts list shows numbers only, no names. Use the contacts table above for name resolution.

### Account status
```bash
/home/wahid/.npm-global/bin/sendblue status
```

### Show API keys
```bash
/home/wahid/.npm-global/bin/sendblue show-keys
```

### Add a contact
```bash
/home/wahid/.npm-global/bin/sendblue add-contact "<number>"
```

## Workflow: Sending a Text

1. User says "text [name]" or "send a message to [name]"
2. Look up the contact name in the contacts table above
3. Compose the message (ask user for content if not provided)
4. Run the send command
5. Confirm delivery

## Reference Doc

Full architecture, config, and troubleshooting documented in `/home/wahid/SENDBLUE.md` — covers NPM proxy config, MikroTik port forwarding, SSL renewal, webhook subscription JSON, adapter patch, and change log.

## Pitfalls

- The `sendblue` binary is NOT in PATH — always use the full path `/home/wahid/.npm-global/bin/sendblue`
- Phone numbers must be in E.164 format with no spaces/dashes (e.g., `+171****5472` not `+1 (714) 350-5472`)
- Free plan has message limits — don't spam
- iMessage only works for recipients with Apple devices; falls back to SMS for others
- `sendblue contacts` shows numbers without names — maintain your own contact mapping (see table above)
- Polling with cron burns tokens; prefer webhooks for incoming message handling
- The old OpenClaw poll script (`sendblue-check.sh`) does dedup via a JSON file — if reusing polling, carry forward the dedup pattern
- **Cannot edit `~/.hermes/config.yaml` directly** — the patch tool blocks it for security. Use `hermes config set <key> <value>` instead
- **Cannot restart the gateway from inside the gateway process** — `systemctl --user restart hermes-gateway` and `hermes gateway restart` both fail when called from within an active gateway session. Run from a separate terminal shell
- **Load the `webhook-subscriptions` skill** when setting up incoming message handling — it covers the `hermes webhook subscribe` command in detail
- **Auto-reply to known contacts only** — unknown numbers should be forwarded to Boss for guidance, not auto-replied
- **Sendblue payloads have no event field** — Sendblue doesn't send `event_type`, `type`, `X-GitHub-Event`, or `X-GitLab-Event`. The webhook adapter defaults to `"unknown"`. Set `events: []` (empty array) in the subscription to accept ALL events. Do NOT use `events: ["*"]` — it's not a wildcard and will reject the event. See `webhook-subscriptions` skill for details.