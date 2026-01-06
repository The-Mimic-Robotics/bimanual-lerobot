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

15 DOF action space:
- 12 DOF: Bimanual arms (6 per arm: 5-axis + gripper)
- 3 DOF: Mobile base (x, y, theta velocities)
"""

from .bi_lekiwi import BiLeKiwi
from .config_bi_lekiwi import BiLeKiwiClientConfig, BiLeKiwiConfig, BiLeKiwiHostConfig

__all__ = [
    "BiLeKiwi",
    "BiLeKiwiConfig",
    "BiLeKiwiHostConfig",
    "BiLeKiwiClientConfig",
]
