#!/usr/bin/env python3

"""
Fix corrupted datasets on Mimic-Robotics by uploading local copies from ac-pate cache.

This script:
1. Loads datasets from local ac-pate cache (where they're complete)
2. Deletes the corrupted versions from Mimic-Robotics on Hugging Face
3. Uploads the good copies to Mimic-Robotics

Usage:
    python fix_corrupted_datasets.py --dry-run  # Preview what will be done
    python fix_corrupted_datasets.py            # Actually fix the datasets
"""

import sys
import os
import argparse
from pathlib import Path
import logging

sys.path.append('/home/odin/bimanual-lerobot/src')

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from huggingface_hub import HfApi
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Corrupted datasets to fix
CORRUPTED_DATASETS = [
    'bimanual_blue_block_handover_14',
    'bimanual_blue_block_handover_15',
    'bimanual_blue_block_handover_17',
]

SOURCE_ACCOUNT = 'ac-pate'  # Where the good local copies are
TARGET_ORG = 'Mimic-Robotics'  # Where to upload fixed versions


def check_local_dataset(dataset_name: str, source_account: str) -> bool:
    """Check if a dataset exists locally and is complete."""
    local_path = Path.home() / '.cache' / 'huggingface' / 'lerobot' / source_account / dataset_name
    info_json = local_path / 'meta' / 'info.json'
    
    if not local_path.exists():
        logger.error(f"❌ Local dataset not found: {local_path}")
        return False
    
    if not info_json.exists():
        logger.error(f"❌ Missing meta/info.json in: {local_path}")
        return False
    
    logger.info(f"✅ Local dataset found and complete: {local_path}")
    return True


def delete_corrupted_dataset(repo_id: str, api: HfApi, dry_run: bool = False):
    """Delete a corrupted dataset from Hugging Face."""
    logger.info(f"🗑️  Deleting corrupted dataset: {repo_id}")
    
    if dry_run:
        logger.info(f"   [DRY RUN] Would delete {repo_id}")
        return True
    
    try:
        # Delete the entire repository
        api.delete_repo(repo_id=repo_id, repo_type="dataset")
        logger.info(f"✅ Deleted corrupted dataset: {repo_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete {repo_id}: {e}")
        return False


def upload_fixed_dataset(dataset_name: str, source_account: str, target_org: str, api: HfApi, dry_run: bool = False):
    """Upload a fixed dataset from local cache to target organization."""
    source_repo_id = f"{source_account}/{dataset_name}"
    target_repo_id = f"{target_org}/{dataset_name}"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Fixing: {target_repo_id}")
    logger.info(f"Source: Local cache from {source_repo_id}")
    logger.info(f"{'='*80}")
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No actual changes will be made")
        logger.info(f"✅ Would load dataset from local cache: {source_repo_id}")
        logger.info(f"✅ Would upload to: {target_repo_id}")
        return True
    
    try:
        # Step 1: Load dataset from local ac-pate cache
        logger.info(f"📥 Loading dataset from local cache: {source_repo_id}...")
        dataset = LeRobotDataset(source_repo_id)
        logger.info(f"✅ Loaded successfully")
        logger.info(f"   - Episodes: {dataset.num_episodes}")
        logger.info(f"   - Frames: {dataset.num_frames}")
        logger.info(f"   - Local path: {dataset.root}")
        
        # Step 2: Change repo_id to target organization
        logger.info(f"📤 Uploading to {target_repo_id}...")
        dataset.repo_id = target_repo_id
        
        # Step 3: Push to target organization (this will create a new repo)
        dataset.push_to_hub(
            tags=['LeRobot', 'bimanual', 'handover', 'fixed'],
            license='apache-2.0',
            private=False
        )
        
        logger.info(f"✅ Successfully uploaded fixed dataset to {target_repo_id}")
        logger.info(f"   View at: https://huggingface.co/datasets/{target_repo_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix {dataset_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Fix corrupted datasets on Mimic-Robotics'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what will be done without making any changes'
    )
    parser.add_argument(
        '--skip-delete',
        action='store_true',
        help='Skip deletion step (useful if already deleted or want to just upload)'
    )
    
    args = parser.parse_args()
    
    logger.info("🔧 Dataset Repair Script")
    logger.info("="*80)
    
    if args.dry_run:
        logger.info("🔍 Running in DRY RUN mode - no changes will be made")
    
    # Initialize HuggingFace API
    api = HfApi()
    
    # Check all local datasets first
    logger.info("\n📋 Checking local datasets...")
    all_present = True
    for dataset_name in CORRUPTED_DATASETS:
        if not check_local_dataset(dataset_name, SOURCE_ACCOUNT):
            all_present = False
    
    if not all_present:
        logger.error("\n❌ Not all local datasets are available. Cannot proceed.")
        logger.error("Please ensure the datasets are downloaded from ac-pate first.")
        return 1
    
    logger.info("\n✅ All local datasets verified!")
    
    # Process each corrupted dataset
    total = len(CORRUPTED_DATASETS)
    successful = 0
    failed = 0
    
    for dataset_name in CORRUPTED_DATASETS:
        target_repo_id = f"{TARGET_ORG}/{dataset_name}"
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {dataset_name}")
        logger.info(f"{'='*80}")
        
        # Step 1: Delete corrupted version (unless skipped)
        if not args.skip_delete:
            if not delete_corrupted_dataset(target_repo_id, api, args.dry_run):
                logger.warning(f"⚠️  Could not delete {target_repo_id}, but continuing...")
        else:
            logger.info(f"⏭️  Skipping deletion step (--skip-delete)")
        
        # Step 2: Upload fixed version
        result = upload_fixed_dataset(dataset_name, SOURCE_ACCOUNT, TARGET_ORG, api, args.dry_run)
        if result:
            successful += 1
        else:
            failed += 1
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("📊 REPAIR SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total datasets: {total}")
    logger.info(f"✅ Successfully fixed: {successful}")
    logger.info(f"❌ Failed: {failed}")
    
    if args.dry_run:
        logger.info("\n🔍 This was a DRY RUN - run without --dry-run to actually fix the datasets")
    else:
        if successful == total:
            logger.info(f"\n🎉 All datasets fixed successfully!")
            logger.info(f"   View at: https://huggingface.co/{TARGET_ORG}")
        else:
            logger.warning(f"\n⚠️  Some datasets failed to fix. Please check the errors above.")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
