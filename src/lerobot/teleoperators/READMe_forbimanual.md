# BiManual SO101 Robot Commands

## Calibration Command
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

## Working Teleoperation Command (Final)
With OpenCV cameras and RealSense camera support:
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

## Working Recording Command (Final)
For dataset recording with multiple cameras:
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
  --dataset.repo_id="test_user/bimanual_test_recording" \
  --dataset.single_task="Test bimanual robot recording" \
  --dataset.num_episodes=1 \
  --dataset.episode_time_s=30 \
  --dataset.fps=30
```

## Notes
- Replace `test_user` with your HuggingFace username
- Adjust camera indices (0, 2) based on your system's available cameras
- Use `python -m lerobot.find_cameras opencv` to detect available cameras
- RealSense serial number should match your device
- Both teleoperation and recording scripts now support multiple camera types

## Setup Requirements
- RealSense library: `pip install pyrealsense2`
- Ensure cameras are on different USB controllers for optimal performance
- Run USB topology analyzer: `./deployment/usb_topology_analyzer.sh`


#with camera
python -m lerobot.teleoperate   --robot.type=bi_so101_follower   --robot.left_arm_port=/dev/ttyACM1   --robot.right_arm_port=/dev/ttyACM2   --robot.id=bimanual_so101 --robot.calibration_dir="./calibration"  --robot.cameras="{wrist_right: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}, wrist_left: {type: opencv, index_or_path:0, width: 640, height: 480, fps: 30} }"  --robot.calibration_dir="./calibration"   --teleop.type=bi_so101_leader   --teleop.left_arm_port=/dev/ttyACM0   --teleop.right_arm_port=/dev/ttyACM3   --teleop.id=bimanual_so101_leader  --teleop.calibration_dir="./calibration"   --display_data=true

#realsense:
python -m lerobot.teleoperate   --robot.type=bi_so101_follower   --robot.left_arm_port=/dev/ttyACM1   --robot.right_arm_port=/dev/ttyACM2   --robot.id=bimanual_so101 --robot.calibration_dir="./calibration"  --robot.cameras="{wrist_right: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist_left: {type: opencv, index_or_path: 3, width: 640, height: 480, fps: 30}, realsense_top: {type: intelrealsense, serial_number_or_name: "027322073278", width: 640, height: 480, fps: 30} }"  --robot.calibration_dir="./calibration"   --teleop.type=bi_so101_leader   --teleop.left_arm_port=/dev/ttyACM0   --teleop.right_arm_port=/dev/ttyACM3   --teleop.id=bimanual_so101_leader  --teleop.calibration_dir="./calibration"   --display_data=true


#wriste camera port


--- Detected Cameras ---
Camera #0:
  Name: OpenCV Camera @ /dev/video0
  Type: OpenCV
  Id: /dev/video0
  Backend api: V4L2
  Default stream profile:
    Format: 0.0
    Width: 640
    Height: 480
    Fps: 30.0
--------------------
Camera #1:
  Name: OpenCV Camera @ /dev/video2 
  Type: OpenCV
  Id: /dev/video2
  Backend api: V4L2
  Default stream profile:
    Format: 0.0
    Width: 640
    Height: 480
    Fps: 30.0
--------------------


#---

python -m lerobot.scripts.calibrate_bimanual_so101   --robot.type=bi_so101_follower   --robot.left_arm_port=/dev/ttyACM1   --robot.right_arm_port=/dev/ttyACM2   --robot.id=bimanual_so101   --robot.cameras="{}"  --robot.calibration_dir="./calibration"   --teleop.type=bi_so101_leader   --teleop.left_arm_port=/dev/ttyACM0   --teleop.right_arm_port=/dev/ttyACM3   --teleop.id=bimanual_so101_leader  --teleop.calibration_dir="./calibration"   --display_data=true


python -m lerobot.teleoperate --robot.type=bi_so101_follower --robot.left_arm_port=/dev/ttyACM1 --robot.right_arm_port=/dev/ttyACM2 --robot.id=bimanual_so101 --robot.calibration_dir=./calibration --robot.cameras='{"wrist_right": {"type": "opencv", "index_or_path": 2, "width": 640, "height": 480, "fps": 30}, "wrist_left": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}' --teleop.type=bi_so101_leader --teleop.left_arm_port=/dev/ttyACM0 --teleop.right_arm_port=/dev/ttyACM3 --teleop.id=bimanual_so101_leader --teleop.calibration_dir=./calibration --display_data=true

, "wrist_left": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}

/dev/video0

python -m lerobot.teleoperate --robot.type=bi_so101_follower --robot.left_arm_port=/dev/ttyACM1 --robot.right_arm_port=/dev/ttyACM2 --robot.id=bimanual_so101 --robot.calibration_dir=./calibration --robot.cameras='{"wrist_right": {"type": "opencv", "index_or_path": /dev/video2, "width": 640, "height": 480, "fps": 30}, "wrist_left": {"type": "opencv", "index_or_path": /dev/video0, "width": 640, "height": 480, "fps": 30}}' --teleop.type=bi_so101_leader --teleop.left_arm_port=/dev/ttyACM0 --teleop.right_arm_port=/dev/ttyACM3 --teleop.id=bimanual_so101_leader --teleop.calibration_dir=./calibration --display_data=true
