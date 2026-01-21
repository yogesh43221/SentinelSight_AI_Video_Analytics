"""
Processing coordinator - ties together stream ingestion, inference, and rules engine
"""
import logging
import threading
import time
from typing import Dict
from backend.services.stream_ingestion import get_stream_ingestion
from backend.services.inference_engine import get_inference_engine
from backend.services.rules_engine import get_rules_engine
from backend.services.camera_manager import get_camera_manager
from backend.services.mqtt_publisher import get_mqtt_publisher

logger = logging.getLogger(__name__)


class ProcessingCoordinator:
    def __init__(self):
        self.stream_ingestion = get_stream_ingestion()
        self.inference_engine = get_inference_engine()
        self.rules_engine = get_rules_engine()
        self.camera_manager = get_camera_manager()
        self.mqtt_publisher = get_mqtt_publisher()
        
        self.processing_threads: Dict[int, threading.Thread] = {}
        self.stop_flags: Dict[int, threading.Event] = {}
        self.running = False

    def start_camera_processing(self, camera_id: int):
        """Start processing pipeline for a camera"""
        if camera_id in self.processing_threads and self.processing_threads[camera_id].is_alive():
            logger.warning(f"Processing already running for camera {camera_id}")
            return

        # Get camera details
        camera = self.camera_manager.get_camera(camera_id)
        if not camera:
            logger.error(f"Camera {camera_id} not found")
            return

        # Start stream ingestion
        self.stream_ingestion.start_camera(camera_id, camera['rtsp_url'])

        # Start processing thread
        self.stop_flags[camera_id] = threading.Event()
        thread = threading.Thread(
            target=self._processing_loop,
            args=(camera_id,),
            daemon=True
        )
        self.processing_threads[camera_id] = thread
        thread.start()
        
        logger.info(f"Started processing for camera {camera_id}")

    def stop_camera_processing(self, camera_id: int):
        """Stop processing pipeline for a camera"""
        if camera_id in self.stop_flags:
            self.stop_flags[camera_id].set()
        
        self.stream_ingestion.stop_camera(camera_id)
        logger.info(f"Stopped processing for camera {camera_id}")

    def _processing_loop(self, camera_id: int):
        """Main processing loop for a camera"""
        logger.info(f"Processing loop started for camera {camera_id}")
        
        while not self.stop_flags[camera_id].is_set():
            try:
                # Get next frame
                frame_data = self.stream_ingestion.get_frame(camera_id, timeout=1.0)
                
                if frame_data is None:
                    continue
                
                frame, timestamp = frame_data
                
                # Run inference
                detections = self.inference_engine.detect_objects(frame)
                
                # Process detections through rules engine
                if detections:
                    self.rules_engine.process_detections(camera_id, frame, detections)
            
            except Exception as e:
                logger.error(f"Error in processing loop for camera {camera_id}: {e}")
                time.sleep(1)  # Prevent tight error loop

        logger.info(f"Processing loop stopped for camera {camera_id}")

    def start_all_cameras(self):
        """Start processing for all cameras in database"""
        cameras = self.camera_manager.get_all_cameras()
        for camera in cameras:
            self.start_camera_processing(camera['id'])

    def stop_all_cameras(self):
        """Stop processing for all cameras"""
        for camera_id in list(self.stop_flags.keys()):
            self.stop_camera_processing(camera_id)

    def get_processing_status(self) -> Dict:
        """Get status of all processing pipelines"""
        status = {}
        for camera_id in self.processing_threads.keys():
            status[camera_id] = {
                'thread_alive': self.processing_threads[camera_id].is_alive(),
                'queue_depth': self.stream_ingestion.get_queue_depth(camera_id)
            }
        return status


# Global processing coordinator instance
_processing_coordinator = None


def get_processing_coordinator() -> ProcessingCoordinator:
    """Get global processing coordinator instance"""
    global _processing_coordinator
    if _processing_coordinator is None:
        _processing_coordinator = ProcessingCoordinator()
    return _processing_coordinator
