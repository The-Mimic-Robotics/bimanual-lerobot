#!/usr/bin/env python3
"""
Update task description in all bimanual handover datasets and push to HuggingFace.
"""

import json
import os
from pathlib import Path
from huggingface_hub import HfApi

# New task description
NEW_TASK = "Grasp the blue block from one side using one arm and transfer it to the other arm on the opposite side"
OLD_TASK = "blue_block_handover"

# Dataset IDs
DATASET_IDS = [
    1, 2, 3, 4, 5, 6, 7, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26
]

HF_ORG = "Mimic-Robotics"
CACHE_DIR = Path.home() / ".cache/huggingface/lerobot"

def update_dataset_task(dataset_num: int, dry_run: bool = False):
    """Update task description in a single dataset."""
    dataset_name = f"bimanual_blue_block_handover_{dataset_num}"
    repo_id = f"{HF_ORG}/{dataset_name}"
    
    # Local cache path
    local_path = CACHE_DIR / HF_ORG / dataset_name / "meta" / "tasks.jsonl"
    
    if not local_path.exists():
        print(f"❌ {dataset_name}: tasks.jsonl not found locally, skipping...")
        return False
    
    # Read current task
    with open(local_path, 'r') as f:
        task_data = json.loads(f.read().strip())
    
    current_task = task_data.get('task', '')
    
    if current_task == NEW_TASK:
        print(f"✓ {dataset_name}: Already has new task description")
        return True
    
    # Update task
    task_data['task'] = NEW_TASK
    
    if dry_run:
        print(f"🔍 {dataset_name}: Would update '{current_task}' -> '{NEW_TASK}'")
        return True
    
    # Write updated task locally
    with open(local_path, 'w') as f:
        json.dump(task_data, f)
    
    print(f"📝 {dataset_name}: Updated local tasks.jsonl")
    
    # Upload to HuggingFace
    try:
        api = HfApi()
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo="meta/tasks.jsonl",
            repo_id=repo_id,
            repo_type="dataset",
            commit_message=f"Update task description to: {NEW_TASK}"
        )
        print(f"✅ {dataset_name}: Uploaded to HuggingFace")
        return True
    except Exception as e:
        print(f"❌ {dataset_name}: Failed to upload - {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update task descriptions in datasets")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    args = parser.parse_args()
    
    print("=" * 80)
    print("UPDATING TASK DESCRIPTIONS IN BIMANUAL HANDOVER DATASETS")
    print("=" * 80)
    print(f"\nOld task: '{OLD_TASK}'")
    print(f"New task: '{NEW_TASK}'")
    print(f"\nMode: {'DRY RUN (no changes will be made)' if args.dry_run else 'LIVE (will update datasets)'}")
    print(f"Datasets to update: {len(DATASET_IDS)}")
    print("=" * 80)
    print()
    
    success_count = 0
    for dataset_num in DATASET_IDS:
        if update_dataset_task(dataset_num, dry_run=args.dry_run):
            success_count += 1
        print()
    
    print("=" * 80)
    print(f"SUMMARY: {success_count}/{len(DATASET_IDS)} datasets updated successfully")
    print("=" * 80)

if __name__ == "__main__":
    main()
