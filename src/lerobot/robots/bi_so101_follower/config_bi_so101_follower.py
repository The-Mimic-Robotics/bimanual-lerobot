#!/usr/bin/env python

# Copyright 2025 The HuggingFace Inc. team. All rights reserved.
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
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig

from ..config import RobotConfig


@RobotConfig.register_subclass("bi_so101_follower")
@dataclass
class BiSO101FollowerConfig(RobotConfig):
    left_arm_port: str
    right_arm_port: str

    # Optional
    left_arm_disable_torque_on_disconnect: bool = True
    left_arm_max_relative_target: int | None = None
    left_arm_use_degrees: bool = False
    right_arm_disable_torque_on_disconnect: bool = True
    right_arm_max_relative_target: int | None = None
    right_arm_use_degrees: bool = False

    # Default camera configuration for bimanual setup:
    # 2 Intel RealSense cameras for context (external)
    # 2 OpenCV cameras mounted on the robot
    cameras: dict[str, CameraConfig] = field(default_factory=lambda: {
        "realsense_left": RealSenseCameraConfig(
            serial_number=None,  # Set your left RealSense serial number
            width=640,
            height=480,
            fps=30,
        ),
        "realsense_right": RealSenseCameraConfig(
            serial_number=None,  # Set your right RealSense serial number
            width=640,
            height=480,
            fps=30,
        ),
        "robot_left": OpenCVCameraConfig(
            index_or_path=0,  # Set your left robot camera index/path
            width=640,
            height=480,
            fps=30,
        ),
        "robot_right": OpenCVCameraConfig(
            index_or_path=1,  # Set your right robot camera index/path
            width=640,
            height=480,
            fps=30,
        ),
    })
