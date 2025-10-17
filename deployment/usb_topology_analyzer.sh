#!/bin/bash

# USB Topology Analyzer for X870 AORUS ELITE WIFI7 ICE
# Helps identify which USB ports are on different controllers for camera separation

echo "🔍 USB Topology Analyzer for BiManual Robot Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running as root for some commands
if [[ $EUID -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

print_header "System Information"
echo "Motherboard: $(sudo dmidecode -s baseboard-product-name 2>/dev/null || echo "Unknown")"
echo "Manufacturer: $(sudo dmidecode -s baseboard-manufacturer 2>/dev/null || echo "Unknown")"

print_header "USB Controllers (PCI)"
echo "Available USB controllers on your motherboard:"
lspci | grep -i usb | while read line; do
    pci_id=$(echo "$line" | cut -d' ' -f1)
    controller_info=$(echo "$line" | cut -d':' -f2- | sed 's/^ *//')
    echo -e "  ${PURPLE}$pci_id${NC}: $controller_info"
done

print_header "USB Bus Topology"
echo "Current USB device tree:"
lsusb -t

print_header "Current Camera Assignment"
cameras_found=0
declare -A camera_controllers
declare -A controller_cameras

for cam in /dev/video*; do
    if [[ -e "$cam" ]]; then
        cameras_found=$((cameras_found + 1))
        
        # Get detailed path info
        path_info=$(udevadm info --query=all --name="$cam" | grep "ID_PATH=" | head -1)
        pci_device=$(echo "$path_info" | grep -o 'pci-[^-]*')
        usb_path=$(echo "$path_info" | grep -o 'usb-[^:]*')
        
        # Get bus info
        bus_info=$(udevadm info --query=all --name="$cam" | grep "DEVPATH" | grep -o 'usb[0-9]*')
        
        echo -e "  ${YELLOW}$cam${NC}:"
        echo -e "    PCI Controller: ${PURPLE}$pci_device${NC}"
        echo -e "    USB Bus: ${CYAN}$bus_info${NC}"
        echo -e "    USB Path: $usb_path"
        
        camera_controllers["$cam"]="$pci_device"
        controller_cameras["$pci_device"]+="$cam "
    fi
done

if [[ $cameras_found -eq 0 ]]; then
    print_error "No cameras found! Check camera connections."
    exit 1
fi

print_header "Controller Assignment Analysis"
unique_controllers=($(printf '%s\n' "${camera_controllers[@]}" | sort -u))
echo "Cameras are distributed across ${#unique_controllers[@]} controller(s):"

for controller in "${unique_controllers[@]}"; do
    cameras_on_controller="${controller_cameras[$controller]}"
    camera_count=$(echo $cameras_on_controller | wc -w)
    
    if [[ $camera_count -gt 1 ]]; then
        print_error "Controller $controller has $camera_count cameras: $cameras_on_controller"
        echo "    ❌ This will cause bandwidth conflicts!"
    else
        print_success "Controller $controller has 1 camera: $cameras_on_controller"
        echo "    ✅ Good separation"
    fi
done

print_header "Bandwidth Analysis"
echo "Checking USB speeds and bandwidth usage..."

for cam in /dev/video*; do
    if [[ -e "$cam" ]]; then
        # Get USB device info
        device_path=$(udevadm info --query=all --name="$cam" | grep "DEVPATH" | cut -d'=' -f2)
        
        # Try to get speed from sysfs
        speed_file="/sys$device_path/../speed"
        if [[ -f "$speed_file" ]]; then
            speed=$(cat "$speed_file" 2>/dev/null)
            case $speed in
                "12") speed_text="USB 1.1 (12 Mbps)" ;;
                "480") speed_text="USB 2.0 (480 Mbps)" ;;
                "5000") speed_text="USB 3.0 (5 Gbps)" ;;
                "10000") speed_text="USB 3.1 (10 Gbps)" ;;
                "20000") speed_text="USB 3.2 (20 Gbps)" ;;
                *) speed_text="Unknown ($speed)" ;;
            esac
            echo -e "  $cam: ${CYAN}$speed_text${NC}"
        else
            echo -e "  $cam: Speed unknown"
        fi
    fi
done

print_header "Motor Controllers"
echo "USB Serial devices (motor controllers):"
motor_count=0
for device in /dev/ttyACM*; do
    if [[ -e "$device" ]]; then
        motor_count=$((motor_count + 1))
        path_info=$(udevadm info --query=all --name="$device" | grep "ID_PATH=" | head -1)
        pci_device=$(echo "$path_info" | grep -o 'pci-[^-]*')
        echo -e "  ${YELLOW}$device${NC}: Controller ${PURPLE}$pci_device${NC}"
    fi
done

if [[ $motor_count -eq 0 ]]; then
    print_warn "No motor controllers found on /dev/ttyACM*"
fi

print_header "USB Traffic Monitoring"
echo "To monitor real-time USB traffic, run:"
echo "  sudo cat /sys/kernel/debug/usb/usbmon/0u"
echo ""
echo "To monitor specific bus (replace X with bus number):"
echo "  sudo cat /sys/kernel/debug/usb/usbmon/Xu"

print_header "IRQ Assignment Check"
echo "USB interrupt assignments (shared IRQs indicate shared controllers):"
cat /proc/interrupts | grep -i usb | while read line; do
    irq=$(echo "$line" | awk '{print $1}' | sed 's/://')
    desc=$(echo "$line" | awk '{for(i=5;i<=NF;i++) printf "%s ", $i; print ""}')
    echo -e "  IRQ ${PURPLE}$irq${NC}: $desc"
done

print_header "Recommended Actions"

# Check if cameras are on same controller
if [[ ${#unique_controllers[@]} -eq 1 ]]; then
    print_error "ALL CAMERAS ARE ON THE SAME USB CONTROLLER!"
    echo ""
    echo "🔧 SOLUTION STEPS:"
    echo "1. Physically disconnect one camera"
    echo "2. Find a USB port on a DIFFERENT physical location on your motherboard"
    echo "3. For X870 AORUS ELITE WIFI7 ICE, try these port combinations:"
    echo "   - Front panel USB ports (usually different controller)"
    echo "   - Top row vs bottom row of rear USB ports"
    echo "   - USB-A vs USB-C ports (often different controllers)"
    echo "4. Reconnect camera to the different port"
    echo "5. Run this script again to verify separation"
    echo ""
    echo "🎯 TARGET: Each camera should show a different PCI controller ID"
    
elif [[ ${#unique_controllers[@]} -gt 1 ]]; then
    print_success "Cameras are properly separated across different USB controllers!"
    echo ""
    echo "✅ Your setup should work without USB bandwidth conflicts"
    echo "If you're still experiencing timeouts, check:"
    echo "1. USB cable quality (use USB 3.0+ cables)"
    echo "2. Camera resolution/FPS settings"
    echo "3. System CPU load during operation"
else
    print_warn "Unexpected controller configuration detected"
fi

print_header "Physical Port Mapping Helper"
echo ""
echo "🔍 To identify which physical ports map to which controllers:"
echo "1. Unplug both cameras"
echo "2. Run: watch -n 1 'lsusb | grep Camera'"
echo "3. Plug camera 1 into a rear USB port, note which controller it appears on"
echo "4. Unplug camera 1"
echo "5. Try different rear USB ports until you find one on a different controller"
echo "6. Plug camera 2 into the different controller port"
echo "7. Plug camera 1 back into original port"
echo ""
echo "💡 TIP: X870 motherboards typically have USB ports from multiple controllers."
echo "   Try USB-A ports vs USB-C ports, or top row vs bottom row."

print_header "System Resource Check"
free -h | head -2
echo ""
lscpu | grep -E "CPU\(s\)|Model name|Core\(s\) per socket|Thread\(s\) per core"

echo ""
echo "🏁 Analysis complete! Follow the recommended actions above."