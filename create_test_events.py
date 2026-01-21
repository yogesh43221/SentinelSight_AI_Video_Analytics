import sys
import os
sys.path.insert(0, '.')
os.chdir('f:/MyProjects_YJ/Internshala/Saimax_Tech_Solutions_AI_Job')

from backend.services.event_store import get_event_store
from datetime import datetime
import cv2

# Create test events
store = get_event_store()

# Create a simple test image
img = cv2.imread('test_video.mp4')  # Just to get dimensions
if img is None:
    print("Creating blank image...")
    img = [[0]*640 for _ in range(480)]
    img = [[0, 255, 0] for row in img]  # Green image

# Save a test snapshot
cv2.imwrite('data/snapshots/test_event.jpg', img)

# Create 5 test events
for i in range(5):
    event = store.create_event(
        camera_id=5,
        rule_type='intrusion' if i % 2 == 0 else 'loitering',
        object_type='person',
        confidence=0.85 + (i * 0.02),
        bbox=[100 + i*10, 100, 200 + i*10, 200],
        snapshot_path='data/snapshots/test_event.jpg',
        priority='high' if i < 2 else 'medium',
        metadata={'test': True, 'index': i}
    )
    print(f"Created event {event['id']}: {event['rule_type']}")

print("\n✅ Created 5 test events! Check the Events page in your browser.")
