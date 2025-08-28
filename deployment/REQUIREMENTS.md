# BiManual Robot System Requirements

## Hardware Requirements

### Motors
- 4x Feetech servo motors (SO101 compatible)
- USB-to-serial adapters (typically built into motor controllers)
- Expected device paths: `/dev/ttyACM0`, `/dev/ttyACM1`, `/dev/ttyACM2`, `/dev/ttyACM3`

### Cameras
- 2x USB cameras (Centerm or compatible)
- Resolution: 640x480 minimum
- Frame rate: 30fps
- USB 2.0 or higher

### Computer
- Ubuntu 20.04+ (recommended) or compatible Linux
- 4+ USB ports (USB hub acceptable)
- 8GB RAM minimum (16GB recommended)
- Python 3.8+

## Software Dependencies

### System Packages (Ubuntu/Debian)
```bash
sudo apt-get install -y \
    python3-pip python3-venv python3-dev \
    build-essential cmake pkg-config \
    libjpeg-dev libpng-dev libtiff-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev \
    libgtk-3-dev libatlas-base-dev gfortran \
    v4l-utils udev
```

### Python Packages
Automatically installed by setup script:
- opencv-python
- numpy
- pyserial
- And other dependencies from requirements.txt

## Network Requirements
None - system operates locally

## Permissions
- User must be in `dialout` group for USB serial access
- Automatically configured by setup script

## Storage
- ~500MB for software installation
- ~50MB for calibration data
- Additional space for recorded data/logs
