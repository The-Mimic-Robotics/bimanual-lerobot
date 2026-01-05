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

"""Unit tests for BiLeKiwi robot (bimanual arms + mobile base)."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _make_bus_mock(motors: dict) -> MagicMock:
    """Return a bus mock with the given motors."""
    bus = MagicMock(name="FeetechBusMock")
    bus.is_connected = False
    bus.motors = motors
    bus.is_calibrated = True
    
    def _connect():
        bus.is_connected = True
    
    def _disconnect(_disable=True):
        bus.is_connected = False
    
    bus.connect.side_effect = _connect
    bus.disconnect.side_effect = _disconnect
    
    @contextmanager
    def _dummy_cm():
        yield
    
    bus.torque_disabled.side_effect = _dummy_cm
    
    # Mock sync_read to return incrementing values
    def _sync_read(register, motor_names):
        if register == "Present_Position":
            return {name: idx * 10.0 for idx, name in enumerate(motor_names, 1)}
        elif register == "Present_Velocity":
            return {name: idx * 5 for idx, name in enumerate(motor_names, 1)}
        return {}
    
    bus.sync_read.side_effect = _sync_read
    bus.sync_write.return_value = None
    bus.write.return_value = None
    bus.disable_torque.return_value = None
    bus.enable_torque.return_value = None
    
    return bus


def _make_camera_mock(name: str) -> MagicMock:
    """Return a camera mock."""
    cam = MagicMock(name=f"CameraMock_{name}")
    cam.is_connected = False
    
    def _connect(warmup=True):
        cam.is_connected = True
    
    def _disconnect():
        cam.is_connected = False
    
    cam.connect.side_effect = _connect
    cam.disconnect.side_effect = _disconnect
    cam.async_read.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
    
    return cam


@pytest.fixture
def bi_lekiwi():
    """Create a BiLeKiwi robot with mocked hardware."""
    from lerobot.robots.bi_lekiwi import BiLeKiwi, BiLeKiwiConfig
    
    left_motors = {
        "left_shoulder_pan": MagicMock(id=1),
        "left_shoulder_lift": MagicMock(id=2),
        "left_elbow_flex": MagicMock(id=3),
        "left_wrist_flex": MagicMock(id=4),
        "left_wrist_roll": MagicMock(id=5),
        "left_gripper": MagicMock(id=6),
    }
    right_motors = {
        "right_shoulder_pan": MagicMock(id=1),
        "right_shoulder_lift": MagicMock(id=2),
        "right_elbow_flex": MagicMock(id=3),
        "right_wrist_flex": MagicMock(id=4),
        "right_wrist_roll": MagicMock(id=5),
        "right_gripper": MagicMock(id=6),
    }
    base_motors = {
        "base_left_wheel": MagicMock(id=7),
        "base_back_wheel": MagicMock(id=8),
        "base_right_wheel": MagicMock(id=9),
    }
    
    left_bus = _make_bus_mock(left_motors)
    right_bus = _make_bus_mock(right_motors)
    base_bus = _make_bus_mock(base_motors)
    
    # Mock camera creation
    cameras = {
        "front": _make_camera_mock("front"),
        "left_wrist": _make_camera_mock("left_wrist"),
        "right_wrist": _make_camera_mock("right_wrist"),
    }
    
    def _make_bus_side_effect(port, motors, calibration=None):
        if "left" in str(motors).lower() and "shoulder" in str(motors).lower():
            left_bus.motors = motors
            return left_bus
        elif "right" in str(motors).lower() and "shoulder" in str(motors).lower():
            right_bus.motors = motors
            return right_bus
        else:
            base_bus.motors = motors
            return base_bus
    
    def _make_cameras_side_effect(config):
        return cameras
    
    with (
        patch(
            "lerobot.robots.bi_lekiwi.bi_lekiwi.FeetechMotorsBus",
            side_effect=_make_bus_side_effect,
        ),
        patch(
            "lerobot.robots.bi_lekiwi.bi_lekiwi.make_cameras_from_configs",
            side_effect=_make_cameras_side_effect,
        ),
        patch.object(BiLeKiwi, "configure", lambda self: None),
        patch.object(BiLeKiwi, "_init_cameras", lambda self: setattr(self, "cameras", cameras) or setattr(self, "failed_cameras", [])),
    ):
        cfg = BiLeKiwiConfig(
            left_arm_port="/dev/null",
            right_arm_port="/dev/null",
            base_port="/dev/null",
            cameras={},  # Empty - we'll inject mocks
        )
        robot = BiLeKiwi(cfg)
        robot.left_bus = left_bus
        robot.right_bus = right_bus
        robot.base_bus = base_bus
        robot.cameras = cameras
        robot.failed_cameras = []
        
        yield robot
        
        if robot.is_connected:
            robot.disconnect()


class TestBiLeKiwiConfig:
    """Test BiLeKiwi configuration."""
    
    def test_config_registration(self):
        """Test that BiLeKiwi config is properly registered."""
        from lerobot.robots import RobotConfig
        
        assert "bi_lekiwi" in RobotConfig._subclasses
    
    def test_default_config(self):
        """Test default configuration values."""
        from lerobot.robots.bi_lekiwi import BiLeKiwiConfig
        
        config = BiLeKiwiConfig(
            left_arm_port="/dev/ttyACM0",
            right_arm_port="/dev/ttyACM1",
            base_port="/dev/ttyACM2",
        )
        
        assert config.left_arm_use_degrees is True
        assert config.right_arm_use_degrees is True
        assert config.camera_max_connect_attempts == 3
        assert config.camera_allow_degraded_mode is True


class TestBiLeKiwiRobot:
    """Test BiLeKiwi robot functionality."""
    
    def test_action_features_15_dof(self, bi_lekiwi):
        """Test that action features have exactly 15 DOF."""
        features = bi_lekiwi.action_features
        
        # 6 left arm + 6 right arm + 3 base = 15 DOF
        assert len(features) == 15
        
        # Check arm joints are present
        assert "left_shoulder_pan.pos" in features
        assert "left_gripper.pos" in features
        assert "right_shoulder_pan.pos" in features
        assert "right_gripper.pos" in features
        
        # Check base velocities are present
        assert "x.vel" in features
        assert "y.vel" in features
        assert "theta.vel" in features
    
    def test_observation_features(self, bi_lekiwi):
        """Test observation features include state and cameras."""
        features = bi_lekiwi.observation_features
        
        # Should have 15 DOF state + cameras
        assert len(features) >= 15
        
        # Check camera features
        assert "front" in features
        assert "left_wrist" in features
        assert "right_wrist" in features
    
    def test_connect_disconnect(self, bi_lekiwi):
        """Test connection lifecycle."""
        assert not bi_lekiwi.is_connected
        
        bi_lekiwi.connect()
        assert bi_lekiwi.is_connected
        
        bi_lekiwi.disconnect()
        assert not bi_lekiwi.is_connected
    
    def test_get_observation(self, bi_lekiwi):
        """Test getting observation from robot."""
        bi_lekiwi.connect()
        obs = bi_lekiwi.get_observation()
        
        # Check arm positions
        assert "left_shoulder_pan.pos" in obs
        assert "right_gripper.pos" in obs
        
        # Check base velocities
        assert "x.vel" in obs
        assert "y.vel" in obs
        assert "theta.vel" in obs
        
        # Check camera images
        assert "front" in obs
        assert obs["front"].shape == (480, 640, 3)
    
    def test_send_action(self, bi_lekiwi):
        """Test sending action to robot."""
        bi_lekiwi.connect()
        
        action = {
            # Left arm
            "left_shoulder_pan.pos": 10.0,
            "left_shoulder_lift.pos": 20.0,
            "left_elbow_flex.pos": 30.0,
            "left_wrist_flex.pos": 40.0,
            "left_wrist_roll.pos": 50.0,
            "left_gripper.pos": 60.0,
            # Right arm
            "right_shoulder_pan.pos": 10.0,
            "right_shoulder_lift.pos": 20.0,
            "right_elbow_flex.pos": 30.0,
            "right_wrist_flex.pos": 40.0,
            "right_wrist_roll.pos": 50.0,
            "right_gripper.pos": 60.0,
            # Base
            "x.vel": 0.1,
            "y.vel": 0.0,
            "theta.vel": 10.0,
        }
        
        returned = bi_lekiwi.send_action(action)
        
        # All actions should be returned
        assert len(returned) == 15
        assert returned["left_shoulder_pan.pos"] == 10.0
        assert returned["x.vel"] == 0.1


class TestBiLeKiwiKinematics:
    """Test mobile base kinematics."""
    
    def test_body_to_wheel_conversion(self, bi_lekiwi):
        """Test body velocity to wheel speed conversion."""
        # Pure forward motion
        wheel_speeds = bi_lekiwi._body_to_wheel_raw(x=0.1, y=0.0, theta=0.0)
        
        assert "base_left_wheel" in wheel_speeds
        assert "base_back_wheel" in wheel_speeds
        assert "base_right_wheel" in wheel_speeds
        
        # All non-zero for forward motion (due to omniwheel geometry)
        assert all(v != 0 for v in wheel_speeds.values())
    
    def test_wheel_to_body_conversion(self, bi_lekiwi):
        """Test wheel speed to body velocity conversion."""
        body_vel = bi_lekiwi._wheel_raw_to_body(
            left_wheel_speed=100,
            back_wheel_speed=100,
            right_wheel_speed=100,
        )
        
        assert "x.vel" in body_vel
        assert "y.vel" in body_vel
        assert "theta.vel" in body_vel
    
    def test_kinematics_roundtrip(self, bi_lekiwi):
        """Test that kinematics round-trip approximately preserves values."""
        original = {"x": 0.1, "y": 0.05, "theta": 5.0}
        
        # Body -> Wheel -> Body
        wheel = bi_lekiwi._body_to_wheel_raw(
            x=original["x"], y=original["y"], theta=original["theta"]
        )
        recovered = bi_lekiwi._wheel_raw_to_body(
            wheel["base_left_wheel"],
            wheel["base_back_wheel"],
            wheel["base_right_wheel"],
        )
        
        # Should be approximately equal (within numerical precision)
        assert abs(recovered["x.vel"] - original["x"]) < 0.01
        assert abs(recovered["y.vel"] - original["y"]) < 0.01
        assert abs(recovered["theta.vel"] - original["theta"]) < 0.5
