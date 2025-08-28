#!/bin/bash

# BiManual LeRobot Deployment Script
# This script sets up the complete bimanual robot system on a new computer

set -e  # Exit on any error

echo "🤖 BiManual LeRobot Deployment Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "src/lerobot" ]]; then
    print_error "Please run this script from the bimanual-lerobot repository root directory"
    exit 1
fi

print_step "1. Installing system dependencies..."

# Check if running on Ubuntu/Debian
if command -v apt-get &> /dev/null; then
    print_status "Detected Ubuntu/Debian system"
    
    # Install system dependencies
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        cmake \
        pkg-config \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libgtk-3-dev \
        libatlas-base-dev \
        gfortran \
        v4l-utils \
        udev
        
    print_status "System dependencies installed"
else
    print_warning "Non-Ubuntu system detected. Please install system dependencies manually:"
    print_warning "- Python 3.8+"
    print_warning "- OpenCV dependencies"
    print_warning "- v4l-utils"
    print_warning "- udev"
fi

print_step "2. Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    print_status "Created virtual environment"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Activated virtual environment"

# Install Python dependencies
pip install --upgrade pip
pip install -e .
print_status "Installed LeRobot package and dependencies"

print_step "3. Setting up calibration files..."

# Create calibration directory
mkdir -p ~/.cache/huggingface/lerobot/

# Copy calibration files if they exist in deployment/
if [[ -d "deployment/calibration" ]]; then
    cp -r deployment/calibration ~/.cache/huggingface/lerobot/
    print_status "Copied calibration files to ~/.cache/huggingface/lerobot/calibration"
    
    # List what calibration files were installed
    echo "Available calibration files:"
    find ~/.cache/huggingface/lerobot/calibration -name "*.json" -type f | sort
else
    print_warning "No calibration files found in deployment/calibration/"
    print_warning "You'll need to run calibration on this system"
fi

print_step "4. Setting up hardware permissions..."

# Add user to dialout group for serial port access
if command -v usermod &> /dev/null; then
    sudo usermod -a -G dialout $USER
    print_status "Added user to dialout group"
    print_warning "You may need to log out and back in for group changes to take effect"
fi

# Create udev rules for consistent device naming
cat > /tmp/99-bimanual-robot.rules << 'EOF'
# BiManual Robot udev rules for consistent device naming
# Motors - Feetech servos
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="*", SYMLINK+="bimanual_motor_%s{serial}"

# Cameras - stable naming by USB port
SUBSYSTEM=="video4linux", KERNELS=="*:1:1.0", ATTR{index}=="0", SYMLINK+="bimanual_cam_left"
SUBSYSTEM=="video4linux", KERNELS=="*:2:1.0", ATTR{index}=="0", SYMLINK+="bimanual_cam_right"
EOF

sudo cp /tmp/99-bimanual-robot.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
print_status "Created udev rules for consistent device naming"

print_step "5. Running hardware detection..."

# Check for connected devices
print_status "Scanning for connected hardware..."

echo "USB Serial Devices:"
ls /dev/ttyACM* 2>/dev/null || echo "  No /dev/ttyACM* devices found"
ls /dev/ttyUSB* 2>/dev/null || echo "  No /dev/ttyUSB* devices found"

echo "Video Devices:"
if command -v v4l2-ctl &> /dev/null; then
    v4l2-ctl --list-devices 2>/dev/null || echo "  No video devices found"
else
    ls /dev/video* 2>/dev/null || echo "  No video devices found"
fi

print_step "6. Creating startup scripts..."

# Create a startup script
cat > start_bimanual_robot.sh << 'EOF'
#!/bin/bash

# BiManual Robot Startup Script
# Usage: ./start_bimanual_robot.sh

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run camera diagnostic first
echo "🔍 Running camera diagnostic..."
python -m lerobot.scripts.camera_diagnostic

echo ""
echo "🤖 Starting BiManual Robot Teleoperation..."
echo "Press Ctrl+C to stop"
echo ""

# Default command - modify as needed
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM2 \
  --robot.right_arm_port=/dev/ttyACM3 \
  --robot.id=bimanual_so101_setup \
  --robot.cameras='{
    left_wrist: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30},
    right_wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30},
  }' \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM0 \
  --teleop.right_arm_port=/dev/ttyACM1 \
  --teleop.id=bimanual_leader_setup \
  --display_data=true
EOF

chmod +x start_bimanual_robot.sh
print_status "Created start_bimanual_robot.sh"

# Create calibration script
cat > calibrate_bimanual_robot.sh << 'EOF'
#!/bin/bash

# BiManual Robot Calibration Script
# Usage: ./calibrate_bimanual_robot.sh

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

echo "🔧 Starting BiManual Robot Calibration..."
echo "Follow the on-screen instructions"
echo ""

python -m lerobot.scripts.calibrate_bimanual_so101 \
  --left_follower_port=/dev/ttyACM2 \
  --right_follower_port=/dev/ttyACM3 \
  --left_leader_port=/dev/ttyACM0 \
  --right_leader_port=/dev/ttyACM1
EOF

chmod +x calibrate_bimanual_robot.sh
print_status "Created calibrate_bimanual_robot.sh"

print_step "7. Deployment complete!"

echo ""
echo "✅ BiManual Robot deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. ${YELLOW}Log out and back in${NC} (for group permissions)"
echo "2. Connect your hardware:"
echo "   - 4 servo motors to USB ports (will appear as /dev/ttyACM0-3)"
echo "   - 2 cameras to USB ports"
echo "3. Run: ${GREEN}./start_bimanual_robot.sh${NC} to start the system"
echo "4. If needed, run: ${GREEN}./calibrate_bimanual_robot.sh${NC} to recalibrate"
echo ""
echo "Troubleshooting:"
echo "- Run: ${GREEN}python -m lerobot.scripts.camera_diagnostic${NC} to check cameras"
echo "- Check hardware connections if devices aren't detected"
echo ""
