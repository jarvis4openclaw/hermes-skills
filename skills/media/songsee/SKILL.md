---
name: songsee
description: "Audio spectrograms/features (mel, chroma, MFCC) via CLI."
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Audio, Visualization, Spectrogram, Music, Analysis]
    homepage: https://github.com/steipete/songsee
    trigger_conditions:
      - "generate a spectrogram"
      - "spectrogram of this audio"
      - "visualize audio"
      - "show me the waveform"
      - "what does this track look like"
      - "audio analysis visualization"
      - "chroma / MFCC / tempogram"
      - "mel spectrogram"
      - "audio feature visualization"
      - "songsee"
      - "self-similarity matrix"
      - "spectral flux"
      - "onset detection"
prerequisites:
  commands: [songsee]
---

# songsee

Generate spectrograms and multi-panel audio feature visualizations from audio files.

## When to Use

- User wants to see what an audio file "looks like" (spectrogram)
- Debugging audio synthesis, compression artifacts, or clipping in generated audio
- Comparing two audio tracks visually (side-by-side spectrograms)
- Extracting pitch/chroma/MFCC features for ML training or analysis
- Visual documentation of audio processing pipelines
- Quick onset detection or tempo estimation from a track
- User asks to "analyze this audio" or "show me the spectral content"

## Not For

- **Transcribing speech to text** → use `whisper` or `youtube-content` instead
- **Audio playback or streaming** → songsee generates images, not audio output
- **Real-time audio processing or live visualization** → songsee works on files; use `touchdesigner` or a DAW for real-time
- **Generating audio from text (TTS)** → use `text_to_speech`, `comfyui`, or `audiocraft` for audio generation
- **Editing or mixing audio tracks** → use `ffmpeg`, `sox`, or a DAW; songsee is read-only visualization
- **Batch processing thousands of files** → songsee is single-file; wrap in a shell loop or use a pipeline tool
- **Detailed acoustic measurement (THD, SNR, phase)** → use specialized measurement tools; songsee visualizes broad features

## Prerequisites

Requires [Go](https://go.dev/doc/install):
```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

Optional: `ffmpeg` for formats beyond WAV/MP3.

## Quick Start

```bash
# Basic spectrogram
songsee track.mp3

# Save to specific file
songsee track.mp3 -o spectrogram.png

# Multi-panel visualization grid
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# Time slice (start at 12.5s, 8s duration)
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg

# From stdin
cat track.mp3 | songsee - --format png -o out.png
```

## Visualization Types

Use `--viz` with comma-separated values:

| Type | Description |
|------|-------------|
| `spectrogram` | Standard frequency spectrogram |
| `mel` | Mel-scaled spectrogram |
| `chroma` | Pitch class distribution |
| `hpss` | Harmonic/percussive separation |
| `selfsim` | Self-similarity matrix |
| `loudness` | Loudness over time |
| `tempogram` | Tempo estimation |
| `mfcc` | Mel-frequency cepstral coefficients |
| `flux` | Spectral flux (onset detection) |

Multiple `--viz` types render as a grid in a single image.

## Common Flags

| Flag | Description |
|------|-------------|
| `--viz` | Visualization types (comma-separated) |
| `--style` | Color palette: `classic`, `magma`, `inferno`, `viridis`, `gray` |
| `--width` / `--height` | Output image dimensions |
| `--window` / `--hop` | FFT window and hop size |
| `--min-freq` / `--max-freq` | Frequency range filter |
| `--start` / `--duration` | Time slice of the audio |
| `--format` | Output format: `jpg` or `png` |
| `-o` | Output file path |

## Pitfalls

1. **songsee not installed** — `command not found: songsee`. Fix: run `go install github.com/steipete/songsee/cmd/songsee@latest` and ensure `$GOPATH/bin` is in PATH (`export PATH=$PATH:$(go env GOPATH)/bin`).

2. **Missing ffmpeg for non-WAV/MP3 formats** — FLAC, AAC, OGG, and other formats fail with "unsupported format." Fix: install `ffmpeg` (system package manager) and retry. Songsee pipes through ffmpeg for non-native formats.

3. **Large audio files exhaust memory** — Processing a 3-hour WAV at full resolution can OOM. Fix: use `--start` and `--duration` to process in smaller slices, or down-sample the audio with ffmpeg first.

4. **Output image is blank/all-black** — This happens when `--min-freq` is set above the audio's actual frequency content or `--start` is past the end of the file. Fix: remove freq/time constraints and retry; verify the audio file actually contains signal with `ffprobe`.

5. **Multi-viz grid is too dense to read** — Passing all 9 visualization types (`--viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux`) produces a grid where individual panels are tiny. Fix: select 4-6 most relevant types for the question at hand; use separate runs for detailed views.

6. **Go toolchain not installed** — `go: command not found` when trying to install. Fix: install Go from `https://go.dev/doc/install` or via system package manager (`apt install golang-go` on Debian/Ubuntu).

7. **Output format mismatch** — PNG is default but some viewers expect JPG. The `--format` flag must be set explicitly; PNG files with `.jpg` extension won't render. Fix: match `--format` to the file extension in `-o`.

8. **`--viz` with typo silently falls back** — `--viz chroma,mel,spectogram` (typo: "spectogram" not "spectrogram") silently drops the mistyped panel. Fix: run `songsee --help` to verify exact viz type names; the list is `spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux`.

9. **stdin mode requires explicit format** — `cat track.mp3 | songsee -` without `--format` may fail or produce garbage. Fix: always pass `--format png` (or jpg) when using stdin mode.

10. **Time slice exceeds file length silently** — `--start 120 --duration 60` on a 150s file produces a truncated output at the file boundary without warning. Fix: check file duration with `ffprobe` first, or omit `--duration` to capture from `--start` to end of file.
