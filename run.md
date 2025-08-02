Here are the commands you need to run on your robot computer for your SO101 bimanual setup with 4 cameras:

## 1. Install Dependencies (One-time setup)
```bash
# Install LeRobot with SmolVLA dependencies
pip install -e ".[smolvla]"

# Login to Hugging Face Hub
huggingface-cli login --token ${HUGGINGFACE_TOKEN} --add-to-git-credential

# Set your username variable
HF_USER=$(huggingface-cli whoami | head -n 1)
echo $HF_USER
```

## 2. Record Your Dataset (50 episodes of one task)
```bash
python -m lerobot.record \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "left": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30}, "right": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 3, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=my_leader_arm \
    --dataset.repo_id=${HF_USER}/bimanual_pickplace_dataset \
    --dataset.single_task="Pick up the red cube with the left hand and place it in the bin" \
    --dataset.num_episodes=50 \
    --dataset.episode_time_s=60 \
    --dataset.reset_time_s=30 \
    --dataset.fps=30 \
    --dataset.push_to_hub=true
```

## 3. Train SmolVLA on Your Dataset
```bash
python -m lerobot.scripts.train \
    --policy.type=smolvla \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=${HF_USER}/bimanual_pickplace_dataset \
    --batch_size=64 \
    --steps=20000 \
    --output_dir=outputs/train/my_bimanual_smolvla \
    --job_name=bimanual_smolvla_training \
    --policy.device=cuda \
    --wandb.enable=true
```

## 4. Test Your Trained Model
```bash
python -m lerobot.record \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "left": {"type": "opencv", "index_or_path": 1, "width": 640, "height": 480, "fps": 30}, "right": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 3, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --dataset.repo_id=${HF_USER}/eval_bimanual_test \
    --dataset.single_task="Pick up the red cube with the left hand and place it in the bin" \
    --dataset.num_episodes=10 \
    --dataset.episode_time_s=50 \
    --policy.path=outputs/train/my_bimanual_smolvla/checkpoints/last/pretrained_model \
    --dataset.push_to_hub=true
```

## Important Notes:

**Before running**, make sure to:
1. **Check your USB ports** - Update the port names (`/dev/tty.usbmodem...`) to match your actual connected devices
2. **Check camera indices** - Update camera `index_or_path` values (0, 1, 2, 3) to match your actual camera setup
3. **Customize the task description** - Change `"Pick up the red cube with the left hand and place it in the bin"` to match your actual task

**During recording (step 2)**:
- Use the leader arm to teleoperate the follower robot
- Perform the task described in `single_task` for each episode
- Between episodes, rearrange objects to create variations
- Use keyboard controls: → (next episode), ← (re-record), ESC (stop)

The workflow is: Record → Train → Test!