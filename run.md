# Bimanual SO101 Workflow: Calibration, Teleoperation, and Training

## 1. Calibrate Both Arms (Follower and Leader)

# Calibrate left follower arm
python -m lerobot.calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM3 \
    --robot.id=my_follower_left

# Calibrate right follower arm
python -m lerobot.calibrate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM2 \
    --robot.id=my_follower_right

# Calibrate left leader arm
python -m lerobot.calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM0 \
    --teleop.id=my_leader_left

# Calibrate right leader arm
python -m lerobot.calibrate \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM1 \
    --teleop.id=my_leader_right


## 2. Test Bimanual Teleoperation

# Use bi_teleoperate for bimanual teleop (uses both arms and both leaders)
python -m lerobot.bi_teleoperate \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/ttyACM2 \
    --robot.right_port=/dev/ttyACM1 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --teleop.left_port=/dev/ttyACM0 \
    --teleop.left_id=my_leader_left \
    --teleop.right_port=/dev/ttyACM3 \
    --teleop.right_id=my_leader_right \
    --display_data=true


python -m lerobot.bi_teleoperate \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/ttyACM3 \
    --robot.right_port=/dev/ttyACM2 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --teleop.left_port=/dev/ttyACM0 \
    --teleop.left_id=my_leader_left \
    --teleop.right_port=/dev/ttyACM1 \
    --teleop.right_id=my_leader_right \
    --display_data=true

## 3. Record Your Dataset (Bimanual Pick & Place)

python -m lerobot.record \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/ttyACM2 \
    --robot.right_port=/dev/ttyACM1 \
    --robot.cameras='{"front": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}, "top": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --teleop.left_port=/dev/ttyACM0 \
    --teleop.left_id=my_leader_left \
    --teleop.right_port=/dev/ttyACM3 \
    --teleop.right_id=my_leader_right \
    --dataset.repo_id=my_local_dataset \
    --dataset.single_task="Pick up the red cube with the left hand and place it in the bin" \
    --dataset.num_episodes=50 \
    --dataset.episode_time_s=60 \
    --dataset.reset_time_s=30 \
    --dataset.fps=30 \
    --dataset.push_to_hub=false \
    --dataset.root=./datasets/bimanual_pickplace_dataset


## 4. Train SmolVLA on Your Dataset

python -m lerobot.scripts.train \
    --policy.type=smolvla \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=my_local_dataset \
    --wandb.enable=false

# The workflow is: Calibrate → Teleoperate → Record → Train → Test!