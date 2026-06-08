---
name: nemo-curator
description: GPU-accelerated data curation for LLM training. Supports text/image/video/audio. Features fuzzy deduplication (16× faster), quality filtering (30+ heuristics), semantic deduplication, PII redaction, NSFW detection. Scales across GPUs with RAPIDS. Use for preparing high-quality training datasets, cleaning web data, or deduplicating large corpora.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [nemo-curator, cudf, dask, rapids]
metadata:
  hermes:
    tags: [Data Processing, NeMo Curator, Data Curation, GPU Acceleration, Deduplication, Quality Filtering, NVIDIA, RAPIDS, PII Redaction, Multimodal, LLM Training Data]
    trigger_conditions:
      - "nemo curator"
      - "data curation"
      - "deduplicate training data"
      - "clean web scrape data"
      - "common crawl filtering"
      - "PII redaction dataset"
      - "fuzzy deduplication GPU"
      - "prepare LLM training data"
      - "quality filter corpus"
      - "NSFW detection dataset"
      - "semantic deduplication"
      - "minhash deduplication"
      - "GPU data processing RAPIDS"

---

# NeMo Curator - GPU-Accelerated Data Curation

NVIDIA's toolkit for preparing high-quality training data for LLMs.

## When to Use

- Preparing LLM training data from web scrapes (Common Crawl, RedPajama)
- Need fast deduplication at scale — 16× faster than CPU-based approaches
- Curating multi-modal datasets (text, images, video, audio)
- Filtering low-quality, repetitive, or toxic content from large corpora
- Scaling data processing across a GPU cluster with Dask/RAPIDS
- Need exact, fuzzy (MinHash+LSH), and semantic deduplication in one pipeline
- Redacting PII (emails, phone numbers, names, locations) from training data
- Running quality classifiers (DeBERTa-based) on raw text at batch scale

## Not For

- **Small datasets (<10GB)** → CPU tools like `datatrove` or `text-dedup` are simpler; GPU overhead isn't worth it
- **Single-node CPU processing** → use `datatrove` instead; NeMo Curator requires GPU
- **General ML data processing (not curation)** → use `Ray Data` or `Apache Spark` instead
- **Streaming/real-time deduplication** → NeMo Curator is batch-oriented; use `bloom-filter` or `simhash` streaming
- **Text-only deduplication at small scale** → use `text-dedup` (MinHash) or `deduplicate-text-datasets` instead
- **Binary deduplication (images/video files)** → use `imagededup` or perceptual hashing instead
- **Training data annotation/labeling** → use `Label Studio` or `Prodigy` instead; NeMo Curator filters, doesn't label

## Quick start

### Installation

```bash
# Text curation (CUDA 12)
uv pip install "nemo-curator[text_cuda12]"

# All modalities
uv pip install "nemo-curator[all_cuda12]"

# CPU-only (slower)
uv pip install "nemo-curator[cpu]"
```

### Basic text curation pipeline

```python
from nemo_curator import ScoreFilter, Modify
from nemo_curator.datasets import DocumentDataset
import pandas as pd

# Load data
df = pd.DataFrame({"text": ["Good document", "Bad doc", "Excellent text"]})
dataset = DocumentDataset(df)

# Quality filtering
def quality_score(doc):
    return len(doc["text"].split()) > 5  # Filter short docs

filtered = ScoreFilter(quality_score)(dataset)

# Deduplication
from nemo_curator.modules import ExactDuplicates
deduped = ExactDuplicates()(filtered)

# Save
deduped.to_parquet("curated_data/")
```

## Data curation pipeline

### Stage 1: Quality filtering

```python
from nemo_curator.filters import (
    WordCountFilter,
    RepeatedLinesFilter,
    UrlRatioFilter,
    NonAlphaNumericFilter
)

# Apply 30+ heuristic filters
from nemo_curator import ScoreFilter

# Word count filter
dataset = dataset.filter(WordCountFilter(min_words=50, max_words=100000))

# Remove repetitive content
dataset = dataset.filter(RepeatedLinesFilter(max_repeated_line_fraction=0.3))

# URL ratio filter
dataset = dataset.filter(UrlRatioFilter(max_url_ratio=0.2))
```

### Stage 2: Deduplication

**Exact deduplication**:
```python
from nemo_curator.modules import ExactDuplicates

# Remove exact duplicates
deduped = ExactDuplicates(id_field="id", text_field="text")(dataset)
```

**Fuzzy deduplication** (16× faster on GPU):
```python
from nemo_curator.modules import FuzzyDuplicates

# MinHash + LSH deduplication
fuzzy_dedup = FuzzyDuplicates(
    id_field="id",
    text_field="text",
    num_hashes=260,      # MinHash parameters
    num_buckets=20,
    hash_method="md5"
)

deduped = fuzzy_dedup(dataset)
```

**Semantic deduplication**:
```python
from nemo_curator.modules import SemanticDuplicates

# Embedding-based deduplication
semantic_dedup = SemanticDuplicates(
    id_field="id",
    text_field="text",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    threshold=0.8  # Cosine similarity threshold
)

deduped = semantic_dedup(dataset)
```

### Stage 3: PII redaction

```python
from nemo_curator.modules import Modify
from nemo_curator.modifiers import PIIRedactor

# Redact personally identifiable information
pii_redactor = PIIRedactor(
    supported_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "PERSON", "LOCATION"],
    anonymize_action="replace"  # or "redact"
)

redacted = Modify(pii_redactor)(dataset)
```

### Stage 4: Classifier filtering

```python
from nemo_curator.classifiers import QualityClassifier

# Quality classification
quality_clf = QualityClassifier(
    model_path="nvidia/quality-classifier-deberta",
    batch_size=256,
    device="cuda"
)

# Filter low-quality documents
high_quality = dataset.filter(lambda doc: quality_clf(doc["text"]) > 0.5)
```

## GPU acceleration

### GPU vs CPU performance

| Operation | CPU (16 cores) | GPU (A100) | Speedup |
|-----------|----------------|------------|---------|
| Fuzzy dedup (8TB) | 120 hours | 7.5 hours | 16× |
| Exact dedup (1TB) | 8 hours | 0.5 hours | 16× |
| Quality filtering | 2 hours | 0.2 hours | 10× |

### Multi-GPU scaling

```python
from nemo_curator import get_client
import dask_cuda

# Initialize GPU cluster
client = get_client(cluster_type="gpu", n_workers=8)

# Process with 8 GPUs
deduped = FuzzyDuplicates(...)(dataset)
```

## Multi-modal curation

### Image curation

```python
from nemo_curator.image import (
    AestheticFilter,
    NSFWFilter,
    CLIPEmbedder
)

# Aesthetic scoring
aesthetic_filter = AestheticFilter(threshold=5.0)
filtered_images = aesthetic_filter(image_dataset)

# NSFW detection
nsfw_filter = NSFWFilter(threshold=0.9)
safe_images = nsfw_filter(filtered_images)

# Generate CLIP embeddings
clip_embedder = CLIPEmbedder(model="openai/clip-vit-base-patch32")
image_embeddings = clip_embedder(safe_images)
```

### Video curation

```python
from nemo_curator.video import (
    SceneDetector,
    ClipExtractor,
    InternVideo2Embedder
)

# Detect scenes
scene_detector = SceneDetector(threshold=27.0)
scenes = scene_detector(video_dataset)

# Extract clips
clip_extractor = ClipExtractor(min_duration=2.0, max_duration=10.0)
clips = clip_extractor(scenes)

# Generate embeddings
video_embedder = InternVideo2Embedder()
video_embeddings = video_embedder(clips)
```

### Audio curation

```python
from nemo_curator.audio import (
    ASRInference,
    WERFilter,
    DurationFilter
)

# ASR transcription
asr = ASRInference(model="nvidia/stt_en_fastconformer_hybrid_large_pc")
transcribed = asr(audio_dataset)

# Filter by WER (word error rate)
wer_filter = WERFilter(max_wer=0.3)
high_quality_audio = wer_filter(transcribed)

# Duration filtering
duration_filter = DurationFilter(min_duration=1.0, max_duration=30.0)
filtered_audio = duration_filter(high_quality_audio)
```

## Common patterns

### Web scrape curation (Common Crawl)

```python
from nemo_curator import ScoreFilter, Modify
from nemo_curator.filters import *
from nemo_curator.modules import *
from nemo_curator.datasets import DocumentDataset

# Load Common Crawl data
dataset = DocumentDataset.read_parquet("common_crawl/*.parquet")

# Pipeline
pipeline = [
    # 1. Quality filtering
    WordCountFilter(min_words=100, max_words=50000),
    RepeatedLinesFilter(max_repeated_line_fraction=0.2),
    SymbolToWordRatioFilter(max_symbol_to_word_ratio=0.3),
    UrlRatioFilter(max_url_ratio=0.3),

    # 2. Language filtering
    LanguageIdentificationFilter(target_languages=["en"]),

    # 3. Deduplication
    ExactDuplicates(id_field="id", text_field="text"),
    FuzzyDuplicates(id_field="id", text_field="text", num_hashes=260),

    # 4. PII redaction
    PIIRedactor(),

    # 5. NSFW filtering
    NSFWClassifier(threshold=0.8)
]

# Execute
for stage in pipeline:
    dataset = stage(dataset)

# Save
dataset.to_parquet("curated_common_crawl/")
```

### Distributed processing

```python
from nemo_curator import get_client
from dask_cuda import LocalCUDACluster

# Multi-GPU cluster
cluster = LocalCUDACluster(n_workers=8)
client = get_client(cluster=cluster)

# Process large dataset
dataset = DocumentDataset.read_parquet("s3://large_dataset/*.parquet")
deduped = FuzzyDuplicates(...)(dataset)

# Cleanup
client.close()
cluster.close()
```

## Performance benchmarks

### Fuzzy deduplication (8TB RedPajama v2)

- **CPU (256 cores)**: 120 hours
- **GPU (8× A100)**: 7.5 hours
- **Speedup**: 16×

### Exact deduplication (1TB)

- **CPU (64 cores)**: 8 hours
- **GPU (4× A100)**: 0.5 hours
- **Speedup**: 16×

### Quality filtering (100GB)

- **CPU (32 cores)**: 2 hours
- **GPU (2× A100)**: 0.2 hours
- **Speedup**: 10×

## Cost comparison

**CPU-based curation** (AWS c5.18xlarge × 10):
- Cost: $3.60/hour × 10 = $36/hour
- Time for 8TB: 120 hours
- **Total**: $4,320

**GPU-based curation** (AWS p4d.24xlarge × 2):
- Cost: $32.77/hour × 2 = $65.54/hour
- Time for 8TB: 7.5 hours
- **Total**: $491.55

**Savings**: 89% reduction ($3,828 saved)

## Supported data formats

- **Input**: Parquet, JSONL, CSV
- **Output**: Parquet (recommended), JSONL
- **WebDataset**: TAR archives for multi-modal

## Use cases

**Production deployments**:
- NVIDIA used NeMo Curator to prepare Nemotron-4 training data
- Open-source datasets curated: RedPajama v2, The Pile

## Pitfalls

1. **`cudf` import error after installing nemo-curator** — RAPIDS/cuDF requires a compatible CUDA version. Verify CUDA toolkit matches: `nvcc --version` and `python -c "import cudf; print(cudf.__version__)"`. If cuDF fails, reinstall with explicit CUDA version: `uv pip install "nemo-curator[text_cuda12]"` (matching your CUDA install).

2. **Dask client hangs on multi-GPU setup** — `LocalCUDACluster` requires `dask-cuda` and `ucx` to be installed. If the client hangs at `get_client()`, install with: `conda install -c rapidsai -c conda-forge dask-cuda ucx`. Also verify `nvidia-smi` shows all GPUs.

3. **Fuzzy deduplication runs out of GPU memory on large datasets** — MinHash signatures for billions of documents can exceed GPU VRAM. Reduce `num_hashes` from 260 to 128, or increase `num_buckets` to 50 to spread the load. For datasets >10TB, use `dask_cuda.LocalCUDACluster` with `device_memory_limit` to spill to CPU.

4. **Semantic deduplication downloads embedding model on every run** — The `SemanticDuplicates` module downloads the embedding model from HuggingFace Hub on first use. Cache it by setting `HF_HOME=/path/to/cache` or running a warm-up: `from sentence_transformers import SentenceTransformer; SentenceTransformer("all-MiniLM-L6-v2")`. This downloads ~80MB.

5. **PII redaction misses non-standard formats** — The default `PIIRedactor` uses Presidio, which detects standard formats (email, phone, SSN). For custom entity types (API keys, tokens, internal IDs), register a custom recognizer: `from presidio_analyzer import PatternRecognizer; pii_redactor.add_recognizer(PatternRecognizer(...))`. See the Presidio docs for regex-based custom recognizers.

6. **Quality classifier OOM on large batches** — The DeBERTa classifier loads a full model. Reduce `batch_size` to 64 or 32. If still OOM, use `device="cpu"` and accept slower throughput, or switch to a lighter classifier like `nvidia/quality-classifier-deberta-v3-small`.

7. **`DocumentDataset.read_parquet` fails on S3 paths** — NeMo Curator uses `dask.dataframe.read_parquet` under the hood. For S3, install `s3fs`: `pip install s3fs`. Pass storage options: `DocumentDataset.read_parquet("s3://bucket/*.parquet", storage_options={"anon": False})`.

8. **Exact dedup removes too many documents** — `ExactDuplicates` uses hash-based matching; even a single whitespace difference makes documents "different." Normalize whitespace first: `from nemo_curator.modifiers import UnicodeReformatter; dataset = Modify(UnicodeReformatter())(dataset)`. This normalizes Unicode and whitespace before dedup.

9. **Language filter removes multilingual documents incorrectly** — `LanguageIdentificationFilter` uses fastText, which may misclassify code-switched or mixed-language documents. Increase the confidence threshold: `LanguageIdentificationFilter(target_languages=["en"], min_confidence=0.9)`. Review a sample of filtered documents to calibrate.

10. **Output parquet files are too small (many tiny files)** — Dask writes one file per partition by default. Repartition before saving: `dataset.df.repartition(npartitions=10).to_parquet(...)`. Aim for ~128-256MB per file for optimal downstream loading.

11. **`NSFWClassifier` requires downloading a ~500MB model** — The NSFW classifier uses a CLIP-based model. On first run, it downloads from HuggingFace Hub. If behind a proxy, set `HF_ENDPOINT=https://hf-mirror.com`. Cache the model in `~/.cache/huggingface/` to avoid repeated downloads.

12. **GPU memory leak when processing many small batches** — Dask+CUDA workers may hold GPU memory between tasks. Set `device_memory_limit="4GB"` in `LocalCUDACluster` to force spilling. After processing, explicitly call `client.restart()` to clear CUDA context and free GPU memory.

## References

- **[Filtering Guide](references/filtering.md)** - 30+ quality filters, heuristics
- **[Deduplication Guide](references/deduplication.md)** - Exact, fuzzy, semantic methods

## Resources

- **GitHub**: https://github.com/NVIDIA/NeMo-Curator ⭐ 500+
- **Docs**: https://docs.nvidia.com/nemo-framework/user-guide/latest/datacuration/
- **Version**: 0.4.0+
- **License**: Apache 2.0