# BiLeKiwi Teleoperation Guide

Teleoperate bimanual SO-101 arms + mecanum mobile base simultaneously.

## Hardware Setup

### Required Ports
| Device | Default Port | Description |
|--------|--------------|-------------|
| Left Master Arm | `/dev/ttyACM0` | Leader arm (left) |
| Right Master Arm | `/dev/ttyACM1` | Leader arm (right) |
| Left Follower Arm | `/dev/ttyACM2` | Slave arm (left) |
| Right Follower Arm | `/dev/ttyACM3` | Slave arm (right) |
| Mecanum Base (ESP32) | `/dev/ttyUSB0` | Base controller |

### USB Device Discovery
```bash
# List all connected USB devices
ls /dev/ttyACM* /dev/ttyUSB*

# Find device by port info
udevadm info -a -n /dev/ttyACM0 | grep serial
```

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/Nicholas/ai/bimanual-lerobot

# Activate environment
source activate_lerobot.sh

# Install lerobot (if not already)
pip install -e .

# Install teleop dependencies
pip install pynput pyserial
```

### 2. Flash Mecanum Base (if needed)
```bash
cd maccanum-base
pio run --target upload
```

### 3. Run Teleoperation
```bash
python scripts/teleop_bi_lekiwi.py \
    --left-master-port /dev/ttyACM0 \
    --right-master-port /dev/ttyACM1 \
    --left-follower-port /dev/ttyACM2 \
    --right-follower-port /dev/ttyACM3 \
    --base-serial-port /dev/ttyUSB0
```

## Controls

### Arm Control
Move master/leader arms → Slave/follower arms mirror movements

### Base Control (Keyboard)
| Key | Action |
|-----|--------|
| **W** | Forward |
| **S** | Backward |
| **A** | Strafe left |
| **D** | Strafe right |
| **Q** | Rotate CCW |
| **E** | Rotate CW |
| **X** | Emergency stop |
| **+/-** | Speed up/down |
| **ESC** | Quit |

## ROS2 Integration (Optional)

If you have ROS2, the mecanum base publishes odometry:

```bash
# Terminal 1: Run base bridge
python maccanum-base/examples/mecanum_bridge_node.py

# Terminal 2: Run teleop (base commands go via bridge)
python scripts/teleop_bi_lekiwi.py

# Terminal 3: View in RViz
rviz2
```

The bridge publishes:
- `/odom` - Odometry messages
- `/tf` - Transform `odom` → `base_link`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied on ports | `sudo chmod 666 /dev/ttyACM*` or add user to dialout group |
| Arms not responding | Check calibration, run `python -m lerobot.calibrate` |
| Base not moving | Check ESP32 serial connection, verify baudrate 115200 |
| Keyboard not detected | Run with display, install pynput |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    teleop_bi_lekiwi.py                      │
├─────────────────────────────────────────────────────────────┤
│  BiSO101Leader (Master Arms)                                │
│  ├── Left Master (/dev/ttyACM0)                             │
│  └── Right Master (/dev/ttyACM1)                            │
│         │                                                   │
│         ▼ get_action() → 12 DOF joint positions            │
│                                                             │
│  BiSO101Follower (Slave Arms)                               │
│  ├── Left Follower (/dev/ttyACM2)                           │
│  └── Right Follower (/dev/ttyACM3)                          │
│         │                                                   │
│         ▼ send_action() → Mirror master movements          │
│                                                             │
│  MecanumBaseController (ESP32)                              │
│  └── Serial (/dev/ttyUSB0)                                  │
│         │                                                   │
│         ▼ TWIST,vx,vy,omega → 3 DOF velocities             │
└─────────────────────────────────────────────────────────────┘
```
