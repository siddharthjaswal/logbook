"""
Pytest configuration and fixtures.

This module provides shared fixtures for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# Import all models to register them with Base
from app.features.users.models import User
from app.features.trips.models import Trip
from app.features.trip_days.models import TripDay

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test.

    Yields:
        Database session for testing
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Create a test client with test database.

    Args:
        db: Test database session

    Yields:
        FastAPI test client
    """
    # Import the actual get_db dependency used in the app
    from app.core.deps import get_db as get_db_dependency

    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Override the dependency
    app.dependency_overrides[get_db_dependency] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "google_id": "test_google_id_123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "email_verified": True,
    }


@pytest.fixture
def test_trip_data():
    """Sample trip data for testing."""
    return {
        "name": "Europe Trip",
        "description": "Summer vacation in Europe",
        "start_date_timestamp": 1717200000,  # June 1, 2024
        "end_date_timestamp": 1719792000,  # June 30, 2024
        "start_timezone": "UTC",
        "end_timezone": "UTC",
        "primary_destination_country": "France",
        "primary_destination_city": "Paris",
        "status": "planning",
        "visibility": "private",
    }


@pytest.fixture
def test_trip_day_data():
    """Sample trip day data for testing."""
    return {
        "trip_id": 1,
        "date": "2024-06-02",
        "day_number": 1,
        "day_type": "sightseeing",
        "title": "Explore Paris",
        "place": "Paris City Center",
        "place_city": "Paris",
        "place_country": "France",
        "timezone": "Europe/Paris",
        "activities": [
            {
                "time": "09:00",
                "name": "Eiffel Tower",
                "duration_hours": 2,
                "cost": 25.0,
            }
        ],
    }


@pytest.fixture
def test_user(db, test_user_data):
    """Create a test user in the database."""
    from app.features.users.crud import create_user
    from app.features.users.schemas import UserCreate

    user_create = UserCreate(**test_user_data)
    user = create_user(db, user_create)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers with a valid JWT token."""
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_trip(db, test_user, test_trip_data):
    """Create a test trip in the database owned by test_user."""
    from app.features.trips.crud import create_trip
    from app.features.trips.schemas import TripCreate

    trip_create = TripCreate(**test_trip_data)
    trip = create_trip(db, trip_create, user_id=test_user.id)
    return trip


@pytest.fixture
def test_other_user(db):
    """Create another test user in the database."""
    from app.features.users.crud import create_user
    from app.features.users.schemas import UserCreate

    user_create = UserCreate(
        google_id="other_google_id_456",
        email="other@example.com",
        first_name="Other",
        last_name="User",
        email_verified=True
    )
    user = create_user(db, user_create)
    return user


@pytest.fixture
def test_trip_other_user(db, test_other_user, test_trip_data):
    """Create a test trip owned by test_other_user."""
    from app.features.trips.crud import create_trip
    from app.features.trips.schemas import TripCreate

    trip_create = TripCreate(**test_trip_data)
    trip = create_trip(db, trip_create, user_id=test_other_user.id)
    return trip


@pytest.fixture
def test_trip_other_user_with_day(db, test_other_user, test_trip_other_user):
    """Create a test trip owned by test_other_user with a trip day."""
    from app.features.trip_days.crud import create_trip_day
    from app.features.trip_days.schemas import TripDayCreate
    from datetime import date

    trip_day_create = TripDayCreate(
        trip_id=test_trip_other_user.id,
        date=date(2025, 7, 15),
        day_number=1,
        place="Paris",
        timezone="UTC"
    )
    trip_day = create_trip_day(db, trip_day_create)

    return {
        "trip_id": test_trip_other_user.id,
        "day_id": trip_day.id
    }
