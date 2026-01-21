"""
Event storage and retrieval service
"""
import logging
import json
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from backend.database.db import get_db

logger = logging.getLogger(__name__)


class EventStore:
    def __init__(self):
        self.db = get_db()

    def create_event(
        self,
        camera_id: int,
        rule_type: str,
        timestamp: datetime = None,
        object_type: str = None,
        confidence: float = None,
        bbox: List[int] = None,
        snapshot_path: str = None,
        priority: str = "medium",
        metadata: dict = None
    ) -> Dict:
        """Create a new event"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            bbox_json = json.dumps(bbox) if bbox else None
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor = self.db.execute(
                """
                INSERT INTO events (
                    camera_id, timestamp, rule_type, object_type, confidence,
                    bbox, snapshot_path, priority, status, metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
                """,
                (
                    camera_id, timestamp, rule_type, object_type, confidence,
                    bbox_json, snapshot_path, priority, metadata_json, datetime.now()
                )
            )
            event_id = cursor.lastrowid
            logger.info(f"Created event: {rule_type} for camera {camera_id} (ID: {event_id})")
            return self.get_event(event_id)
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise

    def get_event(self, event_id: int) -> Optional[Dict]:
        """Get event by ID"""
        row = self.db.fetchone("SELECT * FROM events WHERE id = ?", (event_id,))
        if row:
            event = dict(row)
            if event['bbox']:
                event['bbox'] = json.loads(event['bbox'])
            if event['metadata']:
                event['metadata'] = json.loads(event['metadata'])
            return event
        return None

    def query_events(
        self,
        camera_id: int = None,
        from_time: datetime = None,
        to_time: datetime = None,
        rule_type: str = None,
        priority: str = None,
        status: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict], int]:
        """Query events with filters"""
        query = "SELECT * FROM events WHERE 1=1"
        count_query = "SELECT COUNT(*) as count FROM events WHERE 1=1"
        params = []
        
        if camera_id is not None:
            query += " AND camera_id = ?"
            count_query += " AND camera_id = ?"
            params.append(camera_id)
        
        if from_time:
            query += " AND timestamp >= ?"
            count_query += " AND timestamp >= ?"
            params.append(from_time)
        
        if to_time:
            query += " AND timestamp <= ?"
            count_query += " AND timestamp <= ?"
            params.append(to_time)
        
        if rule_type:
            query += " AND rule_type = ?"
            count_query += " AND rule_type = ?"
            params.append(rule_type)
        
        if priority:
            query += " AND priority = ?"
            count_query += " AND priority = ?"
            params.append(priority)
        
        if status:
            query += " AND status = ?"
            count_query += " AND status = ?"
            params.append(status)
        
        # Get total count
        count_row = self.db.fetchone(count_query, tuple(params))
        total = count_row['count'] if count_row else 0
        
        # Get paginated results
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = self.db.fetchall(query, tuple(params))
        events = []
        for row in rows:
            event = dict(row)
            if event['bbox']:
                event['bbox'] = json.loads(event['bbox'])
            if event['metadata']:
                event['metadata'] = json.loads(event['metadata'])
            events.append(event)
        
        return events, total

    def update_event_status(self, event_id: int, status: str) -> Optional[Dict]:
        """Update event status"""
        self.db.execute(
            "UPDATE events SET status = ? WHERE id = ?",
            (status, event_id)
        )
        logger.info(f"Updated event {event_id} status to {status}")
        return self.get_event(event_id)

    def delete_old_events(self, retention_days: int = 30) -> int:
        """Delete events older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cursor = self.db.execute(
            "DELETE FROM events WHERE created_at < ?",
            (cutoff_date,)
        )
        deleted_count = cursor.rowcount
        logger.info(f"Deleted {deleted_count} events older than {retention_days} days")
        return deleted_count

    def get_event_stats(self, camera_id: int = None, hours: int = 24) -> Dict:
        """Get event statistics"""
        from_time = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT 
                rule_type,
                priority,
                COUNT(*) as count
            FROM events
            WHERE timestamp >= ?
        """
        params = [from_time]
        
        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)
        
        query += " GROUP BY rule_type, priority"
        
        rows = self.db.fetchall(query, tuple(params))
        
        stats = {
            'total': 0,
            'by_rule': {},
            'by_priority': {}
        }
        
        for row in rows:
            count = row['count']
            stats['total'] += count
            
            rule = row['rule_type']
            if rule not in stats['by_rule']:
                stats['by_rule'][rule] = 0
            stats['by_rule'][rule] += count
            
            priority = row['priority']
            if priority not in stats['by_priority']:
                stats['by_priority'][priority] = 0
            stats['by_priority'][priority] += count
        
        return stats


# Global event store instance
_event_store = None


def get_event_store() -> EventStore:
    """Get global event store instance"""
    global _event_store
    if _event_store is None:
        _event_store = EventStore()
    return _event_store
