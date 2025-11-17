#!/usr/bin/env python3

"""
Generate training commands with consolidated Mimic-Robotics datasets.

This script helps you generate training commands after dataset consolidation.
"""

# All consolidated datasets in Mimic-Robotics
MIMIC_ROBOTICS_DATASETS = [
    # From Batonchegg account (originally)
    'Mimic-Robotics/bimanual_blue_block_handover_1',
    'Mimic-Robotics/bimanual_blue_block_handover_2',
    'Mimic-Robotics/bimanual_blue_block_handover_3',
    'Mimic-Robotics/bimanual_blue_block_handover_4',
    'Mimic-Robotics/bimanual_blue_block_handover_5',
    'Mimic-Robotics/bimanual_blue_block_handover_6',
    
    # From ac-pate account (originally)
    'Mimic-Robotics/bimanual_blue_block_handover_7',
    'Mimic-Robotics/bimanual_blue_block_handover_16',
    'Mimic-Robotics/bimanual_blue_block_handover_18',
    'Mimic-Robotics/bimanual_blue_block_handover_19',
    
    # Already in Mimic-Robotics
    'Mimic-Robotics/bimanual_blue_block_handover_14',  # ✅ FIXED
    'Mimic-Robotics/bimanual_blue_block_handover_15',  # ✅ FIXED
    'Mimic-Robotics/bimanual_blue_block_handover_17',  # ✅ FIXED
    'Mimic-Robotics/bimanual_blue_block_handover_20',
    'Mimic-Robotics/bimanual_blue_block_handover_21',
    'Mimic-Robotics/bimanual_blue_block_handover_22',
    'Mimic-Robotics/bimanual_blue_block_handover_23',
    'Mimic-Robotics/bimanual_blue_block_handover_24',
    'Mimic-Robotics/bimanual_blue_block_handover_25',
    'Mimic-Robotics/bimanual_blue_block_handover_26',
]


def generate_cli_command(datasets: list[str], policy_type: str = "smolVLA", computer: str = "ODIN-IEEE", 
                         from_scratch: bool = True, pretrained_path: str = "lerobot/smolvla_base") -> str:
    """Generate CLI training command.
    
    Args:
        datasets: List of dataset repo IDs
        policy_type: Policy type (only used for naming and from_scratch=True)
        computer: Computer name for identification
        from_scratch: If True, use --policy.type. If False, use --policy.path for transfer learning
        pretrained_path: Path to pretrained model (only used when from_scratch=False)
    """
    datasets_str = '["' + '", "'.join(datasets) + '"]'
    
    if from_scratch:
        # Training from scratch - use --policy.type
        policy_param = f"--policy.type={policy_type}"
        training_mode = "FromScratch"
    else:
        # Transfer learning - use --policy.path
        policy_param = f"--policy.path={pretrained_path}"
        training_mode = "TransferLearning"
    
    command = f"""lerobot-train \\
  --dataset.repo_id='{datasets_str}' \\
  {policy_param} \\
  --output_dir=outputs/train/{policy_type}_{computer}_Bimanual_Handover_{training_mode} \\
  --job_name={policy_type}_{computer}_Bimanual_Handover_{training_mode} \\
  --policy.device=cuda \\
  --wandb.enable=true \\
  --wandb.notes="Multi-dataset training on {len(datasets)} bimanual handover datasets - {policy_type} on {computer} - {training_mode}" \\
  --policy.repo_id="Mimic-Robotics/{policy_type}_{computer}_bimanual_handover" \\
  --batch_size=32 \\
  --num_workers=16 \\
  --steps=20000"""
    
    return command


def generate_python_config(datasets: list[str]) -> str:
    """Generate Python configuration for multi_dataset_trainer_fixed.py"""
    config = "repo_ids = [\n"
    for ds in datasets:
        config += f"    '{ds}',\n"
    config += "]"
    return config


def main():
    print("="*80)
    print("CONSOLIDATED DATASET TRAINING COMMAND GENERATOR")
    print("="*80)
    
    print(f"\nTotal datasets available: {len(MIMIC_ROBOTICS_DATASETS)}")
    print("\nDatasets:")
    for i, ds in enumerate(MIMIC_ROBOTICS_DATASETS, 1):
        print(f"  {i}. {ds}")
    
    # Generate both FROM SCRATCH and TRANSFER LEARNING commands
    
    print("\n" + "="*80)
    print("OPTION 1: TRAINING FROM SCRATCH (--policy.type)")
    print("="*80)
    print("\nCLI COMMAND:")
    print(generate_cli_command(MIMIC_ROBOTICS_DATASETS, from_scratch=True))
    
    print("\n" + "="*80)
    print("WITH NOHUP (background training from scratch):")
    print("="*80)
    cmd_scratch = generate_cli_command(MIMIC_ROBOTICS_DATASETS, from_scratch=True)
    print("COMPUTER=\"ODIN-IEEE\" && POLICY_TYPE=\"smolVLA\" && \\")
    print("nohup " + cmd_scratch.replace('\n', ' \\\n  ').replace('smolVLA', '${POLICY_TYPE}').replace('ODIN-IEEE', '${COMPUTER}') + 
          " \\\n  > outputs/logs/${POLICY_TYPE}_${COMPUTER}_FromScratch.log 2>&1 &")
    
    print("\n" + "="*80)
    print("OPTION 2: TRANSFER LEARNING (--policy.path)")
    print("="*80)
    print("\nUsing pretrained model: lerobot/smolvla_base")
    print("\nCLI COMMAND:")
    print(generate_cli_command(MIMIC_ROBOTICS_DATASETS, from_scratch=False, pretrained_path="lerobot/smolvla_base"))
    
    print("\n" + "="*80)
    print("WITH NOHUP (background transfer learning):")
    print("="*80)
    cmd_transfer = generate_cli_command(MIMIC_ROBOTICS_DATASETS, from_scratch=False, pretrained_path="lerobot/smolvla_base")
    print("COMPUTER=\"ODIN-IEEE\" && POLICY_TYPE=\"smolVLA\" && \\")
    print("nohup " + cmd_transfer.replace('\n', ' \\\n  ').replace('smolVLA', '${POLICY_TYPE}').replace('ODIN-IEEE', '${COMPUTER}') + 
          " \\\n  > outputs/logs/${POLICY_TYPE}_${COMPUTER}_TransferLearning.log 2>&1 &")
    
    print("\n" + "="*80)
    print("AVAILABLE PRETRAINED MODELS")
    print("="*80)
    print("SmolVLA models:")
    print("  - lerobot/smolvla_base (Recommended - 450M params)")
    print("  - lerobot/smolvla_anyrobot")
    print("\nOther policy paths:")
    print("  - Mimic-Robotics/{your_trained_model}")
    print("  - {username}/{custom_model}")
    
    print("\n" + "="*80)
    print("PYTHON CONFIG (for multi_dataset_trainer_fixed.py)")
    print("="*80)
    print(generate_python_config(MIMIC_ROBOTICS_DATASETS))
    
    print("\n" + "="*80)
    print("MONITORING")
    print("="*80)
    print("# Monitor training from scratch:")
    print("tail -f outputs/logs/${POLICY_TYPE}_${COMPUTER}_FromScratch.log")
    print("\n# Monitor transfer learning:")
    print("tail -f outputs/logs/${POLICY_TYPE}_${COMPUTER}_TransferLearning.log")
    
    print("\n" + "="*80)
    print("QUICK REFERENCE")
    print("="*80)
    print("Train from scratch:      Use --policy.type=smolVLA")
    print("Transfer learning:       Use --policy.path=lerobot/smolvla_base")
    print("Custom pretrained:       Use --policy.path=Mimic-Robotics/your_model")
    print("="*80)


if __name__ == "__main__":
    main()
