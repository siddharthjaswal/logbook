"""
Initialize database.

Creates all tables defined in SQLAlchemy models.
This is useful for initial setup before Alembic migrations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine, Base


def init_db():
    """Create all database tables."""

    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)
    print("\nCreating all tables...\n")

    try:
        # Import all models to register them with Base
        # TODO: Import models when they're created
        # from app.features.users.models import User
        # from app.features.trips.models import Trip
        # from app.features.trip_days.models import TripDay

        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("✅ All tables created successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print("❌ Failed to create tables!\n")
        print(f"Error: {str(e)}\n")
        print("=" * 60)

        return False


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
