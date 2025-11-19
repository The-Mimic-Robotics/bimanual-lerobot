#!/bin/bash
# Helper script to activate the lerobot conda environment
# Usage: source activate_lerobot.sh

if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    export PATH="$HOME/miniconda3/bin:$PATH"
fi

conda activate lerobot
echo "✅ Activated lerobot conda environment"
echo "Python: $(which python)"
echo "LeRobot ready!"
