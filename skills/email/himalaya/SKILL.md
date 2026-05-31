---
name: himalaya
description: "Himalaya CLI: IMAP/SMTP email from terminal."
version: 1.2.0
author: community
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [himalaya]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
    related_skills: [himalaya]
    trigger_conditions:
      - "himalaya"
      - "email from terminal"
      - "imap cli"
      - "send email from command line"
      - "check email via terminal"
      - "himalaya account configure"
      - "himalaya folder list"
      - "himalaya envelope"
      - "himalaya template"
      - "smtp cli email"
      - "manage emails via terminal"
      - "himalaya config"
      - "email client command line"
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

This skill is separate from the Hermes Email gateway adapter. The gateway
adapter lets people email the agent and uses Hermes' built-in IMAP/SMTP
adapter; this skill lets the agent operate a mailbox from terminal tools and
requires the external `himalaya` CLI.

## When to Use

- User says "check my email" or "list my emails" and `himalaya` is installed
- User asks to send an email from the terminal (non-interactive, scripted)
- User needs to move, copy, or delete emails via CLI
- User wants to configure a new email account in Himalaya
- User says "himalaya" explicitly
- User needs to export a raw MIME message from their mailbox
- User wants to manage email flags (seen, flagged) programmatically
- User asks for a terminal-based email workflow (not GUI/web)

## Not For

- **Sending email via the Hermes Email gateway adapter** → use Hermes' built-in email adapter (not this skill)
- **GUI or web-based email management** → this skill is CLI-only
- **Complex MML composition with attachments** → use a proper email client; MML is error-prone
- **Bulk email marketing or mass sending** → use a transactional email service
- **Email filtering or server-side rules** → use Sieve or your provider's web UI
- **Encrypted email (PGP/GPG)** → Himalaya supports some backends but this skill doesn't cover key management
- **Microsoft Exchange with modern auth** → use a client that supports OAuth2 natively

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

### Installation

```bash
# Pre-built binary (Linux/macOS — recommended)
curl -sSL https://raw.githubusercontent.com/pimalaya/himalaya/master/install.sh | PREFIX=~/.local sh

# macOS via Homebrew
brew install himalaya

# Or via cargo (any platform with Rust)
cargo install himalaya --locked
```

## Configuration Setup

Run the interactive wizard to set up an account:

```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:

```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"  # or use keyring

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"

# Folder aliases (himalaya v1.2.0+ syntax). Required whenever the
# server's folder names don't match himalaya's canonical names
# (inbox/sent/drafts/trash). Gmail is the common case — see
# `references/configuration.md` for the `[Gmail]/Sent Mail` mapping.
folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Trash"
```

> **Heads up on the alias syntax.** Pre-v1.2.0 docs used a
> `[accounts.NAME.folder.alias]` sub-section (singular `alias`).
> v1.2.0 silently ignores that form — TOML parses fine, but the
> alias resolver never reads it, so every lookup falls through to
> the canonical name. On Gmail this means save-to-Sent fails *after*
> SMTP delivery succeeds, and `himalaya message send` exits non-zero.
> Any caller (agent, script, user) that retries on that exit code
> will re-run the entire send — including SMTP — producing duplicate
> emails to recipients. Always use `folder.aliases.X` (plural, dotted
> keys, directly under `[accounts.NAME]`).

## Hermes Integration Notes

- **Reading, listing, searching, moving, deleting** all work directly through the terminal tool
- **Composing/replying/forwarding** — piped input (`cat << EOF | himalaya template send`) is recommended for reliability. Interactive `$EDITOR` mode works with `pty=true` + background + process tool, but requires knowing the editor and its commands
- Use `--output json` for structured output that's easier to parse programmatically
- The `himalaya account configure` wizard requires interactive input — use PTY mode: `terminal(command="himalaya account configure", pty=true)`

## Common Operations

### List Folders

```bash
himalaya folder list
```

### List Emails

List emails in INBOX (default):

```bash
himalaya envelope list
```

List emails in a specific folder:

```bash
himalaya envelope list --folder "Sent"
```

List with pagination:

```bash
himalaya envelope list --page 1 --page-size 20
```

### Search Emails

```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email

Read email by ID (shows plain text):

```bash
himalaya message read 42
```

Export raw MIME:

```bash
himalaya message export 42 --full
```

### Reply to an Email

To reply non-interactively from Hermes, read the original message, compose a reply, and pipe it:

```bash
# Get the reply template, edit it, and send
himalaya template reply 42 | sed 's/^$/\nYour reply text here\n/' | himalaya template send
```

Or build the reply manually:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: sender@example.com
Subject: Re: Original Subject
In-Reply-To: <original-message-id>

Your reply here.
EOF
```

Reply-all (interactive — needs $EDITOR, use template approach above instead):

```bash
himalaya message reply 42 --all
```

### Forward an Email

```bash
# Get forward template and pipe with modifications
himalaya template forward 42 | sed 's/^To:.*/To: newrecipient@example.com/' | himalaya template send
```

### Write a New Email

**Non-interactive (use this from Hermes)** — pipe the message via stdin:

```bash
cat << 'EOF' | himalaya template send
From: you@example.com
To: recipient@example.com
Subject: Test Message

Hello from Himalaya!
EOF
```

Or with headers flag:

```bash
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

Note: `himalaya message write` without piped input opens `$EDITOR`. This works with `pty=true` + background mode, but piping is simpler and more reliable.

### Move/Copy Emails

Move to folder:

```bash
himalaya message move 42 "Archive"
```

Copy to folder:

```bash
himalaya message copy 42 "Important"
```

### Delete an Email

```bash
himalaya message delete 42
```

### Manage Flags

Add flag:

```bash
himalaya flag add 42 --flag seen
```

Remove flag:

```bash
himalaya flag remove 42 --flag seen
```

## Multiple Accounts

List accounts:

```bash
himalaya account list
```

Use a specific account:

```bash
himalaya --account work envelope list
```

## Attachments

Save attachments from a message:

```bash
himalaya attachment download 42
```

Save to specific directory:

```bash
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats

Most commands support `--output` for structured output:

```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Debugging

Enable debug logging:

```bash
RUST_LOG=debug himalaya envelope list
```

Full trace with backtrace:

```bash
RUST_LOG=trace RUST_BACKTRACE=1 himalaya envelope list
```

## Pitfalls

1. **Using the singular `folder.alias` syntax** — As documented above, pre-v1.2.0 used `[accounts.NAME.folder.alias]`. v1.2.0+ requires `folder.aliases.X` (plural, dotted). The singular form parses but is silently ignored. On Gmail, this causes `himalaya message send` to exit non-zero *after* SMTP delivery — every retry sends another copy. Always use plural `folder.aliases`.

2. **Opening `$EDITOR` without `pty=true`** — `himalaya message write` without piped input opens the system editor. Without `pty=true` in the terminal tool, the editor hangs waiting for input that never comes. Use `pty=true` or (better) pipe the message via stdin.

3. **Retrying on `folder not found` error** — This usually means the folder alias mapping is wrong (see pitfall #1) or the folder name has a space that wasn't quoted. Check the alias syntax before retrying.

4. **Message IDs are folder-relative** — `himalaya message read 42` reads ID 42 in the *current* default folder (usually INBOX). After moving a message, its ID in the destination folder may differ. Always re-list after folder changes.

5. **Forgetting `--output json` for programmatic parsing** — Default output is human-readable plain text. Parsing it with string operations is fragile. Always add `--output json` when the result will be used in downstream logic.

6. **Using `himalaya message write` interactively from Hermes** — This requires knowing the user's `$EDITOR` (vim, nano, emacs) and sending the correct key sequence to save and quit. It's error-prone. The piped stdin approach (`cat << EOF | himalaya template send`) is more reliable.

7. **Storing plaintext passwords in config.toml** — `backend.auth.password = "mypassword"` works but is a security risk. Use `backend.auth.cmd = "pass show email/imap"` or a keyring command instead.

8. **Not checking for `himalaya --version` before running** — Syntax changed between versions (e.g., `folder.alias` → `folder.aliases`). Verify the installed version with `himalaya --version` before applying config from this skill or references.

9. **Assuming Gmail folder names are canonical** — Gmail uses `[Gmail]/Sent Mail`, `[Gmail]/Drafts`, etc. Without aliases, himalaya looks for `Sent` and fails. See `references/configuration.md` for the exact Gmail mapping.

10. **Sending a reply without `In-Reply-To` header** — A reply without this header is treated as a new thread by most email clients. When piping a reply, include the original `Message-Id` in the `In-Reply-To:` header. Use `himalaya message read --raw <id>` to find it.

11. **Rate-limiting yourself with rapid `envelope list` calls** — IMAP servers may throttle connections. If listing large folders repeatedly, add `--page-size 50` and paginate instead of requesting thousands of envelopes at once.

12. **Using the default account when `--account` is needed** — If the user has multiple accounts configured, commands run against the `default = true` account unless `--account <name>` is specified. Always check `himalaya account list` first when working with a multi-account setup.
