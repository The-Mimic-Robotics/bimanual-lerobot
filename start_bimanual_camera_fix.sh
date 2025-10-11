#!/bin/bash

# Fixed BiManual Robot Startup Script
# This version handles camera conflicts by using a working configuration

cd "$(dirname "$0")"

echo "🤖 Starting BiManual Robot with Camera Conflict Fix"
echo "=================================================="

# Check hardware
echo "🔍 Checking hardware..."
for port in /dev/ttyACM0 /dev/ttyACM1 /dev/ttyACM2 /dev/ttyACM3; do
    if [[ -e "$port" ]]; then
        echo "✅ $port found"
    else
        echo "❌ $port missing"
    fi
done

# Test cameras briefly
echo "📹 Testing cameras..."
python3 -c "
import cv2
cap0 = cv2.VideoCapture('/dev/video0')
cap2 = cv2.VideoCapture('/dev/video2')
print('video0:', '✅' if cap0.isOpened() else '❌')
print('video2:', '✅' if cap2.isOpened() else '❌')
cap0.release()
cap2.release()
"

echo ""
echo "🚀 Starting teleoperation with camera conflict fix..."
echo "Press Ctrl+C to stop"
echo ""

# Fixed command with proper warmup_s as integer and reduced to 0 (no warmup)
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM1 \
  --robot.right_arm_port=/dev/ttyACM2 \
  --robot.id=bimanual_so101 \
  --robot.calibration_dir=./calibration \
  --robot.cameras='{"wrist_right": {"type": "opencv", "index_or_path": "/dev/video2", "width": 640, "height": 480, "fps": 30, "warmup_s": 0}, "wrist_left": {"type": "opencv", "index_or_path": "/dev/video0", "width": 640, "height": 480, "fps": 30, "warmup_s": 0}}' \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM0 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_so101_leader \
  --teleop.calibration_dir=./calibration \
  --display_data=true

echo ""
echo "🛑 Teleoperation stopped"
