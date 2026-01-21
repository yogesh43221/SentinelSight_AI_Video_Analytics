import sys
import cv2
import sqlite3
import torch
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_full")

sys.path.insert(0, '.')

print("--- DIAGNOSTIC START ---")

# 1. Check Config
try:
    from backend.config.config import get_config
    config = get_config()
    print(f"Config Loaded: Classes={config.inference.classes}, Thresh={config.inference.confidence_threshold}")
    print(f"DB URL: {config.database.url}")
except Exception as e:
    print(f"❌ Config Error: {e}")

# 2. Check Database
try:
    from backend.database.db import get_db
    db = get_db()
    
    # Check cameras
    cameras = db.fetchall("SELECT id, name, rtsp_url, status FROM cameras")
    print(f"Cameras ({len(cameras)}):")
    camera_id = None
    for c in cameras:
        print(f"  ID {c['id']}: {c['name']} ({c['rtsp_url']}) - {c['status']}")
        if 'people' in c['rtsp_url'] or 'walking' in c['rtsp_url']:
            camera_id = c['id']
            
    # Check zones
    zones = db.fetchall("SELECT id, camera_id, name, coordinates FROM zones")
    print(f"Zones ({len(zones)}):")
    current_zone = None
    for z in zones:
        print(f"  ID {z['id']} (Cam {z['camera_id']}): {z['name']} - {z['coordinates']}")
        if camera_id and z['camera_id'] == camera_id:
            current_zone = dict(z)

    # Check events
    event_count = db.fetchone("SELECT count(*) FROM events")[0]
    print(f"Total Events in DB: {event_count}")

except Exception as e:
    print(f"❌ Database Error: {e}")

# 3. Check Inference & Zone Logic
if camera_id:
    try:
        from backend.services.inference_engine import get_inference_engine
        from backend.services.zone_manager import get_zone_manager
        
        engine = get_inference_engine()
        zone_mgr = get_zone_manager()
        
        # Load Video
        video_path = 'people_walking.mp4'
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Failed to open video: {video_path}")
        else:
            print(f"Video opened: {video_path}")
            
            # Process 10 frames
            detections_found = False
            for i in range(10):
                ret, frame = cap.read()
                if not ret: break
                
                detections = engine.detect_objects(frame)
                if detections:
                    detections_found = True
                    print(f"Frame {i}: {len(detections)} detections")
                    for det in detections:
                        center = engine.get_bbox_center(det['bbox'])
                        print(f"  - {det['class_name']} ({det['confidence']:.2f}) at {center}")
                        
                        if current_zone:
                            in_zone = zone_mgr.is_point_in_zone(center, current_zone)
                            print(f"    in_zone? {in_zone}")
                            
            if not detections_found:
                print("❌ No detections in first 10 frames!")
            else:
                print("✅ Detections confirmed.")

    except Exception as e:
        print(f"❌ Inference/Zone Error: {e}")
else:
    print("Warning: Could not find 'people' camera to test inference.")

print("--- DIAGNOSTIC END ---")
