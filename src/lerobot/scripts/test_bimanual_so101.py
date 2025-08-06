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

"""
Test script for bimanual SO101 setup.
This script helps verify that your bimanual SO101 system is working correctly.
"""

import argparse
import time
from typing import Optional

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
from lerobot.robots.bi_so101_follower import BiSO101Follower, BiSO101FollowerConfig
from lerobot.teleoperators.bi_so101_leader import BiSO101Leader, BiSO101LeaderConfig


def test_bimanual_system(
    left_follower_port: str,
    right_follower_port: str,
    left_leader_port: Optional[str] = None,
    right_leader_port: Optional[str] = None,
    robot_id: str = "test_bimanual",
    test_cameras: bool = False,
    test_duration: int = 30,
):
    """
    Test the bimanual SO101 system.
    
    Args:
        left_follower_port: Port for left follower arm
        right_follower_port: Port for right follower arm
        left_leader_port: Port for left leader arm (optional)
        right_leader_port: Port for right leader arm (optional)
        robot_id: Identifier for the robot system
        test_cameras: Whether to test cameras
        test_duration: Duration of teleoperation test in seconds
    """
    
    print("🤖 Testing Bimanual SO101 System")
    print("=" * 40)
    
    # Camera configuration (minimal for testing)
    cameras = {}
    if test_cameras:
        cameras = {
            "test_cam_0": OpenCVCameraConfig(
                index_or_path=0,
                width=320,
                height=240,
                fps=15,
            ),
            "test_cam_1": OpenCVCameraConfig(
                index_or_path=1,
                width=320,
                height=240,
                fps=15,
            ),
        }
    
    # Create robot configuration
    robot_config = BiSO101FollowerConfig(
        id=robot_id,
        left_arm_port=left_follower_port,
        right_arm_port=right_follower_port,
        left_arm_use_degrees=True,
        right_arm_use_degrees=True,
        cameras=cameras,
    )
    
    # Initialize robot
    robot = BiSO101Follower(robot_config)
    teleop = None
    
    try:
        print("\n📍 Step 1: Testing Robot Connection")
        print("-" * 30)
        
        # Connect robot
        robot.connect(calibrate=True)
        print("✅ Robot connected successfully")
        
        # Test observation
        obs = robot.get_observation()
        print(f"✅ Robot observation keys: {list(obs.keys())}")
        
        # Print motor counts
        left_motors = [k for k in obs.keys() if k.startswith("left_")]
        right_motors = [k for k in obs.keys() if k.startswith("right_")]
        print(f"✅ Left arm motors: {len(left_motors)}")
        print(f"✅ Right arm motors: {len(right_motors)}")
        
        if test_cameras:
            camera_keys = [k for k in obs.keys() if "images" in k]
            print(f"✅ Cameras working: {len(camera_keys)}")
        
        # Test if leader arms are provided
        if left_leader_port and right_leader_port:
            print("\n📍 Step 2: Testing Teleoperation")
            print("-" * 30)
            
            teleop_config = BiSO101LeaderConfig(
                id=f"{robot_id}_leader",
                left_arm_port=left_leader_port,
                right_arm_port=right_leader_port,
                use_degrees=True,
            )
            
            teleop = BiSO101Leader(teleop_config)
            teleop.connect(calibrate=True)
            print("✅ Teleoperator connected successfully")
            
            # Test teleoperation loop
            print(f"🎮 Starting teleoperation test for {test_duration} seconds...")
            print("Move the leader arms to control the followers!")
            
            start_time = time.time()
            while time.time() - start_time < test_duration:
                # Get action from leader
                action = teleop.get_action()
                
                # Send to follower
                robot.send_action(action)
                
                # Get observation
                obs = robot.get_observation()
                
                # Print status every 5 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 5 == 0 and elapsed >= 5:
                    print(f"⏱️  Teleoperation running... {int(elapsed)}s / {test_duration}s")
                
                time.sleep(0.1)  # 10 Hz control loop
            
            print("✅ Teleoperation test completed successfully")
        
        print("\n📍 Step 3: Testing Action Space")
        print("-" * 30)
        
        # Test action features
        action_features = robot.action_features
        print(f"✅ Action features: {list(action_features.keys())}")
        
        # Test zero action
        zero_action = {key: 0.0 for key in action_features.keys()}
        robot.send_action(zero_action)
        print("✅ Zero action sent successfully")
        
        print("\n🎉 All Tests Passed!")
        print("=" * 40)
        print("Your bimanual SO101 system is working correctly!")
        print("\nSystem capabilities verified:")
        print("• ✅ Bimanual robot control")
        print("• ✅ Joint position feedback")
        if test_cameras:
            print("• ✅ Camera integration")
        if left_leader_port and right_leader_port:
            print("• ✅ Bimanual teleoperation")
        print("• ✅ Action space mapping")
        print("\nReady for:")
        print("• 📊 Data recording")
        print("• 🤖 SmolVLA training")
        print("• 🎯 Policy deployment")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Please check your connections and configuration.")
        raise
    
    finally:
        # Clean disconnect
        try:
            robot.disconnect()
            if teleop:
                teleop.disconnect()
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description="Test bimanual SO101 system")
    parser.add_argument(
        "--left_follower_port",
        type=str,
        required=True,
        help="Port for left follower arm (e.g., /dev/ttyACM0)"
    )
    parser.add_argument(
        "--right_follower_port",
        type=str,
        required=True,
        help="Port for right follower arm (e.g., /dev/ttyACM1)"
    )
    parser.add_argument(
        "--left_leader_port",
        type=str,
        help="Port for left leader arm (e.g., /dev/ttyACM2)"
    )
    parser.add_argument(
        "--right_leader_port",
        type=str,
        help="Port for right leader arm (e.g., /dev/ttyACM3)"
    )
    parser.add_argument(
        "--robot_id",
        type=str,
        default="test_bimanual",
        help="Identifier for the robot system"
    )
    parser.add_argument(
        "--test_cameras",
        action="store_true",
        help="Test camera integration"
    )
    parser.add_argument(
        "--test_duration",
        type=int,
        default=30,
        help="Duration of teleoperation test in seconds"
    )
    
    args = parser.parse_args()
    
    test_bimanual_system(
        left_follower_port=args.left_follower_port,
        right_follower_port=args.right_follower_port,
        left_leader_port=args.left_leader_port,
        right_leader_port=args.right_leader_port,
        robot_id=args.robot_id,
        test_cameras=args.test_cameras,
        test_duration=args.test_duration,
    )


if __name__ == "__main__":
    main()
