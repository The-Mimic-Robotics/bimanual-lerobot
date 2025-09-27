# BiManual Robot Deployment Guide

This directory contains everything needed to deploy the bimanual SO101 robot system to a new computer.

## Quick Start (New Computer)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd bimanual-lerobot/deployment
   ```

2. **Run the automated setup:**
   ```bash
   ./setup_bimanual_robot.sh
   ```
   
3. **Restart terminal or reload bash:**
   ```bash
   source ~/.bashrc
   ```

4. **Test the installation:**
   ```bash
   ./test_installation.sh
   ```

5. **Connect hardware:**
   - 4 servo motors → USB ports (will appear as `/dev/ttyACM0-3`)
   - 2 cameras → USB ports

6. **Start the robot:**
   ```bash
   ./start_bimanual_robot.sh
   ```

## What's Included

### Calibration Files
- Pre-calibrated motor configurations for follower and leader arms
- Stored in `deployment/calibration/`
- Automatically copied to `~/.cache/huggingface/lerobot/calibration/`

### Scripts
- `setup_bimanual_robot.sh` - Complete system setup with conda
- `start_bimanual_robot.sh` - Start teleoperation (created during setup)
- `calibrate_bimanual_robot.sh` - Recalibration if needed (created during setup)
- `test_installation.sh` - Verify installation works (created during setup)
- `activate_lerobot.sh` - Helper to activate conda environment (created during setup)

### Hardware Detection
- Camera diagnostic tools
- USB device port mapping
- Stable device naming via udev rules

## Hardware Setup

### Motors (Expected Ports)
- Left Leader: `/dev/ttyACM0`
- Right Leader: `/dev/ttyACM1` 
- Left Follower: `/dev/ttyACM2`
- Right Follower: `/dev/ttyACM3`

### Cameras
- The system will auto-detect working cameras
- Uses stable USB path naming when possible
- Falls back to index-based detection

## Troubleshooting

### Test Installation
```bash
./test_installation.sh
```

### Activate Environment Manually
```bash
source activate_lerobot.sh
# or
conda activate lerobot
```

### Check Hardware
```bash
# Activate environment first
conda activate lerobot

# Camera diagnostic
python -m lerobot.scripts.camera_diagnostic

# List USB serial devices
ls /dev/ttyACM*

# List video devices
v4l2-ctl --list-devices
```

### Permission Issues
```bash
# Add user to dialout group (then logout/login)
sudo usermod -a -G dialout $USER

# Check current groups
groups
```

### Recalibration
If motors behave incorrectly, run:
```bash
./calibrate_bimanual_robot.sh
```

### Camera Issues
- Unplug/replug cameras if they don't work
- Try different USB ports
- Run camera diagnostic to identify working cameras

## Customization

### Port Configuration
Edit the port assignments in:
- `start_bimanual_robot.sh`
- `calibrate_bimanual_robot.sh`

### Camera Configuration
Modify camera settings in:
- `src/lerobot/robots/bi_so101_follower/config_bi_so101_follower.py`

## System Requirements

### Ubuntu/Debian (Recommended)
- Ubuntu 20.04+ or Debian 11+
- Python 3.8+
- USB ports for 4 motors + 2 cameras

### Hardware
- 4x Feetech servo motors
- 2x USB cameras (Centerm or compatible)
- USB hub if needed

## Files Structure

```
deployment/
├── calibration/           # Pre-configured calibration files
│   ├── robots/           # Follower arm calibrations
│   └── teleoperators/    # Leader arm calibrations
├── scripts/              # Utility scripts
├── setup_bimanual_robot.sh  # Main setup script
└── README.md             # This file
```

## Support

If you encounter issues:

1. Check hardware connections
2. Run diagnostic scripts
3. Verify USB permissions
4. Check calibration files exist
5. Try recalibration if needed
