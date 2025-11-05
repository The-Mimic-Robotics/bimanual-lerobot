# 🧠 Understanding Batch Size & num_workers for Robot Training

## 📖 Core Concepts

### What is Batch Size?
**Batch size** determines how many data samples are processed together in a single forward/backward pass through the neural network.

```python
# Example: batch_size=16 means
batch = {
    'observation.images': torch.tensor([16, 3, 224, 224]),  # 16 images
    'action': torch.tensor([16, 7]),                        # 16 action vectors
    'robot_state': torch.tensor([16, 12])                   # 16 state vectors
}
```

### What is num_workers?
**num_workers** controls how many CPU processes load and preprocess data in parallel while your GPU trains the model.

```python
# Example: num_workers=8 means
# - 8 CPU processes load videos/images from disk
# - 8 CPU processes apply data transformations  
# - GPU gets a steady stream of preprocessed batches
```

---

## 🤖 ACT vs SmolVLA: Memory & Architecture Differences

### ACT (Action Chunking Transformer)
```yaml
Architecture: Pure transformer encoder-decoder
Memory Usage: 
  - Per sample: ~50-80MB (depends on image resolution)
  - Typical batch_size: 8-32
  - Memory efficient for action prediction
  
Strengths:
  - Lightweight for pure action sequences
  - Fast inference
  - Works well with smaller datasets
```

### SmolVLA (Small Vision-Language-Action)
```yaml
Architecture: Vision-Language model + action head
Memory Usage:
  - Per sample: ~150-300MB (vision encoder + language model)
  - Typical batch_size: 4-16  
  - Higher memory due to vision-language processing
  
Strengths:
  - Understands natural language instructions
  - Better generalization across tasks
  - More robust to environment changes
```

---

## 💾 VRAM to Batch Size Calculator

### Your Hardware: RTX 5070 (12GB VRAM)

#### ACT Policy:
```python
# Conservative estimates for bimanual robot data
Image resolution: 224x224x3 per camera
Cameras: 3 (wrist_left, wrist_right, realsense_top)

Memory per sample ≈ 60MB
Safe batch sizes:
- Single dataset: 16-24
- Multi-dataset (6): 12-16
- With gradient accumulation: 8-12
```

#### SmolVLA Policy:
```python
# Higher memory due to vision-language components
Image resolution: 224x224x3 per camera  
Vision encoder + Language model overhead

Memory per sample ≈ 200MB
Safe batch sizes:
- Single dataset: 12-20
- Multi-dataset (6): 8-16  
- With gradient accumulation: 4-8
```

---

## 🔧 num_workers Optimization Guide

### Your CPU: 32 cores (AMD Ryzen 9 9950X)

#### The Formula:
```python
# General rule for robotics data loading
num_workers = min(
    num_cpu_cores * 0.5,  # Don't use all cores
    batch_size * 2,       # 2 workers per batch item
    16                    # Diminishing returns after 16
)

# For your 32-core system:
optimal_workers = min(16, batch_size * 2)
```

#### Why This Matters:
```python
# TOO FEW workers (2-4):
"GPU waits for data" → Underutilized GPU → Slow training

# OPTIMAL workers (8-16): 
"Steady data flow" → GPU always busy → Fast training

# TOO MANY workers (20+):
"CPU overhead" → Context switching → Slower overall
```

---

## 🎯 Optimal Settings for Your System

### Multi-Dataset Training (6 datasets):
```bash
# SmolVLA - Balanced performance
--batch_size=16 \
--num_workers=16 \

# Memory constrained? Use this:
--batch_size=12 \
--num_workers=12 \
```

### Single Dataset Training:
```bash
# SmolVLA - Maximum performance  
--batch_size=20 \
--num_workers=20 \

# ACT - Can push higher
--batch_size=32 \
--num_workers=24 \
```

---

## 🧪 Memory Debugging Tips

### Check GPU Memory Usage:
```bash
# During training, monitor with:
nvidia-smi -l 1

# Look for:
Memory-Usage: 10500MiB / 12227MiB  # Good - 85% utilization
Memory-Usage: 12150MiB / 12227MiB  # Danger - reduce batch_size
```

### Out of Memory? Try This:
```python
# 1. Reduce batch size by 25%
batch_size = 16 → 12

# 2. Enable gradient checkpointing (saves memory)
--gradient_checkpointing=true

# 3. Use mixed precision training
--bf16=true
```

---

## 📊 Performance Impact Examples

### Batch Size Impact:
```yaml
batch_size=4:  "Slow but safe"  - 100% stability, 60% speed
batch_size=8:  "Balanced"       - 95% stability,  85% speed  
batch_size=16: "Optimal"        - 85% stability, 100% speed
batch_size=32: "Aggressive"     - 60% stability, 105% speed
```

### num_workers Impact:
```yaml
workers=2:  "GPU starved"    - GPU utilization: 40%
workers=8:  "Good flow"      - GPU utilization: 80% 
workers=16: "Optimal"        - GPU utilization: 95%
workers=24: "Diminishing"    - GPU utilization: 93%
```

---

## 🚀 Final Recommendations

### For Your 32-core + RTX 5070 Setup:

**Multi-dataset SmolVLA (Production):**
```bash
lerobot-train \
  --dataset.repo_id='["Batonchegg/bimanual_blue_block_handover_1", ...]' \
  --policy.type=smolvla \
  --batch_size=16 \
  --num_workers=16 \
  --bf16=true \
  --gradient_checkpointing=true
```

**Single dataset ACT (Fast experimentation):**
```bash
lerobot-train \
  --dataset.repo_id="Batonchegg/bimanual_blue_block_handover_1" \
  --policy.type=act \
  --batch_size=24 \
  --num_workers=20 \
  --bf16=true
```

**Emergency fallback (if OOM):**
```bash
# Reduce everything by 25%
--batch_size=12 \
--num_workers=12 \
--gradient_accumulation_steps=2  # Effective batch_size=24
```

Remember: **Start conservative, then increase gradually** while monitoring GPU memory! 🎯