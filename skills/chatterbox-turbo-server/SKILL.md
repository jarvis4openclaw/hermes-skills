---
name: chatterbox-turbo-server
description: Chatterbox-Turbo voice cloning TTS server on Proxmox CT 109. Use when asked to generate speech with voice cloning, test cloned voices, or manage the Chatterbox-Turbo server.
category: devops
tags: [tts, voice-cloning, chatterbox, proxmox]
version: 1.1.0
metadata:
  hermes:
    tags: [tts, voice-cloning, chatterbox, proxmox]
    trigger_conditions:
      - "Generate speech with voice cloning"
      - "Test a cloned voice"
      - "Chatterbox-Turbo / chatterbox server"
      - "Mariah voice TTS"
      - "Manage the TTS server on CT 109"
      - "Voice briefing audio is broken or monotone"
      - "Which TTS engine should the daily brief use"
      - "F5-TTS vs Chatterbox comparison"
      - "192.168.100.49 speech endpoint"
      - "TTS CPU dtype mismatch"
---

# Chatterbox-Turbo Server

Voice cloning TTS using Chatterbox-Turbo (ResembleAI). Runs on CPU-only CT 109. Provides OpenAI-compatible API for voice synthesis with cloned voices from reference audio.

## When to Use

- Generating the daily voice briefing with the Mariah cloned voice.
- Testing or comparing cloned-voice TTS engines (Chatterbox vs F5-TTS vs KittenTTS vs Gemini).
- Diagnosing broken/monotone briefing audio (dtype crashes, temperature/speed tuning).
- Managing the chatterbox systemd service, HF cache, or CT disk usage.
- Patching the two known CPU dtype mismatches after a package reinstall.

## Not For

- General-purpose Hermes TTS (quick text-to-speech outside the briefing) → use `kittentts-server` instead.
- Natural prosody with real pitch/emotion control → use Gemini Flash TTS (`media/audio-transcription`) instead; Chatterbox on CPU lacks true prosody control.
- Installing or tuning F5-TTS itself → use `f5-tts-setup` instead.
- Voice cloning dataset prep (audio → TTS manifests) → use `voice-cloning-workflow` instead.
- Other homelab CT management → use `proxmox-ssh-lifecycle` / `proxmox` instead.

## Infrastructure

- **Host:** CT 109 (chatterbox-tts) on Proxmox pve node
- **IP:** 192.168.100.49
- **SSH:** `ssh root@192.168.100.49` (standard homelab keys)
- **Server:** `/opt/chatterbox-server.py` (FastAPI + uvicorn)
- **Package:** `/opt/chatterbox/` (editable install from ResembleAI/chatterbox)
- **Service:** `systemctl {status,restart} chatterbox`
- **Port:** 8080
- **Python venv:** `/opt/venv/` (PyTorch 2.6.0+cu124, but running CPU-only)

## Reference Voices

| Name | Path | Note |
|---|---|---|
| mariah | `/opt/voices/mariah_ref.wav` | Primary cloned voice (8.1MB reference) |

## API (OpenAI-compatible)

```bash
POST http://192.168.100.49:8080/v1/audio/speech
Content-Type: application/json

{
  "text": "Text to speak",
  "voice": "mariah",
  "response_format": "opus",
  "speed": 1.0
}
```

### Endpoints

- `POST /v1/audio/speech` — Generate speech with cloned voice
- `GET /health` — `{"status":"ok","model":"ChatterboxTurboTTS","sample_rate":24000}`
- `GET /v1/models` — Lists `chatterbox-turbo` model

### Formats

`opus` (64k CBR, 24kHz), `wav` (raw, 24kHz)

## Critical Pitfall: CPU Dtype Mismatch

Chatterbox-Turbo has **two** dtype mismatches when running on CPU (works fine on CUDA). Both must be patched.

### Patch 1: s3tokenizer.py

**Bug:** `RuntimeError: expected scalar type Double but found Float`

**Location:** `/opt/chatterbox/src/chatterbox/models/s3tokenizer/s3tokenizer.py` line 163

**Original code:**
```python
mel_spec = self._mel_filters.to(self.device) @ magnitudes
```

**Fix:**
```python
mel_spec = self._mel_filters.to(self.device).float() @ magnitudes.float()
```

**Apply fix:**
```bash
sed -i 's/mel_spec = self._mel_filters.to(self.device) @ magnitudes/mel_spec = self._mel_filters.to(self.device).float() @ magnitudes.float()/' \
  /opt/chatterbox/src/chatterbox/models/s3tokenizer/s3tokenizer.py
```

### Patch 2: voice_encoder.py

**Bug:** `ValueError: input must have the type torch.float32, got type torch.float64`

**Location:** `/opt/chatterbox/src/chatterbox/models/voice_encoder/voice_encoder.py` line 242

**Original code:**
```python
utt_embeds = self.inference(mels.to(self.device), mel_lens, batch_size=batch_size, **kwargs).numpy()
```

**Fix:**
```python
utt_embeds = self.inference(mels.to(self.device).float(), mel_lens, batch_size=batch_size, **kwargs).numpy()
```

**Apply fix:**
```bash
sed -i 's/self.inference(mels.to(self.device), mel_lens/self.inference(mels.to(self.device).float(), mel_lens/' \
  /opt/chatterbox/src/chatterbox/models/voice_encoder/voice_encoder.py
```

### Restart After Patching

```bash
systemctl restart chatterbox
```

### Why It Happens

On CPU, `_mel_filters` and mel inputs end up as float64 (Double) while the rest of the model expects float32. PyTorch refuses to multiply mismatched dtypes and the LSTM layer rejects float64 inputs. On CUDA, tensors are automatically cast to float32, so these bugs don't appear.

**Note:** The package is installed as **editable** (`pip install -e .`), so source lives at `/opt/chatterbox/src/chatterbox/...`, NOT under `site-packages`. Patching site-packages will fail with `FileNotFoundError`.

## Operations

```bash
# Check status
ssh root@192.168.100.49 systemctl status chatterbox

# Restart service
ssh root@192.168.100.49 systemctl restart chatterbox

# View logs
ssh root@192.168.100.49 journalctl -u chatterbox -n 50 --no-pager

# Test TTS generation (should produce >1KB real audio)
curl -s -X POST http://192.168.100.49:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, this is a test.","response_format":"opus"}' \
  -o /tmp/test.opus
ls -lh /tmp/test.opus
```

## Troubleshooting Order (when the briefing is broken)

Run these checks in order — they cover the four failure modes seen in production:

1. **Is the service up?** `ssh root@192.168.100.49 systemctl is-active chatterbox` — if not, `systemctl restart chatterbox` and re-check.
2. **Is the model loaded correctly?** `ssh root@192.168.100.49 journalctl -u chatterbox -n 20` — the log should show `from_local("/opt/chatterbox/mariah_model")`. If it shows the stock HF base model path, the LoRA fine-tune is not being loaded.
3. **Is the payload reaching the server?** Check the `/opt/chatterbox-server.py` hardcoded generation values (see "LIVE SERVER IGNORES THESE" note) — if the script sends `temperature`/`speed` but the server hardcodes `temperature=0.8, top_p=0.95`, the audio will be flat/monotone regardless of the payload.
4. **Is the audio actually generated?** `curl -s -X POST http://192.168.100.49:8080/v1/audio/speech -H "Content-Type: application/json" -d '{"text":"Hello, this is a test.","response_format":"opus"}' -o /tmp/test.opus && ls -lh /tmp/test.opus` — an `ls` output of `0` bytes or `<1KB` means generation failed (dtype crash, model load failure).

## Fine-Tuned Mariah Model (deployed 2026-08-03)

The server NO LONGER loads the stock HF base model. It loads `ChatterboxTurboTTS.from_local("/opt/chatterbox/mariah_model")` — a **LoRA fine-tune merged into the base T3 transformer**.

- **Training output:** `/mariah/` (adapter_model.safetensors 630MB, checkpoint-epoch-2/, STATUS.md), `/root/voice_prep/` (dataset, training repo `chatterbox-finetuning/`, merge logs)
- **Adapter config:** r=128, lora_alpha=256, dropout=0, targets `c_attn/c_proj/c_fc/spkr_enc`, modules_to_save `text_emb/text_head`, base `ResembleAI/chatterbox-turbo`
- **Dataset:** 5,125 Mariah clips (audiobook narration + Harper's Bazaar), 2,089 transcribed rows; diarization was INCOMPLETE (pyannote API error)
- **Merge:** `merge4.log` — 1,984 new vocab tokens mean-initialized into T3 embedding/head (new vocab 52260); merged weights saved to `chatterbox_output/t3_turbo_finetuned_merged.safetensors`
- **Deploy:** merged file copied to `/opt/chatterbox/mariah_model/t3_turbo_v1.safetensors` (md5 0f8a959d… matches), service restarted 01:02 UTC Aug 3, 0 restarts since
- **Verification:** `md5sum /root/voice_prep/chatterbox-finetuning/chatterbox_output/t3_turbo_finetuned_merged.safetensors /opt/chatterbox/mariah_model/t3_turbo_v1.safetensors` → identical
- Auxiliary weights (`s3gen_meanflow.safetensors`, `ve.safetensors`) are still base — LoRA only touched T3. The served tokenizer files (vocab.json/merges.txt) appear to be base-size (50259) while the T3 embeddings were extended — harmless in practice since extra rows are never addressed.
- **Side note:** the training added tokens to the T3 embedding, so the served `tokenizer_config.json`/`vocab.json` are the base ones while the T3 tensor is extended. Do NOT "fix" this by replacing tokenizer files — the model works and the extra rows are unused.

## Integration with Voice Briefing

The `morning-brief-voice.sh` script uses TTS for the daily voice briefing:
1. Fetches calendar events (Outlook + Family Room + Cal.com)
2. Generates natural monologue via Ollama (`llama3.2:3b`)
3. Synthesizes speech via a TTS endpoint
4. Sends to Telegram as voice message (script handles its own Telegram delivery — cron deliver is `local`)

**Script location:** `~/.hermes/scripts/morning-brief-voice.sh`

**Current cron schedule (2026-07-29):**
- Voice brief (`daily-morning-brief-voice`): **2:00am** — runs overnight so F5-TTS's ~40min CPU generation finishes before morning
- Text brief (`daily-morning-brief`): **8:00am** — fires after the audio is ready

**Overnight CPU TTS pattern:** When using slow CPU-only TTS (F5-TTS), schedule the job at least 1 hour before wake time to absorb CPU inference latency. The script handles download + Telegram delivery on its own; cron deliver is `local` since the script sends directly.

**⚠️ Cron timeout vs TTS speed — critical constraint:** The cron scheduler enforces a hard timeout (default 3600s for this user's profile). F5-TTS on CPU takes ~40 min (2400s) per 30s briefing. This *nearly* fits within a 3600s window but has no margin for error. Chatterbox Turbo (~2-3 min) fits easily. When swapping TTS engines, always verify both the curl `--max-time` AND the cron scheduler's `max_runtime_seconds` — the smaller value wins and silently kills the script.

**2026-07-30 incident:** Script was changed from Chatterbox Turbo (port 8080, ~2-3 min) to F5-TTS (port 7860, ~40 min). Cron killed it at 3600s before F5-TTS finished. Fixed by reverting the engine back to Chatterbox Turbo. The `.bak` file of the script was preserved and used to extract the working Chatterbox payload format (`{text:..., voice:"mariah", response_format:"opus"}`).

### TTS Options (Sorted by User-Preference)

| Service | Voice | Prosody | Speed | Cost | Port |
|---------|-------|---------|-------|------|------|
| Chatterbox-Turbo (current) | Mariah (cloned) | — (flat default) | ~10-15s | $0 | 8080 |
| Chatterbox Variant 1 ★ | Mariah (tuned) | User-says "a lot better" | ~10-15s | $0 | 8080 |
| F5-TTS | Mariah (better clone) | Natural | ~5 min CPU | $0 | 7860 |
| Gemini 3.1 Flash TTS | Zephyr (pre-built) | Excellent | ~2-3s | ~$0.60/mo | — |

**★ Chatterbox Variant 1 (User-Validated Fix — temp=1.2, speed=1.05):**
```json
{
  "text": "Text to speak",
  "voice": "mariah",
  "response_format": "opus",
  "temperature": 1.2,
  "top_p": 0.95,
  "speed": 1.05
}
```
The user explicitly validated these settings sound "a lot better" than default. This is the recommended default. See Tuning Prosody section for limitations.

**⚠️ LIVE SERVER IGNORES THESE (verified 2026-08-04):** `/opt/chatterbox-server.py` hardcodes `temperature=0.8, top_p=0.95, repetition_penalty=1.2` in the `model.generate()` call and never reads `request.speed` or `request.temperature`. So the Variant 1 payload has NO effect on the current server — the voice brief runs at temp 0.8/flat regardless of what the script sends. To actually apply the validated tuning, edit the hardcoded values in `/opt/chatterbox-server.py` and `systemctl restart chatterbox` (back up the file first). The script's payload params are decorative until then.

**✅ FIXED 2026-08-04:** The server now reads `temperature`, `top_p`, and `repetition_penalty` from the request (defaults 0.8/0.95/1.2, overridable). The `speed` param is now honored via ffmpeg `atempo` filter on the WAV before opus encoding (clamped 0.5–100; <1.0 slows down, >1.0 speeds up). `morning-brief-voice.sh` now sends `temperature: 1.2, speed: 0.95` (0.95 = slightly slower than default, user preference — default 1.0 felt too fast).

**⚠️ Name pronunciation: "Waaheed" (phonetic spelling) — user-validated 2026-08-04:** The TTS model does NOT pronounce "Wahid" or "Waheed" cleanly (Whisper hears "Wehide", "Winheed", "Rayene"). The spelling **"Waaheed"** produces the correct "Waheed" pronunciation — user explicitly confirmed "the second audio sounded pretty good" (isolated test with "Good morning Waaheed, have a great day."). The morning-brief prompt now instructs Ollama to spell the name exactly as **"Waaheed"** and never "Wahid". Do NOT revert to "Waheed" or "Wahid" in the dictation text.

**⚠️ CRITICAL: Length limit for the fine-tuned model (~450 chars):** The fine-tuned Mariah model degrades on long text. Verified 2026-08-04: a 588-char brief produced a **cut-off tail with gibberish** (the closing quote + "i love you" were destroyed); a 280-char brief and a 314-char brief completed **cleanly with intact endings**. Root cause: `tts_turbo.py` strips all speech tokens ≥ 6561 (`speech_tokens = speech_tokens[speech_tokens < 6561]`) after generation — with the fine-tune's extended 52,260-token vocab, the model is more likely to emit OOV tokens near the tail of long text, and the whole tail gets removed. Keep briefings **under 450 characters**. Ollama sometimes ignores the 450-char instruction — `morning-brief-voice.sh` now has a **HARD TRUNCATION GUARD**: if dictation >450 chars, it truncates at the last sentence boundary under 450 before sending to TTS.

**⚠️ No "[happy] i love you" closer (removed 2026-08-04):** The script previously appended `[happy] i love you!` to the dictation. User requested its removal — it contributed to the tail truncation and was disliked. The prompt now explicitly says *"Do NOT add any closing sign-off like 'I love you' or similar."*

### F5-TTS (Voice Cloning, port 7860)

F5-TTS is installed on the same CT 109, offering better voice cloning fidelity than Chatterbox-Turbo. See `references/f5-tts.md` for full install/service details (API signature, torchcodec CPU fix, performance benchmarks).

### Alternative TTS: OpenRouter Gemini

`google/gemini-3.1-flash-tts-preview` via OpenRouter is a tested working alternative (PCM-only format, convert to mp3 with ffmpeg). Voice `Zephyr`. See `media/audio-transcription/references/openrouter-tts.md`.

**Monthly cost estimate:** ~$0.60/mo for a daily 500-character brief ($0.02/run).

**Gemini voice cloning:** Not supported — 30 pre-built voices only (Zephyr, Kore, Charon, etc.).

### Script One-Off Test Pattern

To test an alternative TTS without modifying the cron job:
1. Run Ollama dictation manually (extract the curl from the script)
2. Feed resulting text to alternative TTS endpoint
3. Deliver audio to Telegram manually
4. Cron job remains unchanged

## Resource Requirements

- **RAM:** ~1.8GB when model loaded
- **Disk:** 30GB CT (8.4GB venv, 2GB HF cache after cleanup)
- **CPU:** 4 cores
- **GPU:** None required (CPU-only inference)
- **Generation time:** ~10-15s for typical briefing (60-80 tokens)

## Disk Space Management

The HuggingFace cache at `/root/.cache/huggingface` can grow large during model downloads. If you hit "No space left on device":

```bash
ssh root@192.168.100.49 'rm -rf /root/.cache/huggingface && systemctl restart chatterbox'
```

Or expand CT disk from Proxmox host:
```bash
pct resize 109 rootfs 30G  # Adjust size as needed
```

## Model Parameters (Chatterbox-Turbo)

From source code analysis, these parameters matter:
- `temperature` (default 0.8, range 0.8–1.5) — sampling temperature
- `top_p` (default 0.95) — nucleus sampling
- `top_k` (default 1000) — top-k sampling
- `repetition_penalty` (default 1.2) — penalize repeated tokens
- `speed` (default 1.0, range 0.5–2.0) — playback speed

**Ignored by Turbo:**
- `exaggeration` — logged as warning, not used
- `cfg_weight` — logged as warning, not used
- `min_p` — logged as warning, not used

These are ignored because Turbo uses a faster inference path that doesn't support CFG or min_p sampling.

### Tuning Prosody (Fixing Monotone Output)

The Mariah voice at default parameters (temp=0.8, speed=1.0) produces flat, monotone speech due to the Turbo fast-path's limited prosody control. The user described it as "not well-modulated" and "very monotone."

**User-validated fix:** Raise temperature to **1.2** and speed to **1.05**:
```json
{
  "text": "Text to speak",
  "voice": "mariah",
  "response_format": "opus",
  "temperature": 1.2,
  "top_p": 0.95,
  "speed": 1.05
}
```

This introduces enough codec-token variation to add natural pitch contour without audible artifacts. Temperature above 1.5 or speed above 1.1 introduces audible warble/instability.

**Important limitation:** These parameters affect the *codec token distribution* (which words get slightly different phonetic renderings), NOT prosody directly (pitch contour, emotional emphasis, dynamic range). The Turbo model on CPU lacks true prosody control — `exaggeration` is explicitly ignored. Temperature/speed bumps are a workaround, not a fix for the architectural limitation. For natural dynamic range with real prosody, use Gemini 3.1 Flash TTS (see Alternative TTS section).

**One-off comparison test pattern (no script changes):**
```bash
# 1. Run Ollama dictation manually
curl -s http://localhost:11434/api/generate -d '{"model":"llama3.2:3b","stream":false,"prompt":"..."}' | jq -r '.response' > /tmp/dictation.txt

# 2. Feed to Chatterbox (current)
curl -s -X POST http://192.168.100.49:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg text "$(cat /tmp/dictation.txt)" '{text: $text, voice: "mariah", response_format: "opus", temperature: 1.2, speed: 1.05}')" \
  -o /tmp/chatterbox_test.opus

# 3. Feed same text to Gemini TTS for comparison
# ... (see references/openrouter-tts.md)

# 4. Listen to both, cron job unchanged
```

## Comparison with KittenTTS

| Feature | KittenTTS (CT 108) | Chatterbox-Turbo (CT 109) |
|---|---|---|
| **Voice cloning** | ❌ No (fixed voices only) | ✅ Yes (from reference audio) |
| **Voice quality** | Good (pre-trained) | Excellent (cloned + expressive) |
| **Speed** | Fast (RTF ~0.13) | Slower (~10-15s per briefing) |
| **RAM** | ~125MB | ~1.8GB |
| **Use case** | Hermes TTS provider | Cloned voice briefings |
| **API** | OpenAI-compatible | OpenAI-compatible |

Both servers can coexist. Use KittenTTS for general Hermes TTS, Chatterbox-Turbo for voice cloning scenarios.

## Pitfalls

1. **CPU dtype mismatch after any package reinstall** — The two CPU patches (s3tokenizer float() and voice_encoder float()) live in the *editable* source at `/opt/chatterbox/src/chatterbox/...`, not site-packages. A `pip install -e` refresh or package upgrade wipes them → `RuntimeError: expected scalar type Double but found Float` on the next synthesis. Re-apply both `sed` patches (see Critical Pitfall section) and `systemctl restart chatterbox`. Verify with a >1KB opus output, not just a 200 status.

2. **Cron timeout vs TTS speed silently kills the briefing** — The cron scheduler enforces a hard `max_runtime_seconds` (3600s for this user's profile). F5-TTS on CPU takes ~40 min (2400s) per 30s briefing — nearly fits but has zero margin; Chatterbox (~10-15s) fits easily. When swapping engines, verify BOTH the curl `--max-time` and the cron job's `max_runtime_seconds` — the smaller value wins and kills the script silently. Observed 2026-07-30: the F5-TTS switch got killed at 3600s; reverting to Chatterbox fixed it.

3. **Patching site-packages fails with FileNotFoundError** — The package is installed editable (`pip install -e .`), so source lives under `/opt/chatterbox/src/chatterbox/`, NOT `site-packages`. Always patch `/opt/chatterbox/src/chatterbox/...` paths.

4. **Monotone output treated as an engine bug** — Mariah at defaults (temp=0.8, speed=1.0) is flat because Turbo's fast path has no true prosody control (`exaggeration` is logged as a warning and ignored). The user-validated fix is temp=1.2 + speed=1.05; above 1.5/1.1 introduces audible warble. If you need real pitch/emotion range, use Gemini Flash TTS instead — don't fight the architecture.

5. **HF cache grows until "No space left on device"** — `/root/.cache/huggingface` accumulates model downloads on the 30GB CT. Clear it with `ssh root@192.168.100.49 'rm -rf /root/.cache/huggingface && systemctl restart chatterbox'` or resize the CT rootfs with `pct resize 109 rootfs 30G`.

6. **Assuming non-OpenAI params work** — `exaggeration`, `cfg_weight`, and `min_p` are accepted by the API but logged as warnings and ignored by the Turbo fast path. Don't spend time tuning them; only `temperature`, `top_p`, `top_k`, `repetition_penalty`, and `speed` have effect.

7. **Gemini TTS returns PCM-only audio** — If you switch to `google/gemini-3.1-flash-tts-preview`, the output is raw PCM, not mp3/opus. Convert with ffmpeg before delivery, or the Telegram voice message will be unplayable. Cost is ~$0.60/mo for a daily 500-char brief.
