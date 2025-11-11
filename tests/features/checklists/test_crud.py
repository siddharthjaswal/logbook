"""
Unit tests for Checklist CRUD operations.
"""

import pytest
from datetime import date, timedelta
from app.features.checklists import crud
from app.features.checklists.schemas import (
    ChecklistCreate,
    ChecklistUpdate,
    ChecklistItemCreate,
    ChecklistItemUpdate,
)
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.shared.enums import (
    ChecklistType,
    Priority,
    TripType,
    TripStatus,
    TripVisibility,
)


@pytest.fixture
def test_trip(db, test_user):
    """Create a test trip for checklist tests."""
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
def checklist_data(test_trip):
    """Sample checklist data for testing."""
    return {
        "trip_id": test_trip.id,
        "name": "Pre-Departure Checklist",
        "description": "Things to do before leaving",
        "checklist_type": ChecklistType.PRE_DEPARTURE,
    }


@pytest.fixture
def test_checklist(db, checklist_data, test_user):
    """Create a test checklist in the database."""
    checklist_create = ChecklistCreate(**checklist_data)
    return crud.create_checklist(db, checklist_create, user_id=test_user.id)


@pytest.fixture
def checklist_item_data():
    """Sample checklist item data for testing."""
    return {
        "title": "Book flight tickets",
        "description": "Book round-trip tickets to Tokyo",
        "due_date": date.today() + timedelta(days=7),
        "priority": Priority.HIGH,
    }


@pytest.fixture
def test_checklist_item(db, test_checklist, checklist_item_data):
    """Create a test checklist item in the database."""
    item_create = ChecklistItemCreate(**checklist_item_data)
    return crud.create_checklist_item(db, test_checklist.id, item_create)


def test_create_checklist(db, checklist_data, test_user):
    """Test creating a checklist."""
    checklist_create = ChecklistCreate(**checklist_data)
    checklist = crud.create_checklist(db, checklist_create, user_id=test_user.id)

    assert checklist.id is not None
    assert checklist.name == checklist_data["name"]
    assert checklist.description == checklist_data["description"]
    assert checklist.checklist_type == ChecklistType.PRE_DEPARTURE
    assert checklist.trip_id == checklist_data["trip_id"]
    assert checklist.created_by == test_user.id
    assert checklist.deleted_at is None


def test_get_checklist_by_id(db, test_checklist):
    """Test getting a checklist by ID."""
    checklist = crud.get_checklist_by_id(db, test_checklist.id)

    assert checklist is not None
    assert checklist.id == test_checklist.id
    assert checklist.name == test_checklist.name


def test_get_checklist_by_id_not_found(db):
    """Test getting non-existent checklist returns None."""
    checklist = crud.get_checklist_by_id(db, 99999)
    assert checklist is None


def test_get_checklists_by_trip(db, test_trip, checklist_data, test_user):
    """Test getting all checklists for a trip."""
    # Create multiple checklists
    for i in range(3):
        data = checklist_data.copy()
        data["name"] = f"Checklist {i}"
        checklist_create = ChecklistCreate(**data)
        crud.create_checklist(db, checklist_create, user_id=test_user.id)

    checklists = crud.get_checklists_by_trip(db, test_trip.id)

    assert len(checklists) == 3
    assert all(checklist.trip_id == test_trip.id for checklist in checklists)


def test_get_checklists_by_trip_with_type_filter(db, test_trip, checklist_data, test_user):
    """Test getting checklists filtered by type."""
    # Create checklists with different types
    pre_departure_data = checklist_data.copy()
    pre_departure_data["checklist_type"] = ChecklistType.PRE_DEPARTURE
    crud.create_checklist(db, ChecklistCreate(**pre_departure_data), user_id=test_user.id)

    general_data = checklist_data.copy()
    general_data["checklist_type"] = ChecklistType.GENERAL
    general_data["name"] = "General Checklist"
    crud.create_checklist(db, ChecklistCreate(**general_data), user_id=test_user.id)

    pre_departure_checklists = crud.get_checklists_by_trip(
        db, test_trip.id, checklist_type=ChecklistType.PRE_DEPARTURE
    )

    assert len(pre_departure_checklists) == 1
    assert pre_departure_checklists[0].checklist_type == ChecklistType.PRE_DEPARTURE


def test_update_checklist(db, test_checklist):
    """Test updating a checklist."""
    checklist_update = ChecklistUpdate(
        name="Updated Checklist",
        description="Updated description",
        checklist_type=ChecklistType.GENERAL,
    )

    updated_checklist = crud.update_checklist(db, test_checklist, checklist_update)

    assert updated_checklist.name == "Updated Checklist"
    assert updated_checklist.description == "Updated description"
    assert updated_checklist.checklist_type == ChecklistType.GENERAL
    # Original fields should remain unchanged
    assert updated_checklist.trip_id == test_checklist.trip_id


def test_delete_checklist(db, test_checklist):
    """Test soft deleting a checklist."""
    crud.delete_checklist(db, test_checklist)

    assert test_checklist.deleted_at is not None

    # Deleted checklist should not be returned
    checklist = crud.get_checklist_by_id(db, test_checklist.id)
    assert checklist is None


def test_create_checklist_item(db, test_checklist, checklist_item_data):
    """Test creating a checklist item."""
    item_create = ChecklistItemCreate(**checklist_item_data)
    item = crud.create_checklist_item(db, test_checklist.id, item_create)

    assert item.id is not None
    assert item.checklist_id == test_checklist.id
    assert item.title == checklist_item_data["title"]
    assert item.description == checklist_item_data["description"]
    assert item.due_date == checklist_item_data["due_date"]
    assert item.priority == Priority.HIGH
    assert item.is_completed is False
    assert item.completed_at is None
    assert item.completed_by is None


def test_get_checklist_items(db, test_checklist, checklist_item_data):
    """Test getting all items for a checklist."""
    # Create multiple items
    for i in range(3):
        data = checklist_item_data.copy()
        data["title"] = f"Item {i}"
        item_create = ChecklistItemCreate(**data)
        crud.create_checklist_item(db, test_checklist.id, item_create)

    # Note: The crud module doesn't have a get_checklist_items function that returns items
    # We'll query through the checklist relationship
    items = test_checklist.items

    assert len(items) == 3
    assert all(item.checklist_id == test_checklist.id for item in items)


def test_update_checklist_item(db, test_checklist_item):
    """Test updating a checklist item."""
    item_update = ChecklistItemUpdate(
        title="Updated item",
        description="Updated description",
        priority=Priority.CRITICAL,
    )

    updated_item = crud.update_checklist_item(db, test_checklist_item, item_update)

    assert updated_item.title == "Updated item"
    assert updated_item.description == "Updated description"
    assert updated_item.priority == Priority.CRITICAL
    # Original fields should remain unchanged
    assert updated_item.checklist_id == test_checklist_item.checklist_id


def test_delete_checklist_item(db, test_checklist_item):
    """Test deleting a checklist item."""
    item_id = test_checklist_item.id
    crud.delete_checklist_item(db, test_checklist_item)

    # Item should be deleted (hard delete)
    item = crud.get_checklist_item_by_id(db, item_id)
    assert item is None


def test_toggle_complete_status(db, test_checklist_item, test_user):
    """Test toggling completion status of a checklist item."""
    # Toggle to completed
    toggled_item = crud.toggle_completed(db, test_checklist_item, test_user.id)

    assert toggled_item.is_completed is True
    assert toggled_item.completed_at is not None
    assert toggled_item.completed_by == test_user.id

    # Toggle back to incomplete
    toggled_item = crud.toggle_completed(db, test_checklist_item, test_user.id)

    assert toggled_item.is_completed is False
    assert toggled_item.completed_at is None
    assert toggled_item.completed_by is None


def test_get_checklist_summary(db, test_checklist, checklist_item_data, test_user):
    """Test getting checklist summary."""
    # Create items with different priorities and completion statuses
    items_data = [
        (Priority.HIGH, True),
        (Priority.HIGH, False),
        (Priority.MEDIUM, True),
        (Priority.LOW, False),
    ]

    for priority, is_completed in items_data:
        data = checklist_item_data.copy()
        data["priority"] = priority
        item = crud.create_checklist_item(
            db, test_checklist.id, ChecklistItemCreate(**data)
        )
        if is_completed:
            crud.toggle_completed(db, item, test_user.id)

    summary = crud.get_checklist_summary(db, test_checklist.id)

    assert summary["total_items"] == 4
    assert summary["completed_items"] == 2
    assert summary["percentage_completed"] == 50.0
    assert summary["overdue_items"] == 0  # No overdue items since due dates are in the future
    assert "by_priority" in summary
    assert summary["by_priority"]["high"]["total"] == 2
    assert summary["by_priority"]["high"]["completed"] == 1


def test_get_overdue_items(db, test_checklist, checklist_item_data, test_user):
    """Test getting overdue items."""
    # Create items with past due dates
    overdue_data = checklist_item_data.copy()
    overdue_data["due_date"] = date.today() - timedelta(days=2)
    overdue_data["title"] = "Overdue item"
    overdue_item = crud.create_checklist_item(
        db, test_checklist.id, ChecklistItemCreate(**overdue_data)
    )

    # Create item with future due date
    future_data = checklist_item_data.copy()
    future_data["due_date"] = date.today() + timedelta(days=7)
    future_data["title"] = "Future item"
    crud.create_checklist_item(db, test_checklist.id, ChecklistItemCreate(**future_data))

    # Get summary which includes overdue count
    summary = crud.get_checklist_summary(db, test_checklist.id)

    assert summary["overdue_items"] == 1
    assert summary["total_items"] == 2


def test_get_checklist_summary_empty(db, test_checklist):
    """Test getting summary for empty checklist."""
    summary = crud.get_checklist_summary(db, test_checklist.id)

    assert summary["total_items"] == 0
    assert summary["completed_items"] == 0
    assert summary["percentage_completed"] == 0
    assert summary["overdue_items"] == 0
    assert summary["by_priority"] == {}
