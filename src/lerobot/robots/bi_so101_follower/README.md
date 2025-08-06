# Bimanual SO101 for SmolVLA Training

This guide shows you how to set up and use a bimanual SO101 system for SmolVLA training without needing URDF schemas.

## Hardware Requirements

- **2 SO101 Follower Arms** with STS3215 servos (left and right manipulators)
- **2 SO101 Leader Arms** with STS3215 servos (left and right teleoperation)
- **4 Cameras**:
  - 2 Intel RealSense cameras (external context views)
  - 2 OpenCV cameras (mounted on the robot arms)
- **4 USB connections** for the arm controllers

## Quick Start

### 1. Hardware Setup

Connect your arms to different USB ports:
```bash
# Check your ports with:
ls /dev/ttyACM*

# Typical setup:
# /dev/ttyACM0 - Left follower arm
# /dev/ttyACM1 - Right follower arm  
# /dev/ttyACM2 - Left leader arm
# /dev/ttyACM3 - Right leader arm
```

### 2. Calibration

Calibrate both follower and leader arms:

```bash
python -m lerobot.scripts.calibrate_bimanual_so101 \
  --left_follower_port=/dev/ttyACM0 \
  --right_follower_port=/dev/ttyACM1 \
  --left_leader_port=/dev/ttyACM2 \
  --right_leader_port=/dev/ttyACM3 \
  --robot_id=my_bimanual_setup
```

Alternatively, use the standard calibration for each arm:

```bash
# Calibrate individual follower arms
python -m lerobot.calibrate \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM0 \
  --robot.id=left_follower

python -m lerobot.calibrate \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM1 \
  --robot.id=right_follower

# Calibrate individual leader arms  
python -m lerobot.calibrate \
  --robot.type=so101_leader \
  --robot.port=/dev/ttyACM2 \
  --robot.id=left_leader

python -m lerobot.calibrate \
  --robot.type=so101_leader \
  --robot.port=/dev/ttyACM3 \
  --robot.id=right_leader
```

### 3. Test Teleoperation

Test bimanual teleoperation with all 4 cameras:

```bash
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM0 \
  --robot.right_arm_port=/dev/ttyACM1 \
  --robot.id=bimanual_test \
  --robot.cameras='{
    left_wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    right_wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30},
    left_context: {type: realsense, serial_number: "YOUR_LEFT_SERIAL", width: 640, height: 480, fps: 30},
    right_context: {type: realsense, serial_number: "YOUR_RIGHT_SERIAL", width: 640, height: 480, fps: 30}
  }' \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM2 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_leader \
  --display_data=true
```

### 4. Record Dataset

Record bimanual demonstration data for SmolVLA:

```bash
python -m lerobot.record \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM0 \
  --robot.right_arm_port=/dev/ttyACM1 \
  --robot.id=bimanual_so101 \
  --robot.cameras='{
    left_wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    right_wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30},
    left_context: {type: realsense, serial_number: "YOUR_LEFT_SERIAL", width: 640, height: 480, fps: 30},
    right_context: {type: realsense, serial_number: "YOUR_RIGHT_SERIAL", width: 640, height: 480, fps: 30}
  }' \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM2 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_leader \
  --dataset.repo_id=${HF_USER}/bimanual_so101_dataset \
  --dataset.single_task="Pick object with left arm and place in right hand, then place in bin" \
  --dataset.num_episodes=50 \
  --fps=30
```

### 5. Train SmolVLA

Train SmolVLA on your bimanual dataset (no URDF needed!):

```bash
python -m lerobot.scripts.train \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=${HF_USER}/bimanual_so101_dataset \
  --batch_size=32 \
  --steps=20000 \
  --output_dir=outputs/train/bimanual_smolvla \
  --job_name=bimanual_so101_smolvla \
  --policy.device=cuda \
  --wandb.enable=true
```

### 6. Run Inference

Deploy your trained bimanual policy:

```bash
python -m lerobot.record \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM0 \
  --robot.right_arm_port=/dev/ttyACM1 \
  --robot.id=bimanual_so101 \
  --robot.cameras='{
    left_wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    right_wrist: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30},
    left_context: {type: realsense, serial_number: "YOUR_LEFT_SERIAL", width: 640, height: 480, fps: 30},
    right_context: {type: realsense, serial_number: "YOUR_RIGHT_SERIAL", width: 640, height: 480, fps: 30}
  }' \
  --dataset.single_task="Pick object with left arm and place in right hand, then place in bin" \
  --policy.path=${HF_USER}/bimanual_so101_smolvla \
  --fps=30
```

## Configuration Details

### Action Space

The bimanual system provides the following action space:
- `left_joint_1.pos` through `left_joint_6.pos` (left arm joints)
- `right_joint_1.pos` through `right_joint_6.pos` (right arm joints)

### Observation Space

The system provides:
- **State**: Joint positions for both arms (12 DOF total)
- **Images**: 4 camera views (left_wrist, right_wrist, left_context, right_context)

### Camera Setup

- **Robot cameras (OpenCV)**: Mounted on the arms for hand-eye coordination
- **Context cameras (RealSense)**: External views for spatial understanding
- **Resolution**: 640x480 at 30 FPS (adjustable)

## SmolVLA Advantages

✅ **No URDF Required**: SmolVLA works directly with joint positions  
✅ **Bimanual Support**: Handles left/right arm coordination automatically  
✅ **Multi-Camera**: Leverages all 4 camera views for better understanding  
✅ **Language Instructions**: Supports natural language task descriptions  
✅ **Transfer Learning**: Fine-tune from the pretrained smolvla_base model  

## Troubleshooting

### Port Issues
```bash
# Check connected devices
ls /dev/ttyACM*
ls /dev/ttyUSB*

# Check camera devices  
ls /dev/video*
```

### Camera Serial Numbers
```bash
# Find RealSense serial numbers
rs-enumerate-devices
```

### Permission Issues
```bash
# Add user to dialout group for serial ports
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Memory Issues
- Reduce batch size for training: `--batch_size=16`
- Reduce camera resolution: `width: 320, height: 240`
- Use gradient checkpointing: `--policy.use_gradient_checkpointing=true`

## Example Tasks

Good bimanual tasks for SmolVLA training:
- **Handover**: Pick object with one arm, pass to the other
- **Collaborative**: Both arms work together to manipulate large objects
- **Sequential**: Left arm positions, right arm executes
- **Sorting**: Each arm handles different object types

## Next Steps

1. **Start Simple**: Begin with basic pick-and-place with one arm
2. **Add Coordination**: Progress to handover tasks between arms  
3. **Scale Up**: Increase to complex bimanual manipulation
4. **Vary Data**: Record different positions, objects, and lighting
5. **Fine-tune**: Adjust SmolVLA hyperparameters for your specific tasks

For support, join the [LeRobot Discord](https://discord.com/invite/s3KuuzsPFb) community!
