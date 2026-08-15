---
name: voice-cloning-workflow
description: "Voice clone dataset pipeline: raw audio to TTS manifests. Use when building a voice-clone dataset from audiobooks/interviews/podcasts — diarization, Groq Whisper batch transcription, resampling/loudnorm, and F5-TTS/Chatterbox/Qwen3 manifest generation."
version: 1.1.0
tags: [voice-cloning, tts, f5-tts, chatterbox, dataset, audio-pipeline, groq, whisper, fine-tuning]
metadata:
  hermes:
    tags: [voice-cloning, tts, f5-tts, chatterbox, dataset, audio-pipeline, groq, whisper, fine-tuning]
    trigger_conditions:
      - "build a voice clone dataset"
      - "prepare audio for TTS training"
      - "transcribe clips for voice cloning"
      - "diarize audiobook for cloning"
      - "f5-tts dataset prep"
      - "chatterbox dataset prep"
      - "qwen3 tts dataset prep"
      - "resample wav for TTS"
      - "loudnorm wav clips"
      - "groq whisper batch transcribe"
      - "metadata.csv for TTS"
      - "voice clone pipeline"
      - "mariah voice clone"
---

# Voice Cloning Workflow

End-to-end pipeline for producing a cloned voice from raw audio (audiobooks, interviews, podcasts) through to a deployable TTS model. Covers the data preparation phase (Phase 0) that the install/operations skills for individual TTS engines do not cover.

## When to Use

- Building a TTS training dataset from raw audiobook/interview/podcast audio (Phase 0: source → manifests)
- Batch-transcribing hundreds to thousands of short clips with Groq Whisper (resume-safe per-row CSV writes)
- Generating F5-TTS, Chatterbox, or Qwen3-TTS manifests from one resampled WAV pool
- Deciding whether a partial dataset (e.g. ~2,000 of 5,000 clips) is sufficient to move to GPU fine-tuning
- Auditing clip counts across transcription vs resampling vs manifest stages before GPU provisioning

## Not For

- **Installing/configuring F5-TTS** → `f5-tts-setup`
- **Operating the Chatterbox TTS server** → `chatterbox-turbo-server`
- **Single-file transcription or garbled-audio diagnostics** → `audio-transcription`
- **General audio analysis (spectrograms, MFCC features)** → `songsee`

## Pipeline Overview

```
Raw Audio Source (AAX/M4B/MP3)
    ↓ ffmpeg / AAX conversion
WAV files
    ↓ Silence-based diarization
Short clips (~5-10s)
    ↓ Groq Whisper batch transcription
metadata.csv (filename,transcript)
    ↓ ffmpeg resample + loudnorm
24kHz mono S16LE WAVs
    ↓ Multi-engine manifest generation
┌────────┬──────────┬─────────┐
│ F5-TTS │Chatterbox│ Qwen3   │
│ metadata│ LJSpeech │ JSONL   │
└────────┴──────────┴─────────┘
    ↓ GPU provisioning + fine-tuning
    ↓ Deploy to CT 109
```

## Phase 0 — Data Preparation (Runs on CT 109)

This phase runs entirely on the CPU-only CT 109 alongside the two TTS servers. Script at `/root/voice_prep/prep_all.sh`.

### Step 1: Source Audio Acquisition

Sources that work:
- **Audible AAX files:** Use `ffmpeg -i file.aax -c copy output.m4b` (requires Audible key from voucher file)
- **YouTube:** `yt-dlp --no-config -o "video.%(ext)s" URL; ffmpeg -i video -vn -acodec libmp3lame audio.mp3`
- **Existing podcasts/interviews:** Direct WAV or MP3

**Audible voucher key file** contains the base64 activation bytes needed to decrypt AAX:
```bash
activ_bytes=$(cat /path/to/*.voucher | xargs)
ffmpeg -activation_bytes "$activ_bytes" -i input.aax -c copy output.m4b
```

### Step 2: Silence-Based Diarization

Split long audio into short clips using silence detection. Goal: clips of 3-12s.

Key parameters (adjust per source):
- **silence_duration:** How much silence triggers a split (default ~700-1000ms for audiobooks)
- **silence_threshold:** dB level that counts as silence (-30 to -40dB typically)
- **min_segment_length:** Discard clips shorter than this (default ~2s)

**Watch for:** Gaps in audiobook narration (chapter pauses, musical interludes) can produce very long splits. Monitor output for clips >15s.

### Step 3: Batch Transcription via Groq Whisper

Uses `/root/transcribe.py` — Python script that:
- Reads clips from `/mariah/wavs/audiobook_*.wav`
- Calls Groq Whisper API (`whisper-large-v3`) per clip
- Writes each row to `/mariah/metadata.csv` **immediately** (per-row, resume-safe)
- Skips already-transcribed files on restart

**Rate limiting behavior (Groq free tier):**
- ~1 clip/second sustained
- After ~50-100 clips, hits a 30s cooldown
- 5,000 clips ≈ 3-4 hours total
- **Killing mid-run is safe** — per-row CSV write, no batch loss

**API key:** `GROQ_API_KEY` in `~/.hermes/profiles/income/.env`

### Step 4: Resampling + Loudness Normalization

```bash
ffmpeg -y -i input.wav -ar 24000 -ac 1 -sample_fmt s16 \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  output.wav -loglevel error
```

Parameters: 24000 Hz, mono, S16LE, loudnorm to -16 LUFS. Speed: ~500 clips/min (i5-7600K CPU).

### Step 5: Multi-Engine Dataset Manifests

The `prep_all.sh` script at `/root/voice_prep/prep_all.sh` generates **all three dataset formats** from the **same resampled WAV pool** in a single pass. It:
1. Resamples to 24kHz mono S16LE + loudnorm (skips already-done files)
2. Builds F5-TTS `metadata.csv` with `abs_path|text` rows
3. Builds Chatterbox LJSpeech `metadata.csv` with symlinks to resampled WAVs
4. Builds Qwen3-TTS JSONL `train_raw.jsonl` with `ref_audio` pointer
5. Generates `vocab.txt` (unique chars for F5-TTS tokenizer)

**Important count mismatch:** Not all transcribed clips have matching resampled WAVs. The resample step reads from `/mariah/wavs/` while the manifest builders match against `/root/voice_prep/f5/Mariah_v1/wavs/`. If transcription outpaces resampling, manifests only include clips present in both directories. Verify all three counts (transcribed, resampled, manifest rows) before provisioning GPU.

**Expected directory layout:**
```
/mariah/
  wavs/                      ← All raw clips from audiobook / interviews
  sources/
    interview/               ← Multi-speaker material staged for pyannote
  metadata.csv               ← Groq Whisper transcriptions (filename,transcript)
/root/voice_prep/
  f5/Mariah_v1/              ← F5-TTS dataset (wavs/ + metadata.csv + vocab.txt)
  chatterbox/MyTTSDataset/   ← Chatterbox dataset (symlinks + metadata.csv)
  qwen/data/                 ← Qwen3 dataset (wavs/ + train_raw.jsonl)
```

**F5-TTS** (`metadata.csv`): `/path/to/audiobook_00000.wav|This is the transcript text.`

**Chatterbox LJSpeech** (`metadata.csv`): `audiobook_00000.wav|transcript|transcript`

**Qwen3-TTS JSONL** (`train_raw.jsonl`):
```json
{"audio": "data/audiobook_00000.wav", "text": "transcript", "ref_audio": "data/ref.wav"}
```

## Minimum Viable Dataset Size

Estimates assume ~8s clips from audiobook material (silence-based diarization). Interview clips tend to be shorter (3-6s) — more clips per minute of source, less audio per clip.

| Quality target | Clips | Minutes of audio |
|----------------|-------|-------------------|
| Quick test | 100-200 | 10-20 min |
| Serviceable | 500-1,000 | 45-90 min |
| **Good quality** | **~2,000** | **~25-30 min** |
| Production | 3,000-5,000 | 4-8 hours |

**Observation from actual run (Mariah audiobook, 8s clips, Groq Whisper):**
- 2,089 clips (41% of 5,155 total) = ~26 min audio → judged sufficient to move to GPU training
- Transcription ran ~2-3 hours to reach 2,089 clips (Groq free tier rate-limiting)
- The remaining ~3,000 clips would take another ~3-4 hours — the 41% mark is a pragmatic stopping point

## Safety Notes

- Stopping transcription mid-run is safe — per-row CSV write
- Running on same CT as TTS servers is fine — transcription uses <50MB RAM at <1% CPU
- Two TTS servers + transcription fit within 16GB RAM: Chatterbox ~2GB, F5-TTS ~6GB steady (peaks ~10GB during inference), transcription ~50MB. Observed: 9.6GB/16GB in use during concurrent operation.

## Integration with Existing Skills

| Skill | Covers | Gap filled by this skill |
|-------|--------|-------------------------|
| `f5-tts-setup` | F5-TTS install + API server | Does NOT cover dataset preparation |
| `chatterbox-turbo-server` | Chatterbox operations + API usage | No data pipeline |
| `audio-transcription` | Single-file transcription + diagnostics | No batch/resume/resampling |
| This skill | End-to-end voice clone pipeline | Full workflow source-to-deployment |

## Pitfalls

1. **Groq rate limiting is non-deterministic** — Cooldown frequency varies with API load. The `sleep 30` backoff is reactive. If transcription stalls >5 min, kill and restart; per-row CSV writes make this safe.
2. **Clip duration variance** — Silence-based diarization produces variable clip lengths. Some <2s (useless for embedding) while >15s (audible seam risk). Post-process to cull extremes.
3. **Audible voucher files can expire** — AAX decryption key from voucher file is per-purchase. Redownload if `ffmpeg -activation_bytes` fails.
4. **Loudnorm on very short clips (<3s)** can distort. Skip loudnorm on shortest clips or increase min_segment_length.
5. **Phoneme coverage varies by source** — Mix interview material with audiobook for full phonetic range.
6. **Batch cross-fade seams in F5-TTS** — Long text (>200 chars) generates in separate batches with cross-fade. Pitch/speed can slightly vary between batches.
7. **Transcription outpaces resampling → manifest count mismatch** — the resample step reads `/mariah/wavs/` while manifest builders match against `/root/voice_prep/f5/Mariah_v1/wavs/`. Verify all three counts (transcribed, resampled, manifest rows) before GPU provisioning.
8. **Killing transcription is safe, but don't double-run** — the script skips already-transcribed files on restart; restarting mid-run is fine, but a second concurrent instance wastes the free-tier quota.
9. **Groq free-tier quota exhaustion returns opaque errors** — if the API starts failing with non-rate-limit errors after ~hundreds of clips, check the Groq dashboard quota, not the script.
10. **A 41% dataset is a pragmatic stopping point, not a bug** — 2,089 of 5,155 clips (~26 min audio) was judged sufficient for GPU training. Don't block on completeness if the target quality is met.

## References

- `f5-tts-setup` — F5-TTS server installation and API details
- `chatterbox-turbo-server` — Chatterbox operations and tuning
- `audio-transcription` — Single-file Whisper transcription with garbled-audio diagnostics
