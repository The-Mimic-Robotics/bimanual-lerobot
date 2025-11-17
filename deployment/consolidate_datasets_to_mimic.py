#!/usr/bin/env python3

"""
Consolidate datasets from multiple Hugging Face accounts to Mimic-Robotics organization.

This script:
1. Downloads datasets from specified source accounts (Batonchegg, ac-pate)
2. Re-uploads them to the Mimic-Robotics organization
3. Preserves all existing Mimic-Robotics datasets

Usage:
    python consolidate_datasets_to_mimic.py --dry-run  # Preview what will be done
    python consolidate_datasets_to_mimic.py            # Actually perform the consolidation
"""

import sys
import os
import argparse
from pathlib import Path
import logging

sys.path.append('/home/odin/bimanual-lerobot/src')

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from huggingface_hub import HfApi, list_datasets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Source accounts to consolidate from
SOURCE_ACCOUNTS = {
    'Batonchegg': [
        'bimanual_blue_block_handover_1',
        'bimanual_blue_block_handover_2',
        'bimanual_blue_block_handover_3',
        'bimanual_blue_block_handover_4',
        'bimanual_blue_block_handover_5',
        'bimanual_blue_block_handover_6',
    ],
    'ac-pate': [
        'bimanual_blue_block_handover_7',
        'bimanual_blue_block_handover_16',
        'bimanual_blue_block_handover_18',
        'bimanual_blue_block_handover_19',
    ]
}

# Target organization
TARGET_ORG = 'Mimic-Robotics'


def check_dataset_exists(repo_id: str, api: HfApi) -> bool:
    """Check if a dataset already exists on the hub."""
    try:
        api.dataset_info(repo_id)
        return True
    except Exception:
        return False


def get_existing_mimic_datasets(api: HfApi) -> list[str]:
    """Get list of existing datasets in Mimic-Robotics organization."""
    try:
        datasets = list_datasets(author=TARGET_ORG)
        dataset_names = [ds.id.split('/')[-1] for ds in datasets]
        logger.info(f"Found {len(dataset_names)} existing datasets in {TARGET_ORG}")
        return dataset_names
    except Exception as e:
        logger.warning(f"Could not list existing datasets: {e}")
        return []


def consolidate_dataset(source_repo_id: str, target_repo_id: str, api: HfApi, dry_run: bool = False):
    """
    Download a dataset from source and upload to target organization.
    
    Args:
        source_repo_id: Source repository ID (e.g., 'Batonchegg/bimanual_blue_block_handover_1')
        target_repo_id: Target repository ID (e.g., 'Mimic-Robotics/bimanual_blue_block_handover_1')
        api: HuggingFace API instance
        dry_run: If True, only simulate the operation
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {source_repo_id} -> {target_repo_id}")
    logger.info(f"{'='*80}")
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No actual changes will be made")
    
    # Check if target already exists
    if check_dataset_exists(target_repo_id, api):
        logger.warning(f"⚠️  Target dataset {target_repo_id} already exists - SKIPPING")
        return False
    
    if dry_run:
        logger.info(f"✅ Would download {source_repo_id}")
        logger.info(f"✅ Would upload to {target_repo_id}")
        return True
    
    try:
        # Step 1: Download dataset from source
        logger.info(f"📥 Downloading {source_repo_id}...")
        dataset = LeRobotDataset(source_repo_id)
        logger.info(f"✅ Downloaded successfully")
        logger.info(f"   - Episodes: {dataset.num_episodes}")
        logger.info(f"   - Frames: {dataset.num_frames}")
        logger.info(f"   - Local path: {dataset.root}")
        
        # Step 2: Update repo_id to target organization
        logger.info(f"📤 Uploading to {target_repo_id}...")
        dataset.repo_id = target_repo_id
        
        # Step 3: Push to target organization
        dataset.push_to_hub(
            tags=['LeRobot', 'bimanual', 'handover', 'consolidated'],
            license='apache-2.0',
            private=False
        )
        
        logger.info(f"✅ Successfully consolidated {source_repo_id} to {target_repo_id}")
        logger.info(f"   View at: https://huggingface.co/datasets/{target_repo_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to consolidate {source_repo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_dataset_version_tag(repo_id: str, api: HfApi):
    """
    Fix missing version tag for a dataset by reading info.json and creating the tag.
    
    Args:
        repo_id: Repository ID to fix
        api: HuggingFace API instance
    """
    try:
        from huggingface_hub import hf_hub_download
        import json
        
        # Try to download info.json and get the codebase version
        info_path = hf_hub_download(
            repo_id=repo_id,
            filename="meta/info.json",
            repo_type="dataset"
        )
        
        with open(info_path, 'r') as f:
            info = json.load(f)
            codebase_version = info.get('codebase_version')
        
        if codebase_version:
            logger.info(f"   Creating version tag '{codebase_version}' for {repo_id}")
            try:
                api.delete_tag(repo_id, tag=codebase_version, repo_type="dataset")
            except:
                pass  # Tag might not exist
            api.create_tag(repo_id, tag=codebase_version, repo_type="dataset")
            logger.info(f"   ✅ Version tag created successfully")
            return True
    except Exception as e:
        logger.warning(f"   ⚠️ Could not fix version tag: {e}")
    return False


def backup_to_account(source_repo_id: str, target_account: str, api: HfApi, dry_run: bool = False):
    """
    Backup a dataset from Mimic-Robotics to another account (e.g., ac-pate).
    
    Args:
        source_repo_id: Source repository ID (e.g., 'Mimic-Robotics/bimanual_blue_block_handover_14')
        target_account: Target account name (e.g., 'ac-pate')
        api: HuggingFace API instance
        dry_run: If True, only simulate the operation
    """
    # Extract dataset name from source repo_id
    dataset_name = source_repo_id.split('/')[-1]
    target_repo_id = f"{target_account}/{dataset_name}"
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Backing up: {source_repo_id} -> {target_repo_id}")
    logger.info(f"{'='*80}")
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No actual changes will be made")
    
    # Check if target already exists
    if check_dataset_exists(target_repo_id, api):
        logger.info(f"⏭️  Target dataset {target_repo_id} already exists - SKIPPING")
        return False
    
    if dry_run:
        logger.info(f"✅ Would download {source_repo_id}")
        logger.info(f"✅ Would upload to {target_repo_id}")
        return True
    
    try:
        # Step 1: Download dataset from Mimic-Robotics
        logger.info(f"📥 Downloading {source_repo_id}...")
        try:
            dataset = LeRobotDataset(source_repo_id)
        except Exception as e:
            # If download fails due to missing version tag, try to fix it
            if "codebase version" in str(e).lower() or "revision" in str(e).lower():
                logger.info(f"   ⚠️ Dataset missing version tag, attempting to fix...")
                if fix_dataset_version_tag(source_repo_id, api):
                    # Retry download after fixing tag
                    logger.info(f"   🔄 Retrying download...")
                    dataset = LeRobotDataset(source_repo_id)
                else:
                    raise
            else:
                raise
        
        logger.info(f"✅ Downloaded successfully")
        logger.info(f"   - Episodes: {dataset.num_episodes}")
        logger.info(f"   - Frames: {dataset.num_frames}")
        
        # Step 2: Update repo_id to target account
        logger.info(f"📤 Uploading backup to {target_repo_id}...")
        dataset.repo_id = target_repo_id
        
        # Step 3: Push to target account
        dataset.push_to_hub(
            tags=['LeRobot', 'bimanual', 'handover', 'backup'],
            license='apache-2.0',
            private=False
        )
        
        logger.info(f"✅ Successfully backed up {source_repo_id} to {target_repo_id}")
        logger.info(f"   View at: https://huggingface.co/datasets/{target_repo_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to backup {source_repo_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_datasets_in_account(account: str, api: HfApi) -> list[str]:
    """Get list of datasets in a specific account."""
    try:
        datasets = list_datasets(author=account)
        dataset_names = [ds.id.split('/')[-1] for ds in datasets]
        logger.info(f"Found {len(dataset_names)} datasets in {account}")
        return dataset_names
    except Exception as e:
        logger.warning(f"Could not list datasets for {account}: {e}")
        return []



def main():
    parser = argparse.ArgumentParser(
        description='Consolidate datasets from multiple accounts to Mimic-Robotics'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what will be done without making any changes'
    )
    parser.add_argument(
        '--source-accounts',
        nargs='+',
        default=list(SOURCE_ACCOUNTS.keys()),
        help='Source accounts to consolidate from (default: all configured accounts)'
    )
    parser.add_argument(
        '--backup-to-ac-pate',
        action='store_true',
        help='Also backup all Mimic-Robotics datasets to ac-pate account'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Dataset Consolidation Script")
    logger.info("="*80)
    
    if args.dry_run:
        logger.info("🔍 Running in DRY RUN mode - no changes will be made")
    
    # Initialize HuggingFace API
    api = HfApi()
    
    # Get existing datasets in target organization
    existing_datasets = get_existing_mimic_datasets(api)
    logger.info(f"\nExisting datasets in {TARGET_ORG}: {len(existing_datasets)}")
    for ds in existing_datasets:
        logger.info(f"  - {ds}")
    
    # Process datasets from each source account
    total_datasets = 0
    successful = 0
    skipped = 0
    failed = 0
    
    for source_account in args.source_accounts:
        if source_account not in SOURCE_ACCOUNTS:
            logger.warning(f"⚠️  Unknown source account: {source_account}")
            continue
            
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing datasets from: {source_account}")
        logger.info(f"{'='*80}")
        
        for dataset_name in SOURCE_ACCOUNTS[source_account]:
            total_datasets += 1
            source_repo_id = f"{source_account}/{dataset_name}"
            target_repo_id = f"{TARGET_ORG}/{dataset_name}"
            
            # Check if already exists in target
            if dataset_name in existing_datasets:
                logger.info(f"⏭️  Skipping {dataset_name} - already in {TARGET_ORG}")
                skipped += 1
                continue
            
            result = consolidate_dataset(source_repo_id, target_repo_id, api, args.dry_run)
            if result:
                successful += 1
            else:
                if not check_dataset_exists(target_repo_id, api):
                    failed += 1
                else:
                    skipped += 1
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("📊 CONSOLIDATION SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total datasets processed: {total_datasets}")
    logger.info(f"✅ Successful: {successful}")
    logger.info(f"⏭️  Skipped (already exist): {skipped}")
    logger.info(f"❌ Failed: {failed}")
    
    # Backup to ac-pate if requested
    if args.backup_to_ac_pate:
        logger.info(f"\n{'='*80}")
        logger.info("🔄 BACKUP TO AC-PATE")
        logger.info(f"{'='*80}")
        
        # Get all datasets in Mimic-Robotics
        mimic_datasets = get_existing_mimic_datasets(api)
        
        # Get all datasets already in ac-pate
        ac_pate_datasets = get_datasets_in_account('ac-pate', api)
        
        backup_total = 0
        backup_successful = 0
        backup_skipped = 0
        backup_failed = 0
        
        for dataset_name in mimic_datasets:
            backup_total += 1
            source_repo_id = f"{TARGET_ORG}/{dataset_name}"
            
            # Skip if already in ac-pate
            if dataset_name in ac_pate_datasets:
                logger.info(f"⏭️  Skipping {dataset_name} - already in ac-pate")
                backup_skipped += 1
                continue
            
            result = backup_to_account(source_repo_id, 'ac-pate', api, args.dry_run)
            if result:
                backup_successful += 1
            else:
                if not check_dataset_exists(f"ac-pate/{dataset_name}", api):
                    backup_failed += 1
                else:
                    backup_skipped += 1
        
        logger.info(f"\n{'='*80}")
        logger.info("� BACKUP SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total datasets to backup: {backup_total}")
        logger.info(f"✅ Successful backups: {backup_successful}")
        logger.info(f"⏭️  Skipped (already exist): {backup_skipped}")
        logger.info(f"❌ Failed backups: {backup_failed}")
    
    if args.dry_run:
        logger.info("\n�🔍 This was a DRY RUN - run without --dry-run to actually consolidate")
    else:
        logger.info(f"\n🎉 Consolidation complete! View all datasets at:")
        logger.info(f"   https://huggingface.co/datasets?other=LeRobot&sort=trending&search=author%3A{TARGET_ORG}")
        if args.backup_to_ac_pate:
            logger.info(f"   https://huggingface.co/datasets?other=LeRobot&sort=trending&search=author%3Aac-pate")


if __name__ == "__main__":
    main()
