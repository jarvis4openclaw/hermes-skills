---
name: fine-tuning-with-trl
description: Fine-tune LLMs using reinforcement learning with TRL - SFT for instruction tuning, DPO for preference alignment, PPO/GRPO for reward optimization, and reward model training. Use when need RLHF, align model with preferences, or train from human feedback. Works with HuggingFace Transformers.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [trl, transformers, datasets, peft, accelerate, torch]
metadata:
  hermes:
    tags: [Post-Training, TRL, Reinforcement Learning, Fine-Tuning, SFT, DPO, PPO, GRPO, RLHF, Preference Alignment, HuggingFace]
    trigger_conditions:
      - "fine tune llm with rlhf"
      - "train model with human feedback"
      - "preference alignment dpo"
      - "reinforcement learning from human feedback"
      - "sft instruction tuning"
      - "dpo training"
      - "ppo training"
      - "grpo training"
      - "reward model training"
      - "trl library"
      - "align model preferences"
      - "post training llm"
      - "human feedback training"

---

# TRL - Transformer Reinforcement Learning

## Quick start

TRL provides post-training methods for aligning language models with human preferences.

**Installation**:
```bash
pip install trl transformers datasets peft accelerate
```

**Supervised Fine-Tuning** (instruction tuning):
```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    train_dataset=dataset,  # Prompt-completion pairs
)
trainer.train()
```

**DPO** (align with preferences):
```python
from trl import DPOTrainer, DPOConfig

config = DPOConfig(output_dir="model-dpo", beta=0.1)
trainer = DPOTrainer(
    model=model,
    args=config,
    train_dataset=preference_dataset,  # chosen/rejected pairs
    processing_class=tokenizer
)
trainer.train()
```

## Common workflows

### Workflow 1: Full RLHF pipeline (SFT → Reward Model → PPO)

Complete pipeline from base model to human-aligned model.

Copy this checklist:

```
RLHF Training:
- [ ] Step 1: Supervised fine-tuning (SFT)
- [ ] Step 2: Train reward model
- [ ] Step 3: PPO reinforcement learning
- [ ] Step 4: Evaluate aligned model
```

**Step 1: Supervised fine-tuning**

Train base model on instruction-following data:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

# Load model
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")

# Load instruction dataset
dataset = load_dataset("trl-lib/Capybara", split="train")

# Configure training
training_args = SFTConfig(
    output_dir="Qwen2.5-0.5B-SFT",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    learning_rate=2e-5,
    logging_steps=10,
    save_strategy="epoch"
)

# Train
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer
)
trainer.train()
trainer.save_model()
```

**Step 2: Train reward model**

Train model to predict human preferences:

```python
from transformers import AutoModelForSequenceClassification
from trl import RewardTrainer, RewardConfig

# Load SFT model as base
model = AutoModelForSequenceClassification.from_pretrained(
    "Qwen2.5-0.5B-SFT",
    num_labels=1  # Single reward score
)
tokenizer = AutoTokenizer.from_pretrained("Qwen2.5-0.5B-SFT")

# Load preference data (chosen/rejected pairs)
dataset = load_dataset("trl-lib/ultrafeedback_binarized", split="train")

# Configure training
training_args = RewardConfig(
    output_dir="Qwen2.5-0.5B-Reward",
    per_device_train_batch_size=2,
    num_train_epochs=1,
    learning_rate=1e-5
)

# Train reward model
trainer = RewardTrainer(
    model=model,
    args=training_args,
    processing_class=tokenizer,
    train_dataset=dataset
)
trainer.train()
trainer.save_model()
```

**Step 3: PPO reinforcement learning**

Optimize policy using reward model:

```bash
python -m trl.scripts.ppo \
    --model_name_or_path Qwen2.5-0.5B-SFT \
    --reward_model_path Qwen2.5-0.5B-Reward \
    --dataset_name trl-internal-testing/descriptiveness-sentiment-trl-style \
    --output_dir Qwen2.5-0.5B-PPO \
    --learning_rate 3e-6 \
    --per_device_train_batch_size 64 \
    --total_episodes 10000
```

**Step 4: Evaluate**

```python
from transformers import pipeline

# Load aligned model
generator = pipeline("text-generation", model="Qwen2.5-0.5B-PPO")

# Test
prompt = "Explain quantum computing to a 10-year-old"
output = generator(prompt, max_length=200)[0]["generated_text"]
print(output)
```

### Workflow 2: Simple preference alignment with DPO

Align model with preferences without reward model.

Copy this checklist:

```
DPO Training:
- [ ] Step 1: Prepare preference dataset
- [ ] Step 2: Configure DPO
- [ ] Step 3: Train with DPOTrainer
- [ ] Step 4: Evaluate alignment
```

**Step 1: Prepare preference dataset**

Dataset format:
```json
{
  "prompt": "What is the capital of France?",
  "chosen": "The capital of France is Paris.",
  "rejected": "I don't know."
}
```

Load dataset:
```python
from datasets import load_dataset

dataset = load_dataset("trl-lib/ultrafeedback_binarized", split="train")
# Or load your own
# dataset = load_dataset("json", data_files="preferences.json")
```

**Step 2: Configure DPO**

```python
from trl import DPOConfig

config = DPOConfig(
    output_dir="Qwen2.5-0.5B-DPO",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    learning_rate=5e-7,
    beta=0.1,  # KL penalty strength
    max_prompt_length=512,
    max_length=1024,
    logging_steps=10
)
```

**Step 3: Train with DPOTrainer**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOTrainer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

trainer = DPOTrainer(
    model=model,
    args=config,
    train_dataset=dataset,
    processing_class=tokenizer
)

trainer.train()
trainer.save_model()
```

**CLI alternative**:
```bash
trl dpo \
    --model_name_or_path Qwen/Qwen2.5-0.5B-Instruct \
    --dataset_name argilla/Capybara-Preferences \
    --output_dir Qwen2.5-0.5B-DPO \
    --per_device_train_batch_size 4 \
    --learning_rate 5e-7 \
    --beta 0.1
```

### Workflow 3: Memory-efficient online RL with GRPO

Train with reinforcement learning using minimal memory.

Copy this checklist:

```
GRPO Training:
- [ ] Step 1: Define reward function
- [ ] Step 2: Configure GRPO
- [ ] Step 3: Train with GRPOTrainer
```

**Step 1: Define reward function**

```python
def reward_function(completions, **kwargs):
    """
    Compute rewards for completions.

    Args:
        completions: List of generated texts

    Returns:
        List of reward scores (floats)
    """
    rewards = []
    for completion in completions:
        # Example: reward based on length and unique words
        score = len(completion.split())  # Favor longer responses
        score += len(set(completion.lower().split()))  # Reward unique words
        rewards.append(score)
    return rewards
```

Or use a reward model:
```python
from transformers import pipeline

reward_model = pipeline("text-classification", model="reward-model-path")

def reward_from_model(completions, prompts, **kwargs):
    # Combine prompt + completion
    full_texts = [p + c for p, c in zip(prompts, completions)]
    # Get reward scores
    results = reward_model(full_texts)
    return [r["score"] for r in results]
```

**Step 2: Configure GRPO**

```python
from trl import GRPOConfig

config = GRPOConfig(
    output_dir="Qwen2-GRPO",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    learning_rate=1e-5,
    num_generations=4,  # Generate 4 completions per prompt
    max_new_tokens=128
)
```

**Step 3: Train with GRPOTrainer**

```python
from datasets import load_dataset
from trl import GRPOTrainer

# Load prompt-only dataset
dataset = load_dataset("trl-lib/tldr", split="train")

trainer = GRPOTrainer(
    model="Qwen/Qwen2-0.5B-Instruct",
    reward_funcs=reward_function,  # Your reward function
    args=config,
    train_dataset=dataset
)

trainer.train()
```

**CLI**:
```bash
trl grpo \
    --model_name_or_path Qwen/Qwen2-0.5B-Instruct \
    --dataset_name trl-lib/tldr \
    --output_dir Qwen2-GRPO \
    --num_generations 4
```

## When to Use

**Use this skill when:**

- Fine-tuning LLMs with instruction-following data (SFT — Supervised Fine-Tuning)
- Aligning model outputs with human preferences (DPO — Direct Preference Optimization)
- Running full RLHF pipelines (SFT → Reward Model → PPO)
- Training reward models to score generation quality
- Memory-constrained online RL (GRPO — Group Relative Policy Optimization)
- Working with preference datasets (chosen/rejected pairs)
- Training on consumer or mid-range GPUs (LoRA + gradient checkpointing)
- Post-training alignment of already instruct-tuned models

## Not For

- **Basic fine-tuning without RL or preferences** → use `huggingface-trainer` or `axolotl` skill instead
- **YAML-based training configuration** → use `axolotl` skill instead
- **Educational or minimal fine-tuning** → use `litgpt` skill instead
- **Fast LoRA-only training with memory optimization** → use `unsloth` skill instead
- **PEFT (LoRA/QLoRA) without RL** → use `peft-fine-tuning` skill instead
- **Distributed large-scale pretraining** → use `torchtitan` or `distributed-llm-pretraining` skill instead
- **Model evaluation and benchmarking** → use `lm-evaluation-harness` skill instead

## Pitfalls

1. **OOM during DPO training** — DPO stores a reference model, doubling VRAM. Reduce `per_device_train_batch_size=1` and `max_length=512`, increase `gradient_accumulation_steps=8`. Enable `model.gradient_checkpointing_enable()`.

2. **Poor alignment quality after DPO** — Tune `beta` parameter (default 0.1). Higher beta (0.5) stays closer to reference model; lower beta (0.01) is more aggressive. Start at 0.1 and search ±0.05.

3. **Reward model not learning** — Verify dataset has clear chosen/rejected pairs. Increase `num_train_epochs=3`, try `learning_rate=1e-5` to `5e-6`. Check loss is decreasing over steps.

4. **PPO training unstable** — Increase `kl_coef=0.1` (default 0.05) and reduce `cliprange=0.1` (default 0.2). Monitor KL divergence — if it spikes, training diverged.

5. **GRPO reward function returns wrong shape** — Rewards must be a list of floats, one per completion. Default `num_generations=4` means 4 completions per prompt, so return 4 scores.

6. **SFT dataset format mismatch** — SFTTrainer expects specific formats (conversational, instruction, or text). Use `dataset_text_field` for plain text, or format as `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`.

7. **DPO dataset missing required columns** — DPOTrainer needs `prompt`, `chosen`, `rejected` columns. If using UltraFeedback, use `trl-lib/ultrafeedback_binarized` (not raw ultrafeedback).

8. **SFTTrainer ignores custom tokenizer** — Pass `processing_class=tokenizer` (not `tokenizer=tokenizer`). TRL 0.12+ uses `processing_class` instead of `tokenizer` parameter.

9. **Mixed precision crashes on older GPUs** — BF16 requires Ampere+ (A100, H100, RTX 3090+). Use FP16 on older GPUs: `torch_dtype=torch.float16`. Set `bf16=False` in config.

10. **GRPO needs prompt-only dataset** — Unlike SFT/DPO, GRPO generates completions itself. Dataset should only contain prompts (no completions). Use `trl-lib/tldr` for testing.

11. **RewardTrainer requires num_labels=1** — Load `AutoModelForSequenceClassification` with `num_labels=1` for a single reward score. Using the default (2 labels) causes shape mismatch.

12. **Save/Restore: LoRA adapters not merged** — After training with LoRA, call `model.merge_and_unload()` before saving the full model. Otherwise only adapter weights are saved and the model is unusable without the base model.

## Advanced topics

**SFT training guide**: See [references/sft-training.md](references/sft-training.md) for dataset formats, chat templates, packing strategies, and multi-GPU training.

**DPO variants**: See [references/dpo-variants.md](references/dpo-variants.md) for IPO, cDPO, RPO, and other DPO loss functions with recommended hyperparameters.

**Reward modeling**: See [references/reward-modeling.md](references/reward-modeling.md) for outcome vs process rewards, Bradley-Terry loss, and reward model evaluation.

**Online RL methods**: See [references/online-rl.md](references/online-rl.md) for PPO, GRPO, RLOO, and OnlineDPO with detailed configurations.

## Hardware requirements

- **GPU**: NVIDIA (CUDA required)
- **VRAM**: Depends on model and method
  - SFT 7B: 16GB (with LoRA)
  - DPO 7B: 24GB (stores reference model)
  - PPO 7B: 40GB (policy + reward model)
  - GRPO 7B: 24GB (more memory efficient)
- **Multi-GPU**: Supported via `accelerate`
- **Mixed precision**: BF16 recommended (A100/H100)

**Memory optimization**:
- Use LoRA/QLoRA for all methods
- Enable gradient checkpointing
- Use smaller batch sizes with gradient accumulation

## Resources

- Docs: https://huggingface.co/docs/trl/
- GitHub: https://github.com/huggingface/trl
- Papers:
  - "Training language models to follow instructions with human feedback" (InstructGPT, 2022)
  - "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (DPO, 2023)
  - "Group Relative Policy Optimization" (GRPO, 2024)
- Examples: https://github.com/huggingface/trl/tree/main/examples/scripts



