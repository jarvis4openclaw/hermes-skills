---
name: f5-tts-setup
description: Install F5-TTS on CPU-only CT with OpenAI API wrapper.
version: 1.1.0
tags: [devops, tts, f5-tts, voice-cloning, cpu, proxmox]
metadata:
  hermes:
    tags: [devops, tts, f5-tts, voice-cloning, cpu, proxmox]
    trigger_conditions:
      - "install f5-tts"
      - "F5-TTS voice cloning"
      - "TTS on CPU proxmox"
      - "OpenAI compatible TTS server"
      - "f5-server setup"
      - "torchcodec CUDA error"
      - "voice cloning slower real time"
      - "f5-tts systemd service"
      - "replace chatterbox turbo"
      - "CPU only tts inference"
---

# F5-TTS Setup on CPU-Only Proxmox CT

Install F5-TTS voice cloning on a CPU-only LXC container with an OpenAI-compatible API wrapper. Replaces Chatterbox-Turbo for higher quality voice cloning at the cost of speed (~0.02x real-time vs ~real-time).

## When to Use

- Setting up F5-TTS voice cloning on a CPU-only Proxmox LXC.
- Replacing Chatterbox-Turbo with a higher-quality TTS backend.
- Debugging a broken f5-tts install (torchcodec/CUDA errors, server not starting, model lazy-load hangs).
- Wiring an OpenAI-compatible TTS endpoint into a pipeline or agent.
- Estimating whether a given CPU box can run F5-TTS acceptably (RAM/disk/CPU requirements).

## Not For

- GPU-backed TTS or high-throughput synthesis → use a GPU host or a faster engine (e.g. Chatterbox-Turbo) when real-time matters.
- Other TTS engines (Piper, Coqui, ESPnet) → each has its own setup; this skill is F5-TTS specific.
- Audio post-processing, diarization, or ASR → those belong to separate audio skills.
- Setting up TTS inside the main Hermes host rather than an isolated CT → the systemd/venv layout here assumes a dedicated container.

## Hardware Requirements
- **RAM:** 16GB (model uses ~3GB, server overhead ~1GB, ffmpeg/etc)
- **Disk:** 50GB+ (model weights ~1.6GB, venv ~2.2GB)
- **CPU:** Any x86_64 (i5-7600K tested, ~6 min/sec audio)
- **GPU:** None required (CPU-only)

## Installation Steps

### 1. Resize CT from Proxmox
```bash
pct resize <CT_ID> rootfs 50G
pct set <CT_ID> -memory 16384 -swap 2048
pct reboot <CT_ID>
```

### 2. Create venv and install PyTorch CPU
```bash
python3 -m venv /opt/f5-venv
source /opt/f5-venv/bin/activate
pip install --no-cache-dir torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir numpy
pip install --no-cache-dir f5-tts
```

### 3. Uninstall torchcodec (CUDA dependency, breaks on CPU)
```bash
pip uninstall -y torchcodec
```

### 4. Create API server
Deploy `/opt/f5-server.py` — an OpenAI-compatible FastAPI server.

**Key F5TTS API differences from older docs:**
- `F5TTS(device="cpu")` — no model_type arg
- `model.infer(ref_file=..., ref_text=..., gen_text=..., speed=..., nfe_step=32, remove_silence=True)` returns `(wav_array, sample_rate, spectrogram)`
- wav needs normalization: `wav / max(abs(wav)) * 0.95`, then `(wav * 32767).astype(np.int16)`

**OpenAI-compatible endpoint differences:** field is `input` not `text`.

### 5. Create systemd service
```bash
cat > /etc/systemd/system/f5-tts.service << 'EOF'
[Unit]
Description=F5-TTS Voice Cloning Server
After=network.target

[Service]
Type=simple
ExecStart=/opt/f5-venv/bin/python /opt/f5-server.py
WorkingDirectory=/opt
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1
Environment=TORCHCODEC_DISABLE=1

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable --now f5-tts
```

## Pitfalls

1. **torchcodec pulls in CUDA libs by default** — On a CPU-only CT this breaks import or wastes space. Recovery: `pip uninstall -y torchcodec`, set `TORCHCODEC_DISABLE=1` in the systemd unit, and re-test `python -c "import torch; print(torch.cuda.is_available())"` (must be `False`).

2. **Empty `ref_text` triggers auto-transcription** — If `ref_text` is omitted, F5-TTS transcribes the ref audio first (adds ~2 min per request). Recovery: pre-transcribe the reference clip and always pass `ref_text` explicitly for latency-sensitive calls.

3. **CPU synthesis is ~6 min/sec audio on i5-7600K** — A 30s briefing ≈ 40 min of compute. Recovery: set `TTS_TIMEOUT=7200` in calling scripts and generate in the background; never inline a long clip into a foreground flow.

4. **First request lazy-loads the model** — ~6s warm-up on the first call, then the model stays warm in memory. Recovery: pre-warm with a tiny request after restart, or health-check `/health` before timing a real synthesis.

5. **The API field is `input`, not `text`** — The OpenAI-compatible wrapper differs from F5-TTS's native API. Recovery: when a client 422s on `text`, switch to `{"input": ...}` and re-check the server log for the accepted schema.

6. **WAV output must be normalized before int16** — `wav / max(abs(wav)) * 0.95`, then `(wav * 32767).astype(np.int16)`; skipping normalization produces clipped/quiet audio. Recovery: apply the normalization before writing the file and verify peak amplitude.

7. **`pct resize` on a live CT needs a reboot** — Resizing rootfs while running can wedge the filesystem. Recovery: `pct resize` → `pct set -memory/-swap` → `pct reboot` before installing; verify `df -h` after boot.
