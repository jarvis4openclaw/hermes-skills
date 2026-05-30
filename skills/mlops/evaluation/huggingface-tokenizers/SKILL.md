---
name: huggingface-tokenizers
description: Fast tokenizers optimized for research and production. Rust-based implementation tokenizes 1GB in <20 seconds. Supports BPE, WordPiece, and Unigram algorithms. Train custom vocabularies, track alignments, handle padding/truncation. Integrates seamlessly with transformers. Use when you need high-performance tokenization or custom tokenizer training.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [tokenizers, transformers, datasets]
metadata:
  hermes:
    tags: [Tokenization, HuggingFace, BPE, WordPiece, Unigram, Fast Tokenization, Rust, Custom Tokenizer, Alignment Tracking, Production]
    related_skills: [huggingface-hub, nemo-curator, trl-fine-tuning]
    trigger_conditions:
      - "custom tokenizer"
      - "train a tokenizer"
      - "BPE tokenizer"
      - "WordPiece tokenizer"
      - "Unigram tokenizer"
      - "tokenization pipeline"
      - "alignment tracking"
      - "fast tokenization"
      - "tokenizer padding truncation"
      - "convert tokenizer to transformers"
      - "batch encode"
      - "tokenizer vocabulary"
      - "pre-tokenizer configuration"

---

# HuggingFace Tokenizers - Fast Tokenization for NLP

Fast, production-ready tokenizers with Rust performance and Python ease-of-use.

## When to Use

- **Training custom tokenizers from scratch** — BPE, WordPiece, or Unigram on domain-specific corpora (legal, medical, code)
- **High-throughput tokenization** — processing 1GB+ of text where pure Python tokenizers are too slow
- **Alignment tracking** — mapping model predictions back to original text spans (NER, QA, token classification)
- **Padding and truncation at the tokenizer level** — handling variable-length sequences efficiently in batches
- **Converting custom tokenizers to transformers** — wrapping `tokenizers.Tokenizer` as `PreTrainedTokenizerFast` for the HuggingFace ecosystem
- **Multi-processing tokenization** — parallel encoding across CPU cores for large datasets

## Not For

- **Loading pretrained tokenizers only** → `transformers.AutoTokenizer` handles this internally; this skill is only needed when you want the underlying fast tokenizer or custom training
- **SentencePiece-specific training** → T5, ALBERT use SentencePiece natively; this library supports Unigram but the pretrained SentencePiece models load via `transformers` wrapper
- **Real-time streaming tokenization** → `tokenizers` is batch-optimized; for streaming, consider chunked processing or a custom pipeline
- **Text preprocessing before tokenization** (cleaning, deduplication, filtering) → use `nemo-curator` for large-scale corpus curation before tokenizer training
- **Fine-tuning LLMs** → use `trl-fine-tuning` or `axolotl` for the training loop itself; tokenizers are just one component

## Quick start

### Installation

```bash
# Install tokenizers
pip install tokenizers

# With transformers integration
pip install tokenizers transformers
```

### Load pretrained tokenizer

```python
from tokenizers import Tokenizer

# Load from HuggingFace Hub
tokenizer = Tokenizer.from_pretrained("bert-base-uncased")

# Encode text
output = tokenizer.encode("Hello, how are you?")
print(output.tokens)  # ['hello', ',', 'how', 'are', 'you', '?']
print(output.ids)     # [7592, 1010, 2129, 2024, 2017, 1029]

# Decode back
text = tokenizer.decode(output.ids)
print(text)  # "hello, how are you?"
```

### Train custom BPE tokenizer

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Initialize tokenizer with BPE model
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = Whitespace()

# Configure trainer
trainer = BpeTrainer(
    vocab_size=30000,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    min_frequency=2
)

# Train on files
files = ["train.txt", "validation.txt"]
tokenizer.train(files, trainer)

# Save
tokenizer.save("my-tokenizer.json")
```

**Training time**: ~1-2 minutes for 100MB corpus, ~10-20 minutes for 1GB

### Batch encoding with padding

```python
# Enable padding
tokenizer.enable_padding(pad_id=3, pad_token="[PAD]")

# Encode batch
texts = ["Hello world", "This is a longer sentence"]
encodings = tokenizer.encode_batch(texts)

for encoding in encodings:
    print(encoding.ids)
# [101, 7592, 2088, 102, 3, 3, 3]
# [101, 2023, 2003, 1037, 2936, 6251, 102]
```

## Tokenization algorithms

### BPE (Byte-Pair Encoding)

**How it works**:
1. Start with character-level vocabulary
2. Find most frequent character pair
3. Merge into new token, add to vocabulary
4. Repeat until vocabulary size reached

**Used by**: GPT-2, GPT-3, RoBERTa, BART, DeBERTa

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import ByteLevel

tokenizer = Tokenizer(BPE(unk_token="<|endoftext|>"))
tokenizer.pre_tokenizer = ByteLevel()

trainer = BpeTrainer(
    vocab_size=50257,
    special_tokens=["<|endoftext|>"],
    min_frequency=2
)

tokenizer.train(files=["data.txt"], trainer=trainer)
```

**Advantages**:
- Handles OOV words well (breaks into subwords)
- Flexible vocabulary size
- Good for morphologically rich languages

**Trade-offs**:
- Tokenization depends on merge order
- May split common words unexpectedly

### WordPiece

**How it works**:
1. Start with character vocabulary
2. Score merge pairs: `frequency(pair) / (frequency(first) × frequency(second))`
3. Merge highest scoring pair
4. Repeat until vocabulary size reached

**Used by**: BERT, DistilBERT, MobileBERT

```python
from tokenizers import Tokenizer
from tokenizers.models import WordPiece
from tokenizers.trainers import WordPieceTrainer
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.normalizers import BertNormalizer

tokenizer = Tokenizer(WordPiece(unk_token="[UNK]"))
tokenizer.normalizer = BertNormalizer(lowercase=True)
tokenizer.pre_tokenizer = Whitespace()

trainer = WordPieceTrainer(
    vocab_size=30522,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    continuing_subword_prefix="##"
)

tokenizer.train(files=["corpus.txt"], trainer=trainer)
```

**Advantages**:
- Prioritizes meaningful merges (high score = semantically related)
- Used successfully in BERT (state-of-the-art results)

**Trade-offs**:
- Unknown words become `[UNK]` if no subword match
- Saves vocabulary, not merge rules (larger files)

### Unigram

**How it works**:
1. Start with large vocabulary (all substrings)
2. Compute loss for corpus with current vocabulary
3. Remove tokens with minimal impact on loss
4. Repeat until vocabulary size reached

**Used by**: ALBERT, T5, mBART, XLNet (via SentencePiece)

```python
from tokenizers import Tokenizer
from tokenizers.models import Unigram
from tokenizers.trainers import UnigramTrainer

tokenizer = Tokenizer(Unigram())

trainer = UnigramTrainer(
    vocab_size=8000,
    special_tokens=["<unk>", "<s>", "</s>"],
    unk_token="<unk>"
)

tokenizer.train(files=["data.txt"], trainer=trainer)
```

**Advantages**:
- Probabilistic (finds most likely tokenization)
- Works well for languages without word boundaries
- Handles diverse linguistic contexts

**Trade-offs**:
- Computationally expensive to train
- More hyperparameters to tune

## Tokenization pipeline

Complete pipeline: **Normalization → Pre-tokenization → Model → Post-processing**

### Normalization

Clean and standardize text:

```python
from tokenizers.normalizers import NFD, StripAccents, Lowercase, Sequence

tokenizer.normalizer = Sequence([
    NFD(),           # Unicode normalization (decompose)
    Lowercase(),     # Convert to lowercase
    StripAccents()   # Remove accents
])

# Input: "Héllo WORLD"
# After normalization: "hello world"
```

**Common normalizers**:
- `NFD`, `NFC`, `NFKD`, `NFKC` - Unicode normalization forms
- `Lowercase()` - Convert to lowercase
- `StripAccents()` - Remove accents (é → e)
- `Strip()` - Remove whitespace
- `Replace(pattern, content)` - Regex replacement

### Pre-tokenization

Split text into word-like units:

```python
from tokenizers.pre_tokenizers import Whitespace, Punctuation, Sequence, ByteLevel

# Split on whitespace and punctuation
tokenizer.pre_tokenizer = Sequence([
    Whitespace(),
    Punctuation()
])

# Input: "Hello, world!"
# After pre-tokenization: ["Hello", ",", "world", "!"]
```

**Common pre-tokenizers**:
- `Whitespace()` - Split on spaces, tabs, newlines
- `ByteLevel()` - GPT-2 style byte-level splitting
- `Punctuation()` - Isolate punctuation
- `Digits(individual_digits=True)` - Split digits individually
- `Metaspace()` - Replace spaces with ▁ (SentencePiece style)

### Post-processing

Add special tokens for model input:

```python
from tokenizers.processors import TemplateProcessing

# BERT-style: [CLS] sentence [SEP]
tokenizer.post_processor = TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B [SEP]",
    special_tokens=[
        ("[CLS]", 1),
        ("[SEP]", 2),
    ],
)
```

**Common patterns**:
```python
# GPT-2: sentence <|endoftext|>
TemplateProcessing(
    single="$A <|endoftext|>",
    special_tokens=[("<|endoftext|>", 50256)]
)

# RoBERTa: <s> sentence </s>
TemplateProcessing(
    single="<s> $A </s>",
    pair="<s> $A </s> </s> $B </s>",
    special_tokens=[("<s>", 0), ("</s>", 2)]
)
```

## Alignment tracking

Track token positions in original text:

```python
output = tokenizer.encode("Hello, world!")

# Get token offsets
for token, offset in zip(output.tokens, output.offsets):
    start, end = offset
    print(f"{token:10} → [{start:2}, {end:2}): {text[start:end]!r}")

# Output:
# hello      → [ 0,  5): 'Hello'
# ,          → [ 5,  6): ','
# world      → [ 7, 12): 'world'
# !          → [12, 13): '!'
```

**Use cases**:
- Named entity recognition (map predictions back to text)
- Question answering (extract answer spans)
- Token classification (align labels to original positions)

## Integration with transformers

### Load with AutoTokenizer

```python
from transformers import AutoTokenizer

# AutoTokenizer automatically uses fast tokenizers
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# Check if using fast tokenizer
print(tokenizer.is_fast)  # True

# Access underlying tokenizers.Tokenizer
fast_tokenizer = tokenizer.backend_tokenizer
print(type(fast_tokenizer))  # <class 'tokenizers.Tokenizer'>
```

### Convert custom tokenizer to transformers

```python
from tokenizers import Tokenizer
from transformers import PreTrainedTokenizerFast

# Train custom tokenizer
tokenizer = Tokenizer(BPE())
# ... train tokenizer ...
tokenizer.save("my-tokenizer.json")

# Wrap for transformers
transformers_tokenizer = PreTrainedTokenizerFast(
    tokenizer_file="my-tokenizer.json",
    unk_token="[UNK]",
    pad_token="[PAD]",
    cls_token="[CLS]",
    sep_token="[SEP]",
    mask_token="[MASK]"
)

# Use like any transformers tokenizer
outputs = transformers_tokenizer(
    "Hello world",
    padding=True,
    truncation=True,
    max_length=512,
    return_tensors="pt"
)
```

## Common patterns

### Train from iterator (large datasets)

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("wikitext", "wikitext-103-raw-v1", split="train")

# Create batch iterator
def batch_iterator(batch_size=1000):
    for i in range(0, len(dataset), batch_size):
        yield dataset[i:i + batch_size]["text"]

# Train tokenizer
tokenizer.train_from_iterator(
    batch_iterator(),
    trainer=trainer,
    length=len(dataset)  # For progress bar
)
```

**Performance**: Processes 1GB in ~10-20 minutes

### Enable truncation and padding

```python
# Enable truncation
tokenizer.enable_truncation(max_length=512)

# Enable padding
tokenizer.enable_padding(
    pad_id=tokenizer.token_to_id("[PAD]"),
    pad_token="[PAD]",
    length=512  # Fixed length, or None for batch max
)

# Encode with both
output = tokenizer.encode("This is a long sentence that will be truncated...")
print(len(output.ids))  # 512
```

### Multi-processing

```python
from tokenizers import Tokenizer
from multiprocessing import Pool

# Load tokenizer
tokenizer = Tokenizer.from_file("tokenizer.json")

def encode_batch(texts):
    return tokenizer.encode_batch(texts)

# Process large corpus in parallel
with Pool(8) as pool:
    # Split corpus into chunks
    chunk_size = 1000
    chunks = [corpus[i:i+chunk_size] for i in range(0, len(corpus), chunk_size)]

    # Encode in parallel
    results = pool.map(encode_batch, chunks)
```

**Speedup**: 5-8× with 8 cores

## Performance benchmarks

### Training speed

| Corpus Size | BPE (30k vocab) | WordPiece (30k) | Unigram (8k) |
|-------------|-----------------|-----------------|--------------|
| 10 MB       | 15 sec          | 18 sec          | 25 sec       |
| 100 MB      | 1.5 min         | 2 min           | 4 min        |
| 1 GB        | 15 min          | 20 min          | 40 min       |

**Hardware**: 16-core CPU, tested on English Wikipedia

### Tokenization speed

| Implementation | 1 GB corpus | Throughput    |
|----------------|-------------|---------------|
| Pure Python    | ~20 minutes | ~50 MB/min    |
| HF Tokenizers  | ~15 seconds | ~4 GB/min     |
| **Speedup**    | **80×**     | **80×**       |

**Test**: English text, average sentence length 20 words

### Memory usage

| Task                    | Memory  |
|-------------------------|---------|
| Load tokenizer          | ~10 MB  |
| Train BPE (30k vocab)   | ~200 MB |
| Encode 1M sentences     | ~500 MB |

## Supported models

Pre-trained tokenizers available via `from_pretrained()`:

**BERT family**:
- `bert-base-uncased`, `bert-large-cased`
- `distilbert-base-uncased`
- `roberta-base`, `roberta-large`

**GPT family**:
- `gpt2`, `gpt2-medium`, `gpt2-large`
- `distilgpt2`

**T5 family**:
- `t5-small`, `t5-base`, `t5-large`
- `google/flan-t5-xxl`

**Other**:
- `facebook/bart-base`, `facebook/mbart-large-cc25`
- `albert-base-v2`, `albert-xlarge-v2`
- `xlm-roberta-base`, `xlm-roberta-large`

Browse all: https://huggingface.co/models?library=tokenizers

## References

- **[Training Guide](references/training.md)** - Train custom tokenizers, configure trainers, handle large datasets
- **[Algorithms Deep Dive](references/algorithms.md)** - BPE, WordPiece, Unigram explained in detail
- **[Pipeline Components](references/pipeline.md)** - Normalizers, pre-tokenizers, post-processors, decoders
- **[Transformers Integration](references/integration.md)** - AutoTokenizer, PreTrainedTokenizerFast, special tokens

## Pitfalls

1. **Training on a small corpus** — BPE and WordPiece need millions of tokens to learn meaningful subword units. Training on <10MB of text produces a vocabulary of mostly single characters and rare subwords that don't generalize. Aim for at least 100MB of diverse text.

2. **Passing raw strings instead of files to `tokenizer.train()`** — The `train()` method expects file paths, not raw string lists. If you pass `tokenizer.train(["some text here"], trainer)`, the trainer may split on whitespace unexpectedly or treat the string as a file path and fail. Always save corpus to files and pass file paths: `tokenizer.train(files=["corpus.txt"], trainer=trainer)`.

3. **Mismatch between pre-tokenizer and model type** — Using `Whitespace()` pre-tokenizer with BPE (which expects `ByteLevel()`) causes incorrect subword boundaries. GPT-2 style BPE needs `ByteLevel()` pre-tokenization; BERT style WordPiece needs `Whitespace()` or `BertPreTokenizer()`. Match pre-tokenizer to model architecture.

4. **Forgetting to enable truncation before batch encode** — `tokenizer.encode_batch()` without `enable_truncation(max_length=...)` returns variable-length outputs. If you then try to stack them into a tensor for model input, you get shape mismatches. Always call `tokenizer.enable_truncation(max_length=512)` before batch encoding for model training.

5. **Padding without specifying pad_id** — `tokenizer.enable_padding()` without `pad_id` and `pad_token` may use a default that conflicts with your model's expected vocabulary. Explicitly set `pad_id=tokenizer.token_to_id("")` or the model's actual pad token ID.

6. **Converting to transformers without special token mapping** — When wrapping a custom tokenizer as `PreTrainedTokenizerFast`, if you don't map `unk_token`, `pad_token`, `cls_token`, `sep_token`, `mask_token` correctly, the model will produce garbage or crash on inference. Always verify `tokenizer.special_tokens_map` after wrapping.

7. **Alignment offsets off by one on whitespace** — `output.offsets` tracks character positions in the original text. If you strip or normalize text before encoding, the offsets no longer align with the original. Apply normalization through `tokenizer.normalizer` so offsets remain valid.

8. **Training from iterator without `length` parameter** — `train_from_iterator()` without `length=len(dataset)` shows no progress bar and makes it hard to estimate training time. Always pass `length` for large datasets.

9. **Unigram trainer on small vocabularies** — Unigram is probabilistic and needs a large initial vocabulary to prune from. Starting with `vocab_size=8000` on a 10MB corpus may underfit. Use Unigram for languages without clear word boundaries (Chinese, Japanese) or when you need probabilistic tokenization.

10. **Loading tokenizer from pretrained without checking `is_fast`** — `AutoTokenizer.from_pretrained()` may load a slow (Python) tokenizer for some models. Always check `tokenizer.is_fast` and if False, pass `use_fast=True` or use `Tokenizer.from_pretrained()` directly.

11. **Multi-processing race on tokenizer state** — The `Tokenizer` object is not thread-safe for concurrent modifications. When using `Pool` for parallel encoding, load the tokenizer inside the worker function rather than sharing a single instance across processes.

12. **Memory explosion on `encode_batch` with very long texts** — Passing 10,000 long documents to `encode_batch()` without chunking can exhaust RAM. Pre-chunk texts to <4096 tokens per item, or use `train_from_iterator()` for processing massive corpora.

## Resources

- **Docs**: https://huggingface.co/docs/tokenizers
- **GitHub**: https://github.com/huggingface/tokenizers ⭐ 9,000+
- **Version**: 0.20.0+
- **Course**: https://huggingface.co/learn/nlp-course/chapter6/1
- **Paper**: BPE (Sennrich et al., 2016), WordPiece (Schuster & Nakajima, 2012)


