#!/bin/bash

# Test script to verify the bimanual robot installation
# Usage: ./test_installation.sh

echo "🧪 Testing BiManual Robot Installation"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Initialize conda
if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    export PATH="$HOME/miniconda3/bin:$PATH"
fi

# Test 1: Conda environment
print_test "Checking conda environment..."
if conda activate lerobot 2>/dev/null; then
    print_pass "Conda environment 'lerobot' exists and activates"
else
    print_fail "Cannot activate conda environment 'lerobot'"
    echo "Run: conda create -n lerobot python=3.10"
    exit 1
fi

# Test 2: Python imports
print_test "Testing Python imports..."
python -c "
import sys
packages = ['cv2', 'numpy', 'torch', 'serial', 'yaml']
failed = []

for pkg in packages:
    try:
        __import__(pkg)
        print(f'✓ {pkg}')
    except ImportError:
        print(f'✗ {pkg}')
        failed.append(pkg)

if failed:
    print(f'Failed imports: {failed}')
    sys.exit(1)
"

if [[ $? -eq 0 ]]; then
    print_pass "All required Python packages imported successfully"
else
    print_fail "Some Python packages failed to import"
fi

# Test 3: LeRobot package
print_test "Testing LeRobot package..."
if python -c "import lerobot; print('LeRobot version:', lerobot.__version__)" 2>/dev/null; then
    print_pass "LeRobot package imported successfully"
else
    print_fail "Cannot import LeRobot package"
    echo "Run: pip install -e ."
fi

# Test 4: Camera diagnostic
print_test "Testing camera diagnostic..."
if python -m lerobot.scripts.camera_diagnostic > /tmp/camera_test.log 2>&1; then
    print_pass "Camera diagnostic script runs"
    echo "Camera status:"
    tail -10 /tmp/camera_test.log
else
    print_fail "Camera diagnostic script failed"
    echo "Check /tmp/camera_test.log for details"
fi

# Test 5: Hardware detection
print_test "Testing hardware detection..."
echo "Serial devices:"
ls /dev/ttyACM* 2>/dev/null && print_pass "Serial devices found" || print_fail "No serial devices found"

echo "Video devices:"
ls /dev/video* 2>/dev/null && print_pass "Video devices found" || print_fail "No video devices found"

# Test 6: Calibration files
print_test "Testing calibration files..."
if [[ -d "$HOME/.cache/huggingface/lerobot/calibration" ]]; then
    cal_files=$(find "$HOME/.cache/huggingface/lerobot/calibration" -name "*.json" | wc -l)
    if [[ $cal_files -gt 0 ]]; then
        print_pass "Found $cal_files calibration files"
    else
        print_fail "No calibration files found"
    fi
else
    print_fail "Calibration directory not found"
fi

# Test 7: Permissions
print_test "Testing USB permissions..."
if groups | grep -q dialout; then
    print_pass "User is in dialout group"
else
    print_fail "User not in dialout group"
    echo "Run: sudo usermod -a -G dialout \$USER"
    echo "Then logout and login again"
fi

# Test 8: USB Topology Analysis
print_test "Analyzing USB topology for camera separation..."
echo "USB Controllers:"
lspci | grep USB | while read line; do
    echo "  $line"
done

echo ""
echo "Camera USB Controller Analysis:"
for cam in /dev/video*; do
    if [[ -e "$cam" ]]; then
        controller_info=$(udevadm info --query=all --name=$cam | grep "ID_PATH=" | head -1)
        pci_device=$(echo "$controller_info" | grep -o 'pci-[^-]*')
        echo "  $cam -> $pci_device"
    fi
done

echo ""
# Check if cameras are on same controller
cam_controllers=($(for cam in /dev/video*; do 
    if [[ -e "$cam" ]]; then
        udevadm info --query=all --name=$cam | grep "ID_PATH=" | head -1 | grep -o 'pci-[^-]*'
    fi
done | sort -u))

if [[ ${#cam_controllers[@]} -gt 1 ]]; then
    print_pass "Cameras are on separate USB controllers"
else
    print_fail "All cameras are on the same USB controller: ${cam_controllers[0]}"
    echo "Move cameras to different physical USB ports on motherboard"
fi

echo ""
echo "🎯 Installation test completed!"
echo "If all tests pass, run: ./start_bimanual_robot.sh"
