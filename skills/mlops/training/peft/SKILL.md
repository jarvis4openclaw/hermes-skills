---
name: peft-fine-tuning
description: Parameter-efficient fine-tuning for LLMs using LoRA, QLoRA, and 25+ methods. Use when fine-tuning large models (7B-70B) with limited GPU memory, when you need to train <1% of parameters with minimal accuracy loss, or for multi-adapter serving. HuggingFace's official library integrated with transformers ecosystem.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [peft>=0.13.0, transformers>=4.45.0, torch>=2.0.0, bitsandbytes>=0.43.0]
metadata:
  hermes:
    tags: [Fine-Tuning, PEFT, LoRA, QLoRA, Parameter-Efficient, Adapters, Low-Rank, Memory Optimization, Multi-Adapter]
    trigger_conditions:
      - "fine-tune with LoRA"
      - "QLoRA fine-tuning"
      - "PEFT fine-tuning"
      - "parameter-efficient fine-tuning"
      - "LoRA adapter"
      - "train with LoRA"
      - "load LoRA weights"
      - "merge LoRA adapter"
      - "multi-adapter serving"
      - "IA3 fine-tuning"
      - "prefix tuning"
      - "4-bit quantization training"
      - "LoRA target modules"
---

# PEFT (Parameter-Efficient Fine-Tuning)

Fine-tune LLMs by training <1% of parameters using LoRA, QLoRA, and 25+ adapter methods.

## When to Use

- Fine-tuning 7B-70B models on consumer GPUs (RTX 4090, A100) with limited VRAM
- Training multiple task-specific adapters from one base model for multi-tenant serving
- Running QLoRA (4-bit quantization + LoRA) to fit 70B models on a single 24GB GPU
- Iterating quickly on fine-tuning experiments with 6MB adapter checkpoints instead of 16GB full models
- Using LoRA with TRL (SFTTrainer) or Axolotl for supervised fine-tuning
- Merging trained adapters into the base model for deployment
- Switching between adapters at runtime for multi-task inference
- Applying IA3 for ultra-minimal parameter training (0.01% of parameters)

## Not For

- **Training small models (<1B parameters) where full fine-tuning is feasible** → use full fine-tuning instead
- **Maximum quality with no compute budget constraints** → use full fine-tuning instead, LoRA has ~0.5-1% quality gap
- **Evaluating fine-tuned models** → use `evaluating-llms-harness` instead
- **Serving fine-tuned models at scale** → use `vllm` or `tensorrt-llm` instead
- **Training from scratch (pretraining)** → use `torchtitan` or `accelerate` instead
- **RL-based fine-tuning (RLHF/DPO/GRPO)** → use `trl-fine-tuning` or `grpo-rl-training` instead
- **Fine-tuning vision models** → use `stable-diffusion-image-generation` or `segment-anything-model` instead

## When to use PEFT

**Use PEFT/LoRA when:**
- Fine-tuning 7B-70B models on consumer GPUs (RTX 4090, A100)
- Need to train <1% parameters (6MB adapters vs 14GB full model)
- Want fast iteration with multiple task-specific adapters
- Deploying multiple fine-tuned variants from one base model

**Use QLoRA (PEFT + quantization) when:**
- Fine-tuning 70B models on single 24GB GPU
- Memory is the primary constraint
- Can accept ~5% quality trade-off vs full fine-tuning

**Use full fine-tuning instead when:**
- Training small models (<1B parameters)
- Need maximum quality and have compute budget
- Significant domain shift requires updating all weights

## Quick start

### Installation

```bash
# Basic installation
pip install peft

# With quantization support (recommended)
pip install peft bitsandbytes

# Full stack
pip install peft transformers accelerate bitsandbytes datasets
```

### LoRA fine-tuning (standard)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import get_peft_model, LoraConfig, TaskType
from datasets import load_dataset

# Load base model
model_name = "meta-llama/Llama-3.1-8B"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# LoRA configuration
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                          # Rank (8-64, higher = more capacity)
    lora_alpha=32,                 # Scaling factor (typically 2*r)
    lora_dropout=0.05,             # Dropout for regularization
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # Attention layers
    bias="none"                    # Don't train biases
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Output: trainable params: 13,631,488 || all params: 8,043,307,008 || trainable%: 0.17%

# Prepare dataset
dataset = load_dataset("databricks/databricks-dolly-15k", split="train")

def tokenize(example):
    text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
    return tokenizer(text, truncation=True, max_length=512, padding="max_length")

tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)

# Training
training_args = TrainingArguments(
    output_dir="./lora-llama",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=lambda data: {"input_ids": torch.stack([f["input_ids"] for f in data]),
                                 "attention_mask": torch.stack([f["attention_mask"] for f in data]),
                                 "labels": torch.stack([f["input_ids"] for f in data])}
)

trainer.train()

# Save adapter only (6MB vs 16GB)
model.save_pretrained("./lora-llama-adapter")
```

### QLoRA fine-tuning (memory-efficient)

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from peft import get_peft_model, LoraConfig, prepare_model_for_kbit_training

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # NormalFloat4 (best for LLMs)
    bnb_4bit_compute_dtype="bfloat16",   # Compute in bf16
    bnb_4bit_use_double_quant=True       # Nested quantization
)

# Load quantized model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-70B",
    quantization_config=bnb_config,
    device_map="auto"
)

# Prepare for training (enables gradient checkpointing)
model = prepare_model_for_kbit_training(model)

# LoRA config for QLoRA
lora_config = LoraConfig(
    r=64,                              # Higher rank for 70B
    lora_alpha=128,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
# 70B model now fits on single 24GB GPU!
```

## LoRA parameter selection

### Rank (r) - capacity vs efficiency

| Rank | Trainable Params | Memory | Quality | Use Case |
|------|-----------------|--------|---------|----------|
| 4 | ~3M | Minimal | Lower | Simple tasks, prototyping |
| **8** | ~7M | Low | Good | **Recommended starting point** |
| **16** | ~14M | Medium | Better | **General fine-tuning** |
| 32 | ~27M | Higher | High | Complex tasks |
| 64 | ~54M | High | Highest | Domain adaptation, 70B models |

### Alpha (lora_alpha) - scaling factor

```python
# Rule of thumb: alpha = 2 * rank
LoraConfig(r=16, lora_alpha=32)  # Standard
LoraConfig(r=16, lora_alpha=16)  # Conservative (lower learning rate effect)
LoraConfig(r=16, lora_alpha=64)  # Aggressive (higher learning rate effect)
```

### Target modules by architecture

```python
# Llama / Mistral / Qwen
target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# GPT-2 / GPT-Neo
target_modules = ["c_attn", "c_proj", "c_fc"]

# Falcon
target_modules = ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]

# BLOOM
target_modules = ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]

# Auto-detect all linear layers
target_modules = "all-linear"  # PEFT 0.6.0+
```

## Loading and merging adapters

### Load trained adapter

```python
from peft import PeftModel, AutoPeftModelForCausalLM
from transformers import AutoModelForCausalLM

# Option 1: Load with PeftModel
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B")
model = PeftModel.from_pretrained(base_model, "./lora-llama-adapter")

# Option 2: Load directly (recommended)
model = AutoPeftModelForCausalLM.from_pretrained(
    "./lora-llama-adapter",
    device_map="auto"
)
```

### Merge adapter into base model

```python
# Merge for deployment (no adapter overhead)
merged_model = model.merge_and_unload()

# Save merged model
merged_model.save_pretrained("./llama-merged")
tokenizer.save_pretrained("./llama-merged")

# Push to Hub
merged_model.push_to_hub("username/llama-finetuned")
```

### Multi-adapter serving

```python
from peft import PeftModel

# Load base with first adapter
model = AutoPeftModelForCausalLM.from_pretrained("./adapter-task1")

# Load additional adapters
model.load_adapter("./adapter-task2", adapter_name="task2")
model.load_adapter("./adapter-task3", adapter_name="task3")

# Switch between adapters at runtime
model.set_adapter("task1")  # Use task1 adapter
output1 = model.generate(**inputs)

model.set_adapter("task2")  # Switch to task2
output2 = model.generate(**inputs)

# Disable adapters (use base model)
with model.disable_adapter():
    base_output = model.generate(**inputs)
```

## PEFT methods comparison

| Method | Trainable % | Memory | Speed | Best For |
|--------|------------|--------|-------|----------|
| **LoRA** | 0.1-1% | Low | Fast | General fine-tuning |
| **QLoRA** | 0.1-1% | Very Low | Medium | Memory-constrained |
| AdaLoRA | 0.1-1% | Low | Medium | Automatic rank selection |
| IA3 | 0.01% | Minimal | Fastest | Few-shot adaptation |
| Prefix Tuning | 0.1% | Low | Medium | Generation control |
| Prompt Tuning | 0.001% | Minimal | Fast | Simple task adaptation |
| P-Tuning v2 | 0.1% | Low | Medium | NLU tasks |

### IA3 (minimal parameters)

```python
from peft import IA3Config

ia3_config = IA3Config(
    target_modules=["q_proj", "v_proj", "k_proj", "down_proj"],
    feedforward_modules=["down_proj"]
)
model = get_peft_model(model, ia3_config)
# Trains only 0.01% of parameters!
```

### Prefix Tuning

```python
from peft import PrefixTuningConfig

prefix_config = PrefixTuningConfig(
    task_type="CAUSAL_LM",
    num_virtual_tokens=20,      # Prepended tokens
    prefix_projection=True       # Use MLP projection
)
model = get_peft_model(model, prefix_config)
```

## Integration patterns

### With TRL (SFTTrainer)

```python
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig

lora_config = LoraConfig(r=16, lora_alpha=32, target_modules="all-linear")

trainer = SFTTrainer(
    model=model,
    args=SFTConfig(output_dir="./output", max_seq_length=512),
    train_dataset=dataset,
    peft_config=lora_config,  # Pass LoRA config directly
)
trainer.train()
```

### With Axolotl (YAML config)

```yaml
# axolotl config.yaml
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - v_proj
  - k_proj
  - o_proj
lora_target_linear: true  # Target all linear layers
```

### With vLLM (inference)

```python
from vllm import LLM
from vllm.lora.request import LoRARequest

# Load base model with LoRA support
llm = LLM(model="meta-llama/Llama-3.1-8B", enable_lora=True)

# Serve with adapter
outputs = llm.generate(
    prompts,
    lora_request=LoRARequest("adapter1", 1, "./lora-adapter")
)
```

## Performance benchmarks

### Memory usage (Llama 3.1 8B)

| Method | GPU Memory | Trainable Params |
|--------|-----------|------------------|
| Full fine-tuning | 60+ GB | 8B (100%) |
| LoRA r=16 | 18 GB | 14M (0.17%) |
| QLoRA r=16 | 6 GB | 14M (0.17%) |
| IA3 | 16 GB | 800K (0.01%) |

### Training speed (A100 80GB)

| Method | Tokens/sec | vs Full FT |
|--------|-----------|------------|
| Full FT | 2,500 | 1x |
| LoRA | 3,200 | 1.3x |
| QLoRA | 2,100 | 0.84x |

### Quality (MMLU benchmark)

| Model | Full FT | LoRA | QLoRA |
|-------|---------|------|-------|
| Llama 2-7B | 45.3 | 44.8 | 44.1 |
| Llama 2-13B | 54.8 | 54.2 | 53.5 |

## Pitfalls

1. **bitsandbytes CUDA setup fails** — QLoRA requires `bitsandbytes` compiled for your CUDA version. On CUDA 12.x, use `pip install bitsandbytes>=0.43.0`. If you get `CUDA_SETUP: CUDA version mismatch`, install the prebuilt wheel: `pip install bitsandbytes --prefer-binary`. Verify with `python -c "import bitsandbytes; print(bitsandbytes.__version__)"`.

2. **`target_modules` doesn't match model architecture** — Using `["q_proj", "v_proj"]` on a model that uses `["c_attn"]` results in zero trainable parameters. Always check the model's module names: `print([n for n, _ in model.named_modules() if "proj" in n or "attn" in n or "fc" in n])`. Use `"all-linear"` in PEFT 0.6.0+ as a safe default.

3. **`prepare_model_for_kbit_training` not called before QLoRA** — Skipping this step causes `RuntimeError: element 0 of tensors does not require grad`. Always call `model = prepare_model_for_kbit_training(model)` before `get_peft_model()` when using 4-bit quantization.

4. **Merged model size is full model size** — `merge_and_unload()` produces a full-precision model, not just the adapter. A LoRA adapter is 6MB; the merged model is 16GB. Only merge when deploying to production. For development, save and load adapters separately.

5. **`pad_token` not set causes training crash** — If `tokenizer.pad_token` is None, the Trainer fails silently with NaN losses. Always set it: `tokenizer.pad_token = tokenizer.eos_token`. For models without an eos_token, use `tokenizer.add_special_tokens({'pad_token': '[PAD]'})`.

6. **Gradient checkpointing not enabled for large models** — Without `model.gradient_checkpointing_enable()`, a 13B model with LoRA r=16 may still OOM on 24GB. Enable it after `get_peft_model()`: `model.gradient_checkpointing_enable()`. Reduces memory by ~30% at the cost of ~20% slower training.

7. **`lora_alpha` misunderstood as learning rate** — `lora_alpha` is a scaling factor, not a learning rate. The effective scaling is `alpha / r`. `alpha=32, r=16` = scaling factor 2.0. `alpha=16, r=16` = scaling factor 1.0 (conservative). The actual learning rate is set via `TrainingArguments(learning_rate=2e-4)`.

8. **Adapter not found when loading from different path** — `PeftModel.from_pretrained()` expects `adapter_config.json` and `adapter_model.safetensors` in the directory. If you see `OSError: Can't load adapter_model`, check that the directory contains both files. Use `model.save_pretrained("./path")` not `torch.save()`.

9. **Multi-adapter conflicts with same target modules** — Loading two adapters with different ranks but same target modules causes `ValueError: adapter already exists`. Give each adapter a unique name: `model.load_adapter("./path", adapter_name="unique_name")`. Use `model.set_adapter("unique_name")` to switch.

10. **QLoRA with `load_in_4bit=True` but wrong compute dtype** — Using `bnb_4bit_compute_dtype=torch.float16` on bf16-capable GPUs (A100, H100) wastes precision. Use `bnb_4bit_compute_dtype=torch.bfloat16` for Ampere+ GPUs. For older GPUs (V100, T4), float16 is correct.

11. **`save_strategy="epoch"` with large datasets loses intermediate checkpoints** — If training crashes after epoch 2 of 3, all progress is lost. Use `save_strategy="steps"` with `save_steps=500` for more granularity. LoRA adapters are only 6MB — saving frequently has negligible disk cost.

12. **Training with `fp16=True` on bf16-native GPUs** — A100/H100 GPUs train faster and more stably with bf16. Set `bf16=True` instead of `fp16=True` on Ampere+ GPUs. For older GPUs (V100), fp16 is correct. Check with `torch.cuda.is_bf16_supported()`.

## Common issues

### CUDA OOM during training

```python
# Solution 1: Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Solution 2: Reduce batch size + increase accumulation
TrainingArguments(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16
)

# Solution 3: Use QLoRA
from transformers import BitsAndBytesConfig
bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
```

### Adapter not applying

```python
# Verify adapter is active
print(model.active_adapters)  # Should show adapter name

# Check trainable parameters
model.print_trainable_parameters()

# Ensure model in training mode
model.train()
```

### Quality degradation

```python
# Increase rank
LoraConfig(r=32, lora_alpha=64)

# Target more modules
target_modules = "all-linear"

# Use more training data and epochs
TrainingArguments(num_train_epochs=5)

# Lower learning rate
TrainingArguments(learning_rate=1e-4)
```

## Best practices

1. **Start with r=8-16**, increase if quality insufficient
2. **Use alpha = 2 * rank** as starting point
3. **Target attention + MLP layers** for best quality/efficiency
4. **Enable gradient checkpointing** for memory savings
5. **Save adapters frequently** (small files, easy rollback)
6. **Evaluate on held-out data** before merging
7. **Use QLoRA for 70B+ models** on consumer hardware

## References

- **[Advanced Usage](references/advanced-usage.md)** - DoRA, LoftQ, rank stabilization, custom modules
- **[Troubleshooting](references/troubleshooting.md)** - Common errors, debugging, optimization

## Resources

- **GitHub**: https://github.com/huggingface/peft
- **Docs**: https://huggingface.co/docs/peft
- **LoRA Paper**: arXiv:2106.09685
- **QLoRA Paper**: arXiv:2305.14314
- **Models**: https://huggingface.co/models?library=peft