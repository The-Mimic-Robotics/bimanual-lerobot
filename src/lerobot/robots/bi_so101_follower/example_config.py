# Bimanual SO101 Configuration Example
# This configuration shows how to set up a bimanual SO101 robot with 4 cameras
# for use with SmolVLA training and teleoperation

# Example teleoperation command:
"""
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM0 \
  --robot.right_arm_port=/dev/ttyACM1 \
  --robot.id=bimanual_so101_setup \
  --robot.cameras='{
    left_wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    right_wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30},
    left_context: {type: realsense, serial_number: "123456789", width: 640, height: 480, fps: 30},
    right_context: {type: realsense, serial_number: "987654321", width: 640, height: 480, fps: 30}
  }' \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM2 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_leader_setup \
  --display_data=true
"""

# Example recording command:
"""
python -m lerobot.record \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM0 \
  --robot.right_arm_port=/dev/ttyACM1 \
  --robot.id=bimanual_so101_setup \
  --robot.cameras='{
    left_wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    right_wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30},
    left_context: {type: realsense, serial_number: "123456789", width: 640, height: 480, fps: 30},
    right_context: {type: realsense, serial_number: "987654321", width: 640, height: 480, fps: 30}
  }' \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM2 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_leader_setup \
  --dataset.repo_id=${HF_USER}/bimanual_so101_dataset \
  --dataset.single_task="Bimanual manipulation task description" \
  --fps=30
"""

# Example SmolVLA training command:
"""
python -m lerobot.scripts.train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/bimanual_so101_dataset \
  --batch_size=32 \
  --steps=20000 \
  --output_dir=outputs/train/bimanual_smolvla \
  --job_name=bimanual_so101_smolvla_training \
  --policy.device=cuda \
  --wandb.enable=true
"""

# Hardware Setup:
# - 2 SO101 follower arms with STS3215 servos (left and right)
# - 2 SO101 leader arms with STS3215 servos (left and right) 
# - 2 OpenCV cameras mounted on the robot (wrist cameras)
# - 2 Intel RealSense cameras for context views
# 
# Port Configuration:
# - Left follower arm: /dev/ttyACM0
# - Right follower arm: /dev/ttyACM1 
# - Left leader arm: /dev/ttyACM2
# - Right leader arm: /dev/ttyACM3
#
# Camera Configuration:
# - left_wrist: OpenCV camera (index 0) - mounted on left arm
# - right_wrist: OpenCV camera (index 1) - mounted on right arm
# - left_context: RealSense camera - external context view
# - right_context: RealSense camera - external context view
#
# Key Benefits for SmolVLA:
# - No URDF schema required
# - Direct action space mapping for bimanual tasks
# - Multiple camera views for better visual understanding
# - Compatible with SmolVLA's vision-language-action architecture
