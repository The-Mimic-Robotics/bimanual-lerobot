#!/usr/bin/env python

"""
Camera diagnostic script to identify and fix random video device issues.
"""

import cv2
import os
import subprocess
import time

def get_usb_cameras():
    """Get USB camera information."""
    print("📹 USB Camera Analysis")
    print("=" * 50)
    
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True)
        print("Connected cameras:")
        print(result.stdout)
    except Exception as e:
        print(f"Error getting camera info: {e}")

def test_stable_paths():
    """Test stable USB paths."""
    print("\n🔍 Testing Stable USB Paths")
    print("=" * 50)
    
    stable_paths = []
    if os.path.exists('/dev/v4l/by-path/'):
        for item in os.listdir('/dev/v4l/by-path/'):
            if 'video-index0' in item:  # Primary video streams
                stable_paths.append(f'/dev/v4l/by-path/{item}')
    
    working_cameras = []
    
    for i, path in enumerate(stable_paths):
        print(f"\nTesting path {i+1}: {path}")
        
        if os.path.exists(path):
            target = os.readlink(path)
            print(f"  → Points to: {target}")
            
            try:
                cap = cv2.VideoCapture(path)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"  ✅ WORKING - Frame: {frame.shape}")
                        working_cameras.append((path, target.replace('../../', '/dev/')))
                    else:
                        print(f"  ❌ No frame captured")
                else:
                    print(f"  ❌ Failed to open")
                cap.release()
            except Exception as e:
                print(f"  ❌ Error: {e}")
        else:
            print(f"  ❌ Path doesn't exist")
    
    return working_cameras

def test_video_indices():
    """Test current /dev/video indices."""
    print(f"\n🎥 Testing Video Device Indices")
    print("=" * 50)
    
    working_indices = []
    
    for i in range(10):  # Test indices 0-9
        device = f'/dev/video{i}'
        if os.path.exists(device):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"  ✅ /dev/video{i} (index {i}) - Frame: {frame.shape}")
                        working_indices.append(i)
                    else:
                        print(f"  ❌ /dev/video{i} (index {i}) - No frame")
                else:
                    print(f"  ❌ /dev/video{i} (index {i}) - Failed to open")
                cap.release()
            except Exception as e:
                print(f"  ❌ /dev/video{i} error: {e}")
    
    return working_indices

def recommend_config(working_cameras, working_indices):
    """Recommend camera configuration."""
    print(f"\n💡 Configuration Recommendations")
    print("=" * 50)
    
    if len(working_cameras) >= 2:
        print("✅ You have 2+ working cameras with stable paths!")
        print("\nRecommended configuration (stable USB paths):")
        for i, (path, device) in enumerate(working_cameras[:2]):
            camera_name = "left_wrist" if i == 0 else "right_wrist"
            print(f"  {camera_name}: '{path}'")
        
        return "stable_paths", working_cameras[:2]
        
    elif len(working_cameras) == 1:
        print("⚠️  Only 1 camera working with stable path")
        if len(working_indices) >= 2:
            print("But multiple indices are working - use index-based config:")
            for i, idx in enumerate(working_indices[:2]):
                camera_name = "left_wrist" if i == 0 else "right_wrist"  
                print(f"  {camera_name}: {idx}")
            return "indices", working_indices[:2]
        else:
            print("❌ Insufficient working cameras")
            return "insufficient", []
    
    elif len(working_indices) >= 2:
        print("⚠️  No stable paths, but indices working:")
        for i, idx in enumerate(working_indices[:2]):
            camera_name = "left_wrist" if i == 0 else "right_wrist"
            print(f"  {camera_name}: {idx}")
        return "indices", working_indices[:2]
    
    else:
        print("❌ Insufficient working cameras detected")
        print("\nTroubleshooting steps:")
        print("1. Check USB cable connections")
        print("2. Try different USB ports") 
        print("3. Reconnect cameras")
        print("4. Check camera power/settings")
        return "insufficient", []

def main():
    print("🔧 Camera Diagnostic Tool")
    print("=" * 50)
    
    get_usb_cameras()
    working_cameras = test_stable_paths()
    working_indices = test_video_indices()
    
    config_type, config_data = recommend_config(working_cameras, working_indices)
    
    if config_type == "stable_paths":
        print(f"\n🎯 Use these stable paths in your configuration:")
        print("left_wrist: {type: opencv, index_or_path: '" + config_data[0][0] + "', width: 640, height: 480, fps: 30},")
        print("right_wrist: {type: opencv, index_or_path: '" + config_data[1][0] + "', width: 640, height: 480, fps: 30},")
        
    elif config_type == "indices":  
        print(f"\n🎯 Use these indices in your configuration:")
        print("left_wrist: {type: opencv, index_or_path: " + str(config_data[0]) + ", width: 640, height: 480, fps: 30},")
        print("right_wrist: {type: opencv, index_or_path: " + str(config_data[1]) + ", width: 640, height: 480, fps: 30},")

if __name__ == "__main__":
    main()
