---
name: optimizing-attention-flash
description: Optimizes transformer attention with Flash Attention for 2-4x speedup and 10-20x memory reduction. Use when training/running transformers with long sequences (>512 tokens), encountering GPU memory issues with attention, or need faster inference. Supports PyTorch native SDPA, flash-attn library, H100 FP8, and sliding window attention.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [flash-attn, torch, transformers]
metadata:
  hermes:
    tags: [Optimization, Flash Attention, Attention Optimization, Memory Efficiency, Speed Optimization, Long Context, PyTorch, SDPA, H100, FP8, Transformers]
    trigger_conditions:
      - "flash attention"
      - "optimize attention"
      - "speed up attention"
      - "memory efficient attention"
      - "reduce GPU memory attention"
      - "long sequence training OOM"
      - "H100 attention optimization"
      - "FP8 attention"
      - "sliding window attention"
      - "multi-query attention"
      - "scaled dot product attention"
      - "SDPA flash"
      - "install flash-attn"

---

# Flash Attention - Fast Memory-Efficient Attention

## Quick start

Flash Attention provides 2-4x speedup and 10-20x memory reduction for transformer attention through IO-aware tiling and recomputation.

**PyTorch native (easiest, PyTorch 2.2+)**:
```python
import torch
import torch.nn.functional as F

q = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)  # [batch, heads, seq, dim]
k = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)
v = torch.randn(2, 8, 512, 64, device='cuda', dtype=torch.float16)

# Automatically uses Flash Attention if available
out = F.scaled_dot_product_attention(q, k, v)
```

**flash-attn library (more features)**:
```bash
pip install flash-attn --no-build-isolation
```

```python
from flash_attn import flash_attn_func

# q, k, v: [batch, seqlen, nheads, headdim]
out = flash_attn_func(q, k, v, dropout_p=0.0, causal=True)
```

## When to Use

- Training transformers with sequences >512 tokens on NVIDIA GPUs
- Running inference with long context windows (>2K tokens)
- GPU memory constrained (OOM with standard attention)
- Need 2-4x speedup without accuracy loss on Ampere+ GPUs
- Using PyTorch 2.2+ and want zero-code-change acceleration via SDPA
- Deploying on H100 GPUs and want FP8 attention for maximum throughput
- Implementing sliding window or multi-query attention patterns
- Processing batches where attention is the bottleneck

## Not For

- **Sequences <256 tokens** → use standard attention; Flash Attention overhead dominates
- **CPU inference only** → Flash Attention requires GPU (use `torch.nn.MultiheadAttention` instead)
- **Volta GPUs (V100)** → not supported; use `xFormers` memory-efficient attention instead
- **Need diverse attention variants beyond speed** → use `xFormers` instead
- **Training on AMD GPUs** → use `composable_kernel` or `triton` attention instead
- **Float32 precision required** → Flash Attention only supports float16/bfloat16; use standard attention
- **Non-attention bottlenecks** → profile first; Flash Attention won't help if attention isn't the bottleneck

## Common workflows

### Workflow 1: Enable in existing PyTorch model

Copy this checklist:

```
Flash Attention Integration:
- [ ] Step 1: Check PyTorch version (≥2.2)
- [ ] Step 2: Enable Flash Attention backend
- [ ] Step 3: Verify speedup with profiling
- [ ] Step 4: Test accuracy matches baseline
```

**Step 1: Check PyTorch version**

```bash
python -c "import torch; print(torch.__version__)"
# Should be ≥2.2.0
```

If <2.2, upgrade:
```bash
pip install --upgrade torch
```

**Step 2: Enable Flash Attention backend**

Replace standard attention:
```python
# Before (standard attention)
attn_weights = torch.softmax(q @ k.transpose(-2, -1) / math.sqrt(d_k), dim=-1)
out = attn_weights @ v

# After (Flash Attention)
import torch.nn.functional as F
out = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
```

Force Flash Attention backend:
```python
with torch.backends.cuda.sdp_kernel(
    enable_flash=True,
    enable_math=False,
    enable_mem_efficient=False
):
    out = F.scaled_dot_product_attention(q, k, v)
```

**Step 3: Verify speedup with profiling**

```python
import torch.utils.benchmark as benchmark

def test_attention(use_flash):
    q, k, v = [torch.randn(2, 8, 2048, 64, device='cuda', dtype=torch.float16) for _ in range(3)]

    if use_flash:
        with torch.backends.cuda.sdp_kernel(enable_flash=True):
            return F.scaled_dot_product_attention(q, k, v)
    else:
        attn = (q @ k.transpose(-2, -1) / 8.0).softmax(dim=-1)
        return attn @ v

# Benchmark
t_flash = benchmark.Timer(stmt='test_attention(True)', globals=globals())
t_standard = benchmark.Timer(stmt='test_attention(False)', globals=globals())

print(f"Flash: {t_flash.timeit(100).mean:.3f}s")
print(f"Standard: {t_standard.timeit(100).mean:.3f}s")
```

Expected: 2-4x speedup for sequences >512 tokens.

**Step 4: Test accuracy matches baseline**

```python
# Compare outputs
q, k, v = [torch.randn(1, 8, 512, 64, device='cuda', dtype=torch.float16) for _ in range(3)]

# Flash Attention
out_flash = F.scaled_dot_product_attention(q, k, v)

# Standard attention
attn_weights = torch.softmax(q @ k.transpose(-2, -1) / 8.0, dim=-1)
out_standard = attn_weights @ v

# Check difference
diff = (out_flash - out_standard).abs().max()
print(f"Max difference: {diff:.6f}")
# Should be <1e-3 for float16
```

### Workflow 2: Use flash-attn library for advanced features

For multi-query attention, sliding window, or H100 FP8.

Copy this checklist:

```
flash-attn Library Setup:
- [ ] Step 1: Install flash-attn library
- [ ] Step 2: Modify attention code
- [ ] Step 3: Enable advanced features
- [ ] Step 4: Benchmark performance
```

**Step 1: Install flash-attn library**

```bash
# NVIDIA GPUs (CUDA 12.0+)
pip install flash-attn --no-build-isolation

# Verify installation
python -c "from flash_attn import flash_attn_func; print('Success')"
```

**Step 2: Modify attention code**

```python
from flash_attn import flash_attn_func

# Input: [batch_size, seq_len, num_heads, head_dim]
# Transpose from [batch, heads, seq, dim] if needed
q = q.transpose(1, 2)  # [batch, seq, heads, dim]
k = k.transpose(1, 2)
v = v.transpose(1, 2)

out = flash_attn_func(
    q, k, v,
    dropout_p=0.1,
    causal=True,  # For autoregressive models
    window_size=(-1, -1),  # No sliding window
    softmax_scale=None  # Auto-scale
)

out = out.transpose(1, 2)  # Back to [batch, heads, seq, dim]
```

**Step 3: Enable advanced features**

Multi-query attention (shared K/V across heads):
```python
from flash_attn import flash_attn_func

# q: [batch, seq, num_q_heads, dim]
# k, v: [batch, seq, num_kv_heads, dim]  # Fewer KV heads
out = flash_attn_func(q, k, v)  # Automatically handles MQA
```

Sliding window attention (local attention):
```python
# Only attend to window of 256 tokens before/after
out = flash_attn_func(
    q, k, v,
    window_size=(256, 256),  # (left, right) window
    causal=True
)
```

**Step 4: Benchmark performance**

```python
import torch
from flash_attn import flash_attn_func
import time

q, k, v = [torch.randn(4, 4096, 32, 64, device='cuda', dtype=torch.float16) for _ in range(3)]

# Warmup
for _ in range(10):
    _ = flash_attn_func(q, k, v)

# Benchmark
torch.cuda.synchronize()
start = time.time()
for _ in range(100):
    out = flash_attn_func(q, k, v)
    torch.cuda.synchronize()
end = time.time()

print(f"Time per iteration: {(end-start)/100*1000:.2f}ms")
print(f"Memory allocated: {torch.cuda.max_memory_allocated()/1e9:.2f}GB")
```

### Workflow 3: H100 FP8 optimization (FlashAttention-3)

For maximum performance on H100 GPUs.

```
FP8 Setup:
- [ ] Step 1: Verify H100 GPU available
- [ ] Step 2: Install flash-attn with FP8 support
- [ ] Step 3: Convert inputs to FP8
- [ ] Step 4: Run with FP8 attention
```

**Step 1: Verify H100 GPU**

```bash
nvidia-smi --query-gpu=name --format=csv
# Should show "H100" or "H800"
```

**Step 2: Install flash-attn with FP8 support**

```bash
pip install flash-attn --no-build-isolation
# FP8 support included for H100
```

**Step 3: Convert inputs to FP8**

```python
import torch

q = torch.randn(2, 4096, 32, 64, device='cuda', dtype=torch.float16)
k = torch.randn(2, 4096, 32, 64, device='cuda', dtype=torch.float16)
v = torch.randn(2, 4096, 32, 64, device='cuda', dtype=torch.float16)

# Convert to float8_e4m3 (FP8)
q_fp8 = q.to(torch.float8_e4m3fn)
k_fp8 = k.to(torch.float8_e4m3fn)
v_fp8 = v.to(torch.float8_e4m3fn)
```

**Step 4: Run with FP8 attention**

```python
from flash_attn import flash_attn_func

# FlashAttention-3 automatically uses FP8 kernels on H100
out = flash_attn_func(q_fp8, k_fp8, v_fp8)
# Result: ~1.2 PFLOPS, 1.5-2x faster than FP16
```

## Advanced topics

**Integration with HuggingFace Transformers**: See [references/transformers-integration.md](references/transformers-integration.md) for enabling Flash Attention in BERT, GPT, Llama models.

**Performance benchmarks**: See [references/benchmarks.md](references/benchmarks.md) for detailed speed and memory comparisons across GPUs and sequence lengths.

**Algorithm details**: See [references/algorithm.md](references/algorithm.md) for tiling strategy, recomputation, and IO complexity analysis.

**Advanced features**: See [references/advanced-features.md](references/advanced-features.md) for rotary embeddings, ALiBi, paged KV cache, and custom attention masks.

## Hardware requirements

- **GPU**: NVIDIA Ampere+ (A100, A10, A30) or AMD MI200+
- **VRAM**: Same as standard attention (Flash Attention doesn't increase memory)
- **CUDA**: 12.0+ (11.8 minimum)
- **PyTorch**: 2.2+ for native support

**Not supported**: V100 (Volta), CPU inference

## Pitfalls

1. **ImportError: cannot import flash_attn** — CUDA toolkit not found or version mismatch. Install with `pip install flash-attn --no-build-isolation`. If that fails, install CUDA toolkit first: `conda install cuda -c nvidia` then retry the pip install.

2. **No speedup on short sequences** — Flash Attention benefits scale with sequence length. <512 tokens: minimal 10-20% speedup. 512-2K: 2-3x. >2K: 3-4x. Profile with `torch.utils.benchmark.Timer` to confirm attention is actually the bottleneck before assuming Flash Attention will help.

3. **RuntimeError: CUDA error on V100/Volta** — Flash Attention requires Ampere+ (compute capability ≥8.0). Check with `torch.cuda.get_device_capability()`. Turing (T4, compute 7.5) is supported; Volta (V100, compute 7.0) is not. Fall back to `xFormers` memory-efficient attention.

4. **Accuracy degradation with float32 inputs** — Flash Attention only supports float16 and bfloat16. Passing float32 tensors may silently fall back to math attention (no speedup) or produce incorrect results. Always cast: `q = q.to(torch.float16)` or `q = q.to(torch.bfloat16)`.

5. **pip install flash-attn hangs or takes >30 minutes** — The `--no-build-isolation` flag is required because flash-attn needs to compile CUDA kernels against the system CUDA toolkit. Without it, pip tries to build in an isolated environment without CUDA headers. Use `MAX_JOBS=4 pip install flash-attn --no-build-isolation` to limit parallel compilation if memory is tight.

6. **SDPA silently falls back to math attention** — `F.scaled_dot_product_attention` auto-selects the backend. If Flash Attention isn't available (wrong dtype, unsupported GPU, attention mask incompatible), it silently falls back to math attention with no speedup. Use `torch.backends.cuda.sdp_kernel(enable_flash=True, enable_math=False)` to force Flash Attention and get a clear error if it's unavailable.

7. **Transpose confusion between PyTorch SDPA and flash-attn library** — PyTorch SDPA expects `[batch, heads, seq, dim]` (BHSD). The flash-attn library expects `[batch, seq, heads, dim]` (BSHD). Transposing incorrectly causes silent correctness bugs. Always verify your tensor shapes: `print(q.shape)` before calling either function.

8. **Multi-GPU training with `torch.compile` and Flash Attention** — `torch.compile` may reorder operations or fuse kernels in ways that break Flash Attention's IO-aware tiling. If you see `torch._dynamo.exc.BackendCompilerFailed`, disable `torch.compile` on the attention module or use `torch.compiler.set_stance("force_eager")` during debugging.

9. **`window_size` ignored when `causal=False`** — The `window_size` parameter in `flash_attn_func` only applies when `causal=True`. Setting `window_size=(256, 256)` with `causal=False` silently ignores the window and attends to the full sequence. For bidirectional sliding window, use `causal=True` with a left-padded attention mask.

10. **FP8 conversion loses precision for small values** — `torch.float8_e4m3fn` has a limited dynamic range (max ~448). Values outside this range are clamped. For models with large attention logits, quantize with a scaling factor: `q_fp8 = (q / q.abs().max() * 448).to(torch.float8_e4m3fn)`. Apply the inverse scale after attention.

11. **flash-attn build fails with "No CUDA toolset found" on system Python** — The flash-attn build needs `nvcc` in PATH. If using a conda/virtualenv, ensure CUDA toolkit is in the environment. Verify with `which nvcc` and `nvcc --version`. On systems with multiple CUDA versions, set `CUDA_HOME=/usr/local/cuda-12` before installing.

12. **`torch.cuda.OutOfMemoryError` after enabling Flash Attention on large batches** — Flash Attention reduces peak memory but doesn't eliminate it entirely. If you were already near OOM, the memory saving might not be enough. Reduce batch size or sequence length. The memory complexity is O(N) for Flash Attention vs O(N²) for standard attention, but large models still have large activations.

## Resources

- Paper: "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness" (NeurIPS 2022)
- Paper: "FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning" (ICLR 2024)
- Blog: https://tridao.me/blog/2024/flash3/
- GitHub: https://github.com/Dao-AILab/flash-attention
- PyTorch docs: https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html