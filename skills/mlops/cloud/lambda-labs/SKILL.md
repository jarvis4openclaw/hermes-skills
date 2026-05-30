---
name: lambda-labs-gpu-cloud
description: Reserved and on-demand GPU cloud instances for ML training and inference. Use when you need dedicated GPU instances with simple SSH access, persistent filesystems, or high-performance multi-node clusters for large-scale training.
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [lambda-cloud-client>=1.0.0]
metadata:
  hermes:
    tags: [Infrastructure, GPU Cloud, Training, Inference, Lambda Labs]
    related_skills: [modal-serverless-gpu, vllm, trl-fine-tuning, axolotl]
    trigger_conditions:
      - "Lambda Labs GPU"
      - "launch GPU instance"
      - "SSH to GPU cloud"
      - "persistent filesystem GPU"
      - "1-Click Cluster"
      - "Lambda Stack PyTorch"
      - "multi-node training"
      - "H100 cloud instance"
      - "GPU cloud pricing"
      - "distributed training cluster"
      - "Slurm cluster GPU"
      - "cloud checkpoint storage"
      - "InfiniBand GPU"

---

# Lambda Labs GPU Cloud

Comprehensive guide to running ML workloads on Lambda Labs GPU cloud with on-demand instances and 1-Click Clusters.

## When to Use

- **Dedicated GPU instances for ML training** — long-running jobs (hours to days) with full SSH access and root control
- **Multi-node distributed training** — 1-Click Clusters with 16-512 GPUs, InfiniBand, and pre-installed Slurm
- **Persistent storage across sessions** — filesystems that survive instance termination for datasets, checkpoints, and models
- **Pre-installed ML stack** — Lambda Stack with PyTorch, CUDA, cuDNN, NCCL ready out of the box
- **Cost-effective inference endpoints** — A10 or A6000 instances for serving models without serverless cold-start latency
- **Development and prototyping** — quick spin-up of GPU instances for experimentation before scaling to larger clusters

## Not For

- **Serverless, auto-scaling workloads** → use `modal-serverless-gpu` for functions that scale to zero and back
- **Real-time API serving at high throughput** → use `serving-llms-vllm` with dedicated inference infrastructure or Modal
- **Budget-conscious spot/preemptible instances** → RunPod and Vast.ai offer cheaper spot pricing
- **Multi-cloud orchestration** → use SkyPilot or Ray for abstraction across AWS, GCP, Azure, and Lambda
- **Fine-tuning with managed frameworks** → use `trl-fine-tuning` or `axolotl` for the training code itself; Lambda provides the hardware

## Quick start

### Account setup

1. Create account at https://lambda.ai
2. Add payment method
3. Generate API key from dashboard
4. Add SSH key (required before launching instances)

### Launch via console

1. Go to https://cloud.lambda.ai/instances
2. Click "Launch instance"
3. Select GPU type and region
4. Choose SSH key
5. Optionally attach filesystem
6. Launch and wait 3-15 minutes

### Connect via SSH

```bash
# Get instance IP from console
ssh ubuntu@<INSTANCE-IP>

# Or with specific key
ssh -i ~/.ssh/lambda_key ubuntu@<INSTANCE-IP>
```

## GPU instances

### Available GPUs

| GPU | VRAM | Price/GPU/hr | Best For |
|-----|------|--------------|----------|
| B200 SXM6 | 180 GB | $4.99 | Largest models, fastest training |
| H100 SXM | 80 GB | $2.99-3.29 | Large model training |
| H100 PCIe | 80 GB | $2.49 | Cost-effective H100 |
| GH200 | 96 GB | $1.49 | Single-GPU large models |
| A100 80GB | 80 GB | $1.79 | Production training |
| A100 40GB | 40 GB | $1.29 | Standard training |
| A10 | 24 GB | $0.75 | Inference, fine-tuning |
| A6000 | 48 GB | $0.80 | Good VRAM/price ratio |
| V100 | 16 GB | $0.55 | Budget training |

### Instance configurations

```
8x GPU: Best for distributed training (DDP, FSDP)
4x GPU: Large models, multi-GPU training
2x GPU: Medium workloads
1x GPU: Fine-tuning, inference, development
```

### Launch times

- Single-GPU: 3-5 minutes
- Multi-GPU: 10-15 minutes

## Lambda Stack

All instances come with Lambda Stack pre-installed:

```bash
# Included software
- Ubuntu 22.04 LTS
- NVIDIA drivers (latest)
- CUDA 12.x
- cuDNN 8.x
- NCCL (for multi-GPU)
- PyTorch (latest)
- TensorFlow (latest)
- JAX
- JupyterLab
```

### Verify installation

```bash
# Check GPU
nvidia-smi

# Check PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# Check CUDA version
nvcc --version
```

## Python API

### Installation

```bash
pip install lambda-cloud-client
```

### Authentication

```python
import os
import lambda_cloud_client

# Configure with API key
configuration = lambda_cloud_client.Configuration(
    host="https://cloud.lambdalabs.com/api/v1",
    access_token=os.environ["LAMBDA_API_KEY"]
)
```

### List available instances

```python
with lambda_cloud_client.ApiClient(configuration) as api_client:
    api = lambda_cloud_client.DefaultApi(api_client)

    # Get available instance types
    types = api.instance_types()
    for name, info in types.data.items():
        print(f"{name}: {info.instance_type.description}")
```

### Launch instance

```python
from lambda_cloud_client.models import LaunchInstanceRequest

request = LaunchInstanceRequest(
    region_name="us-west-1",
    instance_type_name="gpu_1x_h100_sxm5",
    ssh_key_names=["my-ssh-key"],
    file_system_names=["my-filesystem"],  # Optional
    name="training-job"
)

response = api.launch_instance(request)
instance_id = response.data.instance_ids[0]
print(f"Launched: {instance_id}")
```

### List running instances

```python
instances = api.list_instances()
for instance in instances.data:
    print(f"{instance.name}: {instance.ip} ({instance.status})")
```

### Terminate instance

```python
from lambda_cloud_client.models import TerminateInstanceRequest

request = TerminateInstanceRequest(
    instance_ids=[instance_id]
)
api.terminate_instance(request)
```

### SSH key management

```python
from lambda_cloud_client.models import AddSshKeyRequest

# Add SSH key
request = AddSshKeyRequest(
    name="my-key",
    public_key="ssh-rsa AAAA..."
)
api.add_ssh_key(request)

# List keys
keys = api.list_ssh_keys()

# Delete key
api.delete_ssh_key(key_id)
```

## CLI with curl

### List instance types

```bash
curl -u $LAMBDA_API_KEY: \
  https://cloud.lambdalabs.com/api/v1/instance-types | jq
```

### Launch instance

```bash
curl -u $LAMBDA_API_KEY: \
  -X POST https://cloud.lambdalabs.com/api/v1/instance-operations/launch \
  -H "Content-Type: application/json" \
  -d '{
    "region_name": "us-west-1",
    "instance_type_name": "gpu_1x_h100_sxm5",
    "ssh_key_names": ["my-key"]
  }' | jq
```

### Terminate instance

```bash
curl -u $LAMBDA_API_KEY: \
  -X POST https://cloud.lambdalabs.com/api/v1/instance-operations/terminate \
  -H "Content-Type: application/json" \
  -d '{"instance_ids": ["<INSTANCE-ID>"]}' | jq
```

## Persistent storage

### Filesystems

Filesystems persist data across instance restarts:

```bash
# Mount location
/lambda/nfs/<FILESYSTEM_NAME>

# Example: save checkpoints
python train.py --checkpoint-dir /lambda/nfs/my-storage/checkpoints
```

### Create filesystem

1. Go to Storage in Lambda console
2. Click "Create filesystem"
3. Select region (must match instance region)
4. Name and create

### Attach to instance

Filesystems must be attached at instance launch time:
- Via console: Select filesystem when launching
- Via API: Include `file_system_names` in launch request

### Best practices

```bash
# Store on filesystem (persists)
/lambda/nfs/storage/
  ├── datasets/
  ├── checkpoints/
  ├── models/
  └── outputs/

# Local SSD (faster, ephemeral)
/home/ubuntu/
  └── working/  # Temporary files
```

## SSH configuration

### Add SSH key

```bash
# Generate key locally
ssh-keygen -t ed25519 -f ~/.ssh/lambda_key

# Add public key to Lambda console
# Or via API
```

### Multiple keys

```bash
# On instance, add more keys
echo 'ssh-rsa AAAA...' >> ~/.ssh/authorized_keys
```

### Import from GitHub

```bash
# On instance
ssh-import-id gh:username
```

### SSH tunneling

```bash
# Forward Jupyter
ssh -L 8888:localhost:8888 ubuntu@<IP>

# Forward TensorBoard
ssh -L 6006:localhost:6006 ubuntu@<IP>

# Multiple ports
ssh -L 8888:localhost:8888 -L 6006:localhost:6006 ubuntu@<IP>
```

## JupyterLab

### Launch from console

1. Go to Instances page
2. Click "Launch" in Cloud IDE column
3. JupyterLab opens in browser

### Manual access

```bash
# On instance
jupyter lab --ip=0.0.0.0 --port=8888

# From local machine with tunnel
ssh -L 8888:localhost:8888 ubuntu@<IP>
# Open http://localhost:8888
```

## Training workflows

### Single-GPU training

```bash
# SSH to instance
ssh ubuntu@<IP>

# Clone repo
git clone https://github.com/user/project
cd project

# Install dependencies
pip install -r requirements.txt

# Train
python train.py --epochs 100 --checkpoint-dir /lambda/nfs/storage/checkpoints
```

### Multi-GPU training (single node)

```python
# train_ddp.py
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def main():
    dist.init_process_group("nccl")
    rank = dist.get_rank()
    device = rank % torch.cuda.device_count()

    model = MyModel().to(device)
    model = DDP(model, device_ids=[device])

    # Training loop...

if __name__ == "__main__":
    main()
```

```bash
# Launch with torchrun (8 GPUs)
torchrun --nproc_per_node=8 train_ddp.py
```

### Checkpoint to filesystem

```python
import os

checkpoint_dir = "/lambda/nfs/my-storage/checkpoints"
os.makedirs(checkpoint_dir, exist_ok=True)

# Save checkpoint
torch.save({
    'epoch': epoch,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': loss,
}, f"{checkpoint_dir}/checkpoint_{epoch}.pt")
```

## 1-Click Clusters

### Overview

High-performance Slurm clusters with:
- 16-512 NVIDIA H100 or B200 GPUs
- NVIDIA Quantum-2 400 Gb/s InfiniBand
- GPUDirect RDMA at 3200 Gb/s
- Pre-installed distributed ML stack

### Included software

- Ubuntu 22.04 LTS + Lambda Stack
- NCCL, Open MPI
- PyTorch with DDP and FSDP
- TensorFlow
- OFED drivers

### Storage

- 24 TB NVMe per compute node (ephemeral)
- Lambda filesystems for persistent data

### Multi-node training

```bash
# On Slurm cluster
srun --nodes=4 --ntasks-per-node=8 --gpus-per-node=8 \
  torchrun --nnodes=4 --nproc_per_node=8 \
  --rdzv_backend=c10d --rdzv_endpoint=$MASTER_ADDR:29500 \
  train.py
```

## Networking

### Bandwidth

- Inter-instance (same region): up to 200 Gbps
- Internet outbound: 20 Gbps max

### Firewall

- Default: Only port 22 (SSH) open
- Configure additional ports in Lambda console
- ICMP traffic allowed by default

### Private IPs

```bash
# Find private IP
ip addr show | grep 'inet '
```

## Common workflows

### Workflow 1: Fine-tuning LLM

```bash
# 1. Launch 8x H100 instance with filesystem

# 2. SSH and setup
ssh ubuntu@<IP>
pip install transformers accelerate peft

# 3. Download model to filesystem
python -c "
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-hf')
model.save_pretrained('/lambda/nfs/storage/models/llama-2-7b')
"

# 4. Fine-tune with checkpoints on filesystem
accelerate launch --num_processes 8 train.py \
  --model_path /lambda/nfs/storage/models/llama-2-7b \
  --output_dir /lambda/nfs/storage/outputs \
  --checkpoint_dir /lambda/nfs/storage/checkpoints
```

### Workflow 2: Batch inference

```bash
# 1. Launch A10 instance (cost-effective for inference)

# 2. Run inference
python inference.py \
  --model /lambda/nfs/storage/models/fine-tuned \
  --input /lambda/nfs/storage/data/inputs.jsonl \
  --output /lambda/nfs/storage/data/outputs.jsonl
```

## Cost optimization

### Choose right GPU

| Task | Recommended GPU |
|------|-----------------|
| LLM fine-tuning (7B) | A100 40GB |
| LLM fine-tuning (70B) | 8x H100 |
| Inference | A10, A6000 |
| Development | V100, A10 |
| Maximum performance | B200 |

### Reduce costs

1. **Use filesystems**: Avoid re-downloading data
2. **Checkpoint frequently**: Resume interrupted training
3. **Right-size**: Don't over-provision GPUs
4. **Terminate idle**: No auto-stop, manually terminate

### Monitor usage

- Dashboard shows real-time GPU utilization
- API for programmatic monitoring

## Pitfalls

1. **Instance won't launch in chosen region** — Lambda GPU availability varies by region. If `LaunchInstanceRequest` returns `Insufficient Capacity` or times out, try a different region (`us-west-1`, `us-east-1`, `us-south-1`) or a smaller GPU type. Don't retry the same region more than twice.

2. **SSH connection refused during boot** — Single-GPU instances take 3-5 minutes to initialize; multi-GPU instances take 10-15 minutes. If you SSH immediately after launch, you get `Connection refused`. Wait for the instance state to show `running` in the console, then try again.

3. **Data lost after termination** — Local SSD (`/home/ubuntu/`) is ephemeral. If you terminate the instance without saving to a filesystem, all data is gone. Always store checkpoints, datasets, and outputs on `/lambda/nfs/<filesystem_name>`.

4. **Filesystem not attached at launch** — Persistent filesystems must be specified in the launch request (`file_system_names`). You cannot attach a filesystem to a running instance. If you forget, terminate and relaunch with the filesystem included.

5. **Slow data transfer across regions** — Filesystems are region-bound. If your instance is in `us-west-1` but your filesystem is in `us-east-1`, data transfer is slow and may incur costs. Always match instance region to filesystem region.

6. **GPU not detected after reboot** — Rarely, NVIDIA drivers fail to load after a reboot. Run `nvidia-smi` to verify. If it fails, reboot again or file a support ticket. Do not reinstall drivers manually — Lambda Stack manages them.

7. **Forgetting to terminate idle instances** — Lambda charges by the minute with no auto-stop. An idle 8x H100 instance costs ~$24/hour. Set calendar reminders or use the API to schedule termination after job completion.

8. **Checkpointing only at the end of training** — If a long training job crashes at 99% with no intermediate checkpoints, you lose everything. Save checkpoints every epoch or every N steps to `/lambda/nfs/...` so they persist across instances.

9. **Wrong GPU for the task** — Using an 8x H100 for a 7B model fine-tuning job is overkill and expensive. Conversely, using a single V100 for a 70B model will OOM immediately. Match GPU VRAM to model size: 7B → A100 40GB, 70B → 8x H100.

10. **JupyterLab exposed without firewall rules** — By default only port 22 is open. If you launch Jupyter with `--ip=0.0.0.0`, it's unreachable externally until you add a firewall rule in the Lambda console for port 8888. Use SSH tunneling as a safer default.

11. **SSH key not added before launch** — Lambda requires an SSH key to be uploaded to your account before launching any instance. If you skip this step, the instance launches but you can't connect. Generate and upload the key first, then include it in `ssh_key_names`.

12. **Multi-node training without proper Slurm setup** — 1-Click Clusters handle Slurm, but if you're manually setting up multi-node training, you must set `MASTER_ADDR` and `MASTER_PORT` correctly, and ensure NCCL can communicate over InfiniBand. Verify with `srun --nodes=2 hostname` before launching `torchrun`.

## References

- **[Advanced Usage](references/advanced-usage.md)** - Multi-node training, API automation
- **[Troubleshooting](references/troubleshooting.md)** - Common issues and solutions

## Resources

- **Documentation**: https://docs.lambda.ai
- **Console**: https://cloud.lambda.ai
- **Pricing**: https://lambda.ai/instances
- **Support**: https://support.lambdalabs.com
- **Blog**: https://lambda.ai/blog
