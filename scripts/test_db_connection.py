"""
Test database connection.

This script verifies that PostgreSQL is properly configured
and accessible using the DATABASE_URL from .env file.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def test_connection():
    """Test database connection and display PostgreSQL version."""

    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    print(f"\nDatabase URL: {settings.DATABASE_URL.replace(settings.DATABASE_URL.split('@')[0].split('//')[1], '***') if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print("\nAttempting to connect...\n")

    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)

        # Test connection
        with engine.connect() as conn:
            # Get PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]

            # Get current database name
            result = conn.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]

            # Get current user
            result = conn.execute(text("SELECT current_user;"))
            user = result.fetchone()[0]

            # Display results
            print("✅ Connection successful!\n")
            print(f"Database: {db_name}")
            print(f"User: {user}")
            print(f"\nPostgreSQL Version:")
            print(f"{version}\n")
            print("=" * 60)
            print("✅ Database is ready for use!")
            print("=" * 60)

            return True

    except Exception as e:
        print("❌ Connection failed!\n")
        print(f"Error: {str(e)}\n")
        print("=" * 60)
        print("Troubleshooting steps:")
        print("1. Ensure PostgreSQL is running: brew services list")
        print("2. Verify DATABASE_URL in .env file")
        print("3. Check if database exists: psql -l")
        print("4. See docs/POSTGRESQL_SETUP.md for more help")
        print("=" * 60)

        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
