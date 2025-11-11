"""Check existing tables in database."""
import sys
sys.path.insert(0, '/Users/sid/Projects/Backend/logbook')

from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"))
    tables = result.fetchall()
    print("Existing tables:")
    for table in tables:
        print(f"  - {table[0]}")
