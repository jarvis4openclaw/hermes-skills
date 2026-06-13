---
name: lightrag
description: Query the LightRAG knowledge graph for past decisions, infrastructure, projects, and lessons learned. Use before saying "I don't remember."
version: 1.1.0
metadata:
  hermes:
    tags: [lightrag, knowledge-graph, RAG, retrieval, memory]
    trigger_conditions:
      - "lightrag"
      - "LightRAG"
      - "knowledge graph"
      - "search past decisions"
      - "what do we know about"
      - "query the knowledge graph"
      - "past projects"
      - "lessons learned"
      - "infrastructure query"
      - "lightrag server"
      - "start lightrag"
      - "lightrag search"
      - "reindex knowledge"

# LightRAG Knowledge Graph

Query the LightRAG knowledge graph for past decisions, infrastructure, projects, and lessons learned.

## When To Use
- User asks about past work, decisions, or "what happened with X"
- Need context on projects, hardware, or configurations
- Remembering lessons learned or past issues
- Any question where you'd say "I don't remember" — use this FIRST

## Not For

- Real-time data or live system state → use `terminal` or API health checks
- General web research about topics not in the knowledge graph → use `web_search`
- Session-specific context (what was just said in this chat) → use `session_search` instead
- Storing new knowledge or lessons → ingestion happens via document import, not on-the-fly
- Structured database queries (SQL) → the graph stores documents/entities, not tabular data
- URL or domain lookups → use `domain-intel` or `web_extract`
- Email or calendar queries → use `himalaya` or `google-workspace`

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

## Pitfalls

1. **Server not running — "Connection refused" on query** — The most common failure. The LightRAG server process dies without notice. Recovery: `cd ~/.hermes/lightrag/LightRAG && nohup lightrag-server --port 9623 > ~/.hermes/lightrag/server.log 2>&1 &` to restart.

2. **Slow ingestion when entity extraction overwhelms the LLM** — Large document batches trigger extensive entity extraction, causing 30+ second processing per document. Recovery: use a faster model (Cerebras + Qwen 3 is fastest) or process documents in parallel batches.

3. **Empty or irrelevant query results** — The default `hybrid` mode may miss very specific facts. Recovery: try different query modes — `local` for specific entities, `global` for relationships, `hybrid` for general questions. Rephrase queries to be more entity-specific.

4. **Embedding model not running but server starts** — LightRAG starts without errors even when the embedding model (Ollama) is down. Queries return empty results with no error message. Recovery: `curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])));"` to verify Ollama has models loaded.

5. **Duplicate entities after re-ingestion** — LightRAG auto-merges similar entities, but exact duplicates from re-ingesting the same documents can accumulate. Recovery: use the Web UI at `http://localhost:9623/webui` to manually clean up, or nuclear option: `rm -rf ~/.hermes/lightrag/LightRAG/rag_storage/*` and reingest.

6. **Port 9623 conflict with other services** — The default port may conflict with other local services. Recovery: `ss -tlnp | grep 9623` to check; use `--port <alt>` to change.

7. **Default `hybrid` mode is not always optimal** — Using `hybrid` for every query is wrong. `local` mode targets specific entities (names, projects), `global` reveals relationships and patterns, `hybrid` balances both. Recovery: match the mode to the query type.

8. **Reindex after large batch imports is required** — After ingesting 50+ documents, the entity graph may be stale. Recovery: check entity count with `curl http://localhost:9623/graph/label/list | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} entities')"`, then trigger a reindex.

9. **Server log fills disk silently** — `nohup` redirects all output to `server.log` which can grow to GBs over weeks. Recovery: check log size with `du -h ~/.hermes/lightrag/server.log`, and rotate periodically.

10. **Settings in `.env` override CLI flags** — The LightRAG directory's `.env` file configures the LLM and embedding model. CLI flags like `--port` are respected, but model settings always come from `.env`. Recovery: edit `~/.hermes/lightrag/LightRAG/.env` to change models.
