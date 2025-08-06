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

import logging
from functools import cached_property
from typing import Any

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from ..robot import Robot
from ..so101_follower import SO101Follower, SO101FollowerConfig
from .config_bi_so101_follower import BiSO101FollowerConfig

logger = logging.getLogger(__name__)


class BiSO101Follower(Robot):
    """
    [Bimanual SO-101 Follower Arms](https://github.com/TheRobotStudio/SO-ARM100) designed by TheRobotStudio and Hugging Face
    This bimanual robot uses two SO-101 follower arms with STS3215 servos for bimanual manipulation tasks.
    """

    config_class = BiSO101FollowerConfig
    name = "bi_so101_follower"

    def __init__(self, config: BiSO101FollowerConfig):
        super().__init__(config)
        self.config = config

        left_arm_config = SO101FollowerConfig(
            id=f"{config.id}_left" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=config.left_arm_port,
            disable_torque_on_disconnect=config.left_arm_disable_torque_on_disconnect,
            max_relative_target=config.left_arm_max_relative_target,
            use_degrees=config.left_arm_use_degrees,
            cameras={},
        )

        right_arm_config = SO101FollowerConfig(
            id=f"{config.id}_right" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=config.right_arm_port,
            disable_torque_on_disconnect=config.right_arm_disable_torque_on_disconnect,
            max_relative_target=config.right_arm_max_relative_target,
            use_degrees=config.right_arm_use_degrees,
            cameras={},
        )

        self.left_arm = SO101Follower(left_arm_config)
        self.right_arm = SO101Follower(right_arm_config)
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        return {f"left_{motor}.pos": float for motor in self.left_arm.bus.motors} | {
            f"right_{motor}.pos": float for motor in self.right_arm.bus.motors
        }

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return (
            self.left_arm.bus.is_connected
            and self.right_arm.bus.is_connected
            and all(cam.is_connected for cam in self.cameras.values())
        )

    def connect(self, calibrate: bool = True) -> None:
        self.left_arm.connect(calibrate)
        self.right_arm.connect(calibrate)

        for cam in self.cameras.values():
            cam.connect()

    @property
    def is_calibrated(self) -> bool:
        return self.left_arm.is_calibrated and self.right_arm.is_calibrated

    def calibrate(self) -> None:
        self.left_arm.calibrate()
        self.right_arm.calibrate()

    def configure(self) -> None:
        self.left_arm.configure()
        self.right_arm.configure()

    def setup_motors(self) -> None:
        self.left_arm.setup_motors()
        self.right_arm.setup_motors()

    def get_observation(self) -> dict[str, Any]:
        left_observation = self.left_arm.get_observation()
        right_observation = self.right_arm.get_observation()

        # Prefix motor states with "left_" and "right_"
        observation = {}
        for key, value in left_observation.items():
            if key.endswith(".pos"):
                observation[f"left_{key}"] = value

        for key, value in right_observation.items():
            if key.endswith(".pos"):
                observation[f"right_{key}"] = value

        # Add camera observations
        for cam_name, cam in self.cameras.items():
            observation[f"observation.images.{cam_name}"] = cam.async_read()

        return observation

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        # Separate left and right arm actions
        left_action = {
            key.removeprefix("left_"): value for key, value in action.items() if key.startswith("left_")
        }
        right_action = {
            key.removeprefix("right_"): value for key, value in action.items() if key.startswith("right_")
        }

        sent_action = {}

        # Send actions to both arms
        if left_action:
            sent_left_action = self.left_arm.send_action(left_action)
            for key, value in sent_left_action.items():
                sent_action[f"left_{key}"] = value

        if right_action:
            sent_right_action = self.right_arm.send_action(right_action)
            for key, value in sent_right_action.items():
                sent_action[f"right_{key}"] = value

        return sent_action

    def disconnect(self):
        if self.config.left_arm_disable_torque_on_disconnect:
            self.left_arm.bus.disable_torque()
        if self.config.right_arm_disable_torque_on_disconnect:
            self.right_arm.bus.disable_torque()

        self.left_arm.disconnect()
        self.right_arm.disconnect()

        for cam in self.cameras.values():
            cam.disconnect()

        logger.info(f"{self} disconnected.")
