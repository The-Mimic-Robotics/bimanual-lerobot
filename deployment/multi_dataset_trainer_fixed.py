#!/usr/bin/env python3

"""
Multi-dataset training script that bypasses CLI parsing issues
Uses the working MultiLeRobotDataset directly in Python
"""

import sys
import os
sys.path.append('/home/odin/bimanual-lerobot/src')

from lerobot.configs.train import TrainPipelineConfig
from lerobot.configs.default import DatasetConfig, WandBConfig
from lerobot.configs.policies.smolvla import SmolvlaConfig
from lerobot.scripts.train import train
from pathlib import Path

def create_multi_dataset_config():
    """Create training config with multiple datasets"""
    
    # Define the datasets
    repo_ids = [
        'Batonchegg/bimanual_blue_block_handover_1',
        'Batonchegg/bimanual_blue_block_handover_2', 
        'Batonchegg/bimanual_blue_block_handover_3',
        'Batonchegg/bimanual_blue_block_handover_4',
        'Batonchegg/bimanual_blue_block_handover_5',
        'Batonchegg/bimanual_blue_block_handover_6'
    ]
    
    # Create dataset config with list of repo IDs
    dataset_config = DatasetConfig(repo_id=repo_ids)
    
    # Create policy config
    policy_config = SmolvlaConfig(
        device="cuda",
        repo_id="Mimic-Robotics/smolVLA_bimanual_handover",
        push_to_hub=True,
        use_amp=True
    )
    
    # Create wandb config
    wandb_config = WandBConfig(
        enable=True,
        notes="Multi-dataset training on 6 bimanual handover datasets via Python"
    )
    
    # Create full training config
    config = TrainPipelineConfig(
        dataset=dataset_config,
        policy=policy_config,
        wandb=wandb_config,
        output_dir=Path("outputs/train/smolVLA_MultiDataset_Python"),
        job_name="smolvla_multi_bimanual_python",
        batch_size=32,
        num_workers=16,
        seed=1000
    )
    
    print("🚀 Starting multi-dataset training with:")
    print(f"📦 Datasets: {len(repo_ids)} datasets")
    print(f"🎯 Batch size: {config.batch_size}")
    print(f"👥 Workers: {config.num_workers}")
    print(f"🔧 AMP enabled: {config.policy.use_amp}")
    print(f"📁 Output: {config.output_dir}")
    
    return config

def main():
    """Main training function"""
    print("🧠 Multi-Dataset Training Script")
    print("=" * 50)
    
    # Change to the src directory for proper imports
    os.chdir('/home/odin/bimanual-lerobot/src')
    
    try:
        # Create config with multiple datasets
        config = create_multi_dataset_config()
        
        # Start training
        print("\n🎯 Starting training...")
        train(config)
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()