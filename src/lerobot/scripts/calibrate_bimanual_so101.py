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
Calibration script for bimanual SO101 setup.
This script helps you calibrate both follower and leader arms in the correct sequence.
"""

import argparse
import logging
from pathlib import Path


from lerobot.robots.bi_so101_follower import BiSO101Follower, BiSO101FollowerConfig
from lerobot.teleoperators.bi_so101_leader import BiSO101Leader, BiSO101LeaderConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calibrate_bimanual_system(
    left_follower_port: str,
    right_follower_port: str,
    left_leader_port: str,
    right_leader_port: str,
    robot_id: str = "bimanual_so101",
    use_degrees: bool = True,
    calibration_dir: Path | None = None,
):
    """
    Calibrate the complete bimanual SO101 system.
    
    Args:
        left_follower_port: Port for left follower arm
        right_follower_port: Port for right follower arm  
        left_leader_port: Port for left leader arm
        right_leader_port: Port for right leader arm
        robot_id: Identifier for the robot system
        use_degrees: Whether to use degrees for calibration
    """
    
    print("🤖 Starting Bimanual SO101 Calibration")
    print("=" * 50)
    
    # Create configurations
    robot_config = BiSO101FollowerConfig(
        id=robot_id,
        left_arm_port=left_follower_port,
        right_arm_port=right_follower_port,
        left_arm_use_degrees=use_degrees,
        right_arm_use_degrees=use_degrees,
        cameras={},  # No cameras needed for calibration
        calibration_dir=calibration_dir,
    )
    
    teleop_config = BiSO101LeaderConfig(
        id=f"{robot_id}_leader",
        left_arm_port=left_leader_port,
        right_arm_port=right_leader_port,
        use_degrees=use_degrees,
        calibration_dir=calibration_dir,
    )
    
    # Initialize systems
    robot = BiSO101Follower(robot_config)
    teleop = BiSO101Leader(teleop_config)
    
    try:
        print("\n📍 Step 1: Calibrating Follower Arms")
        print("-" * 30)
        print("This will calibrate both left and right follower arms.")
        print("Follow the on-screen instructions for each arm.")
        input("Press ENTER when ready to start follower calibration...")
        
        # Connect follower arms without calibration first
        robot.left_arm.connect(calibrate=False)
        robot.right_arm.connect(calibrate=False)
        
        print("\n🔧 Calibrating LEFT follower arm...")
        robot.left_arm.calibrate()
        
        print("\n🔧 Calibrating RIGHT follower arm...")
        robot.right_arm.calibrate()
        
        print("✅ Follower arms calibrated successfully!")
        
        # Disconnect follower arms
        robot.left_arm.disconnect()
        robot.right_arm.disconnect()
        
        print("\n📍 Step 2: Calibrating Leader Arms")
        print("-" * 30)
        print("This will calibrate both left and right leader arms.")
        print("Follow the on-screen instructions for each arm.")
        input("Press ENTER when ready to start leader calibration...")
        
        # Connect leader arms without calibration first
        teleop.left_arm.connect(calibrate=False)
        teleop.right_arm.connect(calibrate=False)
        
        print("\n🔧 Calibrating LEFT leader arm...")
        teleop.left_arm.calibrate()
        
        print("\n🔧 Calibrating RIGHT leader arm...")
        teleop.right_arm.calibrate()
        
        print("✅ Leader arms calibrated successfully!")
        
        # Disconnect leader arms
        teleop.left_arm.disconnect()
        teleop.right_arm.disconnect()
        
        print("\n🎉 Bimanual SO101 Calibration Complete!")
        print("=" * 50)
        print("Your bimanual SO101 system is now calibrated and ready for:")
        print("• Teleoperation")
        print("• Data recording")
        print("• SmolVLA training")
        print("\nNext steps:")
        print("1. Test teleoperation with both arms")
        print("2. Record demonstration data")
        print("3. Train your SmolVLA policy")
        
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        print(f"\n❌ Calibration failed: {e}")
        print("Please check your connections and try again.")
    
    finally:
        # Ensure clean disconnect
        try:
            robot.disconnect()
            teleop.disconnect()
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description="Calibrate bimanual SO101 system")
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
        required=True, 
        help="Port for left leader arm (e.g., /dev/ttyACM2)"
    )
    parser.add_argument(
        "--right_leader_port",
        type=str,
        required=True,
        help="Port for right leader arm (e.g., /dev/ttyACM3)"
    )
    parser.add_argument(
        "--robot_id",
        type=str,
        default="bimanual_so101",
        help="Identifier for the robot system"
    )
    parser.add_argument(
        "--use_degrees",
        action="store_true",
        default=True,
        help="Use degrees for calibration (default: True)"
    )
    parser.add_argument(
    "--calibration_dir",
    type=Path,
    default=None,
    help="Custom directory to save calibration files"
)

    
    args = parser.parse_args()
    
    calibrate_bimanual_system(
        left_follower_port=args.left_follower_port,
        right_follower_port=args.right_follower_port,
        left_leader_port=args.left_leader_port,
        right_leader_port=args.right_leader_port,
        robot_id=args.robot_id,
        use_degrees=args.use_degrees,
        calibration_dir=args.calibration_dir,
    )


if __name__ == "__main__":
    main()
