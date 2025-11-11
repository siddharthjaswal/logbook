"""
Unit tests for PackingList CRUD operations.
"""

import pytest
from datetime import datetime
from app.features.packing_lists import crud
from app.features.packing_lists.schemas import (
    PackingListCreate,
    PackingListUpdate,
    PackingItemCreate,
    PackingItemUpdate,
)
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
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
    """Sample packing list data for testing."""
    return {
        "trip_id": test_trip.id,
        "name": "Main Luggage",
        "description": "Items for checked luggage",
    }


@pytest.fixture
def test_packing_list(db, packing_list_data, test_user):
    """Create a test packing list in the database."""
    list_create = PackingListCreate(**packing_list_data)
    return crud.create_packing_list(db, list_create, user_id=test_user.id)


@pytest.fixture
def packing_item_data():
    """Sample packing item data for testing."""
    return {
        "name": "T-Shirt",
        "category": PackingCategory.CLOTHING,
        "quantity": 5,
        "priority": Priority.MEDIUM,
        "notes": "Cotton shirts for summer",
    }


@pytest.fixture
def test_packing_item(db, test_packing_list, packing_item_data):
    """Create a test packing item in the database."""
    item_create = PackingItemCreate(**packing_item_data)
    return crud.create_packing_item(db, test_packing_list.id, item_create)


# PACKING LIST TESTS

def test_create_packing_list(db, packing_list_data, test_user):
    """Test creating a packing list."""
    list_create = PackingListCreate(**packing_list_data)
    packing_list = crud.create_packing_list(db, list_create, user_id=test_user.id)

    assert packing_list.id is not None
    assert packing_list.name == packing_list_data["name"]
    assert packing_list.description == packing_list_data["description"]
    assert packing_list.trip_id == packing_list_data["trip_id"]
    assert packing_list.created_by == test_user.id
    assert packing_list.deleted_at is None


def test_get_packing_list_by_id(db, test_packing_list):
    """Test getting a packing list by ID."""
    packing_list = crud.get_packing_list_by_id(db, test_packing_list.id)

    assert packing_list is not None
    assert packing_list.id == test_packing_list.id
    assert packing_list.name == test_packing_list.name


def test_get_packing_list_by_id_not_found(db):
    """Test getting non-existent packing list returns None."""
    packing_list = crud.get_packing_list_by_id(db, 99999)
    assert packing_list is None


def test_get_packing_lists_by_trip(db, test_trip, packing_list_data, test_user):
    """Test getting all packing lists for a trip."""
    # Create multiple packing lists
    for i in range(3):
        data = packing_list_data.copy()
        data["name"] = f"Packing List {i}"
        list_create = PackingListCreate(**data)
        crud.create_packing_list(db, list_create, user_id=test_user.id)

    packing_lists = crud.get_packing_lists_by_trip(db, test_trip.id)

    assert len(packing_lists) == 3
    assert all(pl.trip_id == test_trip.id for pl in packing_lists)


def test_update_packing_list(db, test_packing_list):
    """Test updating a packing list."""
    list_update = PackingListUpdate(
        name="Updated Luggage",
        description="Updated description for checked luggage",
    )

    updated_list = crud.update_packing_list(db, test_packing_list, list_update)

    assert updated_list.name == "Updated Luggage"
    assert updated_list.description == "Updated description for checked luggage"
    # Original fields should remain unchanged
    assert updated_list.trip_id == test_packing_list.trip_id


def test_delete_packing_list(db, test_packing_list):
    """Test soft deleting a packing list."""
    crud.delete_packing_list(db, test_packing_list)

    assert test_packing_list.deleted_at is not None

    # Deleted packing list should not be returned
    packing_list = crud.get_packing_list_by_id(db, test_packing_list.id)
    assert packing_list is None


# PACKING ITEM TESTS

def test_create_packing_item(db, test_packing_list, packing_item_data):
    """Test creating a packing item."""
    item_create = PackingItemCreate(**packing_item_data)
    item = crud.create_packing_item(db, test_packing_list.id, item_create)

    assert item.id is not None
    assert item.name == packing_item_data["name"]
    assert item.category == PackingCategory.CLOTHING
    assert item.quantity == 5
    assert item.priority == Priority.MEDIUM
    assert item.notes == packing_item_data["notes"]
    assert item.is_packed is False
    assert item.packed_at is None
    assert item.packing_list_id == test_packing_list.id


def test_create_packing_item_with_defaults(db, test_packing_list):
    """Test creating a packing item with default values."""
    item_create = PackingItemCreate(
        name="Passport",
        category=PackingCategory.DOCUMENTS,
    )
    item = crud.create_packing_item(db, test_packing_list.id, item_create)

    assert item.quantity == 1  # Default value
    assert item.priority == Priority.MEDIUM  # Default value
    assert item.notes is None
    assert item.is_packed is False


def test_get_packing_item_by_id(db, test_packing_item):
    """Test getting a packing item by ID."""
    item = crud.get_packing_item_by_id(db, test_packing_item.id)

    assert item is not None
    assert item.id == test_packing_item.id
    assert item.name == test_packing_item.name


def test_get_packing_item_by_id_not_found(db):
    """Test getting non-existent packing item returns None."""
    item = crud.get_packing_item_by_id(db, 99999)
    assert item is None


def test_update_packing_item(db, test_packing_item):
    """Test updating a packing item."""
    item_update = PackingItemUpdate(
        name="Updated T-Shirt",
        quantity=7,
        priority=Priority.HIGH,
    )

    updated_item = crud.update_packing_item(db, test_packing_item, item_update)

    assert updated_item.name == "Updated T-Shirt"
    assert updated_item.quantity == 7
    assert updated_item.priority == Priority.HIGH
    # Original fields should remain unchanged
    assert updated_item.category == test_packing_item.category


def test_delete_packing_item(db, test_packing_item):
    """Test deleting a packing item."""
    item_id = test_packing_item.id
    crud.delete_packing_item(db, test_packing_item)

    # Item should no longer exist
    item = crud.get_packing_item_by_id(db, item_id)
    assert item is None


def test_toggle_pack_status_to_packed(db, test_packing_item):
    """Test toggling pack status from unpacked to packed."""
    assert test_packing_item.is_packed is False
    assert test_packing_item.packed_at is None

    toggled_item = crud.toggle_packed(db, test_packing_item)

    assert toggled_item.is_packed is True
    assert toggled_item.packed_at is not None
    assert isinstance(toggled_item.packed_at, datetime)


def test_toggle_pack_status_to_unpacked(db, test_packing_item):
    """Test toggling pack status from packed to unpacked."""
    # First pack the item
    crud.toggle_packed(db, test_packing_item)
    assert test_packing_item.is_packed is True

    # Then unpack it
    toggled_item = crud.toggle_packed(db, test_packing_item)

    assert toggled_item.is_packed is False
    assert toggled_item.packed_at is None


def test_get_packing_summary_empty(db, test_packing_list):
    """Test getting packing summary for empty list."""
    summary = crud.get_packing_list_summary(db, test_packing_list.id)

    assert summary["total_items"] == 0
    assert summary["packed_items"] == 0
    assert summary["percentage_packed"] == 0
    assert summary["by_category"] == {}


def test_get_packing_summary_with_items(db, test_packing_list):
    """Test getting packing summary with items."""
    # Create multiple items with different categories and pack statuses
    items_data = [
        ("T-Shirt", PackingCategory.CLOTHING, True),
        ("Pants", PackingCategory.CLOTHING, False),
        ("Toothbrush", PackingCategory.TOILETRIES, True),
        ("Toothpaste", PackingCategory.TOILETRIES, True),
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

    summary = crud.get_packing_list_summary(db, test_packing_list.id)

    assert summary["total_items"] == 5
    assert summary["packed_items"] == 3
    assert summary["percentage_packed"] == 60.0
    assert summary["by_category"]["clothing"]["total"] == 2
    assert summary["by_category"]["clothing"]["packed"] == 1
    assert summary["by_category"]["toiletries"]["total"] == 2
    assert summary["by_category"]["toiletries"]["packed"] == 2
    assert summary["by_category"]["electronics"]["total"] == 1
    assert summary["by_category"]["electronics"]["packed"] == 0


def test_get_packing_summary_all_packed(db, test_packing_list):
    """Test getting packing summary when all items are packed."""
    # Create items and pack them all
    for i in range(3):
        item = crud.create_packing_item(
            db,
            test_packing_list.id,
            PackingItemCreate(name=f"Item {i}", category=PackingCategory.CLOTHING),
        )
        crud.toggle_packed(db, item)

    summary = crud.get_packing_list_summary(db, test_packing_list.id)

    assert summary["total_items"] == 3
    assert summary["packed_items"] == 3
    assert summary["percentage_packed"] == 100.0
