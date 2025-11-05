#!/bin/bash

# BiManual LeRobot Deployment Script
# This script sets up the complete bimanual robot system on a new computer

# Remove set -e to handle errors gracefully
# set -e  # Exit on any error

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

print_step "2. Setting up Python environment with Conda..."

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    print_error "Conda is not installed or not in PATH"
    print_status "Installing Miniconda..."
    
    # Download and install miniconda
    cd /tmp
    if [[ "$(uname -m)" == "x86_64" ]]; then
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    elif [[ "$(uname -m)" == "aarch64" ]]; then
        wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -O miniconda.sh  
    else
        print_error "Unsupported architecture: $(uname -m)"
        exit 1
    fi
    
    chmod +x miniconda.sh
    ./miniconda.sh -b -p $HOME/miniconda3
    
    # Add conda to PATH
    export PATH="$HOME/miniconda3/bin:$PATH"
    echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
    
    # Initialize conda
    $HOME/miniconda3/bin/conda init bash
    source ~/.bashrc
    
    print_status "Miniconda installed successfully"
    cd - > /dev/null
else
    print_status "Conda found: $(which conda)"
fi

# Initialize conda in this script
eval "$(conda shell.bash hook)" 2>/dev/null || {
    print_warning "Failed to initialize conda, trying manual setup..."
    if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="$HOME/miniconda3/bin:$PATH"
    fi
}

# Create or activate lerobot environment
CONDA_ENV="lerobot"
if conda env list | grep -q "^${CONDA_ENV} "; then
    print_status "Found existing ${CONDA_ENV} environment"
    conda activate ${CONDA_ENV}
else
    print_status "Creating new conda environment: ${CONDA_ENV}"
    conda create -n ${CONDA_ENV} python=3.10 -y
    conda activate ${CONDA_ENV}
fi

print_status "Activated conda environment: ${CONDA_ENV}"

# Install conda dependencies first
print_status "Installing conda dependencies..."
conda install -y -c conda-forge \
    numpy \
    opencv \
    pillow \
    matplotlib \
    scipy \
    scikit-learn \
    pyyaml \
    tqdm \
    jupyter \
    ipython

# Install PyTorch (CPU version for compatibility)
print_status "Installing PyTorch..."
conda install -y pytorch torchvision torchaudio cpuonly -c pytorch

# Install additional pip dependencies
print_status "Installing additional Python packages..."
pip install --upgrade pip

# Install LeRobot and its dependencies
pip install -e .

# Install additional packages that might be needed
pip install \
    pyserial \
    opencv-contrib-python \
    pyrealsense2 \
    realsense2-python \
    huggingface-hub \
    wandb \
    gym \
    stable-baselines3 \
    imageio \
    imageio-ffmpeg \
    draccus \
    omegaconf

print_status "Python environment setup complete"

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

# Initialize conda
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    export PATH="$HOME/miniconda3/bin:$PATH"
fi

# Activate conda environment
conda activate lerobot || {
    echo "❌ Failed to activate lerobot conda environment"
    echo "Run: conda activate lerobot"
    exit 1
}

# Run camera diagnostic first
echo "🔍 Running camera diagnostic..."
python -m lerobot.scripts.camera_diagnostic

echo ""
echo "🤖 Starting BiManual Robot Teleoperation..."
echo "Press Ctrl+C to stop"
echo ""

# Check for connected devices
echo "Checking for connected devices..."
echo "Serial devices:"
ls /dev/ttyACM* 2>/dev/null || echo "  No serial devices found!"
echo "Video devices:"  
ls /dev/video* 2>/dev/null || echo "  No video devices found!"
echo ""

# Default command - modify ports as needed based on your hardware
# Use working camera indices (2 and 6 are on different USB controllers)
python -m lerobot.teleoperate \
  --robot.type=bi_so101_follower \
  --robot.left_arm_port=/dev/ttyACM1 \
  --robot.right_arm_port=/dev/ttyACM2 \
  --robot.id=bimanual_so101 \
  --robot.calibration_dir="./calibration" \
  --robot.cameras="{wrist_right: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}, wrist_left: {type: opencv, index_or_path: 6, width: 640, height: 480, fps: 30}}" \
  --teleop.type=bi_so101_leader \
  --teleop.left_arm_port=/dev/ttyACM0 \
  --teleop.right_arm_port=/dev/ttyACM3 \
  --teleop.id=bimanual_so101_leader \
  --teleop.calibration_dir="./calibration" \
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

# Initialize conda
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    export PATH="$HOME/miniconda3/bin:$PATH"
fi

# Activate conda environment
conda activate lerobot || {
    echo "❌ Failed to activate lerobot conda environment"
    echo "Run: conda activate lerobot"
    exit 1
}

echo "🔧 Starting BiManual Robot Calibration..."
echo "Follow the on-screen instructions"
echo ""

# Check for connected devices first
echo "Checking for connected devices..."
echo "Serial devices:"
ls /dev/ttyACM* 2>/dev/null || echo "  No serial devices found!"
echo ""

python -m lerobot.scripts.calibrate_bimanual_so101 \
  --left_follower_port=/dev/ttyACM2 \
  --right_follower_port=/dev/ttyACM3 \
  --left_leader_port=/dev/ttyACM0 \
  --right_leader_port=/dev/ttyACM1
EOF

chmod +x calibrate_bimanual_robot.sh
print_status "Created calibrate_bimanual_robot.sh"

print_step "7. Running installation test..."

# Run the test script to verify everything works
if [[ -f "test_installation.sh" ]]; then
    chmod +x test_installation.sh
    ./test_installation.sh
    
    if [[ $? -eq 0 ]]; then
        print_status "✅ All tests passed!"
    else
        print_warning "⚠️ Some tests failed - check output above"
    fi
else
    print_warning "Test script not found, skipping verification"
fi

print_step "8. Creating environment activation helper..."

# Create a helper script to activate the environment
cat > activate_lerobot.sh << 'EOF'
#!/bin/bash
# Helper script to activate the lerobot conda environment
# Usage: source activate_lerobot.sh

if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    export PATH="$HOME/miniconda3/bin:$PATH"
fi

conda activate lerobot
echo "✅ Activated lerobot conda environment"
echo "Python: $(which python)"
echo "LeRobot ready!"
EOF

chmod +x activate_lerobot.sh
print_status "Created activate_lerobot.sh helper script"

print_step "9. Deployment complete!"

echo ""
echo "✅ BiManual Robot deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. ${YELLOW}Restart your terminal or run: source ~/.bashrc${NC}"
echo "2. ${YELLOW}If needed, logout and login${NC} (for group permissions)"
echo "3. Connect your hardware:"
echo "   - 4 servo motors to USB ports (will appear as /dev/ttyACM0-3)"
echo "   - 2 cameras to USB ports"
echo "4. Test installation: ${GREEN}./test_installation.sh${NC}"
echo "5. Start the robot: ${GREEN}./start_bimanual_robot.sh${NC}"
echo "6. If needed, recalibrate: ${GREEN}./calibrate_bimanual_robot.sh${NC}"
echo ""
echo "Troubleshooting:"
echo "- Activate environment manually: ${GREEN}source activate_lerobot.sh${NC}"
echo "- Check cameras: ${GREEN}python -m lerobot.scripts.camera_diagnostic${NC}"
echo "- Check hardware connections if devices aren't detected"
echo ""
echo "Environment info:"
echo "- Conda environment: ${GREEN}lerobot${NC}"
echo "- Calibration files: ${GREEN}~/.cache/huggingface/lerobot/calibration/${NC}"
echo "- Startup scripts: ${GREEN}./start_bimanual_robot.sh${NC}"
echo ""
