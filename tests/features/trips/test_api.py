"""
Integration tests for Trip API endpoints.
"""

import pytest
from fastapi import status
from app.features.trips.schemas import TripCreate
from app.features.trips import crud
from app.shared.enums import TripStatus, TripVisibility, TripType


@pytest.fixture
def trip_data():
    """Sample trip data for testing."""
    return {
        "name": "Japan Adventure",
        "description": "Two-week trip exploring Tokyo and Kyoto",
        "primary_destination_country": "Japan",
        "primary_destination_city": "Tokyo",
        "trip_type": "multi_city",
        "status": "planning",
        "visibility": "private",
        "currency": "USD",
        "tags": ["adventure", "culture"],
    }


@pytest.fixture
def test_trip(db, test_user):
    """Create a test trip in the database."""
    trip_create = TripCreate(
        name="Test Trip",
        description="Test trip description",
        primary_destination_country="Japan",
        trip_type=TripType.SINGLE_DESTINATION,
        status=TripStatus.PLANNING,
        visibility=TripVisibility.PRIVATE,
    )
    return crud.create_trip(db, trip_create, user_id=test_user.id)


def test_create_trip_success(client, auth_headers, trip_data):
    """Test creating a trip."""
    response = client.post(
        "/api/v1/trips",
        json=trip_data,
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == trip_data["name"]
    assert data["id"] is not None
    assert "created_at" in data


def test_create_trip_unauthorized(client, trip_data):
    """Test creating a trip without authentication."""
    response = client.post("/api/v1/trips", json=trip_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_my_trips(client, auth_headers, db, test_user, trip_data):
    """Test listing user's trips."""
    # Create multiple trips
    for i in range(3):
        data = trip_data.copy()
        data["name"] = f"Trip {i}"
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    response = client.get("/api/v1/trips", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3


def test_list_my_trips_with_status_filter(client, auth_headers, db, test_user, trip_data):
    """Test listing trips filtered by status."""
    # Create trips with different statuses
    trip_create = TripCreate(**trip_data)
    crud.create_trip(db, trip_create, user_id=test_user.id)

    data2 = trip_data.copy()
    data2["status"] = TripStatus.UPCOMING
    trip_create2 = TripCreate(**data2)
    crud.create_trip(db, trip_create2, user_id=test_user.id)

    response = client.get(
        "/api/v1/trips?status_filter=planning",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "planning"


def test_get_trip_as_owner(client, auth_headers, test_trip):
    """Test getting trip as owner."""
    response = client.get(f"/api/v1/trips/{test_trip.id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_trip.id
    assert data["name"] == test_trip.name


def test_get_trip_public(client, db, test_trip):
    """Test getting public trip without authentication."""
    # Make trip public
    test_trip.visibility = TripVisibility.PUBLIC
    db.commit()

    response = client.get(f"/api/v1/trips/{test_trip.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_trip.id


def test_get_trip_private_access_denied(client, test_trip):
    """Test getting private trip without authentication."""
    response = client.get(f"/api/v1/trips/{test_trip.id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_trip_not_found(client, auth_headers):
    """Test getting non-existent trip."""
    response = client.get("/api/v1/trips/99999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_trip_as_owner(client, auth_headers, test_trip):
    """Test updating trip as owner."""
    update_data = {
        "name": "Updated Trip Name",
        "status": "upcoming"
    }

    response = client.put(
        f"/api/v1/trips/{test_trip.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Trip Name"
    assert data["status"] == "upcoming"


def test_update_trip_unauthorized(client, test_trip):
    """Test updating trip without authentication."""
    response = client.put(
        f"/api/v1/trips/{test_trip.id}",
        json={"name": "Updated"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_trip_not_found(client, auth_headers):
    """Test updating non-existent trip."""
    response = client.put(
        "/api/v1/trips/99999",
        json={"name": "Updated"},
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_trip_as_owner(client, auth_headers, test_trip, db):
    """Test deleting trip as owner."""
    response = client.delete(f"/api/v1/trips/{test_trip.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["trip_id"] == test_trip.id

    # Verify trip is soft deleted
    db.refresh(test_trip)
    assert test_trip.deleted_at is not None


def test_delete_trip_unauthorized(client, test_trip):
    """Test deleting trip without authentication."""
    response = client.delete(f"/api/v1/trips/{test_trip.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_trip_not_found(client, auth_headers):
    """Test deleting non-existent trip."""
    response = client.delete("/api/v1/trips/99999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_browse_public_trips(client, db, test_user, trip_data):
    """Test browsing public trips."""
    # Create public trips
    for i in range(2):
        data = trip_data.copy()
        data["name"] = f"Public Trip {i}"
        data["visibility"] = TripVisibility.PUBLIC
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    # Create private trip (should not appear)
    private_data = trip_data.copy()
    private_data["visibility"] = TripVisibility.PRIVATE
    trip_create = TripCreate(**private_data)
    crud.create_trip(db, trip_create, user_id=test_user.id)

    response = client.get("/api/v1/trips/public")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_browse_public_trips_with_filters(client, db, test_user, trip_data):
    """Test browsing public trips with filters."""
    # Create trips in different countries
    trip_create = TripCreate(**trip_data)
    trip_create.visibility = TripVisibility.PUBLIC
    crud.create_trip(db, trip_create, user_id=test_user.id)

    france_data = trip_data.copy()
    france_data["primary_destination_country"] = "France"
    france_data["visibility"] = TripVisibility.PUBLIC
    trip_create2 = TripCreate(**france_data)
    crud.create_trip(db, trip_create2, user_id=test_user.id)

    response = client.get("/api/v1/trips/public?country=Japan")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["primary_destination_country"] == "Japan"


def test_search_trips(client, auth_headers, db, test_user, trip_data):
    """Test searching trips."""
    # Create trips
    trip_create = TripCreate(**trip_data)
    trip_create.visibility = TripVisibility.PUBLIC
    crud.create_trip(db, trip_create, user_id=test_user.id)

    response = client.get("/api/v1/trips/search?q=Japan", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 1


def test_search_trips_no_query(client, auth_headers):
    """Test search without query parameter."""
    response = client.get("/api/v1/trips/search", headers=auth_headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_my_trip_stats(client, auth_headers, db, test_user, trip_data):
    """Test getting trip statistics."""
    # Create trips
    for i in range(3):
        data = trip_data.copy()
        data["name"] = f"Trip {i}"
        trip_create = TripCreate(**data)
        crud.create_trip(db, trip_create, user_id=test_user.id)

    response = client.get("/api/v1/trips/stats/me", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_trips"] == 3
    assert data["user_id"] == test_user.id


def test_trip_view_count_increments(client, db, test_trip):
    """Test that view count increments when viewing trip."""
    # Make trip public
    test_trip.visibility = TripVisibility.PUBLIC
    db.commit()

    initial_views = test_trip.views_count

    # View trip (without authentication)
    client.get(f"/api/v1/trips/{test_trip.id}")

    db.refresh(test_trip)
    assert test_trip.views_count == initial_views + 1
