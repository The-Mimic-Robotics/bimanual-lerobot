#!/bin/bash

# Single Dataset Training Command - OPTIMIZED FOR MAX PERFORMANCE
# Aggressive settings for 32-core CPU + RTX 5070 (12GB VRAM)
# Using ONLY valid LeRobot options

lerobot-train \
  --dataset.repo_id="Batonchegg/bimanual_blue_block_handover_1" \
  --policy.type=smolvla \
  --output_dir=outputs/train/smolVLA_Single_Test1 \
  --job_name=smolvla_single_bimanual_training \
  --policy.device=cuda \
  --wandb.enable=true \
  --policy.repo_id="Mimic-Robotics/smolVLA_bimanual_handover_single" \
  --batch_size=36 \
  --num_workers=12 
  