# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
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
Helper to set motor ids and baudrate.

Example:

```shell
python -m lerobot.setup_motors \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbmodem575E0031751
```

Or:

```shell
python -m lerobot.setup_motors \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM2
```
"""

import argparse
import sys
from dataclasses import dataclass

import draccus

from lerobot.robots import (  # noqa: F401
    RobotConfig,
    koch_follower,
    lekiwi,
    make_robot_from_config,
    so100_follower,
    so101_follower,
)
from lerobot.teleoperators import (  # noqa: F401
    TeleoperatorConfig,
    koch_leader,
    make_teleoperator_from_config,
    so100_leader,
    so101_leader,
)

COMPATIBLE_DEVICES = [
    "koch_follower",
    "koch_leader",
    "so100_follower",
    "so100_leader",
    "so101_follower",
    "so101_leader",
    "lekiwi",
]


@dataclass
class SetupConfig:
    teleop: TeleoperatorConfig | None = None
    robot: RobotConfig | None = None

    def __post_init__(self):
        if bool(self.teleop) == bool(self.robot):
            raise ValueError("Choose either a teleop or a robot.")

        self.device = self.robot if self.robot else self.teleop


def parse_args():
    """Custom argument parser to handle both robot and teleop configurations."""
    parser = argparse.ArgumentParser(description="Setup motors for robot or teleoperator")
    
    # Add robot arguments
    robot_group = parser.add_argument_group('robot', 'Robot configuration')
    robot_group.add_argument('--robot.type', dest='robot_type', help='Robot type (e.g., so101_follower)')
    robot_group.add_argument('--robot.port', dest='robot_port', help='Robot port (e.g., /dev/ttyACM2)')
    robot_group.add_argument('--robot.id', dest='robot_id', help='Robot ID', default=None)
    
    # Add teleop arguments  
    teleop_group = parser.add_argument_group('teleop', 'Teleoperator configuration')
    teleop_group.add_argument('--teleop.type', dest='teleop_type', help='Teleoperator type (e.g., so101_leader)')
    teleop_group.add_argument('--teleop.port', dest='teleop_port', help='Teleoperator port (e.g., /dev/ttyACM0)')
    teleop_group.add_argument('--teleop.id', dest='teleop_id', help='Teleoperator ID', default=None)
    
    args = parser.parse_args()
    
    # Check that we have either robot or teleop config, but not both
    has_robot = bool(args.robot_type or args.robot_port)
    has_teleop = bool(args.teleop_type or args.teleop_port)
    
    if has_robot and has_teleop:
        parser.error("Cannot specify both robot and teleop configurations. Choose one.")
    if not has_robot and not has_teleop:
        parser.error("Must specify either robot or teleop configuration.")
        
    # Validate required fields
    if has_robot:
        if not args.robot_type:
            parser.error("--robot.type is required when using robot configuration")
        if not args.robot_port:
            parser.error("--robot.port is required when using robot configuration")
    
    if has_teleop:
        if not args.teleop_type:
            parser.error("--teleop.type is required when using teleop configuration")
        if not args.teleop_port:
            parser.error("--teleop.port is required when using teleop configuration")
    
    return args


def setup_motors_main():
    """Main function that handles argument parsing and device setup."""
    args = parse_args()
    
    # Create device config based on arguments
    if args.robot_type:
        # Import the appropriate robot config class
        if args.robot_type == "so101_follower":
            from lerobot.robots.so101_follower import SO101FollowerConfig
            config = SO101FollowerConfig(
                port=args.robot_port,
                id=args.robot_id or f"robot_{args.robot_type}"
            )
        elif args.robot_type == "so100_follower":
            from lerobot.robots.so100_follower import SO100FollowerConfig
            config = SO100FollowerConfig(
                port=args.robot_port,
                id=args.robot_id or f"robot_{args.robot_type}"
            )
        elif args.robot_type == "koch_follower":
            from lerobot.robots.koch_follower import KochFollowerConfig
            config = KochFollowerConfig(
                port=args.robot_port,
                id=args.robot_id or f"robot_{args.robot_type}"
            )
        elif args.robot_type == "lekiwi":
            from lerobot.robots.lekiwi import LekiwiConfig
            config = LekiwiConfig(
                port=args.robot_port,
                id=args.robot_id or f"robot_{args.robot_type}"
            )
        else:
            raise ValueError(f"Unsupported robot type: {args.robot_type}")
            
        device = make_robot_from_config(config)
        
    else:  # teleop
        # Import the appropriate teleop config class
        if args.teleop_type == "so101_leader":
            from lerobot.teleoperators.so101_leader import SO101LeaderConfig
            config = SO101LeaderConfig(
                port=args.teleop_port,
                id=args.teleop_id or f"teleop_{args.teleop_type}"
            )
        elif args.teleop_type == "so100_leader":
            from lerobot.teleoperators.so100_leader import SO100LeaderConfig
            config = SO100LeaderConfig(
                port=args.teleop_port,
                id=args.teleop_id or f"teleop_{args.teleop_type}"
            )
        elif args.teleop_type == "koch_leader":
            from lerobot.teleoperators.koch_leader import KochLeaderConfig
            config = KochLeaderConfig(
                port=args.teleop_port,
                id=args.teleop_id or f"teleop_{args.teleop_type}"
            )
        else:
            raise ValueError(f"Unsupported teleoperator type: {args.teleop_type}")
            
        device = make_teleoperator_from_config(config)
    
    # Check if device type is supported
    device_type = config.type
    if device_type not in COMPATIBLE_DEVICES:
        raise NotImplementedError(f"Device type '{device_type}' not supported. Supported devices: {COMPATIBLE_DEVICES}")
    
    print(f"Setting up motors for {device_type} on port {config.port}")
    device.setup_motors()
    print("Motor setup completed successfully!")


@draccus.wrap()
def setup_motors(cfg: SetupConfig):
    """Legacy draccus-based function - kept for backward compatibility."""
    if cfg.device.type not in COMPATIBLE_DEVICES:
        raise NotImplementedError

    if isinstance(cfg.device, RobotConfig):
        device = make_robot_from_config(cfg.device)
    else:
        device = make_teleoperator_from_config(cfg.device)

    device.setup_motors()


if __name__ == "__main__":
    setup_motors_main()
