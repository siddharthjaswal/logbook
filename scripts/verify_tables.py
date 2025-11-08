"""
Verify database tables and schema.

This script checks that all tables were created correctly
and displays their structure.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.database import engine


def verify_tables():
    """Verify all tables were created correctly."""

    print("=" * 70)
    print("Database Schema Verification")
    print("=" * 70)

    inspector = inspect(engine)

    # Get all tables
    tables = inspector.get_table_names()

    print(f"\n📊 Found {len(tables)} tables:\n")
    for table in tables:
        print(f"  ✅ {table}")

    # Verify expected tables
    expected_tables = ['users', 'trips', 'trip_days', 'alembic_version']
    missing_tables = set(expected_tables) - set(tables)

    if missing_tables:
        print(f"\n❌ Missing tables: {missing_tables}")
        return False

    # Show table structures
    print("\n" + "=" * 70)
    print("Table Structures")
    print("=" * 70)

    for table_name in ['users', 'trips', 'trip_days']:
        columns = inspector.get_columns(table_name)
        indexes = inspector.get_indexes(table_name)

        print(f"\n📋 {table_name.upper()} ({len(columns)} columns, {len(indexes)} indexes)")
        print("-" * 70)

        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            print(f"  {col['name']:30} {str(col['type']):20} {nullable}{default}")

    # Count records in each table
    print("\n" + "=" * 70)
    print("Table Record Counts")
    print("=" * 70)

    with engine.connect() as conn:
        for table_name in ['users', 'trips', 'trip_days']:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            print(f"  {table_name:20} {count:10} records")

    print("\n" + "=" * 70)
    print("✅ All tables created successfully!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = verify_tables()
    sys.exit(0 if success else 1)
