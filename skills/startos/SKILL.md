---
name: startos
description: Manage Start9 Embassy DIY (kooky-bees 192.168.100.31) via SSH — service lifecycle, podman exec, lightning/bitcoin CLIs, server admin. Use when the user mentions Start9, Embassy, start-cli, podman, c-lightning, lightning-cli, bitcoin-cli, or managing services on the Embassy.
version: 1.1.0
metadata:
  hermes:
    tags: [startos, start9, embassy, homelab, lightning, bitcoin, podman]
    trigger_conditions:
      - "Start9 Embassy"
      - "start-cli"
      - "podman exec"
      - "lightning-cli"
      - "bitcoin-cli"
      - "manage services on the embassy"
      - "kooky-bees"
      - "check embassy service status"
      - "restart a service on start9"
      - "what services are running on the embassy"
      - "embassy server info"
      - "start9 auth / backup / db"
      - "lncli or c-lightning on embassy"
---

# StartOS Embassy Management

Manage the Start9 Embassy DIY ("kooky-bees") at **192.168.100.31** over SSH. This is a homelab StartOS node running c-lightning, bitcoind, and other Embassy services.

## When to Use

- The user asks about Start9 / Embassy / kooky-bees / start-cli / podman services
- You need to check or manage the c-lightning or bitcoind services on the Embassy
- The user asks for server info, service list, auth, backup, or disk state of the Embassy
- A scheduled job or workflow touches the Embassy (e.g. lightning node health)

## Not For

- **Generic podman on other hosts** — this skill is scoped to the Embassy at 192.168.100.31; other podman hosts use their own workflows → use \`proxmox-ssh-lifecycle\` or host-specific tooling instead.
- **Bitcoin/Lightning questions about non-Embassy nodes** (e.g. a different CLN/bitcoind deployment) — use the node's own admin tooling.
- **Start9 cloud account / store purchases** — out of scope; this is node administration only.
- **Setting up a brand-new StartOS unit** — this assumes an already-provisioned Embassy (kooky-bees); initial provisioning belongs to Start9 docs, not this skill.
- **General SSH to the homelab** — use \`proxmox-ssh-lifecycle\` / \`start-tunnel\` instead when the target isn't the Embassy.

## Quick Start

Scripts:

- `scripts/start-cli [args]` — ssh start9@192.168.100.31 start-cli [args]

- `scripts/podman-exec SERVICE [CMD [args...]]` — sudo podman exec -it SERVICE.embassy CMD [args]

Examples:
```
scripts/podman-exec c-lightning lightning-cli listpeers
scripts/podman-exec bitcoind bitcoin-cli getblockchaininfo
scripts/start-cli service ls
scripts/start-cli server info
```

## Server Commands

`scripts/start-cli` subcommands: auth backup db disk echo git-info inspect net notification package server ssh wifi

## Services

List: `sudo podman ps --all` or `start-cli service ls`

Shell: `sudo podman exec -it SERVICE bash`

## Pitfalls

1. **SSH key path** — the scripts use `~/.ssh/id_ed25519` as user `start9@192.168.100.31`. If SSH fails with "Permission denied", check that this key is loaded/valid — do not fall back to password prompts.
2. **`podman exec` needs sudo on the Embassy** — the script wraps `sudo podman exec`; a non-interactive shell without sudo rights will fail with "sudo: a terminal is required". Run through the script, not a raw ssh command, when possible.
3. **Service container names carry the `.embassy` suffix** — `c-lightning` resolves to `c-lightning.embassy`; omitting the suffix yields "no such container". When in doubt, list with `podman ps --all` first.
4. **`start-cli service ls` vs `podman ps --all` can disagree** — start-cli reports the StartOS-managed view; podman shows every container. If a service looks missing in one, check the other before concluding it's down.
5. **Lightning CLI needs the right container** — `lightning-cli` lives inside `c-lightning.embassy`; running it against bitcoind's container fails with "command not found". Match the CLI to its service container.
6. **Docs live at docs.start9.com / community.start9.com** — when a start-cli subcommand behaves unexpectedly, consult the StartOS docs before guessing flags. The skill's references (`references/embassy-cli.md`, `references/container-access.md`) cover the common paths.

## References

- [embassy-cli](references/embassy-cli.md)
- [container-access](references/container-access.md)
