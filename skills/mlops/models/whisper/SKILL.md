---
name: whisper
description: OpenAI's general-purpose speech recognition model. Supports 99 languages, transcription, translation to English, and language identification. Six model sizes from tiny (39M params) to large (1550M params). Use for speech-to-text, podcast transcription, or multilingual audio processing. Best for robust, multilingual ASR.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [openai-whisper, transformers, torch]
metadata:
  hermes:
    tags: [Whisper, Speech Recognition, ASR, Multimodal, Multilingual, OpenAI, Speech-To-Text, Transcription, Translation, Audio Processing]
    trigger_conditions:
      - "transcribe audio"
      - "speech to text"
      - "transcribe this file"
      - "transcribe podcast"
      - "transcribe meeting"
      - "openai whisper"
      - "speech recognition"
      - "audio to text"
      - "transcribe mp3"
      - "transcribe wav"
      - "generate subtitles"
      - "whisper transcription"
      - "convert audio to text"

---

# Whisper - Robust Speech Recognition

OpenAI's multilingual speech recognition model.

## When to use Whisper

**Use when:**
- Speech-to-text transcription (99 languages)
- Podcast/video transcription
- Meeting notes automation
- Translation to English
- Noisy audio transcription
- Multilingual audio processing

**Metrics**:
- **72,900+ GitHub stars**
- 99 languages supported
- Trained on 680,000 hours of audio
- MIT License

**Use alternatives instead**:
- **AssemblyAI**: Managed API, speaker diarization
- **Deepgram**: Real-time streaming ASR
- **Google Speech-to-Text**: Cloud-based

## Not For

- **Real-time streaming transcription** → Whisper is batch-only; use `deepgram` or AssemblyAI for live speech
- **Speaker diarization (who said what)** → Whisper has no speaker labels; use `pyannote-audio` or AssemblyAI
- **Music/song transcription** → Whisper is for speech, not melody/chords; use `demucs` or `basic-pitch`
- **Very long audio (>4 hours)** → memory usage grows with duration; split into chunks first
- **Production serving at scale** → openai-whisper is for local use; use `serving-llms-vllm` or OpenAI API for production
- **Offline/air-gapped environments** → models download on first load (~1.5GB for base); pre-download with `whisper.load_model("base", download_root="./models")`
- **Live captioning with <1s latency** → Whisper processes in chunks; use `faster-whisper` with streaming or dedicated ASR APIs

## Quick start

### Installation

```bash
# Requires Python 3.8-3.11
pip install -U openai-whisper

# Requires ffmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: choco install ffmpeg
```

### Basic transcription

```python
import whisper

# Load model
model = whisper.load_model("base")

# Transcribe
result = model.transcribe("audio.mp3")

# Print text
print(result["text"])

# Access segments
for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s - {segment['end']:.2f}s] {segment['text']}")
```

## Model sizes

```python
# Available models
models = ["tiny", "base", "small", "medium", "large", "turbo"]

# Load specific model
model = whisper.load_model("turbo")  # Fastest, good quality
```

| Model | Parameters | English-only | Multilingual | Speed | VRAM |
|-------|------------|--------------|--------------|-------|------|
| tiny | 39M | ✓ | ✓ | ~32x | ~1 GB |
| base | 74M | ✓ | ✓ | ~16x | ~1 GB |
| small | 244M | ✓ | ✓ | ~6x | ~2 GB |
| medium | 769M | ✓ | ✓ | ~2x | ~5 GB |
| large | 1550M | ✗ | ✓ | 1x | ~10 GB |
| turbo | 809M | ✗ | ✓ | ~8x | ~6 GB |

**Recommendation**: Use `turbo` for best speed/quality, `base` for prototyping

## Transcription options

### Language specification

```python
# Auto-detect language
result = model.transcribe("audio.mp3")

# Specify language (faster)
result = model.transcribe("audio.mp3", language="en")

# Supported: en, es, fr, de, it, pt, ru, ja, ko, zh, and 89 more
```

### Task selection

```python
# Transcription (default)
result = model.transcribe("audio.mp3", task="transcribe")

# Translation to English
result = model.transcribe("spanish.mp3", task="translate")
# Input: Spanish audio → Output: English text
```

### Initial prompt

```python
# Improve accuracy with context
result = model.transcribe(
    "audio.mp3",
    initial_prompt="This is a technical podcast about machine learning and AI."
)

# Helps with:
# - Technical terms
# - Proper nouns
# - Domain-specific vocabulary
```

### Timestamps

```python
# Word-level timestamps
result = model.transcribe("audio.mp3", word_timestamps=True)

for segment in result["segments"]:
    for word in segment["words"]:
        print(f"{word['word']} ({word['start']:.2f}s - {word['end']:.2f}s)")
```

### Temperature fallback

```python
# Retry with different temperatures if confidence low
result = model.transcribe(
    "audio.mp3",
    temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
)
```

## Command line usage

```bash
# Basic transcription
whisper audio.mp3

# Specify model
whisper audio.mp3 --model turbo

# Output formats
whisper audio.mp3 --output_format txt     # Plain text
whisper audio.mp3 --output_format srt     # Subtitles
whisper audio.mp3 --output_format vtt     # WebVTT
whisper audio.mp3 --output_format json    # JSON with timestamps

# Language
whisper audio.mp3 --language Spanish

# Translation
whisper spanish.mp3 --task translate
```

## Batch processing

```python
import os

audio_files = ["file1.mp3", "file2.mp3", "file3.mp3"]

for audio_file in audio_files:
    print(f"Transcribing {audio_file}...")
    result = model.transcribe(audio_file)

    # Save to file
    output_file = audio_file.replace(".mp3", ".txt")
    with open(output_file, "w") as f:
        f.write(result["text"])
```

## Real-time transcription

```python
# For streaming audio, use faster-whisper
# pip install faster-whisper

from faster_whisper import WhisperModel

model = WhisperModel("base", device="cuda", compute_type="float16")

# Transcribe with streaming
segments, info = model.transcribe("audio.mp3", beam_size=5)

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
```

## GPU acceleration

```python
import whisper

# Automatically uses GPU if available
model = whisper.load_model("turbo")

# Force CPU
model = whisper.load_model("turbo", device="cpu")

# Force GPU
model = whisper.load_model("turbo", device="cuda")

# 10-20× faster on GPU
```

## Integration with other tools

### Subtitle generation

```bash
# Generate SRT subtitles
whisper video.mp4 --output_format srt --language English

# Output: video.srt
```

### With LangChain

```python
from langchain.document_loaders import WhisperTranscriptionLoader

loader = WhisperTranscriptionLoader(file_path="audio.mp3")
docs = loader.load()

# Use transcription in RAG
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma.from_documents(docs, OpenAIEmbeddings())
```

### Extract audio from video

```bash
# Use ffmpeg to extract audio
ffmpeg -i video.mp4 -vn -acodec pcm_s16le audio.wav

# Then transcribe
whisper audio.wav
```

## Pitfalls

1. **ffmpeg not installed** — `openai-whisper` silently fails or produces empty output when ffmpeg is missing. Always verify: `ffmpeg -version`. Install with `apt install ffmpeg` (Ubuntu), `brew install ffmpeg` (macOS), or `choco install ffmpeg` (Windows).

2. **Model download blocks first call** — `whisper.load_model("base")` downloads ~1.5GB on first use with no progress bar. Fix: pre-download with `whisper.load_model("base", download_root="./models")` during setup, or use `faster-whisper` which streams the download.

3. **GPU not used despite CUDA being available** — whisper auto-detects CUDA but may silently fall back to CPU if PyTorch wasn't built with CUDA support. Verify with `python -c "import torch; print(torch.cuda.is_available())"`. If False, install PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`.

4. **Wrong model size for available VRAM** — Loading `large` (10GB VRAM) on a 4GB GPU crashes with CUDA OOM. Fix: match model to hardware — `tiny`/`base` for ≤2GB VRAM, `small`/`turbo` for 4-6GB, `medium`/`large` for 8GB+.

5. **Long audio (>30 min) degrades quality** — Whisper's transformer attention span degrades on long-form audio. Fix: split into ≤30-minute chunks with ffmpeg: `ffmpeg -i long_audio.mp3 -f segment -segment_time 1800 -c copy chunk_%03d.mp3`.

6. **Language auto-detection is wrong for multilingual audio** — Whisper may misidentify the language for short clips or code-switched speech. Fix: explicitly set `language=` parameter when you know the language. Use `whisper audio.mp3 --language ja` for known language, or check detection confidence with `result["language"]`.

7. **Repeated phrase hallucination** — On silent or noisy segments, Whisper may repeat the last phrase ("Thank you. Thank you. Thank you…"). Fix: use `condition_on_previous_text=False` for long-form, or set `temperature=0` to reduce hallucination, or pre-process audio to remove silence.

8. **Memory leak on batch processing** — Calling `model.transcribe()` in a loop without reloading can cause RAM to grow unboundedly. Fix: reload the model every 50-100 files, or use `faster-whisper` which has better memory management.

9. **openai-whisper vs faster-whisper confusion** — `openai-whisper` (PyTorch) is the reference implementation; `faster-whisper` (CTranslate2) is 4× faster with same accuracy. If speed matters, install `pip install faster-whisper` and use `from faster_whisper import WhisperModel`.

10. **Temperature fallback loops silently** — When `temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)`, Whisper retries at higher temperatures on low confidence. This means a 30s clip can take 6× longer. Set `temperature=0` for deterministic output when speed matters.

11. **Audio format not supported** — Whisper expects WAV or MP3; FLAC and OGG may work but M4A/AAC often fail silently. Fix: convert with ffmpeg first: `ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav`.

12. **Subtitle timing drift on long videos** — SRT/VTT timestamps can drift by seconds on >1hr content. Fix: use `--word_timestamps True` for more accurate per-word timing, or post-process with `aeneas` for forced alignment.

## Performance

| Model | Real-time factor (CPU) | Real-time factor (GPU) |
|-------|------------------------|------------------------|
| tiny | ~0.32 | ~0.01 |
| base | ~0.16 | ~0.01 |
| turbo | ~0.08 | ~0.01 |
| large | ~1.0 | ~0.05 |

*Real-time factor: 0.1 = 10× faster than real-time*

## Language support

Top-supported languages:
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Japanese (ja)
- Korean (ko)
- Chinese (zh)

Full list: 99 languages total

## Resources

- **GitHub**: https://github.com/openai/whisper ⭐ 72,900+
- **Paper**: https://arxiv.org/abs/2212.04356
- **Model Card**: https://github.com/openai/whisper/blob/main/model-card.md
- **Colab**: Available in repo
- **License**: MIT


