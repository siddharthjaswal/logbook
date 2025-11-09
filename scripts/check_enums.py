"""Check existing enums in database."""
import sys
sys.path.insert(0, '/Users/sid/Projects/Backend/logbook')

from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname;"))
    enums = result.fetchall()
    print("Existing enum types:")
    for enum in enums:
        print(f"  - {enum[0]}")
