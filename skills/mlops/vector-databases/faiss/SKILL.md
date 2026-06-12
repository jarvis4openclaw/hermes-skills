---
name: faiss
description: Facebook's library for efficient similarity search and clustering of dense vectors. Supports billions of vectors, GPU acceleration, and various index types (Flat, IVF, HNSW). Use for fast k-NN search, large-scale vector retrieval, or when you need pure similarity search without metadata. Best for high-performance applications.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [faiss-cpu, faiss-gpu, numpy]
metadata:
  hermes:
    tags: [RAG, FAISS, Similarity Search, Vector Search, Facebook AI, GPU Acceleration, Billion-Scale, K-NN, HNSW, High Performance, Large Scale]
    trigger_conditions:
      - "fast vector similarity search"
      - "FAISS index"
      - "k-NN search large scale"
      - "billion scale vector search"
      - "FAISS install"
      - "FAISS IVF HNSW"
      - "facebook AI similarity search"
      - "GPU vector search"
      - "FAISS with LangChain"
      - "FAISS with LlamaIndex"
      - "FAISS embeddings"
      - "vector search no metadata"
      - "offline batch vector retrieval"

---

# FAISS - Efficient Similarity Search

Facebook AI's library for billion-scale vector similarity search.

## When to use FAISS

**Use FAISS when:**
- Need fast similarity search on large vector datasets (millions/billions)
- GPU acceleration required
- Pure vector similarity (no metadata filtering needed)
- High throughput, low latency critical
- Offline/batch processing of embeddings

## Not For

- **Metadata filtering alongside vector search** → use `chroma`, `qdrant-vector-search`, or `pinecone` — FAISS has no metadata store
- **Managed cloud vector DB** → use `pinecone` for zero-ops hosted vector search
- **Full-text search combined with vector search** → use `qdrant-vector-search` or Weaviate for hybrid search
- **Persistent storage with ACID guarantees** → FAISS is in-memory only; use Qdrant or Pinecone for durability
- **Real-time vector updates at scale** → FAISS IndexFlatL2 doesn't support updates; use Qdrant for updatable indexes

**Metrics**:
- **31,700+ GitHub stars**
- Meta/Facebook AI Research
- **Handles billions of vectors**
- **C++** with Python bindings

**Use alternatives instead**:
- **Chroma/Pinecone**: Need metadata filtering
- **Weaviate**: Need full database features
- **Annoy**: Simpler, fewer features

## Quick start

### Installation

```bash
# CPU only
pip install faiss-cpu

# GPU support
pip install faiss-gpu
```

### Basic usage

```python
import faiss
import numpy as np

# Create sample data (1000 vectors, 128 dimensions)
d = 128
nb = 1000
vectors = np.random.random((nb, d)).astype('float32')

# Create index
index = faiss.IndexFlatL2(d)  # L2 distance
index.add(vectors)             # Add vectors

# Search
k = 5  # Find 5 nearest neighbors
query = np.random.random((1, d)).astype('float32')
distances, indices = index.search(query, k)

print(f"Nearest neighbors: {indices}")
print(f"Distances: {distances}")
```

## Index types

### 1. Flat (exact search)

```python
# L2 (Euclidean) distance
index = faiss.IndexFlatL2(d)

# Inner product (cosine similarity if normalized)
index = faiss.IndexFlatIP(d)

# Slowest, most accurate
```

### 2. IVF (inverted file) - Fast approximate

```python
# Create quantizer
quantizer = faiss.IndexFlatL2(d)

# IVF index with 100 clusters
nlist = 100
index = faiss.IndexIVFFlat(quantizer, d, nlist)

# Train on data
index.train(vectors)

# Add vectors
index.add(vectors)

# Search (nprobe = clusters to search)
index.nprobe = 10
distances, indices = index.search(query, k)
```

### 3. HNSW (Hierarchical NSW) - Best quality/speed

```python
# HNSW index
M = 32  # Number of connections per layer
index = faiss.IndexHNSWFlat(d, M)

# No training needed
index.add(vectors)

# Search
distances, indices = index.search(query, k)
```

### 4. Product Quantization - Memory efficient

```python
# PQ reduces memory by 16-32×
m = 8   # Number of subquantizers
nbits = 8
index = faiss.IndexPQ(d, m, nbits)

# Train and add
index.train(vectors)
index.add(vectors)
```

## Save and load

```python
# Save index
faiss.write_index(index, "large.index")

# Load index
index = faiss.read_index("large.index")

# Continue using
distances, indices = index.search(query, k)
```

## GPU acceleration

```python
# Single GPU
res = faiss.StandardGpuResources()
index_cpu = faiss.IndexFlatL2(d)
index_gpu = faiss.index_cpu_to_gpu(res, 0, index_cpu)  # GPU 0

# Multi-GPU
index_gpu = faiss.index_cpu_to_all_gpus(index_cpu)

# 10-100× faster than CPU
```

## LangChain integration

```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Create FAISS vector store
vectorstore = FAISS.from_documents(docs, OpenAIEmbeddings())

# Save
vectorstore.save_local("faiss_index")

# Load
vectorstore = FAISS.load_local(
    "faiss_index",
    OpenAIEmbeddings(),
    allow_dangerous_deserialization=True
)

# Search
results = vectorstore.similarity_search("query", k=5)
```

## LlamaIndex integration

```python
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

# Create FAISS index
d = 1536
faiss_index = faiss.IndexFlatL2(d)

vector_store = FaissVectorStore(faiss_index=faiss_index)
```

## Best practices

1. **Choose right index type** - Flat for <10K, IVF for 10K-1M, HNSW for quality
2. **Normalize for cosine** - Use IndexFlatIP with normalized vectors
3. **Use GPU for large datasets** - 10-100× faster
4. **Save trained indices** - Training is expensive
5. **Tune nprobe/ef_search** - Balance speed/accuracy
6. **Monitor memory** - PQ for large datasets
7. **Batch queries** - Better GPU utilization

## Performance

| Index Type | Build Time | Search Time | Memory | Accuracy |
|------------|------------|-------------|--------|----------|
| Flat | Fast | Slow | High | 100% |
| IVF | Medium | Fast | Medium | 95-99% |
| HNSW | Slow | Fastest | High | 99% |
| PQ | Medium | Fast | Low | 90-95% |

## Resources

- **GitHub**: https://github.com/facebookresearch/faiss ⭐ 31,700+
- **Wiki**: https://github.com/facebookresearch/faiss/wiki
- **License**: MIT

## Pitfalls

1. **`pip install faiss-gpu` fails without matching CUDA** — `faiss-gpu` requires the CUDA version to match (e.g., `faiss-gpu-cu11` for CUDA 11, `faiss-gpu-cu12` for CUDA 12). Installing the wrong variant gives `ImportError: libcublasLt.so.11: cannot open shared object file`. Use `pip install faiss-gpu-cu12` for CUDA 12 environments.

2. **Vectors must be float32, NOT float64** — FAISS only accepts `float32`. NumPy arrays default to `float64`. Passing them directly gives `TypeError: in method 'IndexFlatL2_add', argument 2 of type 'faiss::idx_t'`. Always cast: `vectors = vectors.astype('float32')`.

3. **IVF index must be trained before adding vectors** — `IndexIVFFlat` and other IVF variants require `index.train(vectors)` before `index.add(vectors)`. Skipping training gives `AssertionError: index must be trained before adding`. Flat and HNSW indexes do NOT require training.

4. **`nprobe` defaults to 1 — gives poor recall** — After creating an IVF index, `nprobe` defaults to 1 (search only 1 cluster). This gives fast but low-recall results. Set `index.nprobe = min(nlist // 10, 64)` for good accuracy vs. speed tradeoff.

5. **Saving trained IVF index loses `nprobe` setting** — After `faiss.write_index(index, path)` and `faiss.read_index(path)`, the loaded index resets `nprobe` to 1. Re-set `index.nprobe` after every load.

6. **GPU index can't be serialized directly** — `faiss.write_index(gpu_index, path)` fails. Convert to CPU first: `cpu_index = faiss.index_gpu_to_cpu(gpu_index)`, then `faiss.write_index(cpu_index, path)`.

7. **`IndexFlatL2` returns squared Euclidean distances, NOT L2 distances** — The returned `distances` are squared L2 (sum of squared differences). If you need true L2 distance, take the square root: `np.sqrt(distances)`. Comparing with a threshold expecting L2 units will be off.

8. **`IndexHNSW` search performance degrades with low `ef_search`** — HNSW search quality is controlled by `index.hnsw.efSearch` (default: 16). Increase to 64–256 for higher recall. Lower values give faster but less accurate results. Unlike IVF, HNSW doesn't need training but takes longer to build.

9. **LangChain `FAISS.load_local` requires `allow_dangerous_deserialization=True`** — In LangChain ≥0.1.0, loading a saved FAISS index raises `ValueError: Cannot load index without allow_dangerous_deserialization=True`. Always pass the flag; it's required, not optional.

10. **`index.search` returns `-1` for missing neighbors** — If the index has fewer vectors than `k`, FAISS pads the result array with `-1` for indices and `0.0` or large float for distances. Always filter out `-1` index results before using them.

11. **Product Quantization (PQ) requires dimension divisible by `m`** — `IndexPQ(d, m, nbits)` requires `d % m == 0`. Using `d=512, m=8` works (64 per subquantizer), but `d=512, m=6` fails with `AssertionError`. Pick `m` as a divisor of `d`.



