# Push from your dev computer first, then on robot computer:
cd ~/lerobot
git pull origin main  # or clone fresh if needed
pip install -e .



python -c "
from lerobot.robots import SO101BimanualConfig, SO101Bimanual
from lerobot.robots.config import RobotConfig
print('Available robot types:', RobotConfig.available_subclasses())
print('SO101Bimanual available!' if 'so101_bimanual' in RobotConfig.available_subclasses() else 'Not found')
"



python -m lerobot.teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/tty.usbmodem58760431541 \
    --robot.id=my_follower_arm \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=my_leader_arm



# First edit the bi_teleoperate.py file to use your USB ports
python -m lerobot.bi_teleoperate



python -m lerobot.teleoperate \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.id=my_bimanual_setup \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=my_leader_arm


python -m lerobot.teleoperate \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.cameras='{"main": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup


# This would load a VLA model and print predicted actions without sending them
python -c "
from lerobot.policies import SmolVLAPolicy
from lerobot.robots.so101_follower import SO101BimanualConfig, SO101Bimanual
from lerobot.cameras.opencv import OpenCVCameraConfig

# Setup robot with camera
camera_config = {'main': OpenCVCameraConfig(index_or_path=0, width=640, height=480, fps=30)}
robot_config = SO101BimanualConfig(
    left_port='/dev/tty.usbmodem58760431541',
    right_port='/dev/tty.usbmodem58760431542',
    cameras=camera_config,
    id='vla_test'
)
robot = SO101Bimanual(robot_config)

# Load VLA model (you'd need a trained one)
# policy = SmolVLAPolicy.from_pretrained('your_model_name')

# Get observation
robot.connect()
obs = robot.get_observation()
print('Observation keys:', obs.keys())

# Test language instruction
instruction = 'Pick up the red cube with your left hand'
print(f'Language instruction: {instruction}')
# action = policy.predict(obs, instruction)
# print('Predicted actions:', action)

robot.disconnect()
"


python -m lerobot.record \
    --robot.type=so101_bimanual \
    --robot.left_port=/dev/tty.usbmodem58760431541 \
    --robot.right_port=/dev/tty.usbmodem58760431542 \
    --robot.cameras='{"main": {"type": "opencv", "index_or_path": 0, "width": 640, "height": 480, "fps": 30}}' \
    --robot.id=my_bimanual_setup \
    --teleop.type=so101_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --teleop.id=my_leader_arm \
    --dataset.repo_id=your_username/bimanual_dataset \
    --dataset.single_task="Pick and place with both hands" \
    --dataset.num_episodes=10