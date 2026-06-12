---
name: tensorrt-llm
description: Optimizes LLM inference with NVIDIA TensorRT for maximum throughput and lowest latency. Use for production deployment on NVIDIA GPUs (A100/H100), when you need 10-100x faster inference than PyTorch, or for serving models with quantization (FP8/INT4), in-flight batching, and multi-GPU scaling.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [tensorrt-llm, torch]
metadata:
  hermes:
    tags: [Inference Serving, TensorRT-LLM, NVIDIA, Inference Optimization, High Throughput, Low Latency, Production, FP8, INT4, In-Flight Batching, Multi-GPU]
    trigger_conditions:
      - "TensorRT-LLM inference"
      - "NVIDIA TensorRT LLM serving"
      - "tensorrt LLM setup"
      - "trtllm-serve"
      - "LLM inference on H100 A100"
      - "FP8 quantized LLM inference"
      - "in-flight batching LLM"
      - "multi-GPU LLM serving TensorRT"
      - "tensor parallelism TensorRT"
      - "tensorrt llm install"
      - "maximum throughput LLM inference"
      - "TensorRT-LLM quantization"
      - "NVIDIA GPU LLM deployment"

---

# TensorRT-LLM

NVIDIA's open-source library for optimizing LLM inference with state-of-the-art performance on NVIDIA GPUs.

## When to use TensorRT-LLM

**Use TensorRT-LLM when:**
- Deploying on NVIDIA GPUs (A100, H100, GB200)
- Need maximum throughput (24,000+ tokens/sec on Llama 3)
- Require low latency for real-time applications
- Working with quantized models (FP8, INT4, FP4)
- Scaling across multiple GPUs or nodes

## Not For

- **Simple LLM API serving on any GPU** → use `serving-llms-vllm` for simpler setup with PagedAttention without TRT compilation overhead
- **AMD GPUs or non-NVIDIA hardware** → use vLLM (ROCm support) or llama.cpp instead
- **CPU or Apple Silicon deployment** → use `llama-cpp` for edge/CPU inference with GGUF format
- **Development/research workflows** → TensorRT-LLM compilation takes 10–60 min per model; use Transformers + PyTorch for fast iteration
- **GGUF quantization** → use `gguf-quantization` for llama.cpp-style quantized models; TRT-LLM uses its own quantization pipeline
- **Local dev machine inference** → designed for datacenter-class NVIDIA GPUs; use `llama-cpp` or `serving-llms-vllm` for local workstations

## Quick start

### Installation

```bash
# Docker (recommended)
docker pull nvidia/tensorrt_llm:latest

# pip install
pip install tensorrt_llm==1.2.0rc3

# Requires CUDA 13.0.0, TensorRT 10.13.2, Python 3.10-3.12
```

### Basic inference

```python
from tensorrt_llm import LLM, SamplingParams

# Initialize model
llm = LLM(model="meta-llama/Meta-Llama-3-8B")

# Configure sampling
sampling_params = SamplingParams(
    max_tokens=100,
    temperature=0.7,
    top_p=0.9
)

# Generate
prompts = ["Explain quantum computing"]
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    print(output.text)
```

### Serving with trtllm-serve

```bash
# Start server (automatic model download and compilation)
trtllm-serve meta-llama/Meta-Llama-3-8B \
    --tp_size 4 \              # Tensor parallelism (4 GPUs)
    --max_batch_size 256 \
    --max_num_tokens 4096

# Client request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3-8B",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

## Key features

### Performance optimizations
- **In-flight batching**: Dynamic batching during generation
- **Paged KV cache**: Efficient memory management
- **Flash Attention**: Optimized attention kernels
- **Quantization**: FP8, INT4, FP4 for 2-4× faster inference
- **CUDA graphs**: Reduced kernel launch overhead

### Parallelism
- **Tensor parallelism (TP)**: Split model across GPUs
- **Pipeline parallelism (PP)**: Layer-wise distribution
- **Expert parallelism**: For Mixture-of-Experts models
- **Multi-node**: Scale beyond single machine

### Advanced features
- **Speculative decoding**: Faster generation with draft models
- **LoRA serving**: Efficient multi-adapter deployment
- **Disaggregated serving**: Separate prefill and generation

## Common patterns

### Quantized model (FP8)

```python
from tensorrt_llm import LLM

# Load FP8 quantized model (2× faster, 50% memory)
llm = LLM(
    model="meta-llama/Meta-Llama-3-70B",
    dtype="fp8",
    max_num_tokens=8192
)

# Inference same as before
outputs = llm.generate(["Summarize this article..."])
```

### Multi-GPU deployment

```python
# Tensor parallelism across 8 GPUs
llm = LLM(
    model="meta-llama/Meta-Llama-3-405B",
    tensor_parallel_size=8,
    dtype="fp8"
)
```

### Batch inference

```python
# Process 100 prompts efficiently
prompts = [f"Question {i}: ..." for i in range(100)]

outputs = llm.generate(
    prompts,
    sampling_params=SamplingParams(max_tokens=200)
)

# Automatic in-flight batching for maximum throughput
```

## Performance benchmarks

**Meta Llama 3-8B** (H100 GPU):
- Throughput: 24,000 tokens/sec
- Latency: ~10ms per token
- vs PyTorch: **100× faster**

**Llama 3-70B** (8× A100 80GB):
- FP8 quantization: 2× faster than FP16
- Memory: 50% reduction with FP8

## Supported models

- **LLaMA family**: Llama 2, Llama 3, CodeLlama
- **GPT family**: GPT-2, GPT-J, GPT-NeoX
- **Qwen**: Qwen, Qwen2, QwQ
- **DeepSeek**: DeepSeek-V2, DeepSeek-V3
- **Mixtral**: Mixtral-8x7B, Mixtral-8x22B
- **Vision**: LLaVA, Phi-3-vision
- **100+ models** on HuggingFace

## References

- **[Optimization Guide](references/optimization.md)** - Quantization, batching, KV cache tuning
- **[Multi-GPU Setup](references/multi-gpu.md)** - Tensor/pipeline parallelism, multi-node
- **[Serving Guide](references/serving.md)** - Production deployment, monitoring, autoscaling

## Resources

- **Docs**: https://nvidia.github.io/TensorRT-LLM/
- **GitHub**: https://github.com/NVIDIA/TensorRT-LLM
- **Models**: https://huggingface.co/models?library=tensorrt_llm

## Pitfalls

1. **Model compilation takes 10–60 minutes** — TensorRT-LLM compiles each model into a TRT engine optimized for your specific GPU. First run is slow. Cache the engine at `~/.cache/tensorrt_llm/` and reuse across runs. Don't run `LLM(model=...)` in tight loops without caching.

2. **CUDA version mismatch crashes silently** — TRT-LLM requires CUDA 13.0.0 and TensorRT 10.13.2 (as of v1.2.0rc3). Running on CUDA 12.x gives `RuntimeError: CUDA version mismatch`. Use the Docker image (`nvidia/tensorrt_llm:latest`) to avoid dependency hell.

3. **`trtllm-serve` requires `--tp_size` to match GPU count** — If `--tp_size 4` is set but only 3 GPUs are available, the server fails with `RuntimeError: Not enough GPUs`. Always verify GPU count with `nvidia-smi` before starting. `--tp_size` must divide evenly into the number of available GPUs.

4. **FP8 quantization only works on H100 (Hopper) or newer** — Attempting FP8 on A100 (Ampere) gives `NotImplementedError: FP8 not supported on Ampere architecture`. Use INT4 for A100 instead: `dtype="int4_awq"`.

5. **`max_num_tokens` and `max_batch_size` together cap throughput** — These two limits interact: `max_num_tokens` is the total token budget per batch (prompt + output). If set too low, in-flight batching degrades to single-request processing. Start with `max_num_tokens=4096 * max_batch_size` as a baseline.

6. **LoRA adapters can't be loaded after engine compilation** — TRT-LLM compiles LoRA slots into the engine at build time. You can't load a new LoRA after the engine is compiled without recompiling. Use `--lora_dir` during engine build to enable LoRA serving.

7. **Multi-node deployment requires identical GPU topology** — TRT-LLM multi-node requires the same number of GPUs per node. Mixing 8×A100 + 4×A100 nodes fails. Use Slurm or torchrun with homogeneous GPU allocation.

8. **OpenAI-compatible API responses may differ in field names** — `trtllm-serve` returns an OpenAI-compatible `/v1/chat/completions` endpoint but some fields (e.g., `usage.prompt_tokens` vs `usage.input_tokens`) may differ from the upstream OpenAI spec. Test your client against the actual TRT-LLM endpoint before assuming compatibility.

9. **Engine cache invalidation on model update** — If you update the model weights or quantization config, the cached TRT engine is stale and will generate incorrect outputs silently. Always delete the engine cache when changing models: `rm -rf ~/.cache/tensorrt_llm/<model>/`.

10. **`LLM` Python API is experimental** — The high-level `tensorrt_llm.LLM` Python class (used in Quick Start) is experimental in v1.x. For production, use `trtllm-serve` or the C++ runtime directly. The Python API may change without warning between minor versions.

11. **Disaggregated serving requires separate prefill and generation instances** — Setting up disaggregated serving (separate prefill + decode nodes) requires NCCL/NIXL configuration and is not supported in single-node setups. Don't attempt it without reading the official disaggregated serving docs first.



