#!/bin/bash

# BiManual Robot Startup Script with Correct Calibration IDs
# This script uses the existing calibration files so you don't need to recalibrate!

cd "$(dirname "$0")"

# Activate conda environment if available
if command -v conda &> /dev/null && [[ -n "$CONDA_DEFAULT_ENV" ]]; then
    echo "📦 Using conda environment: $CONDA_DEFAULT_ENV"
elif [[ -f "venv/bin/activate" ]]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No conda or venv detected - using system Python"
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🤖 Starting BiManual Robot Teleoperation${NC}"
echo "=============================================="

# Check hardware connections
echo "🔍 Checking hardware connections..."

# Check motor ports
missing_ports=()
for port in /dev/ttyACM0 /dev/ttyACM1 /dev/ttyACM2 /dev/ttyACM3; do
    if [[ ! -e "$port" ]]; then
        missing_ports+=("$port")
    fi
done

if [[ ${#missing_ports[@]} -gt 0 ]]; then
    echo -e "${RED}❌ Missing motor ports:${NC} ${missing_ports[*]}"
    echo -e "${YELLOW}💡 Solutions:${NC}"
    echo "   - Check USB connections"
    echo "   - Try unplugging and reconnecting motors"
    echo "   - Check if ports are at different locations:"
    ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "   No serial devices found"
    echo
    read -p "Press ENTER to continue anyway or Ctrl+C to exit..."
else
    echo -e "${GREEN}✅ All motor ports detected${NC}"
fi

# Display current port assignments
echo ""
echo "📍 Current port assignments:"
echo "   Left Leader:    /dev/ttyACM2"
echo "   Right Leader:   /dev/ttyACM3"
echo "   Left Follower:  /dev/ttyACM0" 
echo "   Right Follower: /dev/ttyACM1"
echo ""

# Check calibration files
echo "🔧 Checking calibration files..."
cal_found=0
for file in \
    "$HOME/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/bimanual_leader_setup_left.json" \
    "$HOME/.cache/huggingface/lerobot/calibration/teleoperators/so101_leader/bimanual_leader_setup_right.json" \
    "$HOME/.cache/huggingface/lerobot/calibration/robots/so101_follower/bimanual_so101_setup_left.json" \
    "$HOME/.cache/huggingface/lerobot/calibration/robots/so101_follower/bimanual_so101_setup_right.json"; do
    
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $(basename "$file")${NC}"
        ((cal_found++))
    else
        echo -e "${RED}❌ $(basename "$file")${NC}"
    fi
done

if [[ $cal_found -eq 4 ]]; then
    echo -e "${GREEN}✅ All calibration files found! No recalibration needed.${NC}"
else
    echo -e "${YELLOW}⚠️  Missing calibration files. You might need to recalibrate.${NC}"
fi

echo ""
echo -e "${GREEN}🚀 Starting teleoperation...${NC}"
echo "Press Ctrl+C to stop"
echo ""

# The correct command with matching calibration IDs
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM0 \
  --robot.right_arm_port=/dev/ttyACM1 \
  --robot.id=bimanual_so101_setup \
  --robot.cameras='{}' \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM2 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_leader_setup \
  --display_data=true

echo ""
echo -e "${YELLOW}🛑 Teleoperation stopped${NC}"
