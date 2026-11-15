---
name: heartmula
description: "Generate full songs locally from lyrics plus style tags with HeartMuLa (heartlib) — open-source Apache-2.0 music foundation models (3B/7B) with the HeartCodec vocoder, plus the setup work (dependency pins, RoPE and codec patches, checkpoint downloads) and the parameter tuning. Use for offline or self-hosted AI music generation, a Suno alternative, or heartlib installation. Not for speech/TTS, transcription, or audio repair."
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [music, audio, generation, ai, heartmula, heartcodec, lyrics, songs]
    related_skills: [kittentts-server, f5-tts-setup, audiocraft, social-media-transcription]
    trigger_conditions:
      - "generate a song from lyrics"
      - "make music with AI locally"
      - "open source Suno alternative"
      - "HeartMuLa"
      - "heartlib"
      - "generate music from tags"
      - "offline music generation"
      - "turn lyrics into a song"
      - "install HeartMuLa"
      - "AI song with vocals"
      - "generate an mp3 from a text prompt"
      - "music generation model on my GPU"
      - "Suno but self-hosted"
---

# HeartMuLa - Open-Source Music Generation

## Overview
HeartMuLa is a family of open-source music foundation models (Apache-2.0) that generates music conditioned on lyrics and tags, with multilingual support. Generates full songs from lyrics + tags. Comparable to Suno for open-source. Includes:
- **HeartMuLa** - Music language model (3B/7B) for generation from lyrics + tags
- **HeartCodec** - 12.5Hz music codec for high-fidelity audio reconstruction
- **HeartTranscriptor** - Whisper-based lyrics transcription
- **HeartCLAP** - Audio-text alignment model

## When to Use
- User wants to generate music/songs from text descriptions
- User wants an open-source Suno alternative
- User wants local/offline music generation
- User asks about HeartMuLa, heartlib, or AI music generation
- Setting up heartlib on a fresh machine: venv, the dependency upgrades, the two source patches, checkpoint download
- Choosing model size / device split / `--lazy_load` for the VRAM actually available
- Tuning output: `--temperature`, `--topk`, `--cfg_scale`, `--max_audio_length_ms`
- Diagnosing a run that OOMs, produces silence, or ignores the style tags

## Not For

- **Text-to-speech, voice cloning or dubbing** → use `kittentts-server` (or `f5-tts-setup` to stand one up) instead.
- **Music generation with MusicGen / AudioCraft** → use `audiocraft` instead; this skill covers HeartMuLa only.
- **Transcribing lyrics or speech from an existing audio file** → use `social-media-transcription` instead.
- **Downloading or converting media files** (yt-dlp, format conversion) → use `social-video-download` instead.
- **Building the model itself** (training, fine-tuning, quantization) — nothing here trains; the checkpoints are downloaded and run as-is.
- **A generic "install a Python ML project" request** with no HeartMuLa content — follow the project's own README.

## Hardware Requirements
- **Minimum**: 8GB VRAM with `--lazy_load true` (loads/unloads models sequentially)
- **Recommended**: 16GB+ VRAM for comfortable single-GPU usage
- **Multi-GPU**: Use `--mula_device cuda:0 --codec_device cuda:1` to split across GPUs
- 3B model with lazy_load peaks at ~6.2GB VRAM

## Installation Steps

### 1. Clone Repository
```bash
cd ~/  # or desired directory
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
```

### 2. Create Virtual Environment (Python 3.10 required)
```bash
uv venv --python 3.10 .venv
. .venv/bin/activate
uv pip install -e .
```

### 3. Fix Dependency Compatibility Issues

**IMPORTANT**: As of Feb 2026, the pinned dependencies have conflicts with newer packages. Apply these fixes:

```bash
# Upgrade datasets (old version incompatible with current pyarrow)
uv pip install --upgrade datasets

# Upgrade transformers (needed for huggingface-hub 1.x compatibility)
uv pip install --upgrade transformers
```

### 4. Patch Source Code (Required for transformers 5.x)

**Patch 1 - RoPE cache fix** in `src/heartlib/heartmula/modeling_heartmula.py`:

In the `setup_caches` method of the `HeartMuLa` class, add RoPE reinitialization after the `reset_caches` try/except block and before the `with device:` block:

```python
# Re-initialize RoPE caches that were skipped during meta-device loading
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

**Why**: `from_pretrained` creates model on meta device first; `Llama3ScaledRoPE.rope_init()` skips cache building on meta tensors, then never rebuilds after weights are loaded to real device.

**Patch 2 - HeartCodec loading fix** in `src/heartlib/pipelines/music_generation.py`:

Add `ignore_mismatched_sizes=True` to ALL `HeartCodec.from_pretrained()` calls (there are 2: the eager load in `__init__` and the lazy load in the `codec` property).

**Why**: VQ codebook `initted` buffers have shape `[1]` in checkpoint vs `[]` in model. Same data, just scalar vs 0-d tensor. Safe to ignore.

### 5. Download Model Checkpoints
```bash
cd heartlib  # project root
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

All 3 can be downloaded in parallel. Total size is several GB.

## GPU / CUDA

HeartMuLa uses CUDA by default (`--mula_device cuda --codec_device cuda`). No extra setup needed if the user has an NVIDIA GPU with PyTorch CUDA support installed.

- The installed `torch==2.4.1` includes CUDA 12.1 support out of the box
- `torchtune` may report version `0.4.0+cpu` — this is just package metadata, it still uses CUDA via PyTorch
- To verify GPU is being used, look for "CUDA memory" lines in the output (e.g. "CUDA memory before unloading: 6.20 GB")
- **No GPU?** You can run on CPU with `--mula_device cpu --codec_device cpu`, but expect generation to be **extremely slow** (potentially 30-60+ minutes for a single song vs ~4 minutes on GPU). CPU mode also requires significant RAM (~12GB+ free). If the user has no NVIDIA GPU, recommend using a cloud GPU service (Google Colab free tier with T4, Lambda Labs, etc.) or the online demo at https://heartmula.github.io/ instead.

## Usage

### Basic Generation
```bash
cd heartlib
. .venv/bin/activate
python ./examples/run_music_generation.py \
  --model_path=./ckpt \
  --version="3B" \
  --lyrics="./assets/lyrics.txt" \
  --tags="./assets/tags.txt" \
  --save_path="./assets/output.mp3" \
  --lazy_load true
```

### Input Formatting

**Tags** (comma-separated, no spaces):
```
piano,happy,wedding,synthesizer,romantic
```
or
```
rock,energetic,guitar,drums,male-vocal
```

**Lyrics** (use bracketed structural tags):
```
[Intro]

[Verse]
Your lyrics here...

[Chorus]
Chorus lyrics...

[Bridge]
Bridge lyrics...

[Outro]
```

### Key Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max_audio_length_ms` | 240000 | Max length in ms (240s = 4 min) |
| `--topk` | 50 | Top-k sampling |
| `--temperature` | 1.0 | Sampling temperature |
| `--cfg_scale` | 1.5 | Classifier-free guidance scale |
| `--lazy_load` | false | Load/unload models on demand (saves VRAM) |
| `--mula_dtype` | bfloat16 | Dtype for HeartMuLa (bf16 recommended) |
| `--codec_dtype` | float32 | Dtype for HeartCodec (fp32 recommended for quality) |

### Performance
- RTF (Real-Time Factor) ≈ 1.0 — a 4-minute song takes ~4 minutes to generate
- Output: MP3, 48kHz stereo, 128kbps

## Pitfalls

1. **HeartCodec must not run in bf16** — bf16 degrades audio quality audibly. Keep the default
   `--codec_dtype float32`; only HeartMuLa itself wants bf16 (`--mula_dtype bfloat16`).

2. **Tags are often ignored** — upstream issue #90: lyrics dominate the conditioning and style tags
   land weakly or not at all. Reorder the tags (put the most important style first), shorten the
   lyrics, and re-generate; do not promise the user an exact style match.

3. **Generation OOMs on an 8–16GB card without `--lazy_load true`** — both models resident at once
   need more VRAM than the 3B model alone. Pass `--lazy_load true` (peak ≈6.2GB) and expect 30–60s of
   reload overhead per song; verify with the "CUDA memory" lines in the output.

4. **The pinned dependencies conflict with current packages (as of Feb 2026)** — `datasets` and
   `transformers` must be upgraded inside the venv before the model loads. Skipping this shows up as an
   import error or a `huggingface-hub` API mismatch, not as an obvious dependency failure.

5. **The RoPE cache is never rebuilt after meta-device loading** — `from_pretrained` builds the model on
   the meta device, so `Llama3ScaledRoPE.rope_init()` skips cache construction and never re-runs on the
   real device. Apply Patch 1 in `setup_caches` (re-init every `Llama3ScaledRoPE` whose cache is not
   built) or generation produces garbage with no error.

6. **Patching only one `HeartCodec.from_pretrained()` call site** — there are two (eager load in
   `__init__`, lazy load in the `codec` property). Both need `ignore_mismatched_sizes=True`; the lazy
   path is the one `--lazy_load true` actually hits, so a half-patch looks fine until you enable lazy
   loading.

7. **Missing or misplaced checkpoints** — `hf download --local-dir './ckpt'` for the generator plus
   `./ckpt/HeartMuLa-oss-3B` and `./ckpt/HeartCodec-oss` into the exact directory layout the code
   expects. A wrong path surfaces as a generic load failure, not a "file not found".

8. **No GPU: CPU mode technically works and is unusable in practice** — `--mula_device cpu
   --codec_device cpu` needs ~12GB+ free RAM and can take 30–60+ minutes per song versus ~4 minutes on
   a GPU. Recommend a cloud GPU (Colab T4, Lambda) or the online demo instead of "just waiting".

9. **Triton is unavailable on macOS** — GPU acceleration is Linux/CUDA only; Apple Silicon falls back to
   the CPU path above. Set expectations before installing.

10. **RTX 5080 reports incompatibility upstream** — check the issue tracker before promising a 50-series
    card will work; the workaround may lag the hardware.

11. **macOS/Linux-only install assumptions** — the project targets Linux; on macOS expect CPU-only speed.
    Windows is untested here, so treat it as an experiment rather than a supported path.

## Links
- Repo: https://github.com/HeartMuLa/heartlib
- Models: https://huggingface.co/HeartMuLa
- Paper: https://arxiv.org/abs/2601.10547
- License: Apache-2.0
