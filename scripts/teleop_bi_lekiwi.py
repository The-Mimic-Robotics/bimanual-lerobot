#!/usr/bin/env python

"""BiLeKiwi Teleoperation Script

Teleoperate bimanual SO-101 arms + mecanum mobile base simultaneously:
- Master arms control slave arms (direct joint mirroring)
- Keyboard controls mobile base (WASD) via mecanum ESP32 controller

The mecanum base uses serial communication with the ESP32:
- Send: TWIST,vx,vy,omega (m/s, m/s, rad/s)
- Recv: ODOM,x,y,theta,vx,vy,omega,enc1,enc2,enc3,enc4

Usage:
    python teleop_bi_lekiwi.py \
        --left-master-port /dev/ttyACM0 \
        --right-master-port /dev/ttyACM1 \
        --left-follower-port /dev/ttyACM2 \
        --right-follower-port /dev/ttyACM3 \
        --base-serial-port /dev/ttyUSB0

Controls:
    Arms: Move master arms - slave arms mirror movements
    Base: W/S = forward/back, A/D = strafe, Q/E = rotate, X = stop
    Speed: +/- = adjust base speed
    Quit: ESC
"""

import argparse
import logging
import math
import signal
import sys
import time
from dataclasses import dataclass
from queue import Queue
from threading import Event, Thread
from typing import Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import dependencies
PYNPUT_AVAILABLE = True
try:
    from pynput import keyboard
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not available - keyboard control disabled")

SERIAL_AVAILABLE = True
try:
    import serial
except ImportError:
    serial = None
    SERIAL_AVAILABLE = False
    logger.warning("pyserial not available - base control disabled")


@dataclass
class TeleopConfig:
    """Configuration for BiLeKiwi teleoperation."""
    # Arm ports (Feetech motors)
    left_master_port: str = "/dev/ttyACM0"
    right_master_port: str = "/dev/ttyACM1"
    left_follower_port: str = "/dev/ttyACM2"
    right_follower_port: str = "/dev/ttyACM3"
    
    # Base serial port (ESP32 mecanum controller)
    base_serial_port: str = "/dev/ttyUSB0"
    base_baudrate: int = 115200
    
    # Control settings
    teleop_freq: float = 50.0  # Hz
    use_degrees: bool = True
    
    # Base speed settings (REP-103: x=forward, y=left, omega=CCW rad/s)
    linear_speed: float = 0.3  # m/s
    angular_speed: float = 0.5  # rad/s
    speed_increment: float = 0.1


class MecanumBaseController:
    """Controller for mecanum base via serial to ESP32."""
    
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.last_odom = None
        self.odom_thread = None
        self.should_stop = Event()
    
    def connect(self) -> None:
        if not SERIAL_AVAILABLE:
            logger.warning("Serial not available - base control disabled")
            return
        
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
            time.sleep(2)  # Wait for ESP32 to reset
            logger.info(f"Mecanum base connected on {self.port}")
            
            # Start odometry reading thread
            self.odom_thread = Thread(target=self._read_odom_loop, daemon=True)
            self.odom_thread.start()
        except Exception as e:
            logger.error(f"Failed to connect to base: {e}")
            self.serial_conn = None
    
    def _read_odom_loop(self):
        """Background thread to read odometry from ESP32."""
        while not self.should_stop.is_set():
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line.startswith("ODOM,"):
                        parts = line.split(",")
                        if len(parts) >= 7:
                            self.last_odom = {
                                "x": float(parts[1]),
                                "y": float(parts[2]),
                                "theta": float(parts[3]),
                                "vx": float(parts[4]),
                                "vy": float(parts[5]),
                                "omega": float(parts[6]),
                            }
            except Exception as e:
                pass
            time.sleep(0.01)
    
    def send_velocity(self, vx: float, vy: float, omega: float) -> None:
        """Send velocity command to base.
        
        Args:
            vx: Forward velocity (m/s, positive = forward)
            vy: Lateral velocity (m/s, positive = left)
            omega: Angular velocity (rad/s, positive = CCW)
        """
        if self.serial_conn is None:
            return
        
        try:
            cmd = f"TWIST,{vx:.3f},{vy:.3f},{omega:.3f}\n"
            self.serial_conn.write(cmd.encode('utf-8'))
        except Exception as e:
            logger.warning(f"Failed to send velocity: {e}")
    
    def stop(self) -> None:
        """Stop the base."""
        self.send_velocity(0.0, 0.0, 0.0)
    
    def disconnect(self) -> None:
        self.should_stop.set()
        self.stop()
        if self.serial_conn:
            self.serial_conn.close()
            logger.info("Base disconnected")


class KeyboardController:
    """Keyboard controller for base movement."""
    
    def __init__(self, config: TeleopConfig):
        self.config = config
        self.current_linear_speed = config.linear_speed
        self.current_angular_speed = config.angular_speed
        
        self.event_queue = Queue()
        self.current_pressed = {}
        self.listener = None
        self.should_stop = Event()
    
    def connect(self) -> None:
        if not PYNPUT_AVAILABLE:
            logger.warning("Keyboard control not available")
            return
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self.listener.start()
        logger.info("Keyboard controller connected")
    
    def _on_press(self, key):
        try:
            if hasattr(key, "char") and key.char:
                self.event_queue.put((key.char.lower(), True))
        except AttributeError:
            pass
    
    def _on_release(self, key):
        try:
            if hasattr(key, "char") and key.char:
                self.event_queue.put((key.char.lower(), False))
        except AttributeError:
            pass
        
        if key == keyboard.Key.esc:
            logger.info("ESC pressed - stopping")
            self.should_stop.set()
    
    def _drain_keys(self):
        while not self.event_queue.empty():
            key_char, is_pressed = self.event_queue.get_nowait()
            if is_pressed:
                self.current_pressed[key_char] = True
            else:
                self.current_pressed.pop(key_char, None)
    
    def get_velocity(self) -> tuple[float, float, float]:
        """Get (vx, vy, omega) from keyboard state.
        
        Returns:
            vx: Forward velocity (m/s)
            vy: Lateral velocity (m/s, positive = left)
            omega: Angular velocity (rad/s, positive = CCW)
        """
        if not PYNPUT_AVAILABLE or self.listener is None:
            return (0.0, 0.0, 0.0)
        
        self._drain_keys()
        
        vx = 0.0
        vy = 0.0
        omega = 0.0
        
        keys = set(self.current_pressed.keys())
        
        # Forward/Backward (W/S)
        if "w" in keys:
            vx = self.current_linear_speed
        elif "s" in keys:
            vx = -self.current_linear_speed
        
        # Strafe (A/D) - not turn!
        if "a" in keys:
            vy = self.current_linear_speed  # Left
        elif "d" in keys:
            vy = -self.current_linear_speed  # Right
        
        # Rotate in place (Q/E)
        if "q" in keys:
            omega = self.current_angular_speed  # CCW
        elif "e" in keys:
            omega = -self.current_angular_speed  # CW
        
        # Emergency stop (X)
        if "x" in keys:
            return (0.0, 0.0, 0.0)
        
        # Speed adjustment
        if "=" in keys or "+" in keys:
            self.current_linear_speed = min(1.0, self.current_linear_speed + 0.1)
            self.current_angular_speed = min(2.0, self.current_angular_speed + 0.2)
            logger.info(f"Speed: {self.current_linear_speed:.1f} m/s")
        if "-" in keys:
            self.current_linear_speed = max(0.1, self.current_linear_speed - 0.1)
            self.current_angular_speed = max(0.1, self.current_angular_speed - 0.2)
            logger.info(f"Speed: {self.current_linear_speed:.1f} m/s")
        
        return (vx, vy, omega)
    
    def disconnect(self) -> None:
        if self.listener:
            self.listener.stop()


class BiLeKiwiTeleop:
    """Main teleoperation controller for BiLeKiwi robot."""
    
    def __init__(self, config: TeleopConfig):
        self.config = config
        self.should_stop = Event()
        
        # Controllers
        self.keyboard = KeyboardController(config)
        self.base = MecanumBaseController(config.base_serial_port, config.base_baudrate)
        
        # Robot and teleoperator (lazy loaded)
        self.robot = None
        self.teleop = None
    
    def connect(self) -> None:
        """Connect to all hardware."""
        logger.info("Connecting to BiLeKiwi hardware...")
        
        # Import lerobot modules
        try:
            from lerobot.robots.bi_lekiwi import BiLeKiwi, BiLeKiwiConfig
            from lerobot.teleoperators.bi_so101_leader import BiSO101Leader, BiSO101LeaderConfig
        except ImportError as e:
            logger.error(f"Failed to import lerobot: {e}")
            logger.error("Install with: pip install -e .")
            raise
        
        # Create follower robot (arms only, base via serial)
        robot_config = BiLeKiwiConfig(
            left_arm_port=self.config.left_follower_port,
            right_arm_port=self.config.right_follower_port,
            base_port=self.config.left_follower_port,  # Dummy - we use serial
            left_arm_use_degrees=self.config.use_degrees,
            right_arm_use_degrees=self.config.use_degrees,
            cameras={},
        )
        
        # We'll control base via serial, so create arms-only version
        from lerobot.robots.bi_so101_follower import BiSO101Follower, BiSO101FollowerConfig
        
        arm_config = BiSO101FollowerConfig(
            left_arm_port=self.config.left_follower_port,
            right_arm_port=self.config.right_follower_port,
            left_arm_use_degrees=self.config.use_degrees,
            right_arm_use_degrees=self.config.use_degrees,
            cameras={},
        )
        self.robot = BiSO101Follower(arm_config)
        
        # Create leader teleoperator
        teleop_config = BiSO101LeaderConfig(
            left_arm_port=self.config.left_master_port,
            right_arm_port=self.config.right_master_port,
            use_degrees=self.config.use_degrees,
        )
        self.teleop = BiSO101Leader(teleop_config)
        
        # Connect everything
        logger.info("Connecting master arms...")
        self.teleop.connect()
        
        logger.info("Connecting follower arms...")
        self.robot.connect()
        
        logger.info("Connecting mecanum base...")
        self.base.connect()
        
        logger.info("Connecting keyboard...")
        self.keyboard.connect()
        
        logger.info("✓ All hardware connected!")
        self._print_controls()
    
    def _print_controls(self):
        print("\n" + "="*60)
        print("BiLeKiwi Teleoperation Active")
        print("="*60)
        print("\nARM CONTROL:")
        print("  Move master arms → Slave arms follow")
        print("\nBASE CONTROL (Keyboard):")
        print("  W/S     = Forward / Backward")
        print("  A/D     = Strafe left / right (mecanum)")
        print("  Q/E     = Rotate CCW / CW")
        print("  X       = Emergency stop")
        print("  +/-     = Speed up / down")
        print("  ESC     = Quit")
        print("="*60 + "\n")
    
    def run(self) -> None:
        """Main teleoperation loop."""
        if self.robot is None or self.teleop is None:
            raise RuntimeError("Call connect() first")
        
        period = 1.0 / self.config.teleop_freq
        logger.info(f"Teleop loop: {self.config.teleop_freq} Hz")
        
        try:
            while not self.should_stop.is_set() and not self.keyboard.should_stop.is_set():
                start = time.perf_counter()
                
                # Get arm action from master arms
                arm_action = self.teleop.get_action()
                
                # Get base velocity from keyboard
                vx, vy, omega = self.keyboard.get_velocity()
                
                # Send arm action to follower arms
                self.robot.send_action(arm_action)
                
                # Send base velocity to ESP32
                self.base.send_velocity(vx, vy, omega)
                
                # Maintain loop rate
                elapsed = time.perf_counter() - start
                if elapsed < period:
                    time.sleep(period - elapsed)
        
        except KeyboardInterrupt:
            logger.info("Interrupted")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop and disconnect."""
        self.should_stop.set()
        
        logger.info("Stopping...")
        self.base.stop()
        self.base.disconnect()
        self.keyboard.disconnect()
        
        if self.teleop:
            self.teleop.disconnect()
        if self.robot:
            self.robot.disconnect()
        
        logger.info("Done")


def main():
    parser = argparse.ArgumentParser(description="BiLeKiwi Teleoperation")
    
    parser.add_argument("--left-master-port", default="/dev/ttyACM0")
    parser.add_argument("--right-master-port", default="/dev/ttyACM1")
    parser.add_argument("--left-follower-port", default="/dev/ttyACM2")
    parser.add_argument("--right-follower-port", default="/dev/ttyACM3")
    parser.add_argument("--base-serial-port", default="/dev/ttyUSB0",
                       help="ESP32 mecanum controller serial port")
    parser.add_argument("--freq", type=float, default=50.0)
    parser.add_argument("--linear-speed", type=float, default=0.3)
    parser.add_argument("--angular-speed", type=float, default=0.5)
    
    args = parser.parse_args()
    
    config = TeleopConfig(
        left_master_port=args.left_master_port,
        right_master_port=args.right_master_port,
        left_follower_port=args.left_follower_port,
        right_follower_port=args.right_follower_port,
        base_serial_port=args.base_serial_port,
        teleop_freq=args.freq,
        linear_speed=args.linear_speed,
        angular_speed=args.angular_speed,
    )
    
    teleop = BiLeKiwiTeleop(config)
    
    def signal_handler(sig, frame):
        teleop.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        teleop.connect()
        teleop.run()
    except Exception as e:
        logger.error(f"Error: {e}")
        teleop.stop()
        raise


if __name__ == "__main__":
    main()
