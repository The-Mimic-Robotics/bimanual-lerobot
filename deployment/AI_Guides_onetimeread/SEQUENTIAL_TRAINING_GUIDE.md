# Sequential Multi-Dataset Training Guide

## Overview

This guide explains how to train a policy sequentially on multiple datasets using **continual/incremental learning**, where each dataset builds upon the knowledge learned from previous datasets.

## Sequential vs Multi-Dataset Training

### Sequential Training (This Approach)
```
Dataset 1 → Train → Checkpoint₁
              ↓
Dataset 2 → Load Checkpoint₁ → Train → Checkpoint₂
              ↓
Dataset 3 → Load Checkpoint₂ → Train → Checkpoint₃
              ↓
            ... and so on
```

**Advantages:**
- ✅ Model builds incrementally on previously learned behaviors
- ✅ Can adapt to new data while retaining old knowledge (to some extent)
- ✅ Useful when datasets arrive over time or when you want controlled learning progression
- ✅ Can help with curriculum learning (easy → hard datasets)

**Disadvantages:**
- ❌ Risk of catastrophic forgetting (later datasets may override earlier learning)
- ❌ Training order matters - different orders may yield different results
- ❌ Takes longer (sequential, not parallel)
- ❌ May not see cross-dataset patterns as effectively

### Multi-Dataset Training (Combining All)
```
[Dataset 1 + Dataset 2 + Dataset 3 + ...] → Train → Final Model
```

**Advantages:**
- ✅ Model sees all data diversity from the start
- ✅ Better cross-dataset generalization
- ✅ No catastrophic forgetting issues
- ✅ Training order doesn't matter

**Disadvantages:**
- ❌ Requires more memory (all datasets loaded)
- ❌ May struggle if datasets are very different
- ❌ Can't leverage curriculum learning as easily

## What LeRobot Recommends

Based on the LeRobot codebase and documentation:

1. **Multi-dataset training is the primary approach** - LeRobot has built-in support for training on multiple datasets simultaneously using `MultiLeRobotDataset`

2. **Sequential training is possible** - You can use the checkpoint loading mechanism (`--policy.path`) to implement continual learning

3. **Best practices from robotics research:**
   - If your datasets are similar (same task, different variations): **Multi-dataset is typically better**
   - If you want curriculum learning (easy → complex): **Sequential can be beneficial**
   - If datasets arrive over time: **Sequential is practical**
   - If you want to prevent catastrophic forgetting: Consider using **regularization techniques** like EWC (Elastic Weight Consolidation)

## Sequential Training Script

### Script Location
```bash
deployment/sequential_dataset_training.sh
```

### Configuration

Edit the script to customize:

```bash
# Datasets to train on (in order)
DATASETS=(
    "Batonchegg/bimanual_blue_block_handover_1"
    "Batonchegg/bimanual_blue_block_handover_2"
    "Batonchegg/bimanual_blue_block_handover_3"
    "Batonchegg/bimanual_blue_block_handover_4"
    "Batonchegg/bimanual_blue_block_handover_5"
    "Batonchegg/bimanual_blue_block_handover_6"
)

# Training steps per dataset
STEPS_PER_DATASET=20000  # Adjust based on dataset size

# Other hyperparameters
BATCH_SIZE=32
NUM_WORKERS=16
```

### Usage

1. **Make the script executable:**
```bash
chmod +x deployment/sequential_dataset_training.sh
```

2. **Run the script:**
```bash
cd /home/odin/bimanual-lerobot
./deployment/sequential_dataset_training.sh
```

3. **Monitor progress:**
- Check terminal output for progress
- View WandB dashboard for metrics
- Checkpoints saved in `outputs/train/smolVLA_Sequential/stage_N_*/`

### Output Structure

```
outputs/train/smolVLA_Sequential/
├── stage_1_bimanual_blue_block_handover_1/
│   ├── checkpoints/
│   │   ├── 005000/
│   │   ├── 010000/
│   │   └── 020000/
│   │       └── pretrained_model/  ← Loaded for next stage
│   └── train_config.json
├── stage_2_bimanual_blue_block_handover_2/
│   └── checkpoints/...
├── stage_3_bimanual_blue_block_handover_3/
│   └── checkpoints/...
...
└── stage_6_bimanual_blue_block_handover_6/
    └── checkpoints/
        └── 020000/
            └── pretrained_model/  ← Final model
```

## How It Works

### Stage 1: Initial Training
```bash
lerobot-train \
  --dataset.repo_id='Batonchegg/bimanual_blue_block_handover_1' \
  --policy.type=smolvla \
  --output_dir=outputs/train/smolVLA_Sequential/stage_1_... \
  --steps=20000 \
  --batch_size=32
```

### Stage 2+: Load Previous Checkpoint
```bash
lerobot-train \
  --dataset.repo_id='Batonchegg/bimanual_blue_block_handover_2' \
  --policy.type=smolvla \
  --policy.path=outputs/.../stage_1_.../checkpoints/020000/pretrained_model \
  --output_dir=outputs/train/smolVLA_Sequential/stage_2_... \
  --steps=20000 \
  --batch_size=32
```

The `--policy.path` argument loads the model weights from the previous checkpoint, and training continues from there on the new dataset.

