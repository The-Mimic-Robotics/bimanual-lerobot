#!/usr/bin/env python3

"""
Test script to verify MultiLeRobotDataset functionality
"""

import sys
sys.path.append('/home/odin/bimanual-lerobot/src')

from lerobot.datasets.lerobot_dataset import MultiLeRobotDataset

def test_multi_dataset():
    print("🧪 Testing MultiLeRobotDataset with your 6 datasets...")
    
    repo_ids = [
        'Batonchegg/bimanual_blue_block_handover_1',
        'Batonchegg/bimanual_blue_block_handover_2', 
        'Batonchegg/bimanual_blue_block_handover_3',
        'Batonchegg/bimanual_blue_block_handover_4',
        'Batonchegg/bimanual_blue_block_handover_5',
        'Batonchegg/bimanual_blue_block_handover_6'
    ]
    
    try:
        # Test MultiLeRobotDataset creation
        dataset = MultiLeRobotDataset(
            repo_ids=repo_ids,
            download_videos=False  # Use cached data
        )
        
        print(f"✅ SUCCESS! MultiLeRobotDataset created with {len(dataset)} total frames")
        print(f"📊 Total episodes: {dataset.num_episodes}")
        print(f"🎯 Repo mapping: {dataset.repo_id_to_index}")
        print(f"🎥 FPS: {dataset.fps}")
        
        # Test getting a sample
        sample = dataset[0]
        print(f"📦 Sample keys: {list(sample.keys())}")
        print(f"🔢 Dataset index in sample: {sample.get('dataset_index', 'Not found')}")
        
        print("\n🚀 Multi-dataset training is READY!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔍 Falling back to single dataset training...")
        return False

if __name__ == "__main__":
    test_multi_dataset()