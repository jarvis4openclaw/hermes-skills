---
name: kittentts-server
description: KittenTTS Rust server — OpenAI-compatible TTS API running on Proxmox CT 108. Use when asked to generate speech, test TTS, or manage the KittenTTS server.
version: 1.1.0
category: devops
metadata:
  hermes:
    tags: [tts, kittentts, speech, homelab, openai-compatible]
    trigger_conditions:
      - "generate speech"
      - "test TTS"
      - "manage the KittenTTS server"
      - "text to speech homelab"
      - "kittentts"
      - "TTS voice samples"
      - "nova Rosie voice"
      - "OpenAI-compatible TTS"
      - "restart kittentts"
      - "KittenTTS CT 108"
      - "voice mapping alloy echo fable"
---

# KittenTTS Server

## When to Use

- Generating speech via the homelab KittenTTS server (OpenAI-compatible endpoint at `192.168.100.51:8080`).
- Testing TTS voices, generating samples for voice selection, or switching the active model.
- Managing the KittenTTS service (status, restart) or its systemd unit on CT 108.
- Wiring Hermes TTS to a local provider (`hermes config set tts.*`).

## Not For

- **Voice cloning with F5-TTS (longer, natural-voice pipelines)** → use `voice-cloning-workflow` instead
- **Installing F5-TTS on a CPU-only CT with an OpenAI API wrapper** → use `f5-tts-setup` instead
- **Gemini TTS / cloud TTS provider decisions** → KittenTTS is the homelab alternative; cloud TTS (Gemini Zephyr, ~$0.60/mo) is configured via Hermes TTS providers, not this skill
- **Text-to-speech for daily briefings where voice identity matters more than latency** → `voice-cloning-workflow` / F5-TTS is the right lane; KittenTTS is the fast local option

## Infrastructure

- **Host:** CT 108 (kittentts) on Proxmox pve node
- **IP:** 192.168.100.51
- **SSH:** `ssh root@192.168.100.51` (standard homelab keys)
- **Binary:** `/opt/kitten-tts-server` (Rust, v0.2.2 from second-state/kitten_tts_rs)
- **Model:** `/opt/models/kitten-tts-mini` (80M params, 77MB, best quality)
- **Service:** `systemctl {status,restart} kittentts`
- **Port:** 8080

## Available Models

| Model | Path | Params | Size | Note |
|---|---|---|---|---|
| mini | `/opt/models/kitten-tts-mini` | 80M | 77 MB | **Active**. Best quality |
| micro | `/opt/models/kitten-tts-micro` | 40M | 42 MB | Balanced |
| nano | `/opt/models/kitten-tts-nano` | 15M | 55 MB | fp32 |
| nano-int8 | `/opt/models/kitten-tts-nano-int8` | 15M | 26 MB | Smallest |

## API (OpenAI-compatible)

```
POST http://192.168.100.51:8080/v1/audio/speech
Content-Type: application/json

{
  "input": "Text to speak",
  "voice": "onyx",
  "model": "kitten-tts",
  "response_format": "mp3",
  "speed": 1.0
}
```

### Voice Mapping

| OpenAI name | KittenTTS voice | Gender |
|---|---|---|
| alloy | Bella | Female |
| echo | Jasper | Male |
| fable | Luna | Female |
| onyx | Bruno | Male |
| nova | Rosie | Female |
| shimmer | Hugo | Male |

Also available directly: `Kiki` (F), `Leo` (M)

### Formats

`mp3` (128k CBR, 44.1kHz), `opus` (OGG, 48kHz), `flac` (24kHz), `wav` (16-bit PCM, 24kHz), `pcm` (raw 16-bit LE, 24kHz — required for SSE streaming)

### Streaming (SSE)

Set `"stream": true` with `"response_format": "pcm"` for Server-Sent Events with base64 PCM chunks. Compatible with OpenAI streaming format.

### Other Endpoints

- `GET /health` — `{"status":"ok"}`
- `GET /v1/models` — lists `kitten-tts` model

## Operations

```bash
# Restart
ssh root@192.168.100.51 systemctl restart kittentts

# Check status
ssh root@192.168.100.51 systemctl status kittentts

# CLI test
ssh root@192.168.100.51 /opt/kitten-tts /opt/models/kitten-tts-mini "test" -v Jasper -o /tmp/test.wav

# Switch to a different model
ssh root@192.168.100.51 systemctl stop kittentts
ssh root@192.168.100.51 "sed -i 's|models/kitten-tts-mini|models/kitten-tts-nano-int8|' /etc/systemd/system/kittentts.service"
ssh root@192.168.100.51 "systemctl daemon-reload && systemctl start kittentts"
```

## Hermes Integration

KittenTTS replaces EdgeTTS as Hermes' TTS provider via the `openai` TTS path redirected to the local server.

### Config changes (`hermes config set`)

```bash
hermes config set tts.provider openai
hermes config set tts.openai.model kitten-tts
hermes config set tts.openai.voice nova      # Rosie; see voice mapping above
hermes config set tts.openai.base_url http://192.168.100.51:8080/v1
```

**Backup first:** `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.backup-kittentts`

**Dummy API key required:** The OpenAI TTS provider expects an API key even though KittenTTS needs none. Add to `~/.hermes/.env`:
```
VOICE_TOOLS_OPENAI_KEY=kittentts-local-no-auth
```

**Config file is write-protected** — Hermes blocks direct `patch`/`write_file` edits to `~/.hermes/config.yaml`. Must use `hermes config set` CLI commands instead. After config changes, restart the gateway (`systemctl --user restart hermes-gateway`) or exit/relaunch CLI for the new TTS to take effect.

### Voice selection

Generate samples for all voices from the server to let the user pick:
```bash
for voice in alloy echo fable onyx nova shimmer; do
  curl -s -X POST http://192.168.100.51:8080/v1/audio/speech \
    -H "Content-Type: application/json" \
    -d "{\"input\": \"Hello, I'm ${voice}.\", \"voice\": \"$voice\"}" \
    -o /tmp/kittentts-${voice}.mp3
done
```

Online demo also available at https://kitten-tts.com for all 8 voices.

### CLI Gotcha

The CLI takes model dir as a **positional** arg, not `--model`:
```bash
# WRONG
./kitten-tts --model kitten-tts-mini "text"

# RIGHT
./kitten-tts models/kitten-tts-mini "text" --voice Jasper --output /tmp/test.wav
```

## Pitfalls

1. **CLI takes the model dir as a positional arg, not `--model`** — `./kitten-tts --model kitten-tts-mini "text"` silently fails or uses the wrong model. Recovery: `./kitten-tts models/kitten-tts-mini "text" --voice Jasper --output /tmp/test.wav` (positional model dir first).
2. **SSH to the wrong host** — The server is on CT 108 at `192.168.100.51`, not the PVE host. Recovery: `ssh root@192.168.100.51` for service management; `ssh root@192.168.100.23` only if you need PVE-level access.
3. **Editing `~/.hermes/config.yaml` directly** — Hermes blocks direct `patch`/`write_file` edits to the config file. Recovery: use `hermes config set tts.*` CLI commands, then restart the gateway (`systemctl --user restart hermes-gateway`).
4. **Skipping the dummy API key** — The OpenAI TTS provider expects a key even though KittenTTS needs none. Without `VOICE_TOOLS_OPENAI_KEY=kittentts-local-no-auth` in `~/.hermes/.env`, requests fail auth. Recovery: add the dummy key, then restart.
5. **Not restarting the gateway after config changes** — `hermes config set` alone doesn't reload TTS. Recovery: `systemctl --user restart hermes-gateway` (or relaunch CLI) after changing `tts.*`.
6. **Forgetting `response_format: pcm` for SSE streaming** — Streaming only works with `"stream": true` AND `"response_format": "pcm"`. Recovery: request PCM for streamed output; use mp3/opus for file output.
7. **Switching models without daemon-reload** — Editing the systemd unit path then only `systemctl start` may run the old unit definition. Recovery: `systemctl daemon-reload && systemctl start kittentts` after `sed` on the unit.
8. **Expecting GPU** — KittenTTS is CPU-only; a slow first request (cold load ~125 MB) is normal, not a fault. Recovery: warm it with a health check (`GET /health`) before latency-sensitive calls.

## Resources

- ~125 MB RAM idle (mini model loaded)
- CPU-only, no GPU required
- 5.28s to generate 3.99s of audio (RTF ~0.13 for API warm)
