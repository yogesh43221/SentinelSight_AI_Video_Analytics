"""
Inference engine using YOLOv8 for object detection
"""
import logging
import time
import threading
from typing import List, Dict, Optional
import numpy as np
from ultralytics import YOLO
from backend.config.config import get_config

logger = logging.getLogger(__name__)


class InferenceEngine:
    def __init__(self):
        self.config = get_config()
        self.model = None
        self.model_loaded = False
        self.inference_times = []
        self.lock = threading.Lock()
        self._load_model()

    def _load_model(self):
        """Load YOLO model"""
        try:
            model_path = self.config.inference.model
            logger.info(f"Loading YOLO model: {model_path}")
            
            self.model = YOLO(model_path)
            
            # Warm up model
            dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model(dummy_frame, verbose=False)
            
            self.model_loaded = True
            logger.info("YOLO model loaded and warmed up successfully")
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            self.model_loaded = False

    def detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame
        
        Returns:
            List of detections with format:
            {
                'class_id': int,
                'class_name': str,
                'confidence': float,
                'bbox': [x1, y1, x2, y2]
            }
        """
        if not self.model_loaded or self.model is None:
            return []

        try:
            start_time = time.time()
            
            # Convert BGR to RGB (OpenCV uses BGR, YOLO expects RGB)
            import cv2
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Prepare classes filter (None or empty list should be None for YOLO to detect all)
            classes = self.config.inference.classes
            if not classes:
                classes = None

            # Run inference
            results = self.model(
                rgb_frame,
                conf=self.config.inference.confidence_threshold,
                classes=classes,
                verbose=False
            )
            
            # Track inference time
            inference_time = (time.time() - start_time) * 1000  # ms
            with self.lock:
                self.inference_times.append(inference_time)
                if len(self.inference_times) > 100:
                    self.inference_times = self.inference_times[-100:]
            
            # Parse results
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Get class and confidence
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    class_name = result.names[class_id]
                    
                    detections.append({
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': [int(x1), int(y1), int(x2), int(y2)]
                    })
            
            return detections
        
        except Exception as e:
            logger.error(f"Error during inference: {e}")
            return []

    def get_bbox_center(self, bbox: List[int]) -> tuple:
        """Get center point of bounding box (bottom-center for zone checking)"""
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) // 2
        center_y = y2  # Bottom of bbox for better zone detection
        return (center_x, center_y)

    def get_avg_inference_time(self) -> float:
        """Get average inference time in milliseconds"""
        with self.lock:
            if not self.inference_times:
                return 0.0
            return sum(self.inference_times) / len(self.inference_times)

    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model_loaded


# Global inference engine instance
_inference_engine = None


def get_inference_engine() -> InferenceEngine:
    """Get global inference engine instance"""
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = InferenceEngine()
    return _inference_engine
