import sqlite3
import os

db_path = 'data/sentinelsight.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path, timeout=5)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM events")
    count = cursor.fetchone()[0]
    print(f"Event count: {count}")
    conn.close()
except sqlite3.OperationalError as e:
    print(f"DB Error: {e}")
except Exception as e:
    print(f"Error: {e}")
