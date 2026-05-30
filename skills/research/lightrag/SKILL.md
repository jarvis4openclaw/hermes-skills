---
name: lightrag
description: Query the LightRAG knowledge graph for past decisions, infrastructure, projects, and lessons learned. Use before saying "I don't remember."
---

# LightRAG Knowledge Graph

Query the LightRAG knowledge graph for past decisions, infrastructure, projects, and lessons learned.

## When To Use
- User asks about past work, decisions, or "what happened with X"
- Need context on projects, hardware, or configurations
- Remembering lessons learned or past issues
- Any question where you'd say "I don't remember" — use this FIRST

# Starting the service
The service can be started in the background using: nohup lightrag-server --port 9623 > ~/.hermes/lightrag/server.log 2>&1 &
Settings are in the .env file in the LightRAG directory. LLM is configured to use OpenRouter models optimized for RAG and Embeddings.

## Usage
```bash
curl -s -X POST http://localhost:9623/query \
  -H "Content-Type: application/json" \
  -d '{"query": "YOUR QUERY", "mode": "hybrid", "only_need_context": true}'
```

## Search Modes
- hybrid (default): Combined vector + graph search
- local: Entity-focused (specific facts)
- global: Relationship-focused (how things connect)
- naive: Vector-only (simple lookups)

# Important
- ALWAYS search this before saying "I don't remember"
- Results supersede general knowledge about the setup
- Reference entity names when citing results


### Query from a Script

Create `~/.hermes/skills/research/lightrag/scripts/lightrag_search.py`:

```python
#!/usr/bin/env python3
"""LightRAG search script for Hermes skill integration."""
import json
import sys
import urllib.request

def search(query: str, mode: str = "hybrid") -> str:
    url = "http://localhost:9623/query"
    payload = json.dumps({
        "query": query,
        "mode": mode,
        "only_need_context": True
    }).encode()
    
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("response", result.get("data", str(result)))
    except Exception as e:
        return f"LightRAG query failed: {e}"

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not query:
        print("Usage: lightrag_search.py <query>")
        sys.exit(1)
    print(search(query))
```

## Reindex After Bulk Changes
After ingesting a large batch of new documents:

### Check entity count
curl http://localhost:9623/graph/label/list | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} entities')"

## Use the Right Query Mode
Don't always default to hybrid. Use:

- local when asking about a specific thing ("Tell me about the GPU setup")
- global when asking about connections ("How do the projects relate?")
- hybrid for general questions ("What decisions were made last week?")

## Monitor and Prune
The Web UI at http://localhost:9623/webui lets you:

- Browse the knowledge graph visually
- See entity relationships
- Identify orphaned or redundant entities

## Troubleshooting
### "Connection refused" on query
The server isn't running. Start it:

cd ~/.hermes/lightrag/LightRAG && lightrag-server --port 9623

### Slow ingestion
Entity extraction is LLM-bound. Speed it up:

- Use a faster model for ingestion (Cerebras + Qwen 3 is the fastest option, or Kimi 2.5)
- Process documents in parallel batches
- Use a local model if you have GPU capacity

### Empty or irrelevant results
- Check that documents were actually ingested (Web UI → entities)
- Try different query modes (local vs global vs hybrid)
- Rephrase your query — be more specific about entities
- Check embedding model is actually running (curl http://localhost:11434/api/tags for Ollama)

### Duplicate entities after re-ingestion
LightRAG merges similar entities automatically, but exact duplicates can happen. Use the Web UI to manually clean up, or reindex from scratch:

#### Nuclear option: wipe and reingest
rm -rf ~/.hermes/lightrag/LightRAG/rag_storage/*
#### Then re-ingest your documents
