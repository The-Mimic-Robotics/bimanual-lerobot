#!/bin/bash

# X870 AORUS Physical Port Identifier
# Helps you map physical USB ports to controllers

echo "🗺️  X870 AORUS USB Port Mapping Helper"
echo "======================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo ""
echo "This script helps you identify which physical USB ports connect to different controllers."
echo ""
echo -e "${YELLOW}INSTRUCTIONS:${NC}"
echo "1. Unplug ALL cameras and USB devices (except keyboard/mouse)"
echo "2. Run this script"
echo "3. When prompted, plug ONE camera into a specific USB port"
echo "4. The script will show which controller that port uses"
echo "5. Repeat for different ports to find separation"
echo ""

read -p "Press Enter when ready to start mapping..."

# Show initial state
echo ""
echo -e "${BLUE}=== Initial USB State ===${NC}"
echo "Current USB controllers:"
lspci | grep -i usb | while read line; do
    pci_id=$(echo "$line" | cut -d' ' -f1)
    controller_info=$(echo "$line" | cut -d':' -f2- | sed 's/^ *//')
    echo -e "  ${PURPLE}$pci_id${NC}: $controller_info"
done

echo ""
echo -e "${BLUE}=== Current cameras detected ===${NC}"
camera_count=0
for cam in /dev/video*; do
    if [[ -e "$cam" ]]; then
        camera_count=$((camera_count + 1))
        echo "  Found: $cam"
    fi
done

if [[ $camera_count -eq 0 ]]; then
    echo "  No cameras currently detected (good!)"
fi

echo ""
echo -e "${YELLOW}PORT MAPPING PROCESS:${NC}"
echo ""

# Port mapping helper
ports_to_test=(
    "Rear panel - Top row leftmost USB-A port"
    "Rear panel - Top row rightmost USB-A port" 
    "Rear panel - Bottom row leftmost USB-A port"
    "Rear panel - Bottom row rightmost USB-A port"
    "Rear panel - USB-C port (if available)"
    "Front panel - USB-A port"
    "Front panel - USB-C port (if available)"
    "Case USB ports - Top of case"
    "Case USB ports - Front of case"
)

for i in "${!ports_to_test[@]}"; do
    port_desc="${ports_to_test[$i]}"
    
    echo -e "\n${GREEN}=== Testing Port $((i+1)): $port_desc ===${NC}"
    echo ""
    echo "📍 Plug ONE camera into: $port_desc"
    echo "   (If this port doesn't exist, skip it)"
    echo ""
    
    read -p "Press Enter after plugging camera (or 's' to skip): " skip
    
    if [[ "$skip" == "s" ]]; then
        echo "   Skipped."
        continue
    fi
    
    # Wait a moment for USB detection
    sleep 2
    
    # Check what appeared
    echo "   Scanning for new camera..."
    
    new_camera=""
    for cam in /dev/video*; do
        if [[ -e "$cam" ]]; then
            new_camera="$cam"
            break
        fi
    done
    
    if [[ -n "$new_camera" ]]; then
        # Get controller info
        path_info=$(udevadm info --query=all --name="$new_camera" | grep "ID_PATH=" | head -1)
        pci_device=$(echo "$path_info" | grep -o 'pci-[^-]*')
        bus_info=$(udevadm info --query=all --name="$new_camera" | grep "DEVPATH" | grep -o 'usb[0-9]*')
        
        echo -e "   ✅ Camera detected: ${YELLOW}$new_camera${NC}"
        echo -e "   📍 PCI Controller: ${PURPLE}$pci_device${NC}"
        echo -e "   📍 USB Bus: $bus_info"
        
        # Store this mapping
        echo "$port_desc -> $pci_device ($bus_info)" >> /tmp/usb_port_mapping.txt
        
    else
        echo "   ❌ No camera detected. Check connection or try a different port."
    fi
    
    echo ""
    echo "📤 Unplug the camera before testing the next port..."
    read -p "Press Enter after unplugging camera: "
    
    # Wait for disconnect
    sleep 1
done

echo ""
echo -e "${GREEN}=== PORT MAPPING SUMMARY ===${NC}"
if [[ -f /tmp/usb_port_mapping.txt ]]; then
    echo "Here's what we discovered:"
    echo ""
    cat /tmp/usb_port_mapping.txt | while read line; do
        echo "  $line"
    done
    
    echo ""
    echo -e "${YELLOW}RECOMMENDATIONS:${NC}"
    echo "1. Find TWO ports that map to DIFFERENT PCI controllers"
    echo "2. Connect Camera 1 to one controller"
    echo "3. Connect Camera 2 to the different controller"
    echo "4. Run the main topology analyzer to verify separation"
    
    # Clean up
    rm -f /tmp/usb_port_mapping.txt
else
    echo "No port mappings were recorded."
fi

echo ""
echo "🎯 Once you've identified separated ports, connect your cameras and run:"
echo "   ./usb_topology_analyzer.sh"