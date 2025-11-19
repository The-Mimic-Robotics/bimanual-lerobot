#!/bin/bash

# BiManual Robot Calibration Script
# Usage: ./calibrate_bimanual_robot.sh

cd "$(dirname "$0")"

# Initialize conda
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    export PATH="$HOME/miniconda3/bin:$PATH"
fi

# Activate conda environment
conda activate lerobot || {
    echo "❌ Failed to activate lerobot conda environment"
    echo "Run: conda activate lerobot"
    exit 1
}

echo "🔧 Starting BiManual Robot Calibration..."
echo "Follow the on-screen instructions"
echo ""

# Check for connected devices first
echo "Checking for connected devices..."
echo "Serial devices:"
ls /dev/ttyACM* 2>/dev/null || echo "  No serial devices found!"
echo ""

python -m lerobot.scripts.calibrate_bimanual_so101 \
  --left_follower_port=/dev/ttyACM2 \
  --right_follower_port=/dev/ttyACM3 \
  --left_leader_port=/dev/ttyACM0 \
  --right_leader_port=/dev/ttyACM1
