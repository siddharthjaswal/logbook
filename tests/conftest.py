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

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
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


# TODO: Add fixtures for:
# - test_user (created user in database)
# - auth_token (JWT token for authenticated requests)
# - test_trip (created trip in database)
