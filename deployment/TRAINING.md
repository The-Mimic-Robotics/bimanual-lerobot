# BiManual Training Setup User Manual
This guide explains how to correctly set up and run the data collection script for the robot.
Please follow each step in order — this ensures the cameras and motors connect properly and proper ID's are assigned to them.


# Hardware Setup

Before running any commands, you need to make sure that all USB's are connected in the following order:

# Motor control USB
1) USB for motor control must be connected in the front port of the ODIN computer.

# Wrist camras USB's (Braided)
2) Right wrist camera must be connected first at one of the top USB rows at the back of ODIN computer. 

3) Left wrist camera must be connecteed second at any blue port below the top row. 

# Realsense camera USB
4) Realsense camera USB must be conneced last at the bottom row (either BIOS USB port, or port next to it).



# Calibration Command
If you want to recalibrate the arms you can use the following command in the terminal: 

```bash
python -m lerobot.scripts.calibrate_bimanual_so101 \
  --left_follower_port=/dev/ttyACM1 \
  --right_follower_port=/dev/ttyACM2 \
  --left_leader_port=/dev/ttyACM0 \
  --right_leader_port=/dev/ttyACM3 \
  --robot_id=bimanual_so101 \
  --use_degrees \
  --calibration_dir=./calibration
```

After the calibration, calibration files will be saved in '/src/calibration' directory

# How to run teleoperation script
Use this command if you want to run teleoperation (not data recording*) with OpenCV cameras and RealSense camera support:

```bash
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM1 \
  --robot.right_arm_port=/dev/ttyACM2 \
  --robot.id=bimanual_so101 \
  --robot.calibration_dir="./calibration" \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM0 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_so101_leader \
  --teleop.calibration_dir="./calibration" \
  --display_data=true \
  --robot.cameras="{wrist_right: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist_left: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}, realsense_top: {type: intelrealsense, serial_number_or_name: \"027322073278\", width: 640, height: 480, fps: 30}}"
```



# How to run data collection script

Before collecting data we need to set the huggingface user: 

```bash
HF_USER=$(hf auth whoami | head -n 1)
echo $HF_USER
```


To perform data collection use the below command, making sure you define the task that you are recording in --dataset.single_task parameter. You can also adjust other parameters like length of the episode or number of episodes. 
After recording the episode, data will be automatically uploaded to huggingface repository of the specified user. 

```bash
python -m lerobot.record \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM1 \
  --robot.right_arm_port=/dev/ttyACM2 \
  --robot.id=bimanual_so101 \
  --robot.calibration_dir="./calibration" \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM0 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_so101_leader \
  --teleop.calibration_dir="./calibration" \
  --display_data=true \
  --robot.cameras="{wrist_right: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist_left: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}, realsense_top: {type: intelrealsense, serial_number_or_name: \"027322073278\", width: 640, height: 480, fps: 30}}" \
  --dataset.repo_id="${HF_USER}/bimanual_test_recording" \
  --dataset.single_task="Test bimanual robot recording" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=30 \
  --dataset.fps=30
```

---

# 🚀 Training Robot Policies

After collecting your bimanual manipulation dataset, you can train various policy types to control your robot autonomously. This section covers training setup, optimization, and best practices.

### Optimized Training Command

```bash
lerobot-train \
  --dataset.repo_id="Batonchegg/bimanual_training_recording1" \
  --policy.type=smolvla \
  --output_dir=outputs/train/smolVLA_Mimic_Test1 \
  --job_name=smolvla_bimanual_training \
  --policy.device=cuda \
  --wandb.enable=true \
  --policy.repo_id="Batonchegg/smolVLA" \
  --batch_size=6 \
```

### 🔧 Parameter Explanations

#### Core Parameters
- **`--dataset.repo_id`**: Your Hugging Face dataset repository
  - Format: `{username}/{dataset_name}`
  - Example: `"Batonchegg/bimanual_training_recording1"`
  
- **`--policy.type`**: Policy architecture to use
  - `smolvla`: Vision-Language-Action model (450M parameters)
  - Alternatives: `act`, `diffusion`, `tdmpc`, `vqbet`
  
- **`--output_dir`**: Where to save checkpoints and logs
  - Default: `outputs/train/{job_name}`
  - Contains: model checkpoints, training logs, configuration files

- **`--job_name`**: Identifier for this training run
  - Used in WandB dashboard and file naming
  - Keep it descriptive: `smolvla_bimanual_training`

#### GPU Optimization Parameters

- **`--batch_size=6`**: Number of samples processed simultaneously
  - **Why 6?** Optimized for RTX 3080 (10GB VRAM)
  - Calculation: `~1,222 MiB per sample × 6 = ~7,332 MiB (75% GPU utilization)`
  - **Benefits**: 3x faster training than batch_size=2
  
  **Batch Size Guidelines:**
  ```
  10GB (RTX 3080) - Recommended Batch Size 6-7
  ```


- **`--policy.use_amp=true`**: Enable Automatic Mixed Precision
  - **What it does**: Uses float16 for most operations, float32 for precision-critical parts
  - **Memory savings**: ~50% reduction in GPU memory usage
  - **Speed boost**: ~2x faster computation on modern GPUs
  - **Accuracy**: No loss in final model performance
  
  **Technical Details:**
  ```python
  # Without AMP (float32):
  450M parameters × 4 bytes = 1,800 MB
  
  # With AMP (float16):
  450M parameters × 2 bytes = 900 MB
  + gradients + optimizer states
  ≈ 4-5 GB total
  ```


