"""
Unit tests for Trip CRUD operations.
"""

import pytest
from app.features.trips import crud
from app.features.trips.schemas import TripCreate, TripUpdate
from app.shared.enums import TripStatus, TripVisibility, TripType


@pytest.fixture
def trip_data():
    """Sample trip data for testing."""
    return {
        "name": "Japan Adventure",
        "description": "Two-week trip exploring Tokyo and Kyoto",
        "primary_destination_country": "Japan",
        "primary_destination_city": "Tokyo",
        "trip_type": TripType.MULTI_CITY,
        "status": TripStatus.PLANNING,
        "visibility": TripVisibility.PRIVATE,
        "currency": "USD",
        "tags": ["adventure", "culture"],
    }


@pytest.fixture
def test_trip(db, test_user, trip_data):
    """Create a test trip in the database."""
    trip_create = TripCreate(**trip_data)
    trip = crud.create_trip(db, trip_create, user_id=test_user.id)
    return trip


def test_create_trip(db, test_user, trip_data):
    """Test creating a trip."""
    trip_create = TripCreate(**trip_data)
    trip = crud.create_trip(db, trip_create, user_id=test_user.id)

    assert trip.id is not None
    assert trip.name == trip_data["name"]
    assert trip.created_by == test_user.id
    assert trip.status == TripStatus.PLANNING
    assert trip.visibility == TripVisibility.PRIVATE
    assert trip.deleted_at is None


def test_get_trip_by_id_owner(db, test_trip, test_user):
    """Test getting trip by ID as owner."""
    trip = crud.get_trip_by_id(db, test_trip.id, user_id=test_user.id)

    assert trip is not None
    assert trip.id == test_trip.id
    assert trip.name == test_trip.name


def test_get_trip_by_id_public(db, test_trip):
    """Test getting public trip without authentication."""
    # Make trip public
    test_trip.visibility = TripVisibility.PUBLIC
    db.commit()

    trip = crud.get_trip_by_id(db, test_trip.id)

    assert trip is not None
    assert trip.id == test_trip.id


def test_get_trip_by_id_private_no_access(db, test_trip):
    """Test getting private trip without authentication returns None."""
    trip = crud.get_trip_by_id(db, test_trip.id)

    assert trip is None


def test_get_trips_by_user(db, test_user, trip_data):
    """Test getting all trips for a user."""
    # Create multiple trips
    for i in range(3):
        data = trip_data.copy()
        data["name"] = f"Trip {i}"
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    trips = crud.get_trips_by_user(db, test_user.id)

    assert len(trips) == 3
    assert all(trip.created_by == test_user.id for trip in trips)


def test_get_trips_by_user_with_status_filter(db, test_user, trip_data):
    """Test getting trips filtered by status."""
    # Create trips with different statuses
    for status in [TripStatus.PLANNING, TripStatus.UPCOMING, TripStatus.PLANNING]:
        data = trip_data.copy()
        data["status"] = status
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    planning_trips = crud.get_trips_by_user(db, test_user.id, status_filter=TripStatus.PLANNING)

    assert len(planning_trips) == 2
    assert all(trip.status == TripStatus.PLANNING for trip in planning_trips)


def test_get_public_trips(db, test_user, trip_data):
    """Test getting public trips."""
    # Create public and private trips
    for i in range(2):
        data = trip_data.copy()
        data["name"] = f"Public Trip {i}"
        data["visibility"] = TripVisibility.PUBLIC
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    # Private trip
    private_data = trip_data.copy()
    private_data["visibility"] = TripVisibility.PRIVATE
    trip_create = TripCreate(**private_data)
    crud.create_trip(db, trip_create, user_id=test_user.id)

    public_trips = crud.get_public_trips(db)

    assert len(public_trips) == 2
    assert all(trip.visibility == TripVisibility.PUBLIC for trip in public_trips)


def test_update_trip(db, test_trip):
    """Test updating a trip."""
    trip_update = TripUpdate(
        name="Updated Trip Name",
        status=TripStatus.UPCOMING,
        budget_total=5000.00
    )

    updated_trip = crud.update_trip(db, test_trip, trip_update)

    assert updated_trip.name == "Updated Trip Name"
    assert updated_trip.status == TripStatus.UPCOMING
    assert updated_trip.budget_total == 5000.00
    # Other fields should remain unchanged
    assert updated_trip.description == test_trip.description


def test_delete_trip(db, test_trip):
    """Test soft deleting a trip."""
    crud.delete_trip(db, test_trip)

    assert test_trip.deleted_at is not None

    # Deleted trip should not be returned
    trip = crud.get_trip_by_id(db, test_trip.id, user_id=test_trip.created_by)
    assert trip is None


def test_check_trip_ownership_owner(test_trip, test_user):
    """Test checking ownership when user is owner."""
    is_owner = crud.check_trip_ownership(test_trip, test_user.id)
    assert is_owner is True


def test_check_trip_ownership_not_owner(test_trip):
    """Test checking ownership when user is not owner."""
    is_owner = crud.check_trip_ownership(test_trip, 99999)
    assert is_owner is False


def test_increment_trip_views(db, test_trip):
    """Test incrementing trip view count."""
    initial_views = test_trip.views_count

    crud.increment_trip_views(db, test_trip)

    assert test_trip.views_count == initial_views + 1


def test_get_user_trip_count(db, test_user, trip_data):
    """Test getting total trip count for user."""
    # Create multiple trips
    for i in range(5):
        data = trip_data.copy()
        data["name"] = f"Trip {i}"
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    count = crud.get_user_trip_count(db, test_user.id)

    assert count == 5


def test_search_trips(db, test_user, trip_data):
    """Test searching trips."""
    # Create trips with different names
    trip_names = ["Japan Adventure", "France Culinary Tour", "Japan Spring Trip"]
    for name in trip_names:
        data = trip_data.copy()
        data["name"] = name
        data["visibility"] = TripVisibility.PUBLIC
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    # Search for "Japan"
    # Note: All trips have Japan in country field from trip_data fixture,
    # plus two have "Japan" in the name, so we expect all 3 to match
    results = crud.search_trips(db, "Japan")

    assert len(results) == 3
    # Verify search matches on country (all 3) or name (2 of them)
    assert all("Japan" in trip.name or trip.primary_destination_country == "Japan" for trip in results)


def test_search_trips_includes_user_private(db, test_user, trip_data):
    """Test search includes user's private trips when authenticated."""
    # Create private trip with "Japan"
    data = trip_data.copy()
    data["name"] = "Japan Private Trip"
    data["visibility"] = TripVisibility.PRIVATE
    trip_create = TripCreate(**data)
    crud.create_trip(db, trip_create, user_id=test_user.id)

    # Search as the user
    results = crud.search_trips(db, "Japan", user_id=test_user.id)

    assert len(results) == 1
    assert results[0].visibility == TripVisibility.PRIVATE


def test_search_trips_excludes_others_private(db, test_user, trip_data):
    """Test search excludes other users' private trips."""
    # Create private trip
    data = trip_data.copy()
    data["name"] = "Japan Private Trip"
    data["visibility"] = TripVisibility.PRIVATE
    trip_create = TripCreate(**data)
    crud.create_trip(db, trip_create, user_id=test_user.id)

    # Search as different user (or unauthenticated)
    results = crud.search_trips(db, "Japan", user_id=99999)

    assert len(results) == 0
