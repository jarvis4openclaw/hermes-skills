---
name: mcporter
description: Use the mcporter CLI to list, configure, auth, and call MCP servers/tools directly (HTTP or stdio), including ad-hoc servers, config edits, and CLI/type generation.
version: 1.0.0
author: community
license: MIT
metadata:
  hermes:
    tags: [MCP, Tools, API, Integrations, Interop]
    homepage: https://mcporter.dev
    trigger_conditions:
      - "mcporter"
      - "MCP server"
      - "MCP client"
      - "configure MCP"
      - "discover MCP tools"
      - "call MCP tool"
      - "mcporter list"
      - "mcporter config"
      - "mcporter auth"
      - "mcporter daemon"
      - "ad-hoc MCP server"
      - "MCP code generation"
      - "mcporter CLI"
prerequisites:
  commands: [npx]
---

# mcporter

## When to Use

- Need to discover what MCP servers are already configured on the machine
- Want to call an MCP server tool from the terminal without setting up a client
- Testing or debugging an MCP server before integrating it into Hermes
- Connecting to an ad-hoc MCP server by URL without permanent configuration
- Managing mcporter's own configuration (add/remove servers, OAuth, config import)
- Generating CLI wrappers or TypeScript types for an MCP server
- Running MCP servers via stdio for one-off tool calls

## Not For

- Persistent MCP server connections for production use → use `native-mcp` (Hermes' built-in MCP client)
- Configuring Hermes' own MCP integration → use `native-mcp` and `hermes config`
- General Node.js package management → use `npm` or `npx` directly
- Python-based MCP implementations → mcporter handles stdio, but execution uses Python runtime
- Long-running MCP daemons in production → mcporter daemon is for development; prefer systemd services
- Docker-containerized MCP servers → mcporter can call them if exposed, but container orchestration is separate

Use `mcporter` to discover, call, and manage [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) servers and tools directly from the terminal.

## Prerequisites

Requires Node.js:
```bash
# No install needed (runs via npx)
npx mcporter list

# Or install globally
npm install -g mcporter
```

## Quick Start

```bash
# List MCP servers already configured on this machine
mcporter list

# List tools for a specific server with schema details
mcporter list <server> --schema

# Call a tool
mcporter call <server.tool> key=value
```

## Discovering MCP Servers

mcporter auto-discovers servers configured by other MCP clients (Claude Desktop, Cursor, etc.) on the machine. To find new servers to use, browse registries like [mcpfinder.dev](https://mcpfinder.dev) or [mcp.so](https://mcp.so), then connect ad-hoc:

```bash
# Connect to any MCP server by URL (no config needed)
mcporter list --http-url https://some-mcp-server.com --name my_server

# Or run a stdio server on the fly
mcporter list --stdio "npx -y @modelcontextprotocol/server-filesystem" --name fs
```

## Calling Tools

```bash
# Key=value syntax
mcporter call linear.list_issues team=ENG limit:5

# Function syntax
mcporter call "linear.create_issue(title: \"Bug fix needed\")"

# Ad-hoc HTTP server (no config needed)
mcporter call https://api.example.com/mcp.fetch url=https://example.com

# Ad-hoc stdio server
mcporter call --stdio "bun run ./server.ts" scrape url=https://example.com

# JSON payload
mcporter call <server.tool> --args '{"limit": 5}'

# Machine-readable output (recommended for Hermes)
mcporter call <server.tool> key=value --output json
```

## Auth and Config

```bash
# OAuth login for a server
mcporter auth <server | url> [--reset]

# Manage config
mcporter config list
mcporter config get <key>
mcporter config add <server>
mcporter config remove <server>
mcporter config import <path>
```

Config file location: `./config/mcporter.json` (override with `--config`).

## Daemon

For persistent server connections:
```bash
mcporter daemon start
mcporter daemon status
mcporter daemon stop
mcporter daemon restart
```

## Code Generation

```bash
# Generate a CLI wrapper for an MCP server
mcporter generate-cli --server <name>
mcporter generate-cli --command <url>

# Inspect a generated CLI
mcporter inspect-cli <path> [--json]

# Generate TypeScript types/client
mcporter emit-ts <server> --mode client
mcporter emit-ts <server> --mode types
```

## Pitfalls

1. **npx not installed — Node.js missing** — mcporter requires `npx` which comes with Node.js. Recovery: install Node.js (`curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo bash - && sudo apt-get install -y nodejs`); verify with `which npx`.

2. **Server not listed: auto-discovery only finds MCP clients** — mcporter discovers servers configured by other MCP clients (Claude Desktop, Cursor, etc.), not standalone servers. If no clients exist on the machine, `mcporter list` returns empty. Recovery: add servers manually with `mcporter config add` or use ad-hoc `--http-url`.

3. **Function syntax quoting issues in shell** — `mcporter call "server.tool(key: value)"` with spaces inside quotes can break due to shell splitting. Recovery: use the `key=value` syntax instead (`mcporter call server.tool key=value`), or use `--args '{"key": "value"}'`.

4. **Ad-hoc HTTP server hangs if URL is unreachable** — mcporter tries to connect indefinitely when the MCP server URL is down. Recovery: test the URL first with `curl -I <url>`; use `--output json` to see connection errors in structured format.

5. **mcporter daemon fails to start because port is in use** — The daemon binds a default port; another instance or service may hold it. Recovery: `mcporter daemon stop` first; check with `ss -tlnp | grep <port>`; restart with `mcporter daemon restart`.

6. **Config file corruption prevents listing servers** — Manual edits to `./config/mcporter.json` with invalid JSON cause mcporter to silently fail. Recovery: `mcporter config list` to test readability; hand-edit with `python3 -m json.tool ./config/mcporter.json > /tmp/fixed.json && mv /tmp/fixed.json ./config/mcporter.json`.

7. **OAuth flow opens browser but can't reach callback URL** — Headless servers without a display fail OAuth. Recovery: use `pty=true` in terminal for interactive flows; for headless, pre-generate API keys instead of OAuth.

8. **emit-ts generates types for wrong server** — Without specifying `--mode`, the generated output may default to client mode instead of types. Recovery: explicitly set `--mode types` or `--mode client` per your need.

9. **generate-cli wrapper can't find the server at runtime** — Generated CLI wrappers reference the server by name; if the server was removed from config, the wrapper breaks. Recovery: keep the server in `mcporter config`; re-add if removed.

10. **Calling tools on a server that needs auth without login** — Some MCP servers require OAuth or API keys; mcporter will return auth errors rather than tool results. Recovery: run `mcporter auth <server>` first; verify with a test call.

## Notes

- Use `--output json` for structured output that's easier to parse
- Ad-hoc servers (HTTP URL or `--stdio` command) work without any config — useful for one-off calls
- OAuth auth may require interactive browser flow — use `terminal(command="mcporter auth <server>", pty=true)` if needed
