import sys
sys.path.insert(0, '.')
from backend.database.db import get_db

print("Initializing database...")
db = get_db()
print(f"Database initialized at {db.db_path}")

# Check tables
tables = db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
print(f"Tables: {[t['name'] for t in tables]}")
