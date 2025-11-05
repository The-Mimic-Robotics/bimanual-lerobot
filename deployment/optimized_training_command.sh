#!/bin/bash

# Multi-Dataset Training Command for SmolVLA on Bimanual Handover Data
# Using all 6 datasets directly with MultiLeRobotDataset
# Optimized for 32-core CPU + RTX 5070 (12GB VRAM)

lerobot-train \
  --dataset.repo_id=[Batonchegg/bimanual_blue_block_handover_1,Batonchegg/bimanual_blue_block_handover_2,Batonchegg/bimanual_blue_block_handover_3,Batonchegg/bimanual_blue_block_handover_4,Batonchegg/bimanual_blue_block_handover_5,Batonchegg/bimanual_blue_block_handover_6] \
  --policy.type=smolvla \
  --output_dir=outputs/train/smolVLA_MultiDataset_Test1 \
  --job_name=smolvla_multi_bimanual_training \
  --policy.device=cuda \
  --wandb.enable=true \
  --wandb.notes="Multi-dataset training on 6 bimanual handover datasets" \
  --policy.repo_id="Mimic-Robotics/smolVLA_bimanual_handover" \
  --batch_size=32 \
  --num_workers=16
  