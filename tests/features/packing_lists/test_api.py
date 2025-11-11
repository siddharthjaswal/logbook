"""
Integration tests for PackingList API endpoints.
"""

import pytest
from fastapi import status
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.features.packing_lists import crud
from app.features.packing_lists.schemas import (
    PackingListCreate,
    PackingItemCreate,
)
from app.shared.enums import (
    PackingCategory,
    Priority,
    TripType,
    TripStatus,
    TripVisibility,
)


@pytest.fixture
def test_trip(db, test_user):
    """Create a test trip for packing list tests."""
    trip_create = TripCreate(
        name="Test Trip",
        primary_destination_country="Japan",
        trip_type=TripType.SINGLE_DESTINATION,
        status=TripStatus.PLANNING,
        visibility=TripVisibility.PRIVATE,
        currency="USD",
    )
    return trips_crud.create_trip(db, trip_create, user_id=test_user.id)


@pytest.fixture
def packing_list_data(test_trip):
    """Sample packing list data for API testing."""
    return {
        "trip_id": test_trip.id,
        "name": "Main Luggage",
        "description": "Items for checked luggage",
    }


@pytest.fixture
def test_packing_list(db, test_trip, test_user):
    """Create a test packing list in the database."""
    list_create = PackingListCreate(
        trip_id=test_trip.id,
        name="Test Packing List",
        description="Test description",
    )
    return crud.create_packing_list(db, list_create, user_id=test_user.id)


@pytest.fixture
def packing_item_data():
    """Sample packing item data for API testing."""
    return {
        "name": "T-Shirt",
        "category": "clothing",
        "quantity": 5,
        "priority": "medium",
        "notes": "Cotton shirts for summer",
    }


@pytest.fixture
def test_packing_item(db, test_packing_list):
    """Create a test packing item in the database."""
    item_create = PackingItemCreate(
        name="Test Item",
        category=PackingCategory.CLOTHING,
        quantity=3,
        priority=Priority.MEDIUM,
    )
    return crud.create_packing_item(db, test_packing_list.id, item_create)


# PACKING LIST API TESTS

def test_create_packing_list_success(client, auth_headers, packing_list_data):
    """Test creating a packing list."""
    response = client.post(
        "/api/v1/packing-lists", json=packing_list_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == packing_list_data["name"]
    assert data["description"] == packing_list_data["description"]
    assert data["trip_id"] == packing_list_data["trip_id"]
    assert data["id"] is not None


def test_create_packing_list_unauthorized(client, packing_list_data):
    """Test creating a packing list without authentication."""
    response = client.post("/api/v1/packing-lists", json=packing_list_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_packing_list_by_id_owner(client, auth_headers, test_packing_list):
    """Test getting packing list by ID as owner."""
    response = client.get(
        f"/api/v1/packing-lists/{test_packing_list.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_packing_list.id
    assert data["name"] == test_packing_list.name


def test_get_packing_list_unauthorized(client, test_packing_list):
    """Test getting packing list without authentication."""
    response = client.get(f"/api/v1/packing-lists/{test_packing_list.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_packing_list_not_found(client, auth_headers):
    """Test getting non-existent packing list."""
    response = client.get("/api/v1/packing-lists/99999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_trip_packing_lists(client, auth_headers, db, test_trip, test_user):
    """Test listing all packing lists for a trip."""
    # Create multiple packing lists
    for i in range(3):
        list_create = PackingListCreate(
            trip_id=test_trip.id,
            name=f"Packing List {i}",
            description=f"Description {i}",
        )
        crud.create_packing_list(db, list_create, user_id=test_user.id)

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/packing-lists", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    assert all(pl["trip_id"] == test_trip.id for pl in data)


def test_delete_packing_list_owner(client, auth_headers, test_packing_list, db):
    """Test deleting packing list as owner."""
    response = client.delete(
        f"/api/v1/packing-lists/{test_packing_list.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify soft delete
    db.refresh(test_packing_list)
    assert test_packing_list.deleted_at is not None


def test_delete_packing_list_unauthorized(client, test_packing_list):
    """Test deleting packing list without authentication."""
    response = client.delete(f"/api/v1/packing-lists/{test_packing_list.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_packing_list_not_found(client, auth_headers):
    """Test deleting non-existent packing list."""
    response = client.delete("/api/v1/packing-lists/99999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


# PACKING ITEM API TESTS

def test_create_packing_item_success(client, auth_headers, test_packing_list, packing_item_data):
    """Test creating a packing item."""
    response = client.post(
        f"/api/v1/packing-lists/{test_packing_list.id}/items",
        json=packing_item_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == packing_item_data["name"]
    assert data["category"] == packing_item_data["category"]
    assert data["quantity"] == packing_item_data["quantity"]
    assert data["is_packed"] is False
    assert data["id"] is not None


def test_create_packing_item_unauthorized(client, test_packing_list, packing_item_data):
    """Test creating a packing item without authentication."""
    response = client.post(
        f"/api/v1/packing-lists/{test_packing_list.id}/items",
        json=packing_item_data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_packing_item_success(client, auth_headers, test_packing_item):
    """Test updating a packing item."""
    update_data = {
        "name": "Updated Item",
        "quantity": 10,
        "priority": "high",
    }

    response = client.put(
        f"/api/v1/packing-items/{test_packing_item.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Item"
    assert data["quantity"] == 10
    assert data["priority"] == "high"


def test_update_packing_item_unauthorized(client, test_packing_item):
    """Test updating a packing item without authentication."""
    response = client.put(
        f"/api/v1/packing-items/{test_packing_item.id}",
        json={"name": "Updated"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_packing_item_not_found(client, auth_headers):
    """Test updating non-existent packing item."""
    response = client.put(
        "/api/v1/packing-items/99999",
        json={"name": "Updated"},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_toggle_pack_status_success(client, auth_headers, test_packing_item, db):
    """Test toggling pack status of an item."""
    # Initially unpacked
    assert test_packing_item.is_packed is False

    response = client.post(
        f"/api/v1/packing-items/{test_packing_item.id}/toggle-pack",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_packed"] is True
    assert data["packed_at"] is not None

    # Toggle again to unpack
    response = client.post(
        f"/api/v1/packing-items/{test_packing_item.id}/toggle-pack",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_packed"] is False
    assert data["packed_at"] is None


def test_toggle_pack_status_unauthorized(client, test_packing_item):
    """Test toggling pack status without authentication."""
    response = client.post(
        f"/api/v1/packing-items/{test_packing_item.id}/toggle-pack"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_toggle_pack_status_not_found(client, auth_headers):
    """Test toggling pack status of non-existent item."""
    response = client.post(
        "/api/v1/packing-items/99999/toggle-pack",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_packing_summary_success(client, auth_headers, db, test_packing_list):
    """Test getting packing summary for a list."""
    # Create multiple items with different pack statuses
    items_data = [
        ("T-Shirt", PackingCategory.CLOTHING, True),
        ("Pants", PackingCategory.CLOTHING, False),
        ("Toothbrush", PackingCategory.TOILETRIES, True),
        ("Phone Charger", PackingCategory.ELECTRONICS, False),
    ]

    for name, category, is_packed in items_data:
        item = crud.create_packing_item(
            db,
            test_packing_list.id,
            PackingItemCreate(name=name, category=category),
        )
        if is_packed:
            crud.toggle_packed(db, item)

    response = client.get(
        f"/api/v1/packing-lists/{test_packing_list.id}/summary",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 4
    assert data["packed_items"] == 2
    assert data["percentage_packed"] == 50.0
    assert "by_category" in data
    assert data["by_category"]["clothing"]["total"] == 2
    assert data["by_category"]["clothing"]["packed"] == 1


def test_get_packing_summary_empty_list(client, auth_headers, test_packing_list):
    """Test getting packing summary for empty list."""
    response = client.get(
        f"/api/v1/packing-lists/{test_packing_list.id}/summary",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 0
    assert data["packed_items"] == 0
    assert data["percentage_packed"] == 0
    assert data["by_category"] == {}


def test_get_packing_summary_unauthorized(client, test_packing_list):
    """Test getting packing summary without authentication."""
    response = client.get(
        f"/api/v1/packing-lists/{test_packing_list.id}/summary"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
