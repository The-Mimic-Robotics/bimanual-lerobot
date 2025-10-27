#!/usr/bin/env python3
"""
Simple ZED SDK test to check camera initialization
"""

try:
    import pyzed.sl as sl
    print("✅ ZED SDK imported successfully")
    
    # Create a Camera object
    zed = sl.Camera()
    
    # Create InitParameters object and set configuration parameters
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.VGA  # Lower resolution
    init_params.camera_fps = 15  # Lower FPS
    init_params.depth_mode = sl.DEPTH_MODE.PERFORMANCE
    init_params.coordinate_units = sl.UNIT.METER
    init_params.sdk_verbose = 1
    
    print("📷 Opening ZED camera...")
    
    # Open the camera
    status = zed.open(init_params)
    
    if status != sl.ERROR_CODE.SUCCESS:
        print(f"❌ Camera initialization failed: {status}")
        print("Available error codes:")
        for attr in dir(sl.ERROR_CODE):
            if not attr.startswith('_'):
                print(f"   {attr}: {getattr(sl.ERROR_CODE, attr)}")
        exit(1)
    
    print("✅ ZED camera opened successfully!")
    
    # Get camera information
    camera_info = zed.get_camera_information()
    print(f"📋 Camera Info:")
    print(f"   Serial: {camera_info.serial_number}")
    print(f"   Firmware: {camera_info.camera_firmware_version}")
    print(f"   Resolution: {camera_info.camera_configuration.resolution.width}x{camera_info.camera_configuration.resolution.height}")
    
    # Try to capture a frame
    image = sl.Mat()
    runtime_params = sl.RuntimeParameters()
    
    if zed.grab(runtime_params) == sl.ERROR_CODE.SUCCESS:
        print("✅ Frame captured successfully!")
        zed.retrieve_image(image, sl.VIEW.LEFT)
        print(f"   Image dimensions: {image.get_width()}x{image.get_height()}")
    else:
        print("❌ Failed to capture frame")
    
    # Close camera
    zed.close()
    print("📷 Camera closed")

except ImportError as e:
    print(f"❌ Cannot import ZED SDK: {e}")
except Exception as e:
    print(f"❌ Error: {e}")