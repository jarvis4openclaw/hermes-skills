---
name: qdrant-vector-search
description: High-performance vector similarity search engine for RAG and semantic search. Use when building production RAG systems requiring fast nearest neighbor search, hybrid search with filtering, or scalable vector storage with Rust-powered performance.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [qdrant-client>=1.12.0]
metadata:
  hermes:
    tags: [RAG, Vector Search, Qdrant, Semantic Search, Embeddings, Similarity Search, HNSW, Production, Distributed]
    trigger_conditions:
      - "set up qdrant"
      - "vector database"
      - "qdrant vector search"
      - "semantic search with qdrant"
      - "RAG with qdrant"
      - "qdrant collection"
      - "qdrant docker"
      - "qdrant quantization"
      - "hybrid search qdrant"
      - "sparse vectors qdrant"
      - "qdrant payload index"
      - "qdrant cloud"
      - "qdrant performance tuning"
---

# Qdrant - Vector Similarity Search Engine

High-performance vector database written in Rust for production RAG and semantic search.

## When to Use

- Setting up a vector database for production RAG with low-latency requirements
- Performing hybrid search combining dense vectors with metadata filtering
- Running Qdrant via Docker for local development with persistent storage
- Creating collections with custom HNSW parameters for your vector dimensions
- Enabling quantization (scalar/product/binary) for memory-efficient large collections
- Indexing payload fields for faster filtered search
- Deploying with Qdrant Cloud for managed infrastructure
- Using multi-vector or sparse vector (BM25/SPLADE) collections

## Not For

- **Simple embedded vector storage for prototyping** → use `chroma` instead
- **Maximum raw speed for research/batch processing** → use `faiss` instead
- **Fully managed zero-ops vector database** → use `pinecone` instead
- **GraphQL-native queries with built-in vectorizers** → use Weaviate instead
- **Training embeddings or fine-tuning models** → use `peft-fine-tuning` or `sentence-transformers` instead
- **Evaluating retrieval quality** → use `evaluating-llms-harness` instead
- **Local LLM inference with vector search** → use `llama-cpp` instead

## When to use Qdrant

**Use Qdrant when:**
- Building production RAG systems requiring low latency
- Need hybrid search (vectors + metadata filtering)
- Require horizontal scaling with sharding/replication
- Want on-premise deployment with full data control
- Need multi-vector storage per record (dense + sparse)
- Building real-time recommendation systems

**Key features:**
- **Rust-powered**: Memory-safe, high performance
- **Rich filtering**: Filter by any payload field during search
- **Multiple vectors**: Dense, sparse, multi-dense per point
- **Quantization**: Scalar, product, binary for memory efficiency
- **Distributed**: Raft consensus, sharding, replication
- **REST + gRPC**: Both APIs with full feature parity

**Use alternatives instead:**
- **Chroma**: Simpler setup, embedded use cases
- **FAISS**: Maximum raw speed, research/batch processing
- **Pinecone**: Fully managed, zero ops preferred
- **Weaviate**: GraphQL preference, built-in vectorizers

## Quick start

### Installation

```bash
# Python client
pip install qdrant-client

# Docker (recommended for development)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Docker with persistent storage
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### Basic usage

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Insert vectors with payload
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, ...],  # 384-dim vector
            payload={"title": "Doc 1", "category": "tech"}
        ),
        PointStruct(
            id=2,
            vector=[0.3, 0.4, ...],
            payload={"title": "Doc 2", "category": "science"}
        )
    ]
)

# Search with filtering
results = client.search(
    collection_name="documents",
    query_vector=[0.15, 0.25, ...],
    query_filter={
        "must": [{"key": "category", "match": {"value": "tech"}}]
    },
    limit=10
)

for point in results:
    print(f"ID: {point.id}, Score: {point.score}, Payload: {point.payload}")
```

## Core concepts

### Points - Basic data unit

```python
from qdrant_client.models import PointStruct

# Point = ID + Vector(s) + Payload
point = PointStruct(
    id=123,                              # Integer or UUID string
    vector=[0.1, 0.2, 0.3, ...],        # Dense vector
    payload={                            # Arbitrary JSON metadata
        "title": "Document title",
        "category": "tech",
        "timestamp": 1699900000,
        "tags": ["python", "ml"]
    }
)

# Batch upsert (recommended)
client.upsert(
    collection_name="documents",
    points=[point1, point2, point3],
    wait=True  # Wait for indexing
)
```

### Collections - Vector containers

```python
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

# Create with HNSW configuration
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,                        # Vector dimensions
        distance=Distance.COSINE         # COSINE, EUCLID, DOT, MANHATTAN
    ),
    hnsw_config=HnswConfigDiff(
        m=16,                            # Connections per node (default 16)
        ef_construct=100,                # Build-time accuracy (default 100)
        full_scan_threshold=10000        # Switch to brute force below this
    ),
    on_disk_payload=True                 # Store payload on disk
)

# Collection info
info = client.get_collection("documents")
print(f"Points: {info.points_count}, Vectors: {info.vectors_count}")
```

### Distance metrics

| Metric | Use Case | Range |
|--------|----------|-------|
| `COSINE` | Text embeddings, normalized vectors | 0 to 2 |
| `EUCLID` | Spatial data, image features | 0 to ∞ |
| `DOT` | Recommendations, unnormalized | -∞ to ∞ |
| `MANHATTAN` | Sparse features, discrete data | 0 to ∞ |

## Search operations

### Basic search

```python
# Simple nearest neighbor search
results = client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, ...],
    limit=10,
    with_payload=True,
    with_vectors=False  # Don't return vectors (faster)
)
```

### Filtered search

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# Complex filtering
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="tech")),
            FieldCondition(key="timestamp", range=Range(gte=1699000000))
        ],
        must_not=[
            FieldCondition(key="status", match=MatchValue(value="archived"))
        ]
    ),
    limit=10
)

# Shorthand filter syntax
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter={
        "must": [
            {"key": "category", "match": {"value": "tech"}},
            {"key": "price", "range": {"gte": 10, "lte": 100}}
        ]
    },
    limit=10
)
```

### Batch search

```python
from qdrant_client.models import SearchRequest

# Multiple queries in one request
results = client.search_batch(
    collection_name="documents",
    requests=[
        SearchRequest(vector=[0.1, ...], limit=5),
        SearchRequest(vector=[0.2, ...], limit=5, filter={"must": [...]}),
        SearchRequest(vector=[0.3, ...], limit=10)
    ]
)
```

## RAG integration

### With sentence-transformers

```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# Initialize
encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Index documents
documents = [
    {"id": 1, "text": "Python is a programming language", "source": "wiki"},
    {"id": 2, "text": "Machine learning uses algorithms", "source": "textbook"},
]

points = [
    PointStruct(
        id=doc["id"],
        vector=encoder.encode(doc["text"]).tolist(),
        payload={"text": doc["text"], "source": doc["source"]}
    )
    for doc in documents
]
client.upsert(collection_name="knowledge_base", points=points)

# RAG retrieval
def retrieve(query: str, top_k: int = 5) -> list[dict]:
    query_vector = encoder.encode(query).tolist()
    results = client.search(
        collection_name="knowledge_base",
        query_vector=query_vector,
        limit=top_k
    )
    return [{"text": r.payload["text"], "score": r.score} for r in results]

# Use in RAG pipeline
context = retrieve("What is Python?")
prompt = f"Context: {context}\n\nQuestion: What is Python?"
```

### With LangChain

```python
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Qdrant.from_documents(documents, embeddings, url="http://localhost:6333", collection_name="docs")
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
```

### With LlamaIndex

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex, StorageContext

vector_store = QdrantVectorStore(client=client, collection_name="llama_docs")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
query_engine = index.as_query_engine()
```

## Multi-vector support

### Named vectors (different embedding models)

```python
from qdrant_client.models import VectorParams, Distance

# Collection with multiple vector types
client.create_collection(
    collection_name="hybrid_search",
    vectors_config={
        "dense": VectorParams(size=384, distance=Distance.COSINE),
        "sparse": VectorParams(size=30000, distance=Distance.DOT)
    }
)

# Insert with named vectors
client.upsert(
    collection_name="hybrid_search",
    points=[
        PointStruct(
            id=1,
            vector={
                "dense": dense_embedding,
                "sparse": sparse_embedding
            },
            payload={"text": "document text"}
        )
    ]
)

# Search specific vector
results = client.search(
    collection_name="hybrid_search",
    query_vector=("dense", query_dense),  # Specify which vector
    limit=10
)
```

### Sparse vectors (BM25, SPLADE)

```python
from qdrant_client.models import SparseVectorParams, SparseIndexParams, SparseVector

# Collection with sparse vectors
client.create_collection(
    collection_name="sparse_search",
    vectors_config={},
    sparse_vectors_config={"text": SparseVectorParams(index=SparseIndexParams(on_disk=False))}
)

# Insert sparse vector
client.upsert(
    collection_name="sparse_search",
    points=[PointStruct(id=1, vector={"text": SparseVector(indices=[1, 5, 100], values=[0.5, 0.8, 0.2])}, payload={"text": "document"})]
)
```

## Quantization (memory optimization)

```python
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig, ScalarType

# Scalar quantization (4x memory reduction)
client.create_collection(
    collection_name="quantized",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type=ScalarType.INT8,
            quantile=0.99,        # Clip outliers
            always_ram=True      # Keep quantized in RAM
        )
    )
)

# Search with rescoring
results = client.search(
    collection_name="quantized",
    query_vector=query,
    search_params={"quantization": {"rescore": True}},  # Rescore top results
    limit=10
)
```

## Payload indexing

```python
from qdrant_client.models import PayloadSchemaType

# Create payload index for faster filtering
client.create_payload_index(
    collection_name="documents",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="documents",
    field_name="timestamp",
    field_schema=PayloadSchemaType.INTEGER
)

# Index types: KEYWORD, INTEGER, FLOAT, GEO, TEXT (full-text), BOOL
```

## Production deployment

### Qdrant Cloud

```python
from qdrant_client import QdrantClient

# Connect to Qdrant Cloud
client = QdrantClient(
    url="https://your-cluster.cloud.qdrant.io",
    api_key="your-api-key"
)
```

### Performance tuning

```python
# Optimize for search speed (higher recall)
client.update_collection(
    collection_name="documents",
    hnsw_config=HnswConfigDiff(ef_construct=200, m=32)
)

# Optimize for indexing speed (bulk loads)
client.update_collection(
    collection_name="documents",
    optimizer_config={"indexing_threshold": 20000}
)
```

## Best practices

1. **Batch operations** - Use batch upsert/search for efficiency
2. **Payload indexing** - Index fields used in filters
3. **Quantization** - Enable for large collections (>1M vectors)
4. **Sharding** - Use for collections >10M vectors
5. **On-disk storage** - Enable `on_disk_payload` for large payloads
6. **Connection pooling** - Reuse client instances

## Pitfalls

1. **Docker container not reachable on port 6333** — The default Docker run command maps ports but doesn't survive container restarts. Use `docker run -d --name qdrant --restart unless-stopped -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant` for persistent setup. Verify with `curl http://localhost:6333/health`.

2. **Collection already exists error** — `create_collection` raises `qdrant_client.http.exceptions.UnexpectedResponse` if the collection name is taken. Use `client.collection_exists("name")` to check first, or call `client.delete_collection("name")` if you want to recreate it. In production, use `client.get_collections()` to list existing collections.

3. **Vector dimension mismatch** — The `size` parameter in `VectorParams` must match your embedding model's output dimension. MiniLM-L6-v2 = 384, text-embedding-ada-002 = 1536, BGE-large = 1024. Mismatch causes `UnexpectedResponse: Wrong input: Vector dimension error`. Always verify with `len(embedding)` before creating the collection.

4. **Port 6333 vs 6334 confusion** — Port 6333 is REST API, 6334 is gRPC. The Python client defaults to REST (6333). If using gRPC (`prefer_grpc=True`), ensure port 6334 is exposed. Docker must publish both ports: `-p 6333:6333 -p 6334:6334`.

5. **Filter on unindexed field is slow** — Filtering on a payload field without an index triggers a full scan. Always create payload indexes on fields used in filters: `client.create_payload_index(collection_name="docs", field_name="category", field_schema=PayloadSchemaType.KEYWORD)`. Check existing indexes with `client.list_snapshots()`.

6. **Out of memory with large collections** — Collections over 1M vectors without quantization can exhaust RAM. Enable scalar quantization: `quantization_config=ScalarQuantization(scalar=ScalarQuantizationConfig(type=ScalarType.INT8, quantile=0.99, always_ram=True))`. Also set `on_disk_payload=True` to store payloads on disk.

7. **gRPC connection errors on cloud** — Qdrant Cloud uses HTTPS with API key auth. The gRPC port may be blocked by corporate firewalls. Always test REST first: `client = QdrantClient(url="https://your-cluster.cloud.qdrant.io", api_key="your-key")`. If gRPC fails, the client falls back to REST automatically.

8. **Point ID collision on upsert** — `upsert` with the same ID overwrites the existing point. Use UUIDs for deduplication: `import uuid; point_id = str(uuid.uuid4())`. For idempotent inserts, use `client.set_payload()` on existing points instead of re-upserting.

9. **Sparse vector index requires explicit configuration** — Creating a sparse vector collection without `SparseIndexParams` silently succeeds but search fails. Always include `index=SparseIndexParams(on_disk=False)` in `SparseVectorParams`. For production, set `on_disk=True` to save RAM.

10. **Quantization rescore overhead** — `rescore=True` improves accuracy but doubles query latency. For latency-sensitive applications, disable rescore: `search_params={"quantization": {"rescore": False}}`. Test accuracy impact on your data before disabling.

11. **wait=True blocks on large batches** — Setting `wait=True` on `upsert` with 100k+ points blocks until indexing completes. For bulk loads, use `wait=False` and check progress with `client.count(collection_name)`. The collection is searchable immediately but results improve as indexing progresses.

12. **Distance metric affects search quality** — COSINE is correct for normalized embeddings (most text models). Using DOT on unnormalized vectors produces poor results. For embeddings from sentence-transformers (which are L2-normalized), COSINE and DOT are equivalent. Check your embedding model's normalization before choosing.

## Common issues

**Slow search with filters:**
```python
# Create payload index for filtered fields
client.create_payload_index(
    collection_name="docs",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)
```

**Out of memory:**
```python
# Enable quantization and on-disk storage
client.create_collection(
    collection_name="large_collection",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    quantization_config=ScalarQuantization(...),
    on_disk_payload=True
)
```

**Connection issues:**
```python
# Use timeout and retry
client = QdrantClient(
    host="localhost",
    port=6333,
    timeout=30,
    prefer_grpc=True  # gRPC for better performance
)
```

## References

- **[Advanced Usage](references/advanced-usage.md)** - Distributed mode, hybrid search, recommendations
- **[Troubleshooting](references/troubleshooting.md)** - Common issues, debugging, performance tuning

## Resources

- **GitHub**: https://github.com/qdrant/qdrant (22k+ stars)
- **Docs**: https://qdrant.tech/documentation/
- **Python Client**: https://github.com/qdrant/qdrant-client
- **Cloud**: https://cloud.qdrant.io
- **Version**: 1.12.0+
- **License**: Apache 2.0