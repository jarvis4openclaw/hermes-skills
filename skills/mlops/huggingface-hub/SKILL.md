---
name: huggingface-hub
description: "HuggingFace hf CLI: search/download/upload models, datasets."
version: 1.1.0
author: Hugging Face
license: MIT
tags: [huggingface, hf, models, datasets, hub, mlops]
platforms: [linux, macos, windows]
metadata:
  hermes:
    trigger_conditions:
      - "huggingface hub"
      - "hf CLI"
      - "download model from huggingface"
      - "upload to huggingface"
      - "hf download"
      - "hf upload"
      - "hf login"
      - "huggingface auth"
      - "hf datasets"
      - "hf models"
      - "hf spaces"
      - "hf cache"
      - "huggingface-cli"
---

# Hugging Face CLI (`hf`) Reference Guide

The `hf` command is the modern command-line interface for interacting with the Hugging Face Hub, providing tools to manage repositories, models, datasets, and Spaces.

> **IMPORTANT:** The `hf` command replaces the now deprecated `huggingface-cli` command.

## When to Use

- Downloading models or datasets from the Hugging Face Hub via CLI
- Uploading trained models, datasets, or files to a Hugging Face repository
- Managing Hugging Face authentication (`hf auth login`, token switching)
- Searching for models or datasets (`hf models list`, `hf datasets list`)
- Running SQL queries against dataset parquet URLs via DuckDB
- Managing Spaces (deploy, dev mode, hot-reload)
- Performing large-folder resumable uploads (`hf upload-large-folder`)
- Cleaning up local HF cache (`hf cache prune`, `hf cache verify`)
- Creating or deleting repositories programmatically

## Not For

- Fine-tuning models on Hugging Face datasets → use `axolotl`, `unsloth`, or `fine-tuning-with-trl` instead
- Running inference on HF models locally → use `llama-cpp`, `vllm`, or `serving-llms-vllm` instead
- Training ML models — this CLI manages assets, not computation → use ML training skills
- Browsing the HF Hub website interactively → use `browser_navigate` to `huggingface.co`
- Quantitative evaluation of models (MMLU, GSM8K) → use `evaluating-llms-harness`
- Quantizing models to GGUF format → use `gguf-quantization`
- Working with embeddings or vector search → use `chroma`, `faiss`, `pinecone`, or `qdrant-vector-search`

## Quick Start
*   **Installation:** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **Help:** Use `hf --help` to view all available functions and real-world examples.
*   **Authentication:** Recommended via `HF_TOKEN` environment variable or the `--token` flag.

---

## Core Commands

### General Operations
*   `hf download REPO_ID`: Download files from the Hub.
*   `hf upload REPO_ID`: Upload files/folders (recommended for single-commit).
*   `hf upload-large-folder REPO_ID LOCAL_PATH`: Recommended for resumable uploads of large directories.
*   `hf sync`: Sync files between a local directory and a bucket.
*   `hf env` / `hf version`: View environment and version details.

### Authentication (`hf auth`)
*   `login` / `logout`: Manage sessions using tokens from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
*   `list` / `switch`: Manage and toggle between multiple stored access tokens.
*   `whoami`: Identify the currently logged-in account.

### Repository Management (`hf repos`)
*   `create` / `delete`: Create or permanently remove repositories.
*   `duplicate`: Clone a model, dataset, or Space to a new ID.
*   `move`: Transfer a repository between namespaces.
*   `branch` / `tag`: Manage Git-like references.
*   `delete-files`: Remove specific files using patterns.

---

## Specialized Hub Interactions

### Datasets & Models
*   **Datasets:** `hf datasets list`, `info`, and `parquet` (list parquet URLs).
*   **SQL Queries:** `hf datasets sql SQL` — Execute raw SQL via DuckDB against dataset parquet URLs.
*   **Models:** `hf models list` and `info`.
*   **Papers:** `hf papers list` — View daily papers.

### Discussions & Pull Requests (`hf discussions`)
*   Manage the lifecycle of Hub contributions: `list`, `create`, `info`, `comment`, `close`, `reopen`, and `rename`.
*   `diff`: View changes in a PR.
*   `merge`: Finalize pull requests.

### Infrastructure & Compute
*   **Endpoints:** Deploy and manage Inference Endpoints (`deploy`, `pause`, `resume`, `scale-to-zero`, `catalog`).
*   **Jobs:** Run compute tasks on HF infrastructure. Includes `hf jobs uv` for running Python scripts with inline dependencies and `stats` for resource monitoring.
*   **Spaces:** Manage interactive apps. Includes `dev-mode` and `hot-reload` for Python files without full restarts.

### Storage & Automation
*   **Buckets:** Full S3-like bucket management (`create`, `cp`, `mv`, `rm`, `sync`).
*   **Cache:** Manage local storage with `list`, `prune` (remove detached revisions), and `verify` (checksum checks).
*   **Webhooks:** Automate workflows by managing Hub webhooks (`create`, `watch`, `enable`/`disable`).
*   **Collections:** Organize Hub items into collections (`add-item`, `update`, `list`).

---

## Advanced Usage & Tips

### Global Flags
*   `--format json`: Produces machine-readable output for automation.
*   `-q` / `--quiet`: Limits output to IDs only.

## Pitfalls

1. **`huggingface-cli` is deprecated — use `hf`** — The old `huggingface-cli` command no longer receives updates. Running it may produce stale results or fail on newer features. Recovery: always use `hf` instead.

2. **Auth token not set causes 401 on private repos** — `hf download` on private models/datasets fails silently with a 401 if no token is configured. Recovery: `hf auth login` or set `HF_TOKEN` environment variable.

3. **Multiple stored tokens can cause confusion** — `hf auth switch` may leave you on the wrong account without an obvious indicator. Recovery: always run `hf auth whoami` after switching to confirm the active account.

4. **Large model downloads timeout on slow connections** — Multi-GB models may timeout or fail mid-transfer on unstable connections. Recovery: use `hf download --resume` for interrupted downloads, or `hf upload-large-folder` for uploads.

5. **HF cache can consume 50+ GB silently** — Every downloaded model revision is cached locally in `~/.cache/huggingface/`. Recovery: use `hf cache list` to check usage, `hf cache prune` to remove detached revisions, and `hf cache verify` for checksum issues.

6. **Repository name collisions on upload** — `hf upload` overwrites existing files at the target repo without confirmation. Recovery: check the target repo contents first with `hf models info <repo>` or `hf datasets info <repo>`.

7. **`hf datasets sql` requires DuckDB knowledge** — The SQL query interface runs against parquet URLs but column names and types vary by dataset. Recovery: use `hf datasets info <dataset>` first to inspect the schema before writing SQL.

8. **Spaces hot-reload only works for Python files** — `hf spaces hot-reload` reloads `.py` files but not static assets, config, or dependencies. Recovery: for non-Python changes, redeploy the Space with `hf spaces restart`.

9. **`curl` installer script needs `bash` explicitly** — The `curl -LsSf https://hf.co/cli/install.sh | bash -s` command fails in `sh` or `dash` shells that don't support `bash`-specific syntax. Recovery: use `bash` explicitly.

10. **Permissions on uploaded repos default to private** — New repos created via `hf repos create` default to private visibility. Recovery: use `--private=false` or change visibility in the HF Hub web UI settings.
