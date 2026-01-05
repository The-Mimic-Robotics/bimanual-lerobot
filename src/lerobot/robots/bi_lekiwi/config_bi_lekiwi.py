#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team and Mimic Robotics. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig
from lerobot.cameras.configs import Cv2Rotation
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig

from ..config import RobotConfig


def bi_lekiwi_cameras_config() -> dict[str, CameraConfig]:
    """Default camera configuration for BiLeKiwi robot.
    
    - 2 RealSense cameras for external context (left/right views)
    - 2 wrist-mounted cameras (left/right arm)
    - 1 front camera on mobile base
    """
    return {
        # External context cameras (Intel RealSense)
        "realsense_left": RealSenseCameraConfig(
            serial_number_or_name=None,  # Configure with your serial number
            width=640,
            height=480,
            fps=30,
        ),
        "realsense_right": RealSenseCameraConfig(
            serial_number_or_name=None,  # Configure with your serial number
            width=640,
            height=480,
            fps=30,
        ),
        # Wrist cameras (USB/OpenCV)
        "left_wrist": OpenCVCameraConfig(
            index_or_path="/dev/video0",
            width=640,
            height=480,
            fps=30,
        ),
        "right_wrist": OpenCVCameraConfig(
            index_or_path="/dev/video2",
            width=640,
            height=480,
            fps=30,
        ),
        # Front camera on base
        "front": OpenCVCameraConfig(
            index_or_path="/dev/video4",
            width=640,
            height=480,
            fps=30,
            rotation=Cv2Rotation.ROTATE_180,
        ),
    }


@RobotConfig.register_subclass("bi_lekiwi")
@dataclass
class BiLeKiwiConfig(RobotConfig):
    """Configuration for BiLeKiwi: bimanual SO-101 arms with omniwheel mobile base.
    
    This robot combines:
    - Two SO-101 follower arms (12 DOF: 6 joints each)
    - Three omniwheel mobile base (3 DOF: x, y, theta velocities)
    
    Total action space: 15 DOF
    """
    
    # Arm ports (required)
    left_arm_port: str = "/dev/ttyACM0"
    right_arm_port: str = "/dev/ttyACM1"
    
    # Base port (same bus as one arm, or separate)
    base_port: str = "/dev/ttyACM2"
    
    # Arm configuration
    left_arm_disable_torque_on_disconnect: bool = True
    left_arm_max_relative_target: int | None = None
    left_arm_use_degrees: bool = True
    
    right_arm_disable_torque_on_disconnect: bool = True
    right_arm_max_relative_target: int | None = None
    right_arm_use_degrees: bool = True
    
    # Base configuration
    base_disable_torque_on_disconnect: bool = True
    base_use_degrees: bool = False
    
    # Camera configuration
    cameras: dict[str, CameraConfig] = field(default_factory=bi_lekiwi_cameras_config)
    
    # Camera retry configuration for hardened handling
    camera_max_connect_attempts: int = 3
    camera_connect_retry_delay_s: float = 1.0
    camera_allow_degraded_mode: bool = True  # Continue with available cameras if some fail


@dataclass
class BiLeKiwiHostConfig:
    """Configuration for running BiLeKiwi as a remote host (robot side)."""
    
    # Network Configuration
    port_zmq_cmd: int = 5555
    port_zmq_observations: int = 5556
    
    # Duration and watchdog
    connection_time_s: int = 30
    watchdog_timeout_ms: int = 500
    max_loop_freq_hz: int = 30


@RobotConfig.register_subclass("bi_lekiwi_client")
@dataclass
class BiLeKiwiClientConfig(RobotConfig):
    """Configuration for BiLeKiwi remote client (laptop/operator side)."""
    
    # Network Configuration
    remote_ip: str = "192.168.1.100"  # Robot's IP address
    port_zmq_cmd: int = 5555
    port_zmq_observations: int = 5556
    
    # Keyboard teleoperation keys for mobile base
    teleop_keys: dict[str, str] = field(
        default_factory=lambda: {
            # Base movement
            "forward": "w",
            "backward": "s",
            "left": "a",
            "right": "d",
            "rotate_left": "z",
            "rotate_right": "x",
            # Speed control
            "speed_up": "r",
            "speed_down": "f",
            # Quit
            "quit": "q",
        }
    )
    
    cameras: dict[str, CameraConfig] = field(default_factory=bi_lekiwi_cameras_config)
    polling_timeout_ms: int = 15
    connect_timeout_s: int = 5
