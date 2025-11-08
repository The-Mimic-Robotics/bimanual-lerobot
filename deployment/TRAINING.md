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
Before running mkae sure to be in the src folder
```


```bash 
ls /dev/ttyACM* 
```

--robot.calibration_dir="/home/odin/bimanual-lerobot/src/calibration"

```bash
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM1 \
  --robot.right_arm_port=/dev/ttyACM2 \
  --robot.calibration_dir="/home/odin/bimanual-lerobot/src/calibration" \
  --robot.id=bimanual_so101 \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM0 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --robot.calibration_dir="/home/odin/bimanual-lerobot/src/calibration" \
  --teleop.id=bimanual_so101_leader \
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
  --robot.calibration_dir="/home/odin/bimanual-lerobot/src/calibration" \
  --robot.id=bimanual_so101 \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM0 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --robot.calibration_dir="/home/odin/bimanual-lerobot/src/calibration" \
  --teleop.id=bimanual_so101_leader \
  --display_data=true \
  --robot.cameras="{wrist_right: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist_left: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}, realsense_top: {type: intelrealsense, serial_number_or_name: \"027322073278\", width: 640, height: 480, fps: 30}}" \
  --dataset.repo_id="Batonchegg/bimanual_blue_block_handover_6" \
  --dataset.single_task="blue_block_handover" \
  --dataset.num_episodes=25 \
  --dataset.episode_time_s=45 \
  --dataset.reset_time_s=5 \
  --dataset.fps=30
```

-------
***    replay~~~    ***
```bash
python -m lerobot.replay \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM1 \
  --robot.right_arm_port=/dev/ttyACM2 \
  --robot.calibration_dir="/home/odin/bimanual-lerobot/src/calibration" \
  --robot.id=bimanual_so101 \
  --robot.cameras='{wrist_right: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist_left: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}, realsense_top: {type: intelrealsense, serial_number_or_name: "027322073278", width: 640, height: 480, fps: 30}}' \
  --dataset.repo_id="Batonchegg/bimanual_blue_block_handover_4" \
  --dataset.episode=8
```
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




# (Recommended  Approach) Running Training in the Background (Safe from SSH Disconnects)

If you are running training over SSH or want your training to continue even if you close your terminal, use `nohup` and bash variables for easy, robust runs.

**Example:**
```bash
nohup lerobot-train ... > outputs/train/myrun/training.log 2>&1 &
```
- All output (including errors) will be saved in `training.log`.
- The process will keep running even if you close your terminal or disconnect SSH.

## Using Bash Variables for Flexible Training

Set your policy type and computer name as variables at the top of your terminal session:

```bash
POLICY_TYPE=smolvla   # or act, diffusion, etc.
COMPUTER=odin         # set to your machine name (e.g., odin, orenda)
```

## Start Training with nohup (Recommended)

This command will:
- Run in the background (safe from SSH disconnects)
- Save all logs to a file in your output directory
- Use your variables for easy naming and reproducibility

#### Nyquist: -> batch_size=12, num_workers=6

```bash
COMPUTER="odin" && POLICY_TYPE="smolvla" && \
nohup lerobot-train \
  --dataset.repo_id='["Batonchegg/bimanual_blue_block_handover_1", "Batonchegg/bimanual_blue_block_handover_2", "Batonchegg/bimanual_blue_block_handover_3", "Batonchegg/bimanual_blue_block_handover_4", "Batonchegg/bimanual_blue_block_handover_5", "Batonchegg/bimanual_blue_block_handover_6"]' \
  --policy.type=$POLICY_TYPE \
  --output_dir=outputs/train/${POLICY_TYPE}_${COMPUTER}_Bimanual_Handover_MultiDatasetTraining \
  --job_name=${POLICY_TYPE}_${COMPUTER}_Bimanual_Handover_MultiDatasetTraining \
  --policy.device=cuda \
  --wandb.enable=true \
  --wandb.notes="Multi-dataset training on 6 bimanual handover datasets - $POLICY_TYPE on $COMPUTER" \
  --policy.repo_id="Mimic-Robotics/${POLICY_TYPE}_${COMPUTER}_bimanual_handover" \
  --batch_size=32 \
  --num_workers=16  > outputs/logs/${POLICY_TYPE}_${COMPUTER}_Bimanual_Handover_MultiDatasetTraining.log 2>&1 &
```
#### View logs:
  ```bash
  tail -f outputs/logs/${POLICY_TYPE}_${COMPUTER}_Bimanual_Handover_MultiDatasetTraining.log
  ```
#### Delete cmd

```bash
rm -rf outputs/train/${POLICY_TYPE}_${COMPUTER}_Bimanual_Handover_MultiDatasetTraining
```

- Change `POLICY_TYPE` and `COMPUTER` as needed for each run.
- All logs will be in the output folder for that run.
- You can safely disconnect SSH and training will continue.

## Monitoring and Stopping Training

- **Check if running:**
  ```bash
  ps aux | grep lerobot-train
  ```
- **View logs:**
  ```bash
  tail -f outputs/train/${POLICY_TYPE}_${COMPUTER}_Bimanual_Handover_MultiDatasetTraining/training.log
  ```
- **Stop training:**
  ```bash
  pkill -f lerobot-train
  ```

## What does `> ... 2>&1 &` mean?

- `>` redirects the standard output (what you normally see in the terminal) to a file (e.g., `training.log`).
- `2>&1` redirects the standard error (errors and warnings) to the same place as standard output, so both go into the log file.
- `&` at the end runs the command in the background, so you get your terminal prompt back and the process keeps running.

---

You can use this method for any policy type or machine, and it is safe and simple for all users!



# Evaluating Trained Models for Different Policies 

Once training is complete, you can evaluate your policy using the lerobot-record command with your trained policy. This will run inference and record evaluation episodes:

```bash
COMPUTER="nyquist" && POLICY_TYPE="act" && \
lerobot-record \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM1 \
  --robot.right_arm_port=/dev/ttyACM2 \
  --robot.id=bimanual_so101 \
  --robot.cameras='{"wrist_right": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "wrist_left": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}, "realsense_top": {"type": "intelrealsense", "serial_number_or_name": "027322073278", "width": 640, "height": 480, "fps": 30}}' \
  --display_data=true \
  --dataset.num_episodes=10 \
  --policy.device=cuda \
  \
  --dataset.repo_id="Mimic-Robotics/eval_${POLICY_TYPE}_${COMPUTER}_bimanual_blue_block_handover" \
  --policy.path="Mimic-Robotics/${POLICY_TYPE}_${COMPUTER}_bimanual_handover" \
  --dataset.single_task="Pick the BLUE object from one side with one arm and place it on the other side with other arm" 
```
Cmd to delete between every trial
```bash
rm -rf '/home/odin/.cache/huggingface/lerobot/Mimic-Robotics/eval_${POLICY_TYPE}_${COMPUTER}_bimanual_blue_block_handover'
```

