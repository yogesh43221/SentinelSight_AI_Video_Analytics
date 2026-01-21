"""
Zone management service
"""
import logging
import json
from typing import List, Optional, Dict
from datetime import datetime
from shapely.geometry import Point, Polygon
from backend.database.db import get_db

logger = logging.getLogger(__name__)


class ZoneManager:
    def __init__(self):
        self.db = get_db()

    def create_zone(self, camera_id: int, name: str, zone_type: str, coordinates: List[List[int]]) -> Dict:
        """Create a new zone"""
        try:
            # Validate coordinates
            if zone_type == "polygon" and len(coordinates) < 3:
                raise ValueError("Polygon must have at least 3 points")
            if zone_type == "rectangle" and len(coordinates) != 2:
                raise ValueError("Rectangle must have exactly 2 points (top-left, bottom-right)")
            
            coords_json = json.dumps(coordinates)
            cursor = self.db.execute(
                """
                INSERT INTO zones (camera_id, name, type, coordinates, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (camera_id, name, zone_type, coords_json, datetime.now())
            )
            zone_id = cursor.lastrowid
            logger.info(f"Created zone: {name} for camera {camera_id} (ID: {zone_id})")
            return self.get_zone(zone_id)
        except Exception as e:
            logger.error(f"Error creating zone: {e}")
            raise

    def get_zone(self, zone_id: int) -> Optional[Dict]:
        """Get zone by ID"""
        row = self.db.fetchone("SELECT * FROM zones WHERE id = ?", (zone_id,))
        if row:
            zone = dict(row)
            zone['coordinates'] = json.loads(zone['coordinates'])
            return zone
        return None

    def get_zones_by_camera(self, camera_id: int) -> List[Dict]:
        """Get all zones for a camera"""
        rows = self.db.fetchall("SELECT * FROM zones WHERE camera_id = ?", (camera_id,))
        zones = []
        for row in rows:
            zone = dict(row)
            zone['coordinates'] = json.loads(zone['coordinates'])
            zones.append(zone)
        return zones

    def get_all_zones(self) -> List[Dict]:
        """Get all zones"""
        rows = self.db.fetchall("SELECT * FROM zones")
        zones = []
        for row in rows:
            zone = dict(row)
            zone['coordinates'] = json.loads(zone['coordinates'])
            zones.append(zone)
        return zones

    def update_zone(self, zone_id: int, **kwargs) -> Optional[Dict]:
        """Update zone"""
        allowed_fields = ['name', 'type', 'coordinates']
        updates = {}
        
        for k, v in kwargs.items():
            if k in allowed_fields and v is not None:
                if k == 'coordinates':
                    updates[k] = json.dumps(v)
                else:
                    updates[k] = v
        
        if not updates:
            return self.get_zone(zone_id)
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [zone_id]
        
        self.db.execute(
            f"UPDATE zones SET {set_clause} WHERE id = ?",
            tuple(values)
        )
        
        logger.info(f"Updated zone {zone_id}")
        return self.get_zone(zone_id)

    def delete_zone(self, zone_id: int) -> bool:
        """Delete zone"""
        self.db.execute("DELETE FROM zones WHERE id = ?", (zone_id,))
        logger.info(f"Deleted zone {zone_id}")
        return True

    def is_point_in_zone(self, point: tuple, zone: Dict) -> bool:
        """Check if a point is inside a zone"""
        try:
            coordinates = zone['coordinates']
            
            if zone['type'] == 'polygon':
                polygon = Polygon(coordinates)
                return polygon.contains(Point(point))
            
            elif zone['type'] == 'rectangle':
                # Rectangle: [[x1, y1], [x2, y2]]
                x, y = point
                x1, y1 = coordinates[0]
                x2, y2 = coordinates[1]
                return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2)
            
            return False
        except Exception as e:
            logger.error(f"Error checking point in zone: {e}")
            return False


# Global zone manager instance
_zone_manager = None


def get_zone_manager() -> ZoneManager:
    """Get global zone manager instance"""
    global _zone_manager
    if _zone_manager is None:
        _zone_manager = ZoneManager()
    return _zone_manager
