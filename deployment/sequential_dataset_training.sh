#!/bin/bash

################################################################################
# Sequential Multi-Dataset Training Script for LeRobot
#
# This script trains a policy sequentially on multiple datasets, implementing
# a form of continual/incremental learning where each dataset builds upon
# the knowledge learned from previous datasets.
#
# Strategy:
# 1. Train on dataset_1 from scratch
# 2. Load checkpoint from dataset_1, continue training on dataset_2
# 3. Load checkpoint from dataset_2, continue training on dataset_3
# ... and so on
#
# Sequential Execution Guarantee:
# - The script uses `set -e` to exit immediately if any command fails
# - Each training stage checks the exit code ($?) before proceeding
# - If dataset_N fails, the script stops and does NOT continue to dataset_N+1
# - Checkpoints are verified to exist before moving to next stage
#
# This approach allows the model to:
# - Build upon previously learned behaviors
# - Potentially achieve better generalization
# - Avoid catastrophic forgetting (to some extent)
#
# Note: This is different from multi-dataset training where all datasets
# are combined and trained together.
#
# Usage:
#   cd /home/odin/bimanual-lerobot/deployment
#   ./sequential_dataset_training.sh
################################################################################

set -e  # Exit immediately if any command fails (guarantees sequential execution)
set -u  # Exit if undefined variable is used
set -o pipefail  # Exit if any command in a pipeline fails

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root (parent of deployment directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
# Set the src directory
SRC_DIR="$PROJECT_ROOT/src"

print_info() {
    echo "[INFO] $1"
}

# Verify we can access the src directory
if [ ! -d "$SRC_DIR" ]; then
    echo "[ERROR] Source directory not found: $SRC_DIR"
    exit 1
fi

print_info "Script directory: $SCRIPT_DIR"
print_info "Project root: $PROJECT_ROOT"
print_info "Source directory: $SRC_DIR"
print_info "All commands will run from: $SRC_DIR"
echo ""

# Dataset IDs to train on sequentially
DATASETS=(
    "Batonchegg/bimanual_blue_block_handover_1"
    "Batonchegg/bimanual_blue_block_handover_2"
    "Batonchegg/bimanual_blue_block_handover_3"
    "Batonchegg/bimanual_blue_block_handover_4"
    "Batonchegg/bimanual_blue_block_handover_5"
    "Batonchegg/bimanual_blue_block_handover_6"
)

# Training configuration
POLICY_TYPE="smolvla"
BASE_OUTPUT_DIR="outputs/train/smolVLA_Sequential"
HUB_REPO_ID="Mimic-Robotics/smolVLA_bimanual_handover_sequential"

# Training hyperparameters
BATCH_SIZE=32
NUM_WORKERS=16
STEPS_PER_DATASET=20000  # Train for 20K steps on each dataset (120K total)
SAVE_FREQ=5000
EVAL_FREQ=5000

# WandB configuration
WANDB_ENABLE=true
WANDB_NOTES="Sequential training on 6 bimanual handover datasets"

# Device configuration
DEVICE="cuda"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
    echo ""
}

print_info() {
    echo "[INFO] $1"
}

print_success() {
    echo "[SUCCESS] $1"
}

print_error() {
    echo "[ERROR] $1"
}

# ============================================================================
# MAIN TRAINING LOOP
# ============================================================================

print_header "Sequential Multi-Dataset Training"
print_info "Training on ${#DATASETS[@]} datasets sequentially"
print_info "Policy Type: $POLICY_TYPE"
print_info "Steps per dataset: $STEPS_PER_DATASET"
print_info "Base Output Directory: $BASE_OUTPUT_DIR"
echo ""

PREVIOUS_CHECKPOINT=""
TOTAL_STEPS=0

for i in "${!DATASETS[@]}"; do
    DATASET_NUM=$((i + 1))
    DATASET_ID="${DATASETS[$i]}"
    DATASET_NAME=$(basename "$DATASET_ID")
    
    print_header "Training on Dataset $DATASET_NUM/$${#DATASETS[@]}: $DATASET_NAME"
    
    # Create output directory for this stage
    OUTPUT_DIR="${BASE_OUTPUT_DIR}/stage_${DATASET_NUM}_${DATASET_NAME}"
    JOB_NAME="smolvla_seq_stage${DATASET_NUM}_${DATASET_NAME}"
    
    print_info "Output directory: $OUTPUT_DIR"
    print_info "Job name: $JOB_NAME"
    
    # Build training command
    TRAIN_CMD="lerobot-train"
    TRAIN_CMD="$TRAIN_CMD --dataset.repo_id='$DATASET_ID'"
    TRAIN_CMD="$TRAIN_CMD --policy.type=$POLICY_TYPE"
    TRAIN_CMD="$TRAIN_CMD --output_dir=$OUTPUT_DIR"
    TRAIN_CMD="$TRAIN_CMD --job_name=$JOB_NAME"
    TRAIN_CMD="$TRAIN_CMD --policy.device=$DEVICE"
    TRAIN_CMD="$TRAIN_CMD --batch_size=$BATCH_SIZE"
    TRAIN_CMD="$TRAIN_CMD --num_workers=$NUM_WORKERS"
    TRAIN_CMD="$TRAIN_CMD --steps=$STEPS_PER_DATASET"
    TRAIN_CMD="$TRAIN_CMD --save_freq=$SAVE_FREQ"
    TRAIN_CMD="$TRAIN_CMD --eval_freq=$EVAL_FREQ"
    TRAIN_CMD="$TRAIN_CMD --wandb.enable=$WANDB_ENABLE"
    TRAIN_CMD="$TRAIN_CMD --wandb.notes='Sequential training - Stage $DATASET_NUM: $DATASET_NAME'"
    
    # If this is not the first dataset, load from previous checkpoint
    if [ -n "$PREVIOUS_CHECKPOINT" ]; then
        print_info "Loading from previous checkpoint: $PREVIOUS_CHECKPOINT"
        TRAIN_CMD="$TRAIN_CMD --policy.path=$PREVIOUS_CHECKPOINT"
    else
        print_info "Training from scratch (first dataset)"
    fi
    
    # Add Hub configuration for final stage only
    if [ $DATASET_NUM -eq ${#DATASETS[@]} ]; then
        print_info "This is the final stage - will push to Hub"
        TRAIN_CMD="$TRAIN_CMD --policy.push_to_hub=true"
        TRAIN_CMD="$TRAIN_CMD --policy.repo_id=$HUB_REPO_ID"
    fi
    
    print_info "Running command:"
    echo "$TRAIN_CMD"
    echo ""
    
    # Change to src directory before running training command
    print_info "Changing to directory: $SRC_DIR"
    cd "$SRC_DIR" || {
        print_error "Failed to change to src directory: $SRC_DIR"
        exit 1
    }
    
    # Execute training and capture exit code
    # This BLOCKS until training completes (guarantees sequential execution)
    print_info "Starting training... (this will block until complete)"
    eval $TRAIN_CMD
    TRAIN_EXIT_CODE=$?
    
    # Check if training succeeded
    if [ $TRAIN_EXIT_CODE -eq 0 ]; then
        print_success "Successfully completed training on $DATASET_NAME"
        
        # Change back to project root to find checkpoints
        cd "$PROJECT_ROOT" || {
            print_error "Failed to change back to project root"
            exit 1
        }
        
        # Find the latest checkpoint in the output directory
        LATEST_CHECKPOINT=$(find "$OUTPUT_DIR/checkpoints" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -n 1)
        
        if [ -n "$LATEST_CHECKPOINT" ]; then
            PREVIOUS_CHECKPOINT="$LATEST_CHECKPOINT/pretrained_model"
            print_info "Latest checkpoint: $LATEST_CHECKPOINT"
            print_info "Will load from: $PREVIOUS_CHECKPOINT for next stage"
            
            # Verify checkpoint exists before continuing
            if [ ! -d "$PREVIOUS_CHECKPOINT" ]; then
                print_error "Checkpoint directory does not exist: $PREVIOUS_CHECKPOINT"
                print_error "Cannot continue to next dataset"
                exit 1
            fi
        else
            print_error "No checkpoint found in $OUTPUT_DIR/checkpoints"
            print_error "Cannot continue to next dataset"
            exit 1
        fi
        
        TOTAL_STEPS=$((TOTAL_STEPS + STEPS_PER_DATASET))
        print_info "Total training steps so far: $TOTAL_STEPS"
        print_success "✓ Stage $DATASET_NUM complete. Ready for next stage."
    else
        print_error "Training failed on $DATASET_NAME (exit code: $TRAIN_EXIT_CODE)"
        print_error "Sequential training stopped. Not proceeding to next dataset."
        exit 1
    fi
    
    echo ""
done

# Change back to project root for final summary
cd "$PROJECT_ROOT" || {
    print_error "Failed to change back to project root"
    exit 1
}

print_header "Sequential Training Complete!"
print_success "Trained on ${#DATASETS[@]} datasets"
print_success "Total training steps: $TOTAL_STEPS"
print_success "Final model saved to: $PREVIOUS_CHECKPOINT"

if [ "$WANDB_ENABLE" = "true" ]; then
    print_info "Check WandB for training metrics and comparisons"
fi

echo ""
print_info "To evaluate the final model, run:"
echo "lerobot-eval --policy.path=$PREVIOUS_CHECKPOINT"
echo "or"
echo "lerobot-eval --policy.path=$HUB_REPO_ID"
echo ""

print_header "Training Summary"
echo "Sequential training allows the model to:"
echo "  ✓ Build upon previously learned behaviors"
echo "  ✓ Incrementally adapt to new data"
echo "  ✓ Potentially achieve better generalization"
echo ""
echo "The final model has been pushed to: https://huggingface.co/$HUB_REPO_ID"
echo ""
echo "Compare this with multi-dataset training (all datasets together) to see"
echo "which approach works better for your use case!"
echo ""
