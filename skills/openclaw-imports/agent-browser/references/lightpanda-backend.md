# Lightpanda Browser Backend

## What is Lightpanda?

Lightpanda is a headless browser built in Zig — no rendering pipeline, instant startup, tiny memory footprint (~10x lower than Chrome). Designed for agentic workloads: navigation, DOM scraping, form filling.

## Installation

### x86_64 Linux
```bash
mkdir -p ~/.local/bin
curl -fsSL -o ~/.local/bin/lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux
chmod +x ~/.local/bin/lightpanda
```

### Apple Silicon macOS
```bash
curl -fsSL -o lightpanda \
  https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-macos
chmod +x lightpanda
sudo mv lightpanda /usr/local/bin/
```

### Verify
```bash
lightpanda --help
# Should show: fetch, serve, mcp, help commands
```

## Hermes Configuration

```yaml
# ~/.hermes/config.yaml
browser:
  engine: lightpanda
```

Requires Hermes Agent >= v0.13.0.

## Capability Matrix

| Feature | Lightpanda | Chrome Fallback |
|---------|-----------|-----------------|
| Navigation (open, back, forward) | Yes | — |
| DOM snapshot | Yes | — |
| Click / Type / Scroll / Press | Yes | — |
| JavaScript eval | Yes | — |
| Screenshots | No | Yes (auto) |
| PDF generation | No | Yes (auto) |
| File uploads | No | Yes (auto) |
| Multi-tab contexts | No | Yes (auto) |
| Clipboard | No | Yes (auto) |
| Geolocation emulation | No | Yes (auto) |
| Any command that errors | — | Yes (auto retry) |

## How Fallback Works

When `engine: lightpanda` is set, Hermes launches `agent-browser --engine lightpanda`. If a command fails or calls something Lightpanda doesn't support, Hermes transparently retries with Chrome. The user never sees the fallback.

## Updating

Lightpanda is a nightly build. Re-download the binary when:
- You update Hermes Agent
- Browser tool starts failing on commands that previously worked
- You see Lightpanda version errors in logs

## Troubleshooting

- `lightpanda: command not found`: Ensure install dir is on PATH
- Commands hanging: Lightpanda may not support a feature — check if Chrome fallback kicks in
- Binary won't execute: Check `chmod +x` and correct architecture

## References

- Lightpanda source: https://github.com/lightpanda-io/browser
- Hermes integration PR: https://github.com/NousResearch/hermes-agent/pull/7144
- Lightpanda docs: https://lightpanda.io/docs/open-source/installation
- Hermes usage guide: https://lightpanda.io/docs/open-source/guides/use-hermes
