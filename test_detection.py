import sys
sys.path.insert(0, '.')
from backend.services.inference_engine import get_inference_engine
from backend.services.zone_manager import get_zone_manager
from backend.config.config import get_config
import cv2

# Check config
config = get_config()
print(f"Config classes: {config.inference.classes}")
print(f"Confidence threshold: {config.inference.confidence_threshold}\n")

# Load video
cap = cv2.VideoCapture('test_video.mp4')

# Get zones
zone_mgr = get_zone_manager()
zones = zone_mgr.get_zones_by_camera(5)  # Try camera ID 5 (latest)
if not zones:
    zones = zone_mgr.get_all_zones()

print(f"Zones found: {len(zones)}")
for zone in zones:
    print(f"  Zone '{zone['name']}' for camera {zone['camera_id']}: {zone['coordinates']}\n")

# Process first 10 frames
engine = get_inference_engine()
frame_count = 0
detection_count = 0

while frame_count < 5:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    detections = engine.detect_objects(frame)
    current_classes = config.inference.classes
    print(f"Config path usage: Default? {config.inference.classes}")

    if detections:
        detection_count += len(detections)
        print(f"Frame {frame_count}: {len(detections)} detections")
        for det in detections[:2]:
            center = engine.get_bbox_center(det['bbox'])
            print(f"  - {det['class_name']} ({det['confidence']:.2f}) at {det['bbox']}, center: {center}")
            
            # Check if in zone
            for zone in zones:
                in_zone = zone_mgr.is_point_in_zone(center, zone)
                if in_zone:
                    print(f"    ✓ IN ZONE '{zone['name']}'!")

print(f"\nTotal: {detection_count} detections in {frame_count} frames")

cap.release()
