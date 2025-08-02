Here are the commands you need to run on your robot computer for your SO101 bimanual setup with 4 cameras:

## 1. Install Dependencies (One-time setup)
```bash
# Install LeRobot with SmolVLA dependencies
pip install -e ".[smolvla]"

# OPTION A: Login to Hugging Face Hub (replace hf_xxxxx with your actual token)
# huggingface-cli login --token hf_xxxPnWv --add-to-git-credential
# HF_USER=$(huggingface-cli whoami | head -n 1)
# echo $HF_USER

# OPTION B: Work completely offline (no HF account needed)
# Skip the login commands above and use the local dataset paths in the commands below
```

## 2. Configure and Test Hardware (Run on external computer)
```bash
# Find and list available cameras
python -m lerobot.find_cameras
# Example output:
# Camera 0: /dev/video0 (USB Camera)
# Camera 1: /dev/video1 (Webcam)
# Camera 2: /dev/video2 (External Camera)
# Camera 3: /dev/video3 (USB Camera)
# 
# Update the camera indices in steps 3, 4, and 6 based on your actual cameras

# Find and list available USB ports for robots
python -m lerobot.find_port
# Example output:
# /dev/tty.usbmodem14101
# /dev/tty.usbmodem14201
# /dev/tty.usbmodem14301
#
# Update the port names in all commands based on your actual ports

# Setup and configure motors (run this for each robot - leader and followers)
# For follower left arm:

python -m lerobot.setup_motors \
    --robot-type=so101_follower \
    --port=/dev/ttyACM2
# For follower right arm:
python -m lerobot.setup_motors \
    --robot-type=so101_follower \
    --port=/dev/tty.usbmodem58760431542

# For leader left arm: /dev/ttyACM0
python -m lerobot.setup_motors \
    --robot-type=so101_leader \
    --port=/dev/tty.usbmodem58760431551

# Set motors to position control mode (run for each robot)
# For follower left arm:  /dev/ttyACM2
python -m lerobot.set_motors \
    --robot-type=so101_follower \
    --port=/dev/tty.usbmodem58760431541 \
    --operating-mode=position

# For follower right arm:  /dev/ttyACM1
python -m lerobot.set_motors \
    --robot-type=so101_follower \
    --port=/dev/tty.usbmodem58760431542 \
    --operating-mode=position

# For leader right arm: /dev/ttyACM3
python -m lerobot.set_motors \
    --robot-type=so101_leader \
    --port=/dev/tty.usbmodem58760431551 \
    --operating-mode=position
```

## 3. Test Teleoperation
```bash
# First, test basic teleoperation to make sure everything works
# UPDATE: Based on your find_cameras output (video0 and video2), using only 2 cameras
python -m lerobot.teleoperate \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=my_leader_arm \
    --display_data=true

# Alternative: Test bimanual teleoperation directly (if available)
python -m lerobot.bi_teleoperate
```

## 4. Record Your Dataset (50 episodes of one task)
```bash
# UPDATE: Based on your find_cameras output (video0 and video2), using only 2 cameras
python -m lerobot.record \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=my_leader_arm \
    --dataset.repo_id=my_local_dataset \
    --dataset.single_task="Pick up the red cube with the left hand and place it in the bin" \
    --dataset.num_episodes=50 \
    --dataset.episode_time_s=60 \
    --dataset.reset_time_s=30 \
    --dataset.fps=30 \
    --dataset.push_to_hub=false \
    --dataset.root=./datasets/bimanual_pickplace_dataset

# Alternative: If you want to upload to HuggingFace (after successful login):
# --dataset.repo_id=${HF_USER}/bimanual_pickplace_dataset \
# --dataset.push_to_hub=true \
# Remove --dataset.root line
```

## 5. Train SmolVLA on Your Dataset
```bash
# OPTION A: Using local dataset + pretrained SmolVLA (recommended)
python -m lerobot.scripts.train \
    --policy.type=smolvla \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=my_local_dataset \
    --dataset.root=./datasets/bimanual_pickplace_dataset \
    --batch_size=64 \
    --steps=20000 \
    --output_dir=outputs/train/my_bimanual_smolvla \
    --job_name=bimanual_smolvla_training \
    --policy.device=cuda \
    --wandb.enable=false

# OPTION B: Using HuggingFace dataset + pretrained SmolVLA (if logged in)
# python -m lerobot.scripts.train \
#     --policy.type=smolvla \
#     --policy.path=lerobot/smolvla_base \
#     --dataset.repo_id=${HF_USER}/bimanual_pickplace_dataset \
#     --batch_size=64 \
#     --steps=20000 \
#     --output_dir=outputs/train/my_bimanual_smolvla \
#     --job_name=bimanual_smolvla_training \
#     --policy.device=cuda \
#     --wandb.enable=true
```

## 6. Test Your Trained Model
```bash
# UPDATE: Based on your find_cameras output (video0 and video2), using only 2 cameras
# Using local evaluation dataset
python -m lerobot.record \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --dataset.repo_id=my_local_eval_dataset \
    --dataset.single_task="Pick up the red cube with the left hand and place it in the bin" \
    --dataset.num_episodes=10 \
    --dataset.episode_time_s=50 \
    --policy.path=outputs/train/my_bimanual_smolvla/checkpoints/last/pretrained_model \
    --dataset.push_to_hub=false \
    --dataset.root=./datasets/bimanual_eval_dataset
```

## Important Notes:

**Before running**, make sure to:
1. **Check your USB ports** - Update the port names (`/dev/tty.usbmodem...`) to match your actual connected devices
2. **Check camera indices** - Update camera `index_or_path` values (0, 1, 2, 3) to match your actual camera setup
3. **Customize the task description** - Change `"Pick up the red cube with the left hand and place it in the bin"` to match your actual task

**During hardware configuration (step 2)**:
- Run `find_cameras` and `find_port` first to identify your actual device indices and ports
- Update all the port names in subsequent commands based on what you find
- The motor setup is crucial - make sure all motors are properly configured before teleoperation
- If motors don't respond, try power cycling the robots and running setup commands again

**During teleoperation setup (step 3)**:
- Make sure all USB devices are connected and recognized
- The `--display_data=true` flag will show camera feeds and robot state for debugging
- Test smooth control of both arms using the leader arm
- Verify all 4 camera feeds are working properly

**During recording (step 4)**:
- Use the leader arm to teleoperate the follower robot
- Perform the task described in `single_task` for each episode
- Between episodes, rearrange objects to create variations
- Use keyboard controls: → (next episode), ← (re-record), ESC (stop)

The workflow is: Record → Train → Test!