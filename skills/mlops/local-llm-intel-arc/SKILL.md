---
name: local-llm-intel-arc
description: "Deploy local GGUF LLMs on Intel Arc GPUs (Xe2 iGPU, Lunar Lake / Battlemage) via llama.cpp SYCL backend. Covers oneAPI setup, NVFP4 incompatibility, batch-file pitfalls, ctx/RAM sizing, and Hermes OpenAI-compatible wiring."
version: 1.1.0
author: Jarvis (Hermes)
license: MIT
tags: [intel-arc, xe2, sycl, oneapi, llama.cpp, gguf, lunar-lake, battlemage, local-llm, hermes]
platforms: [windows, linux]
metadata:
  hermes:
    trigger_conditions:
      - "run llama.cpp on Intel Arc"
      - "Intel Arc 140V local LLM"
      - "SYCL backend llama.cpp"
      - "oneAPI setvars llama-server"
      - "NVFP4 not running on Intel Arc"
      - "local LLM on Lunar Lake Surface"
      - "Intel GPU GGUF inference"
      - "Hermes local model Intel Arc"
      - "llama-server silent exit no output"
      - "GGUF quant fit unified memory"
      - "llama.cpp build GGML_SYCL clang"
      - "Arc iGPU n-gpu-layers 99"
      - "Qwen GGUF huggingface download include"
---

# Local LLM on Intel Arc (Xe2 iGPU) via llama.cpp SYCL

Use this skill when the user wants to run a local GGUF model on an **Intel Arc GPU** (Lunar Lake Arc 130V/140V, Battlemage B570/B580, Arc Pro B-series). This is a different backend from CUDA/ROCm/Metal — it uses **SYCL (oneAPI)** and the GPU shares **unified system RAM**.

## When to use
- Run a local LLM on Intel Arc (iGPU or dGPU) via llama.cpp
- Pick a GGUF quant that fits an Arc machine's unified memory
- Wire a locally-served model into Hermes as an OpenAI-compatible provider
- Diagnose "server starts then quits" / silent-exit on Arc
- Verify tool calling works against the local endpoint

## NOT for
- NVIDIA CUDA / AMD ROCm / Apple Metal deployment → use the `llama-cpp` skill
- NVFP4 / Blackwell checkpoints → these **cannot** run on Arc (see below)
- Production high-throughput serving → vLLM (no Intel Arc support yet for FP4)
- Training or fine-tuning workloads → this skill covers inference serving only
- Cloud GPU / rented instances → use `lambda-labs-gpu-cloud` or a cloud provider
- GUI chat apps (LM Studio, Ollama desktop) → LM Studio does not support Arc; use llama.cpp SYCL or the Vulkan fallback

## Hard rule: NVFP4 does NOT run on Intel Arc
NVFP4 (the `...-FP4` repos, e.g. `NVFP4/Qwen3-Coder-30B-A3B-Instruct-FP4`) requires **NVIDIA Blackwell 5th-gen Tensor Cores** (B200/B300/RTX 5090/RTX PRO 6000). It is NOT available on any prior generation or non-NVIDIA silicon. Intel Arc 140V is Xe2-LPG: INT8/INT4/FP16 only — no FP4 tensor hardware, no NVFP4 decoder. A `...-FP4` checkpoint is unrunnable on Arc; you must use a **standard GGUF** (Q4_K_M / IQ) build of the same model family.

If a "fit" tool (llmfit, etc.) claims an NVFP4 repo runs on an Arc iGPU, it is wrong — double-check the quant format against the GPU architecture.

## Model / quant selection for Arc (unified RAM)
Weights + KV cache + OS all share 16/32 GB LPDDR5X. Rule of thumb:
- Arc 140V on 32 GB with ~15 GB free: **Qwen3-14B-Instruct Q4_K_M (~8.6 GB)** fits comfortably. Qwen2.5-Coder-14B Q4_K_M (~9.0 GB) also fits.
- The 30B-A3B Q4 (~18.6 GB) **exceeds 15 GB free** → swap-to-disk, don't.
- Smaller options: Qwen3-14B IQ4_XS (~7.7 GB) for extra headroom.

## SYCL build + oneAPI
```bash
# build with SYCL (clang from oneAPI)
cmake -B build -DGGML_SYCL=ON -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++
cmake --build build --config Release
```
**oneAPI env is mandatory** — a SYCL build exits near-instantly (silent quit) without it, in the same shell:
```bat
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
```

## Critical pitfalls (these bite every time)
1. **`hf download --include` silently succeeds with 0 files** — if the glob matches no filename, `hf` downloads an empty snapshot, prints `Fetching 0 files / Download complete` at 0.00B, and does NOT error. Verify exact filenames first via `curl -sS https://huggingface.co/api/models/<REPO>/tree/main` — repo IDs often PREFIX the base name (e.g. `bartowski/Qwen_Qwen3-14B-GGUF` stores `Qwen_Qwen3-14B-Q4_K_M.gguf`, NOT `Qwen3-14B-Q4_K_M.gguf`). Prefer `--local-dir .` and confirm bytes > 0.
2. **Windows `cmd` `set VAR=x :: comment` corrupts the value** — `cmd.exe` does NOT strip `::` trailing comments from `set`. The comment text becomes part of the variable, so `--n-gpu-layers 30 :: note` passes `30 :: note` → invalid number → server aborts silently. Use `set "VAR=value"` quoting; put comments on their own `rem` lines.
3. **`--cont-batching` is a REMOVED flag** — continuous batching is now default-on; passing it aborts with `unrecognized arguments`. Omit it.
4. **`--flash-attn` may be absent in your SYCL build** — flash attention is compiled per-backend; if not built, the server errors on an unknown flag. Omit unless you built with it.
5. **`-ngl 25-35` is wrong for iGPU** — that's discrete-VRAM guidance. Arc has no VRAM; use `-ngl 99` so all layers compute on the Xe2 GPU, else CPU fallback = glacial.
6. **Browser at `/` returns 404 — EXPECTED** — `llama-server` is a bare API, not a website. Verify with `curl http://127.0.0.1:8080/health` (→ `{"status":"ok"}`) and `/v1/models`. Agents hit `/v1/chat/completions`.
7. **LM Studio does NOT support Intel Arc** (confirmed) — use llama.cpp SYCL or the Vulkan fallback.
8. **SYCL server exits near-instantly (silent quit)** — without `setvars.bat` sourced in the SAME shell, a SYCL build dies before printing anything. If `llama-server` starts and vanishes with no error, the oneAPI environment is missing — source it first.
9. **30B-A3B Q4 exceeds unified RAM headroom** — the ~18.6 GB quant on a 32 GB machine with ~15 GB free swaps to disk. Check `-ngl`/quant against free RAM; prefer Q4_K_M/IQ_XS of 14B-class models.
10. **Model name must match `/v1/models` output exactly** — a mismatched `model` field in the Hermes provider block returns 404 on `/v1/chat/completions`. Query `/v1/models` once and copy the exact id.

## Known-good batch file (Windows, SYCL)
```bat
@echo off
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
set "MODEL_PATH=C:\Users\wahid\.cache\huggingface\ub\models--bartowski--Qwen_Qwen3-14B-GGUF\snapshots\<commit>\Qwen_Qwen3-14B-Q4_K_M.gguf"
set "LLAMA_SERVER=build\bin\llama-server.exe"
"%LLAMA_SERVER%" --model "%MODEL_PATH%" --n-gpu-layers 99 --ctx-size 16384 --batch-size 256 --host 127.0.0.1 --port 8080 --threads 8
pause
```

## ctx / RAM math (32 GB unified, ~15 GB free)
Weights (Q4_K_M) ≈ constant 8.6 GB; only KV scales with ctx:
| ctx | KV @14B (fp16) | fits 15 GB free? |
|-----|----------------|------------------|
| 8192  | ~1.5 GB | yes, comfortable |
| 16384 | ~2–3 GB | yes, recommended |
| 32768 | ~5–6 GB | risky (swaps) |

Use **16384** for Hermes (modest agent turns; 16K gives room for tool loops). 8K is the safe floor.

## Hermes provider block (OpenAI-compatible)
```yaml
providers:
  - name: qwen3-14b-arc
    type: openai
    base_url: http://127.0.0.1:8080/v1
    api_key: not-needed
    models:
      - qwen3-14b-arc:
          model: Qwen_Qwen3-14B-Q4_K_M.gguf
```
Model name MUST match `/v1/models` output. Use `127.0.0.1` (not `0.0.0.0`) to keep it local.

## Tool-calling verification
Qwen chat template emits native tool calls via llama.cpp:
```bash
curl http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"Qwen_Qwen3-14B-Q4_K_M.gguf\",\"messages\":[{\"role\":\"user\",\"content\":\"What is 2+2?\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"calc\",\"description\":\"Add two numbers\",\"parameters\":{\"type\":\"object\",\"properties\":{\"a\":{\"type\":\"number\"},\"b\":{\"type\":\"number\"}},\"required\":[\"a\",\"b\"]}}}]}"
```
Expect a `choices[0].message.tool_calls` array.

## References
- **[intel-arc.md](references/intel-arc.md)** — full reproduction recipe, NVFP4 incompatibility detail, tool-calling curl, ctx/RAM table, Arc-specific pitfalls.
