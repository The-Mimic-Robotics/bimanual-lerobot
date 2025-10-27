#!/usr/bin/env python3
"""
Simple ZED camera test script
"""
import pyzed.sl as sl

def test_zed_camera():
    # Initialize ZED camera
    zed = sl.Camera()
    
    # Set configuration parameters
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.HD720
    init_params.camera_fps = 30
    
    print("Attempting to open ZED camera...")
    
    # Open the camera
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        print(f"Error opening ZED camera: {err}")
        return False
    
    print("✅ ZED camera opened successfully!")
    
    # Get camera information
    camera_info = zed.get_camera_information()
    print(f"Camera model: {camera_info.camera_model}")
    print(f"Serial number: {camera_info.serial_number}")
    print(f"Firmware version: {camera_info.camera_firmware_version}")
    
    # Close camera
    zed.close()
    print("Camera closed.")
    return True

if __name__ == "__main__":
    test_zed_camera()