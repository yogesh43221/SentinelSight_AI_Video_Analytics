"""
Rules engine for event generation based on detections and zones
"""
import logging
import cv2
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from backend.services.zone_manager import get_zone_manager
from backend.services.event_store import get_event_store
from backend.services.inference_engine import get_inference_engine
from backend.config.config import get_config

logger = logging.getLogger(__name__)


class RulesEngine:
    def __init__(self):
        self.zone_manager = get_zone_manager()
        self.event_store = get_event_store()
        self.inference_engine = get_inference_engine()
        self.config = get_config()
        
        # Track objects in zones for loitering detection
        self.zone_occupancy: Dict[int, Dict] = defaultdict(dict)  # {zone_id: {object_key: first_seen_time}}
        
        # Event deduplication
        self.recent_events: Dict[str, datetime] = {}  # {event_hash: timestamp}
        self.dedup_window = timedelta(seconds=5)
        
        # Snapshot directory
        self.snapshot_dir = Path(self.config.system.snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        self.lock = threading.Lock()

    def process_detections(self, camera_id: int, frame, detections: List[Dict]):
        """Process detections and generate events based on rules"""
        if not detections:
            return

        # Get zones for this camera
        zones = self.zone_manager.get_zones_by_camera(camera_id)
        if not zones:
            return

        # Check each detection against zones
        for detection in detections:
            bbox = detection['bbox']
            center = self.inference_engine.get_bbox_center(bbox)
            object_type = detection['class_name']
            confidence = detection['confidence']

            for zone in zones:
                if self.zone_manager.is_point_in_zone(center, zone):
                    # Object is in zone
                    self._check_intrusion_rule(
                        camera_id, zone, detection, frame
                    )
                    self._check_loitering_rule(
                        camera_id, zone, detection, frame
                    )

        # Clean up old zone occupancy data
        self._cleanup_zone_occupancy()
        self._cleanup_recent_events()

    def _check_intrusion_rule(self, camera_id: int, zone: Dict, detection: Dict, frame):
        """Check intrusion rule: object enters restricted zone"""
        rule_config = self.config.rules.get('intrusion', {})
        if not rule_config.get('enabled', True):
            return

        # Create event hash for deduplication
        event_hash = f"{camera_id}_{zone['id']}_intrusion_{detection['class_name']}"
        
        if self._is_duplicate_event(event_hash):
            return

        # Generate event
        snapshot_path = self._save_snapshot(
            frame, detection['bbox'], camera_id, 'intrusion'
        )

        priority = rule_config.get('priority', 'high')
        
        metadata = {
            'zone_id': zone['id'],
            'zone_name': zone['name'],
            'inference_time_ms': self.inference_engine.get_avg_inference_time()
        }

        self.event_store.create_event(
            camera_id=camera_id,
            rule_type='intrusion',
            object_type=detection['class_name'],
            confidence=detection['confidence'],
            bbox=detection['bbox'],
            snapshot_path=snapshot_path,
            priority=priority,
            metadata=metadata
        )

        # Mark as recent event
        with self.lock:
            self.recent_events[event_hash] = datetime.now()

        logger.info(f"Intrusion event: {detection['class_name']} in zone '{zone['name']}' (camera {camera_id})")

    def _check_loitering_rule(self, camera_id: int, zone: Dict, detection: Dict, frame):
        """Check loitering rule: object remains in zone > threshold seconds"""
        rule_config = self.config.rules.get('loitering', {})
        if not rule_config.get('enabled', True):
            return

        threshold_seconds = rule_config.get('threshold_seconds', 30)
        
        # Only track persons for loitering
        if detection['class_name'] != 'person':
            return

        # Create object key (simple tracking by bbox center)
        center = self.inference_engine.get_bbox_center(detection['bbox'])
        object_key = f"{center[0]//50}_{center[1]//50}"  # Grid-based tracking
        
        zone_id = zone['id']
        current_time = datetime.now()

        with self.lock:
            if object_key not in self.zone_occupancy[zone_id]:
                # First time seeing this object in this zone
                self.zone_occupancy[zone_id][object_key] = current_time
                return
            
            # Check how long object has been in zone
            first_seen = self.zone_occupancy[zone_id][object_key]
            duration = (current_time - first_seen).total_seconds()

            if duration >= threshold_seconds:
                # Loitering detected
                event_hash = f"{camera_id}_{zone_id}_loitering_{object_key}"
                
                if self._is_duplicate_event(event_hash):
                    return

                # Generate event
                snapshot_path = self._save_snapshot(
                    frame, detection['bbox'], camera_id, 'loitering'
                )

                priority = rule_config.get('priority', 'medium')
                
                metadata = {
                    'zone_id': zone['id'],
                    'zone_name': zone['name'],
                    'duration_seconds': int(duration),
                    'inference_time_ms': self.inference_engine.get_avg_inference_time()
                }

                self.event_store.create_event(
                    camera_id=camera_id,
                    rule_type='loitering',
                    object_type=detection['class_name'],
                    confidence=detection['confidence'],
                    bbox=detection['bbox'],
                    snapshot_path=snapshot_path,
                    priority=priority,
                    metadata=metadata
                )

                # Mark as recent event
                self.recent_events[event_hash] = current_time
                
                # Reset tracking for this object
                del self.zone_occupancy[zone_id][object_key]

                logger.info(f"Loitering event: person in zone '{zone['name']}' for {int(duration)}s (camera {camera_id})")

    def _save_snapshot(self, frame, bbox: List[int], camera_id: int, rule_type: str) -> str:
        """Save snapshot with bounding box overlay"""
        try:
            # Draw bounding box on frame
            frame_copy = frame.copy()
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add timestamp
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame_copy, timestamp_str,
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0), 2
            )

            # Generate filename
            filename = f"cam{camera_id}_{rule_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = self.snapshot_dir / filename
            
            # Save image
            cv2.imwrite(str(filepath), frame_copy)
            
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
            return ""

    def _is_duplicate_event(self, event_hash: str) -> bool:
        """Check if event is a duplicate within dedup window"""
        with self.lock:
            if event_hash in self.recent_events:
                last_time = self.recent_events[event_hash]
                if datetime.now() - last_time < self.dedup_window:
                    return True
            return False

    def _cleanup_zone_occupancy(self):
        """Remove old zone occupancy data"""
        current_time = datetime.now()
        timeout = timedelta(seconds=60)  # Clear if not seen for 60s
        
        with self.lock:
            for zone_id in list(self.zone_occupancy.keys()):
                for object_key in list(self.zone_occupancy[zone_id].keys()):
                    first_seen = self.zone_occupancy[zone_id][object_key]
                    if current_time - first_seen > timeout:
                        del self.zone_occupancy[zone_id][object_key]

    def _cleanup_recent_events(self):
        """Remove old events from deduplication cache"""
        current_time = datetime.now()
        
        with self.lock:
            expired_keys = [
                k for k, v in self.recent_events.items()
                if current_time - v > self.dedup_window
            ]
            for key in expired_keys:
                del self.recent_events[key]


# Global rules engine instance
_rules_engine = None


def get_rules_engine() -> RulesEngine:
    """Get global rules engine instance"""
    global _rules_engine
    if _rules_engine is None:
        _rules_engine = RulesEngine()
    return _rules_engine
