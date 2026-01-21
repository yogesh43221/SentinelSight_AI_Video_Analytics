"""
Database schema and initialization for SentinelSight
"""
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "../data/sentinelsight.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.lock = threading.Lock()
        self.initialize()

    def initialize(self):
        """Initialize database with schema"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Database initialized at {self.db_path}")

    def _create_tables(self):
        """Create all database tables"""
        cursor = self.conn.cursor()

        # Cameras table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location_tag TEXT,
                rtsp_url TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'offline',
                fps REAL DEFAULT 0,
                last_frame_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Zones table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'polygon',
                coordinates TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE
            )
        """)

        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                rule_type TEXT NOT NULL,
                object_type TEXT,
                confidence REAL,
                bbox TEXT,
                snapshot_path TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'new',
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for fast queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_rule ON events(rule_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_priority ON events(priority)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_events_composite ON events(camera_id, timestamp DESC)"
        )

        self.conn.commit()
        logger.info("Database tables created successfully")

    def execute(self, query: str, params: tuple = ()):
        """Execute a query and return cursor"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor

    def fetchone(self, query: str, params: tuple = ()):
        """Fetch one result"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()):
        """Fetch all results"""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Global database instance
db = None


def get_db():
    """Get database instance"""
    global db
    if db is None:
        from backend.config.config import get_config
        config = get_config()
        # Parse path from URL (remove sqlite:/// prefix)
        db_path = config.database.url.replace("sqlite:///", "")
        db = Database(db_path)
    return db


def close_db():
    """Close database connection"""
    global db
    if db:
        db.close()
        db = None
