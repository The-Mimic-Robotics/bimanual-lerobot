# LeRobot Multi-Dataset Training Guide

This guide provides multiple approaches to combine and train on multiple LeRobot datasets from HuggingFace.

## 🎯 Your Goal
Combine 6 bimanual handover datasets from Batonchegg organization and train a policy using the Mimic-Robotics organization.

**Source Datasets:**
- `Batonchegg/bimanual_blue_block_handover_1` through `6`

**Target:** 
- Train a policy on all combined data
- Optionally create `Mimic-Robotics/bimanual_blue_block_handover_combined`

## 🚀 Recommended Approach: MultiLeRobotDataset Training

**This is the fastest and most practical solution for training on multiple datasets.**

### Step 1: Test Dataset Loading

```bash
cd /home/odin/bimanual-lerobot/deployment
python simple_multi_dataset_training.py
```

This will:
- ✅ Test loading all 6 datasets with MultiLeRobotDataset
- 📊 Show combined statistics (total frames, episodes)
- 💾 Generate training configuration files

### Step 2: Enable MultiLeRobotDataset Support

LeRobot has MultiLeRobotDataset but it's currently disabled. Enable it:

```bash
python factory_patcher.py
# Choose option 1 to patch the factory
```

### Step 3: Train with Multiple Datasets

```bash
# Generate the training config
python factory_patcher.py
# Choose option 3 to create config

# Run training
python -m lerobot.train train_multi_dataset.yaml
```

## 📁 Alternative Approaches

### Approach 1: Create Permanent Combined Dataset

If you want a single combined dataset on your organization:

```bash
python lerobot_dataset_combiner.py
# Choose option 2 for permanent combined dataset
```

This creates `Mimic-Robotics/bimanual_blue_block_handover_combined`.

### Approach 2: Git-like Local Combination

For local-first approach with full control:

```bash
python lerobot_dataset_combiner.py
# Choose option 3 for git-like download and combine
```

## 🔧 Files Created

| File | Purpose |
|------|---------|
| `simple_multi_dataset_training.py` | Test MultiLeRobotDataset and create basic configs |
| `lerobot_dataset_combiner.py` | Comprehensive combiner with 3 approaches |
| `factory_patcher.py` | Enable MultiLeRobotDataset in LeRobot factory |
| `train_multi_dataset.yaml` | Training configuration for multiple datasets |

## 🎯 Training Configuration

The generated training config includes:

```yaml
dataset:
  repo_id: 
    - "Batonchegg/bimanual_blue_block_handover_1"
    - "Batonchegg/bimanual_blue_block_handover_2"
    # ... all 6 datasets
    
policy:
  type: "act"  # Configure based on your needs
  
batch_size: 8
steps: 100000
```

## 📊 Dataset Statistics

After running the test script, you'll see:
- **Total frames**: Sum of all dataset frames
- **Total episodes**: Sum of all episodes
- **Features**: Common features across datasets
- **Camera keys**: Available camera streams
- **Video format**: Whether datasets use videos or images

## 🔍 Troubleshooting

### Issue: "List feature type not found"
**Solution**: Use LeRobot's native MultiLeRobotDataset instead of regular HuggingFace datasets.

### Issue: "MultiLeRobotDataset isn't supported"
**Solution**: Use the factory patcher to enable it.

### Issue: Authentication problems
**Solution**: Your HF auth is already set up for Mimic-Robotics organization.

## 🎉 Success Criteria

You'll know it's working when:
1. ✅ `simple_multi_dataset_training.py` shows successful dataset loading
2. ✅ Training starts without errors
3. ✅ WandB/logs show data from all 6 source datasets
4. ✅ Model checkpoints are saved to your output directory

## 💡 Pro Tips

1. **Start with MultiLeRobotDataset**: It's the most efficient for training
2. **Monitor training**: Watch for equal representation from all datasets
3. **Backup configs**: Save your working configurations
4. **Check features**: Ensure all datasets have compatible feature spaces

## 🔄 Restore Original Setup

If you need to revert changes:

```bash
python factory_patcher.py
# Choose option 2 to restore original factory
```

---

**Next Steps:** Run `simple_multi_dataset_training.py` to get started! 🚀