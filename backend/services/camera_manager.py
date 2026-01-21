"""
Camera management service
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict
import json
from backend.database.db import get_db

logger = logging.getLogger(__name__)


class CameraManager:
    def __init__(self):
        self.db = get_db()

    def create_camera(self, name: str, rtsp_url: str, location_tag: Optional[str] = None) -> Dict:
        """Create a new camera"""
        try:
            cursor = self.db.execute(
                """
                INSERT INTO cameras (name, location_tag, rtsp_url, status, created_at, updated_at)
                VALUES (?, ?, ?, 'offline', ?, ?)
                """,
                (name, location_tag, rtsp_url, datetime.now(), datetime.now())
            )
            camera_id = cursor.lastrowid
            logger.info(f"Created camera: {name} (ID: {camera_id})")
            return self.get_camera(camera_id)
        except Exception as e:
            logger.error(f"Error creating camera: {e}")
            raise

    def get_camera(self, camera_id: int) -> Optional[Dict]:
        """Get camera by ID"""
        row = self.db.fetchone("SELECT * FROM cameras WHERE id = ?", (camera_id,))
        if row:
            return dict(row)
        return None

    def get_all_cameras(self) -> List[Dict]:
        """Get all cameras"""
        rows = self.db.fetchall("SELECT * FROM cameras ORDER BY created_at DESC")
        return [dict(row) for row in rows]

    def update_camera(self, camera_id: int, **kwargs) -> Optional[Dict]:
        """Update camera fields"""
        allowed_fields = ['name', 'location_tag', 'rtsp_url', 'status', 'fps', 'last_frame_time']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        
        if not updates:
            return self.get_camera(camera_id)
        
        updates['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [camera_id]
        
        self.db.execute(
            f"UPDATE cameras SET {set_clause} WHERE id = ?",
            tuple(values)
        )
        
        logger.info(f"Updated camera {camera_id}: {updates}")
        return self.get_camera(camera_id)

    def delete_camera(self, camera_id: int) -> bool:
        """Delete camera"""
        self.db.execute("DELETE FROM cameras WHERE id = ?", (camera_id,))
        logger.info(f"Deleted camera {camera_id}")
        return True

    def update_status(self, camera_id: int, status: str, fps: float = 0.0):
        """Update camera status and FPS"""
        self.update_camera(
            camera_id,
            status=status,
            fps=fps,
            last_frame_time=datetime.now() if status == 'online' else None
        )

    def get_camera_by_url(self, rtsp_url: str) -> Optional[Dict]:
        """Get camera by RTSP URL"""
        row = self.db.fetchone("SELECT * FROM cameras WHERE rtsp_url = ?", (rtsp_url,))
        if row:
            return dict(row)
        return None


# Global camera manager instance
_camera_manager = None


def get_camera_manager() -> CameraManager:
    """Get global camera manager instance"""
    global _camera_manager
    if _camera_manager is None:
        _camera_manager = CameraManager()
    return _camera_manager
