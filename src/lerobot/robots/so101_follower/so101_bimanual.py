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
from typing import Any

from lerobot.cameras import make_cameras_from_configs
from lerobot.robots.robot import Robot

from .config_so101_bimanual import SO101BimanualConfig
from .so101_follower import SO101Follower

logger = logging.getLogger(__name__)


class SO101Bimanual(Robot):
    config_class = SO101BimanualConfig
    name = "so101_bimanual"

    def __init__(self, config: SO101BimanualConfig):
        super().__init__(config)
        self.config = config

        # Create individual SO101 followers for left and right arms
        from .config_so101_follower import SO101FollowerConfig
        
        left_config = SO101FollowerConfig(
            port=config.left_port,
            id=f"{config.id}_left" if config.id else "left_arm",
            max_relative_target=config.max_relative_target,
            disable_torque_on_disconnect=config.disable_torque_on_disconnect,
        )
        
        right_config = SO101FollowerConfig(
            port=config.right_port,
            id=f"{config.id}_right" if config.id else "right_arm",
            max_relative_target=config.max_relative_target,
            disable_torque_on_disconnect=config.disable_torque_on_disconnect,
        )

        self.left_arm = SO101Follower(left_config)
        self.right_arm = SO101Follower(right_config)
        
        # Set up cameras
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def observation_features(self) -> dict[str, Any]:
        """Combine observation features from both arms and cameras."""
        features = {}
        
        # Add left arm features with prefix
        for key, feature in self.left_arm.observation_features.items():
            features[f"left_{key}"] = feature
            
        # Add right arm features with prefix
        for key, feature in self.right_arm.observation_features.items():
            features[f"right_{key}"] = feature
            
        # Add camera features
        for key, camera in self.cameras.items():
            features[key] = camera.features
            
        return features

    @property
    def action_features(self) -> dict[str, Any]:
        """Combine action features from both arms."""
        features = {}
        
        # Add left arm features with prefix
        for key, feature in self.left_arm.action_features.items():
            features[f"left_{key}"] = feature
            
        # Add right arm features with prefix
        for key, feature in self.right_arm.action_features.items():
            features[f"right_{key}"] = feature
            
        return features

    def connect(self, calibrate: bool = True) -> None:
        """Connect both arms and cameras."""
        self.left_arm.connect(calibrate=calibrate)
        self.right_arm.connect(calibrate=calibrate)
        
        for camera in self.cameras.values():
            camera.connect()

    def configure(self) -> None:
        """Configure both arms."""
        self.left_arm.configure()
        self.right_arm.configure()

    def calibrate(self) -> None:
        """Calibrate both arms sequentially."""
        logger.info("Calibrating left arm...")
        self.left_arm.calibrate()
        
        logger.info("Calibrating right arm...")
        self.right_arm.calibrate()

    def get_observation(self) -> dict[str, Any]:
        """Get observations from both arms and all cameras."""
        obs = {}
        
        # Get left arm observation with prefix
        left_obs = self.left_arm.get_observation()
        for key, value in left_obs.items():
            obs[f"left_{key}"] = value
            
        # Get right arm observation with prefix
        right_obs = self.right_arm.get_observation()
        for key, value in right_obs.items():
            obs[f"right_{key}"] = value
            
        # Get camera observations
        for key, camera in self.cameras.items():
            obs[key] = camera.read()
            
        return obs

    def send_action(self, action: dict[str, float]) -> dict[str, float]:
        """Send actions to both arms."""
        # Separate left and right actions
        left_action = {}
        right_action = {}
        
        for key, value in action.items():
            if key.startswith("left_"):
                left_action[key[5:]] = value  # Remove "left_" prefix
            elif key.startswith("right_"):
                right_action[key[6:]] = value  # Remove "right_" prefix
                
        # Send actions to respective arms
        sent_action = {}
        
        if left_action:
            left_sent = self.left_arm.send_action(left_action)
            for key, value in left_sent.items():
                sent_action[f"left_{key}"] = value
                
        if right_action:
            right_sent = self.right_arm.send_action(right_action)
            for key, value in right_sent.items():
                sent_action[f"right_{key}"] = value
                
        return sent_action

    def disconnect(self) -> None:
        """Disconnect both arms and cameras."""
        self.left_arm.disconnect()
        self.right_arm.disconnect()
        
        for camera in self.cameras.values():
            camera.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if both arms are connected."""
        return self.left_arm.is_connected and self.right_arm.is_connected
