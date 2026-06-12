---
name: clip
description: OpenAI's model connecting vision and language. Enables zero-shot image classification, image-text matching, and cross-modal retrieval. Trained on 400M image-text pairs. Use for image search, content moderation, or vision-language tasks without fine-tuning. Best for general-purpose image understanding.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [transformers, torch, pillow]
metadata:
  hermes:
    tags: [Multimodal, CLIP, Vision-Language, Zero-Shot, Image Classification, OpenAI, Image Search, Cross-Modal Retrieval, Content Moderation]
    trigger_conditions:
      - "use CLIP for image search"
      - "zero-shot image classification"
      - "image text similarity"
      - "cross-modal retrieval"
      - "content moderation with CLIP"
      - "openai CLIP model"
      - "image classification without training"
      - "CLIP embeddings"
      - "image semantic search CLIP"
      - "vision language zero shot"
      - "CLIP install"
      - "CLIP ViT"
      - "clip encode image"

---

# CLIP - Contrastive Language-Image Pre-Training

OpenAI's model that understands images from natural language.

## When to use CLIP

**Use when:**
- Zero-shot image classification (no training data needed)
- Image-text similarity/matching
- Semantic image search
- Content moderation (detect NSFW, violence)
- Visual question answering
- Cross-modal retrieval (image→text, text→image)

## Not For

- **Generating image captions** → use `llava` or BLIP-2 for caption generation (CLIP is a classifier/retriever, not a generator)
- **Image segmentation** → use `segment-anything-model` for precise image segmentation
- **Video understanding** → CLIP processes static frames only; use dedicated video models for temporal tasks
- **Fine-grained recognition (car models, dog breeds)** → CLIP's zero-shot performance degrades on fine-grained categories without fine-tuning
- **Counting or spatial reasoning** → CLIP has no bounding boxes or spatial understanding; use object detection models (e.g., YOLO) instead
- **Generating images from text** → use `stable-diffusion-image-generation` for text-to-image generation

**Metrics**:
- **25,300+ GitHub stars**
- Trained on 400M image-text pairs
- Matches ResNet-50 on ImageNet (zero-shot)
- MIT License

**Use alternatives instead**:
- **BLIP-2**: Better captioning
- **LLaVA**: Vision-language chat
- **Segment Anything**: Image segmentation

## Quick start

### Installation

```bash
pip install git+https://github.com/openai/CLIP.git
pip install torch torchvision ftfy regex tqdm
```

### Zero-shot classification

```python
import torch
import clip
from PIL import Image

# Load model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Load image
image = preprocess(Image.open("photo.jpg")).unsqueeze(0).to(device)

# Define possible labels
text = clip.tokenize(["a dog", "a cat", "a bird", "a car"]).to(device)

# Compute similarity
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    # Cosine similarity
    logits_per_image, logits_per_text = model(image, text)
    probs = logits_per_image.softmax(dim=-1).cpu().numpy()

# Print results
labels = ["a dog", "a cat", "a bird", "a car"]
for label, prob in zip(labels, probs[0]):
    print(f"{label}: {prob:.2%}")
```

## Available models

```python
# Models (sorted by size)
models = [
    "RN50",           # ResNet-50
    "RN101",          # ResNet-101
    "ViT-B/32",       # Vision Transformer (recommended)
    "ViT-B/16",       # Better quality, slower
    "ViT-L/14",       # Best quality, slowest
]

model, preprocess = clip.load("ViT-B/32")
```

| Model | Parameters | Speed | Quality |
|-------|------------|-------|---------|
| RN50 | 102M | Fast | Good |
| ViT-B/32 | 151M | Medium | Better |
| ViT-L/14 | 428M | Slow | Best |

## Image-text similarity

```python
# Compute embeddings
image_features = model.encode_image(image)
text_features = model.encode_text(text)

# Normalize
image_features /= image_features.norm(dim=-1, keepdim=True)
text_features /= text_features.norm(dim=-1, keepdim=True)

# Cosine similarity
similarity = (image_features @ text_features.T).item()
print(f"Similarity: {similarity:.4f}")
```

## Semantic image search

```python
# Index images
image_paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
image_embeddings = []

for img_path in image_paths:
    image = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model.encode_image(image)
        embedding /= embedding.norm(dim=-1, keepdim=True)
    image_embeddings.append(embedding)

image_embeddings = torch.cat(image_embeddings)

# Search with text query
query = "a sunset over the ocean"
text_input = clip.tokenize([query]).to(device)
with torch.no_grad():
    text_embedding = model.encode_text(text_input)
    text_embedding /= text_embedding.norm(dim=-1, keepdim=True)

# Find most similar images
similarities = (text_embedding @ image_embeddings.T).squeeze(0)
top_k = similarities.topk(3)

for idx, score in zip(top_k.indices, top_k.values):
    print(f"{image_paths[idx]}: {score:.3f}")
```

## Content moderation

```python
# Define categories
categories = [
    "safe for work",
    "not safe for work",
    "violent content",
    "graphic content"
]

text = clip.tokenize(categories).to(device)

# Check image
with torch.no_grad():
    logits_per_image, _ = model(image, text)
    probs = logits_per_image.softmax(dim=-1)

# Get classification
max_idx = probs.argmax().item()
max_prob = probs[0, max_idx].item()

print(f"Category: {categories[max_idx]} ({max_prob:.2%})")
```

## Batch processing

```python
# Process multiple images
images = [preprocess(Image.open(f"img{i}.jpg")) for i in range(10)]
images = torch.stack(images).to(device)

with torch.no_grad():
    image_features = model.encode_image(images)
    image_features /= image_features.norm(dim=-1, keepdim=True)

# Batch text
texts = ["a dog", "a cat", "a bird"]
text_tokens = clip.tokenize(texts).to(device)

with torch.no_grad():
    text_features = model.encode_text(text_tokens)
    text_features /= text_features.norm(dim=-1, keepdim=True)

# Similarity matrix (10 images × 3 texts)
similarities = image_features @ text_features.T
print(similarities.shape)  # (10, 3)
```

## Integration with vector databases

```python
# Store CLIP embeddings in Chroma/FAISS
import chromadb

client = chromadb.Client()
collection = client.create_collection("image_embeddings")

# Add image embeddings
for img_path, embedding in zip(image_paths, image_embeddings):
    collection.add(
        embeddings=[embedding.cpu().numpy().tolist()],
        metadatas=[{"path": img_path}],
        ids=[img_path]
    )

# Query with text
query = "a sunset"
text_embedding = model.encode_text(clip.tokenize([query]))
results = collection.query(
    query_embeddings=[text_embedding.cpu().numpy().tolist()],
    n_results=5
)
```

## Best practices

1. **Use ViT-B/32 for most cases** - Good balance
2. **Normalize embeddings** - Required for cosine similarity
3. **Batch processing** - More efficient
4. **Cache embeddings** - Expensive to recompute
5. **Use descriptive labels** - Better zero-shot performance
6. **GPU recommended** - 10-50× faster
7. **Preprocess images** - Use provided preprocess function

## Performance

| Operation | CPU | GPU (V100) |
|-----------|-----|------------|
| Image encoding | ~200ms | ~20ms |
| Text encoding | ~50ms | ~5ms |
| Similarity compute | <1ms | <1ms |

## Limitations

1. **Not for fine-grained tasks** - Best for broad categories
2. **Requires descriptive text** - Vague labels perform poorly
3. **Biased on web data** - May have dataset biases
4. **No bounding boxes** - Whole image only
5. **Limited spatial understanding** - Position/counting weak

## Resources

- **GitHub**: https://github.com/openai/CLIP ⭐ 25,300+
- **Paper**: https://arxiv.org/abs/2103.00020
- **Colab**: https://colab.research.google.com/github/openai/clip/
- **License**: MIT

## Pitfalls

1. **Wrong install package name** — The PyPI package is `git+https://github.com/openai/CLIP.git`, NOT `pip install clip` (a different package). Using `pip install clip` installs a color palette library. Always install from the GitHub source.

2. **Float16 dtype mismatch on CPU** — CLIP's ViT models default to float16 on CUDA but fall back to float32 on CPU. If you see `RuntimeError: expected scalar type Half but found Float`, explicitly set `model = model.float()` when running on CPU.

3. **`clip.tokenize` truncates long text silently** — CLIP's tokenizer has a 77-token limit. Text beyond 77 tokens is silently truncated to 77. Verify prompt length before tokenizing: `len(clip.tokenize([text])[0].nonzero())`.

4. **Embeddings not normalized before cosine similarity** — `model.encode_image()` and `model.encode_text()` return unnormalized embeddings. Using `@` (dot product) directly without normalization does NOT give cosine similarity — it gives a scaled inner product. Always normalize: `feat /= feat.norm(dim=-1, keepdim=True)`.

5. **`import clip` fails after pip install** — The openai/CLIP repo installs as `clip` module but depends on `ftfy`, `regex`, `tqdm`. If those are missing, the import fails silently. Install with: `pip install git+https://github.com/openai/CLIP.git ftfy regex tqdm`.

6. **Image preprocessing must use CLIP's own `preprocess` function** — CLIP requires a specific resize + center crop + normalization pipeline. Using `torchvision.transforms.ToTensor()` directly gives wrong results. Always use `model, preprocess = clip.load("ViT-B/32")` and apply `preprocess(image)`.

7. **`logits_per_image.softmax(dim=-1)` doesn't give probabilities across multiple batches** — `softmax` over `dim=-1` normalizes across labels within each image. If you have multiple images, each row is a separate distribution. Misreading the matrix shape `(N_images, N_texts)` leads to incorrect ranking.

8. **GPU OOM on large batches** — ViT-L/14 uses ~2GB VRAM just for the model weights. Processing 100 images simultaneously can OOM a 16GB GPU. Use `torch.utils.data.DataLoader` with `batch_size=16` and process in chunks.

9. **Vague text labels degrade zero-shot accuracy** — CLIP performs poorly with ambiguous labels like "type 1" or "category A". Use descriptive natural language: "a photo of a dog sitting in a park" outperforms "dog". Ensemble multiple phrasings: `["a photo of a dog", "a dog", "a pet dog"]`.

10. **`chromadb` incompatibility with `allow_dangerous_deserialization`** — When loading LangChain FAISS/CLIP index with `FAISS.load_local(..., allow_dangerous_deserialization=True)`, the flag is REQUIRED in LangChain ≥0.1.0 or you'll get a `ValueError: Cannot load index without allow_dangerous_deserialization=True`. Always pass the flag.

11. **CLIP v1 (openai/CLIP) vs OpenCLIP** — The original `openai/CLIP` repo is not the same as `open-clip-torch` (OpenCLIP from LAION). They have different model names, loading APIs, and performance characteristics. Don't mix imports. For production, prefer `open-clip-torch` which supports newer ViT-H and ViT-bigG models.



