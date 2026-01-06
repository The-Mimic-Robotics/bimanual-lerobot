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

"""BiLeKiwi: Bimanual SO-101 arms with omniwheel mobile base.

This robot combines:
- Two SO-101 follower arms (12 DOF: 6 joints each for 5-axis motion + gripper)
- Three omniwheel mobile base (3 DOF: x, y, theta velocities)

Total action space: 15 DOF

Example usage:
    from lerobot.robots.bi_lekiwi import BiLeKiwi, BiLeKiwiConfig
    
    config = BiLeKiwiConfig(
        left_arm_port="/dev/ttyACM0",
        right_arm_port="/dev/ttyACM1",
        base_port="/dev/ttyACM2",
    )
    robot = BiLeKiwi(config)
    robot.connect()
    
    # Get observation (15 DOF state + camera images)
    obs = robot.get_observation()
    
    # Send action (15 DOF: 12 arm positions + 3 base velocities)
    action = {
        "left_shoulder_pan.pos": 0.0,
        "left_shoulder_lift.pos": 0.0,
        # ... other arm joints ...
        "x.vel": 0.1,  # m/s forward
        "y.vel": 0.0,  # m/s lateral
        "theta.vel": 0.0,  # deg/s rotation
    }
    robot.send_action(action)
"""

import logging
import time
from functools import cached_property
from typing import Any

import numpy as np

from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError
from lerobot.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus, OperatingMode

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_bi_lekiwi import BiLeKiwiConfig

logger = logging.getLogger(__name__)


# Motor definitions for SO-101 arms
LEFT_ARM_MOTORS = {
    "left_shoulder_pan": Motor(1, "sts3215", MotorNormMode.DEGREES),
    "left_shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
    "left_elbow_flex": Motor(3, "sts3215", MotorNormMode.DEGREES),
    "left_wrist_flex": Motor(4, "sts3215", MotorNormMode.DEGREES),
    "left_wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
    "left_gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}

RIGHT_ARM_MOTORS = {
    "right_shoulder_pan": Motor(1, "sts3215", MotorNormMode.DEGREES),
    "right_shoulder_lift": Motor(2, "sts3215", MotorNormMode.DEGREES),
    "right_elbow_flex": Motor(3, "sts3215", MotorNormMode.DEGREES),
    "right_wrist_flex": Motor(4, "sts3215", MotorNormMode.DEGREES),
    "right_wrist_roll": Motor(5, "sts3215", MotorNormMode.DEGREES),
    "right_gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}

BASE_MOTORS = {
    "base_left_wheel": Motor(7, "sts3215", MotorNormMode.RANGE_M100_100),
    "base_back_wheel": Motor(8, "sts3215", MotorNormMode.RANGE_M100_100),
    "base_right_wheel": Motor(9, "sts3215", MotorNormMode.RANGE_M100_100),
}


class BiLeKiwi(Robot):
    """Bimanual SO-101 arms with omniwheel mobile base.
    
    This robot provides a unified interface for controlling:
    - Two SO-101 follower arms (12 DOF positions)
    - Three omniwheel mobile base (3 DOF velocities)
    
    The action space is 15 DOF total:
    - 12 arm joint positions (6 per arm)
    - 3 base velocities (x, y, theta)
    """
    
    config_class = BiLeKiwiConfig
    name = "bi_lekiwi"
    
    def __init__(self, config: BiLeKiwiConfig):
        super().__init__(config)
        self.config = config
        
        # Create motor norm modes based on config
        norm_mode_left = MotorNormMode.DEGREES if config.left_arm_use_degrees else MotorNormMode.RANGE_M100_100
        norm_mode_right = MotorNormMode.DEGREES if config.right_arm_use_degrees else MotorNormMode.RANGE_M100_100
        
        # Left arm motor bus
        self.left_bus = FeetechMotorsBus(
            port=config.left_arm_port,
            motors={
                "left_shoulder_pan": Motor(1, "sts3215", norm_mode_left),
                "left_shoulder_lift": Motor(2, "sts3215", norm_mode_left),
                "left_elbow_flex": Motor(3, "sts3215", norm_mode_left),
                "left_wrist_flex": Motor(4, "sts3215", norm_mode_left),
                "left_wrist_roll": Motor(5, "sts3215", norm_mode_left),
                "left_gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
            },
            calibration=self._get_calibration("left"),
        )
        
        # Right arm motor bus
        self.right_bus = FeetechMotorsBus(
            port=config.right_arm_port,
            motors={
                "right_shoulder_pan": Motor(1, "sts3215", norm_mode_right),
                "right_shoulder_lift": Motor(2, "sts3215", norm_mode_right),
                "right_elbow_flex": Motor(3, "sts3215", norm_mode_right),
                "right_wrist_flex": Motor(4, "sts3215", norm_mode_right),
                "right_wrist_roll": Motor(5, "sts3215", norm_mode_right),
                "right_gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
            },
            calibration=self._get_calibration("right"),
        )
        
        # Base motor bus
        self.base_bus = FeetechMotorsBus(
            port=config.base_port,
            motors={
                "base_left_wheel": Motor(7, "sts3215", MotorNormMode.RANGE_M100_100),
                "base_back_wheel": Motor(8, "sts3215", MotorNormMode.RANGE_M100_100),
                "base_right_wheel": Motor(9, "sts3215", MotorNormMode.RANGE_M100_100),
            },
            calibration=self._get_calibration("base"),
        )
        
        # Motor name lists for convenience
        self.left_arm_motors = list(self.left_bus.motors.keys())
        self.right_arm_motors = list(self.right_bus.motors.keys())
        self.base_motors = list(self.base_bus.motors.keys())
        
        # Initialize cameras with hardened handling
        self.cameras = {}
        self.failed_cameras = []
        self._init_cameras()
    
    def _get_calibration(self, arm_type: str) -> dict | None:
        """Get calibration for a specific arm/base from stored calibration."""
        if self.calibration is None:
            return None
        # Filter calibration entries for this arm type
        prefix = f"{arm_type}_" if arm_type != "base" else "base_"
        return {k: v for k, v in self.calibration.items() if k.startswith(prefix)}
    
    def _init_cameras(self) -> None:
        """Initialize cameras with retry logic and graceful degradation."""
        camera_configs = self.config.cameras
        
        for cam_name, cam_config in camera_configs.items():
            try:
                from lerobot.cameras.utils import make_camera_from_config
                camera = make_camera_from_config(cam_config)
                self.cameras[cam_name] = camera
            except Exception as e:
                logger.warning(f"Failed to initialize camera '{cam_name}': {e}")
                if not self.config.camera_allow_degraded_mode:
                    raise
                self.failed_cameras.append(cam_name)
        
        if self.failed_cameras:
            logger.warning(f"Running in degraded mode without cameras: {self.failed_cameras}")
    
    @property
    def _arm_state_ft(self) -> dict[str, type]:
        """State features for both arms (12 DOF)."""
        return {
            # Left arm (6 DOF)
            "left_shoulder_pan.pos": float,
            "left_shoulder_lift.pos": float,
            "left_elbow_flex.pos": float,
            "left_wrist_flex.pos": float,
            "left_wrist_roll.pos": float,
            "left_gripper.pos": float,
            # Right arm (6 DOF)
            "right_shoulder_pan.pos": float,
            "right_shoulder_lift.pos": float,
            "right_elbow_flex.pos": float,
            "right_wrist_flex.pos": float,
            "right_wrist_roll.pos": float,
            "right_gripper.pos": float,
        }
    
    @property
    def _base_state_ft(self) -> dict[str, type]:
        """State features for mobile base (3 DOF velocities)."""
        return {
            "x.vel": float,
            "y.vel": float,
            "theta.vel": float,
        }
    
    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        """Camera features (only for connected cameras)."""
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3)
            for cam in self.cameras
        }
    
    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        """Full observation features: 15 DOF state + cameras."""
        return {**self._arm_state_ft, **self._base_state_ft, **self._cameras_ft}
    
    @cached_property
    def action_features(self) -> dict[str, type]:
        """Full action features: 15 DOF (12 arm positions + 3 base velocities)."""
        return {**self._arm_state_ft, **self._base_state_ft}
    
    @property
    def is_connected(self) -> bool:
        """Check if all motor buses and cameras are connected."""
        buses_connected = (
            self.left_bus.is_connected
            and self.right_bus.is_connected
            and self.base_bus.is_connected
        )
        # Only check cameras that were successfully initialized
        cameras_connected = all(cam.is_connected for cam in self.cameras.values())
        return buses_connected and cameras_connected
    
    def connect(self, calibrate: bool = True) -> None:
        """Connect to all hardware components."""
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")
        
        # Connect motor buses
        logger.info("Connecting left arm...")
        self.left_bus.connect()
        
        logger.info("Connecting right arm...")
        self.right_bus.connect()
        
        logger.info("Connecting base...")
        self.base_bus.connect()
        
        # Calibrate if needed
        if calibrate:
            if not self.left_bus.is_calibrated:
                logger.info("Left arm needs calibration")
                self._calibrate_arm("left")
            if not self.right_bus.is_calibrated:
                logger.info("Right arm needs calibration")
                self._calibrate_arm("right")
            if not self.base_bus.is_calibrated:
                logger.info("Base needs calibration")
                self._calibrate_base()
        
        # Connect cameras with retry logic
        self._connect_cameras()
        
        # Configure motors
        self.configure()
        
        logger.info(f"{self} connected.")
    
    def _connect_cameras(self) -> None:
        """Connect cameras with retry logic."""
        for cam_name, cam in list(self.cameras.items()):
            connected = False
            for attempt in range(self.config.camera_max_connect_attempts):
                try:
                    cam.connect()
                    connected = True
                    logger.info(f"Camera '{cam_name}' connected on attempt {attempt + 1}")
                    break
                except Exception as e:
                    logger.warning(f"Camera '{cam_name}' connection attempt {attempt + 1} failed: {e}")
                    if attempt < self.config.camera_max_connect_attempts - 1:
                        time.sleep(self.config.camera_connect_retry_delay_s)
            
            if not connected:
                if self.config.camera_allow_degraded_mode:
                    logger.warning(f"Camera '{cam_name}' failed to connect. Continuing in degraded mode.")
                    self.failed_cameras.append(cam_name)
                    del self.cameras[cam_name]
                else:
                    raise DeviceNotConnectedError(f"Camera '{cam_name}' failed to connect after {self.config.camera_max_connect_attempts} attempts")
    
    @property
    def is_calibrated(self) -> bool:
        return self.left_bus.is_calibrated and self.right_bus.is_calibrated and self.base_bus.is_calibrated
    
    def calibrate(self) -> None:
        """Calibrate all components."""
        self._calibrate_arm("left")
        self._calibrate_arm("right")
        self._calibrate_base()
    
    def _calibrate_arm(self, side: str) -> None:
        """Calibrate a single arm."""
        bus = self.left_bus if side == "left" else self.right_bus
        motors = self.left_arm_motors if side == "left" else self.right_arm_motors
        
        bus.disable_torque(motors)
        for name in motors:
            bus.write("Operating_Mode", name, OperatingMode.POSITION.value)
        
        input(f"Move {side} arm to the middle of its range of motion and press ENTER...")
        homing_offsets = bus.set_half_turn_homings(motors)
        
        full_turn_motors = [m for m in motors if "wrist_roll" in m or "gripper" in m]
        unknown_range_motors = [m for m in motors if m not in full_turn_motors]
        
        print(f"Move all {side} arm joints except {full_turn_motors} through their full range.")
        print("Press ENTER when done...")
        range_mins, range_maxes = bus.record_ranges_of_motion(unknown_range_motors)
        
        for name in full_turn_motors:
            range_mins[name] = 0
            range_maxes[name] = 4095
        
        calibration = {}
        for name, motor in bus.motors.items():
            calibration[name] = MotorCalibration(
                id=motor.id,
                drive_mode=0,
                homing_offset=homing_offsets[name],
                range_min=range_mins[name],
                range_max=range_maxes[name],
            )
        
        bus.write_calibration(calibration)
        if self.calibration is None:
            self.calibration = {}
        self.calibration.update(calibration)
        self._save_calibration()
        logger.info(f"{side.capitalize()} arm calibration saved")
    
    def _calibrate_base(self) -> None:
        """Calibrate mobile base motors."""
        # Base motors don't need complex calibration - just set homing offsets to 0
        calibration = {}
        for name, motor in self.base_bus.motors.items():
            calibration[name] = MotorCalibration(
                id=motor.id,
                drive_mode=0,
                homing_offset=0,
                range_min=0,
                range_max=4095,
            )
        
        self.base_bus.write_calibration(calibration)
        if self.calibration is None:
            self.calibration = {}
        self.calibration.update(calibration)
        self._save_calibration()
        logger.info("Base calibration saved")
    
    def configure(self) -> None:
        """Configure all motors for operation."""
        # Configure arm motors for position control
        for bus in [self.left_bus, self.right_bus]:
            bus.disable_torque()
            bus.configure_motors()
            for name in bus.motors:
                bus.write("Operating_Mode", name, OperatingMode.POSITION.value)
                bus.write("P_Coefficient", name, 16)
                bus.write("I_Coefficient", name, 0)
                bus.write("D_Coefficient", name, 32)
            bus.enable_torque()
        
        # Configure base motors for velocity control
        self.base_bus.disable_torque()
        self.base_bus.configure_motors()
        for name in self.base_motors:
            self.base_bus.write("Operating_Mode", name, OperatingMode.VELOCITY.value)
        self.base_bus.enable_torque()
    
    def setup_motors(self) -> None:
        """Set up motor IDs interactively."""
        print("Setting up left arm motors...")
        for motor in reversed(self.left_arm_motors):
            input(f"Connect the controller board to the '{motor}' motor only and press enter.")
            self.left_bus.setup_motor(motor)
            print(f"'{motor}' motor id set to {self.left_bus.motors[motor].id}")
        
        print("Setting up right arm motors...")
        for motor in reversed(self.right_arm_motors):
            input(f"Connect the controller board to the '{motor}' motor only and press enter.")
            self.right_bus.setup_motor(motor)
            print(f"'{motor}' motor id set to {self.right_bus.motors[motor].id}")
        
        print("Setting up base motors...")
        for motor in reversed(self.base_motors):
            input(f"Connect the controller board to the '{motor}' motor only and press enter.")
            self.base_bus.setup_motor(motor)
            print(f"'{motor}' motor id set to {self.base_bus.motors[motor].id}")
    
    # Base kinematics (from LeKiwi)
    @staticmethod
    def _degps_to_raw(degps: float) -> int:
        """Convert degrees per second to raw motor command."""
        steps_per_deg = 4096.0 / 360.0
        speed_in_steps = degps * steps_per_deg
        speed_int = int(round(speed_in_steps))
        speed_int = max(-0x8000, min(0x7FFF, speed_int))
        return speed_int
    
    @staticmethod
    def _raw_to_degps(raw_speed: int) -> float:
        """Convert raw motor speed to degrees per second."""
        steps_per_deg = 4096.0 / 360.0
        return raw_speed / steps_per_deg
    
    def _body_to_wheel_raw(
        self,
        x: float,
        y: float,
        theta: float,
        wheel_radius: float = 0.05,
        base_radius: float = 0.125,
        max_raw: int = 3000,
    ) -> dict:
        """Convert body velocities to wheel commands."""
        theta_rad = theta * (np.pi / 180.0)
        velocity_vector = np.array([x, y, theta_rad])
        
        angles = np.radians(np.array([240, 0, 120]) - 90)
        m = np.array([[np.cos(a), np.sin(a), base_radius] for a in angles])
        
        wheel_linear_speeds = m.dot(velocity_vector)
        wheel_angular_speeds = wheel_linear_speeds / wheel_radius
        wheel_degps = wheel_angular_speeds * (180.0 / np.pi)
        
        # Scale if exceeding max
        steps_per_deg = 4096.0 / 360.0
        raw_floats = [abs(degps) * steps_per_deg for degps in wheel_degps]
        max_raw_computed = max(raw_floats)
        if max_raw_computed > max_raw:
            scale = max_raw / max_raw_computed
            wheel_degps = wheel_degps * scale
        
        wheel_raw = [self._degps_to_raw(deg) for deg in wheel_degps]
        
        return {
            "base_left_wheel": wheel_raw[0],
            "base_back_wheel": wheel_raw[1],
            "base_right_wheel": wheel_raw[2],
        }
    
    def _wheel_raw_to_body(
        self,
        left_wheel_speed: int,
        back_wheel_speed: int,
        right_wheel_speed: int,
        wheel_radius: float = 0.05,
        base_radius: float = 0.125,
    ) -> dict[str, float]:
        """Convert wheel speeds to body velocities."""
        wheel_degps = np.array([
            self._raw_to_degps(left_wheel_speed),
            self._raw_to_degps(back_wheel_speed),
            self._raw_to_degps(right_wheel_speed),
        ])
        
        wheel_radps = wheel_degps * (np.pi / 180.0)
        wheel_linear_speeds = wheel_radps * wheel_radius
        
        angles = np.radians(np.array([240, 0, 120]) - 90)
        m = np.array([[np.cos(a), np.sin(a), base_radius] for a in angles])
        
        m_inv = np.linalg.inv(m)
        velocity_vector = m_inv.dot(wheel_linear_speeds)
        x, y, theta_rad = velocity_vector
        theta = theta_rad * (180.0 / np.pi)
        
        return {"x.vel": x, "y.vel": y, "theta.vel": theta}
    
    def get_observation(self) -> dict[str, Any]:
        """Get current observation: 15 DOF state + camera images."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        start = time.perf_counter()
        obs_dict = {}
        
        # Read arm positions
        left_pos = self.left_bus.sync_read("Present_Position", self.left_arm_motors)
        right_pos = self.right_bus.sync_read("Present_Position", self.right_arm_motors)
        
        for k, v in left_pos.items():
            obs_dict[f"{k}.pos"] = v
        for k, v in right_pos.items():
            obs_dict[f"{k}.pos"] = v
        
        # Read base velocities
        base_wheel_vel = self.base_bus.sync_read("Present_Velocity", self.base_motors)
        base_vel = self._wheel_raw_to_body(
            base_wheel_vel["base_left_wheel"],
            base_wheel_vel["base_back_wheel"],
            base_wheel_vel["base_right_wheel"],
        )
        obs_dict.update(base_vel)
        
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")
        
        # Capture camera images
        for cam_name, cam in self.cameras.items():
            try:
                start = time.perf_counter()
                obs_dict[cam_name] = cam.async_read()
                dt_ms = (time.perf_counter() - start) * 1e3
                logger.debug(f"{self} read {cam_name}: {dt_ms:.1f}ms")
            except Exception as e:
                logger.warning(f"Failed to read camera '{cam_name}': {e}")
                # Return empty frame if camera fails during operation
                if self.config.camera_allow_degraded_mode:
                    h, w = self.config.cameras[cam_name].height, self.config.cameras[cam_name].width
                    obs_dict[cam_name] = np.zeros((h, w, 3), dtype=np.uint8)
                else:
                    raise
        
        return obs_dict
    
    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Send action to robot: 12 arm positions + 3 base velocities."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        # Separate arm and base actions
        left_arm_goal = {k: v for k, v in action.items() if k.startswith("left_") and k.endswith(".pos")}
        right_arm_goal = {k: v for k, v in action.items() if k.startswith("right_") and k.endswith(".pos")}
        base_goal = {k: v for k, v in action.items() if k.endswith(".vel")}
        
        sent_action = {}
        
        # Apply safety limits to arm positions if configured
        if self.config.left_arm_max_relative_target is not None:
            present_left = self.left_bus.sync_read("Present_Position", self.left_arm_motors)
            goal_present = {k: (left_arm_goal.get(f"{k}.pos", 0), present_left[k]) for k in self.left_arm_motors}
            left_arm_goal = {f"{k}.pos": v for k, v in ensure_safe_goal_position(goal_present, self.config.left_arm_max_relative_target).items()}
        
        if self.config.right_arm_max_relative_target is not None:
            present_right = self.right_bus.sync_read("Present_Position", self.right_arm_motors)
            goal_present = {k: (right_arm_goal.get(f"{k}.pos", 0), present_right[k]) for k in self.right_arm_motors}
            right_arm_goal = {f"{k}.pos": v for k, v in ensure_safe_goal_position(goal_present, self.config.right_arm_max_relative_target).items()}
        
        # Send arm positions
        if left_arm_goal:
            left_goal_raw = {k.replace(".pos", ""): v for k, v in left_arm_goal.items()}
            self.left_bus.sync_write("Goal_Position", left_goal_raw)
            sent_action.update(left_arm_goal)
        
        if right_arm_goal:
            right_goal_raw = {k.replace(".pos", ""): v for k, v in right_arm_goal.items()}
            self.right_bus.sync_write("Goal_Position", right_goal_raw)
            sent_action.update(right_arm_goal)
        
        # Send base velocities
        if base_goal:
            base_wheel_goal = self._body_to_wheel_raw(
                base_goal.get("x.vel", 0.0),
                base_goal.get("y.vel", 0.0),
                base_goal.get("theta.vel", 0.0),
            )
            self.base_bus.sync_write("Goal_Velocity", base_wheel_goal)
            sent_action.update(base_goal)
        
        return sent_action
    
    def stop_base(self) -> None:
        """Stop the mobile base."""
        self.base_bus.sync_write("Goal_Velocity", dict.fromkeys(self.base_motors, 0), num_retry=5)
        logger.info("Base motors stopped")
    
    def disconnect(self) -> None:
        """Disconnect from all hardware."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        # Stop base first for safety
        self.stop_base()
        
        # Disconnect motor buses
        if self.config.left_arm_disable_torque_on_disconnect:
            self.left_bus.disable_torque()
        self.left_bus.disconnect()
        
        if self.config.right_arm_disable_torque_on_disconnect:
            self.right_bus.disable_torque()
        self.right_bus.disconnect()
        
        if self.config.base_disable_torque_on_disconnect:
            self.base_bus.disable_torque()
        self.base_bus.disconnect()
        
        # Disconnect cameras
        for cam in self.cameras.values():
            cam.disconnect()
        
        logger.info(f"{self} disconnected.")
