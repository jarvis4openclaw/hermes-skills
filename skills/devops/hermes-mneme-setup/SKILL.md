---
name: hermes-mneme-setup
version: 1.1.0
description: Install and configure hermes-mneme context engine plugin for Hermes Agent — execution-graph-aware short-term memory paired with Mnemosyne for long-term recall.
tags: [hermes, plugin, memory, context-engine, embeddings, ollama, mneme, mnemosyne]
created: 2026-07-10
updated: 2026-07-10
metadata:
  hermes:
    tags: [hermes, plugin, memory, context-engine, embeddings, ollama, mneme, mnemosyne]
    trigger_conditions:
      - "install hermes-mneme"
      - "configure mneme context engine"
      - "nomic-embed-text ollama embedding"
      - "mneme embedding dimension mismatch"
      - "context engine plugin hermes"
      - "reranker endpoint LiteLLM"
      - "mneme circuit breaker disabled embeddings"
      - "gateway restart from outside"
      - "sqlite-vec KNN silently fails"
      - "hermes-mneme update plugin"
      - "mneme context_window_usage_percent"
      - "execution-graph-aware memory"
      - "memory provider mneme vs mnemosyne"
---

# Hermes-Mneme Setup

Hermes-Mneme is a retrieval-based context engine plugin that replaces Hermes' default lossy compressor with a state-aware memory layer. It pairs with **Mnemosyne** (cross-session long-term memory) — Mneme handles *within-session* context assembly, Mnemosyne handles *cross-session* recall.

## When to Use

- Installing or re-installing the hermes-mneme plugin from source.
- Switching the embedding backend (e.g. from the default Jina-MLX to Ollama nomic-embed-text).
- Tuning context-budget knobs (`context_window_usage_percent`, `protected_tail_turns`, etc.).
- Diagnosing silent memory failures (no embeddings, dimension mismatch, reranker timeouts).

## Not For

- **Cross-session long-term memory** → that is Mnemosyne (see `hermes-memory-provider-management`); Mneme is within-session only.
- **Writing durable facts to memory** → use the `mnemosyne_remember` path, not this plugin's config.
- **Choosing memory providers or migrating memories** → use `hermes-memory-provider-management`.
- **Debugging the Hermes gateway itself** (not the plugin) → use `hermes-config-management` / `hermes-gateway-platforms`.

## Architecture

- **Mneme** — within-session: embeds every turn, segments by topic drift, tracks execution graph, assembles prompt from token-budget mix of recent turns + retrieved context + execution state.
- **Mnemosyne** — cross-session: persists facts, episodic memories, working memory with FTS + vector search across sessions.

They don't conflict — different layers.

## Installation

```bash
cd ~
git clone https://github.com/johnnykor82/hermes-mneme.git ~/.hermes/plugins/hermes-mneme
cd ~/.hermes/plugins/hermes-mneme
./install.sh
```

All deps (tiktoken, yaml, requests, numpy, sqlite_vec) are already in the Hermes venv.

## Embedding Configuration

The plugin defaults to a local Jina-MLX server at `:8000` which isn't available. We patched it to use **Ollama nomic-embed-text** (768-dim, ~274MB, runs on CPU).

### Pull the embedding model

```bash
ollama pull nomic-embed-text
```

### Patch `index.py`

Edit `~/.hermes/plugins/hermes-mneme/index.py`:

```python
# Embedding Configuration — Ollama nomic-embed-text via OpenAI-compatible API
JINA_API_URL = "http://127.0.0.1:11434/v1/embeddings"
JINA_API_KEY = "ollama"
JINA_MODEL = "nomic-embed-text"
```

And change the embedding dimension in `__init__`:

```python
self.embedding_dim = 768  # nomic-embed-text dimension
```

### Patch `config.py`

Edit `~/.hermes/plugins/hermes-mneme/config.py`:

```python
"embedding_provider": "ollama",
"embedding_model": "nomic-embed-text",
"embedding_endpoint": "http://127.0.0.1:11434",
"embedding_api_key": "ollama",
```

Disable reranker (no LiteLLM running):

```python
"reranker_enabled": False,
```

## Key Config Knobs

| Setting | Default | Notes |
|---|---|---|
| `context_window_usage_percent` | 0.70 | 70% of model context window |
| `protected_tail_turns` | 64 | Last N turns always included verbatim |
| `state_budget_ratio` | 0.05 | 5% for execution state |
| `retrieved_budget_ratio` | 0.30 | 30% for retrieved context |
| `protected_tail_ratio` | 0.55 | 55% for protected tail |
| `drift_threshold` | 0.35 | Embedding drift threshold for segment boundary |
| `dependency_max_depth` | 4 | Execution graph propagation depth |
| `dependency_decay` | 0.6 | Decay factor per graph hop |
| `llm_enrichment_enabled` | True | Extracts open_loops, decisions, entities every N turns |
| `enricher_every_n_turns` | 5 | LLM enrichment frequency |

## Activation

Restart Hermes from outside the gateway:

```bash
hermes gateway restart
```

Verify:

```bash
tail -f ~/.hermes/logs/agent.log | grep -i mneme
```

Should see: `Hermes-Mneme context engine loaded.`

## Verification

Test embedding endpoint:

```bash
curl -s http://127.0.0.1:11434/v1/embeddings \
  -d '{"model":"nomic-embed-text","input":"test"}' | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print('dim:', len(d['data'][0]['embedding']))"
```

Should return `dim: 768`.

## Pitfalls

1. **Cannot restart gateway from inside itself** — run `hermes gateway restart` from a separate terminal (or via cron/systemd outside the gateway tree). An in-process restart is killed by the gateway's own guard.
2. **Embedding dimension mismatch (silent KNN failure)** — if you change the embedding model, you MUST also update `self.embedding_dim` in `index.py` (768 for nomic-embed-text) or sqlite-vec KNN silently returns garbage. Symptom: no error, but retrieval results are nonsense/empty.
3. **Reranker endpoint defaults to LiteLLM `:4000`** — if LiteLLM is not running, keep `reranker_enabled: False` or every retrieval times out waiting for the reranker.
4. **LLM enrichment uses the current model** — if your model is expensive/slow, raise `enricher_every_n_turns` (e.g. 10) or disable `llm_enrichment_enabled` entirely.
5. **Circuit breaker disables embeddings silently** — after 3 consecutive embedding failures, the plugin disables embeddings for 300s and falls back to keyword/recency. Check logs for `Embedding endpoint disabled` before debugging "why is retrieval dumb".
6. **Ollama embedding endpoint must be OpenAI-compatible** — the patched `JINA_API_URL` points at `http://127.0.0.1:11434/v1/embeddings` with key `ollama`; if Ollama runs on a different host/port or the model isn't pulled, verification fails with `dim:` empty.
7. **`hermes gateway restart` from cron has env pitfalls** — cron runs under systemd (PPID 1) outside the gateway tree; ensure `XDG_RUNTIME_DIR` is set or `systemctl --user` calls fail (see the recycle-script lessons in session history).
8. **Runtime data survives updates** — `db/plugin.db` and `trace.jsonl` are gitignored; a `git pull`/`./install.sh` does not reset them. If you WANT a clean state, delete them manually.
9. **Config edits require a gateway restart** — changing `config.py` knobs does not hot-reload; verify with `tail -f ~/.hermes/logs/agent.log | grep -i mneme` → `Hermes-Mneme context engine loaded.`
10. **Embedding dim must match the vector table** — if `sqlite-vec` was initialized with a different dimension, the KNN query fails or returns zero rows even with a matching model. Recreate the plugin DB when changing dimensions.

## Updating

```bash
cd ~/.hermes/plugins/hermes-mneme
git pull
./install.sh  # reinstalls deps if requirements.txt changed
```

Runtime data (`db/plugin.db`, `trace.jsonl`) is gitignored and survives updates.

## Source

- Repo: https://github.com/johnnykor82/hermes-mneme
- Pairs with: https://github.com/johnnykor82/mnemosyne (Mnemosyne)
