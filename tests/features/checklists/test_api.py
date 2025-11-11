"""
Integration tests for Checklist API endpoints.
"""

import pytest
from datetime import date, timedelta
from fastapi import status
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.features.checklists import crud
from app.features.checklists.schemas import (
    ChecklistCreate,
    ChecklistItemCreate,
)
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
    """Sample checklist data for API testing."""
    return {
        "trip_id": test_trip.id,
        "name": "Pre-Departure Checklist",
        "description": "Things to do before leaving",
        "checklist_type": "pre_departure",
    }


@pytest.fixture
def test_checklist(db, test_trip, test_user):
    """Create a test checklist in the database."""
    checklist_create = ChecklistCreate(
        trip_id=test_trip.id,
        name="Test Checklist",
        description="Test description",
        checklist_type=ChecklistType.GENERAL,
    )
    return crud.create_checklist(db, checklist_create, user_id=test_user.id)


@pytest.fixture
def checklist_item_data():
    """Sample checklist item data for API testing."""
    return {
        "title": "Book flight tickets",
        "description": "Book round-trip tickets to Tokyo",
        "due_date": str(date.today() + timedelta(days=7)),
        "priority": "high",
    }


@pytest.fixture
def test_checklist_item(db, test_checklist, test_user):
    """Create a test checklist item in the database."""
    item_create = ChecklistItemCreate(
        title="Test Item",
        description="Test item description",
        due_date=date.today() + timedelta(days=7),
        priority=Priority.MEDIUM,
    )
    return crud.create_checklist_item(db, test_checklist.id, item_create)


def test_create_checklist_success(client, auth_headers, checklist_data):
    """Test creating a checklist."""
    response = client.post(
        "/api/v1/checklists", json=checklist_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == checklist_data["name"]
    assert data["checklist_type"] == checklist_data["checklist_type"]
    assert data["id"] is not None


def test_create_checklist_unauthorized(client, checklist_data):
    """Test creating a checklist without authentication."""
    response = client.post("/api/v1/checklists", json=checklist_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_checklist_by_id_owner(client, auth_headers, test_checklist):
    """Test getting checklist by ID as owner."""
    response = client.get(
        f"/api/v1/checklists/{test_checklist.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_checklist.id
    assert data["name"] == test_checklist.name


def test_get_checklist_unauthorized(client, test_checklist):
    """Test getting checklist without authentication."""
    response = client.get(f"/api/v1/checklists/{test_checklist.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_checklist_not_found(client, auth_headers):
    """Test getting non-existent checklist."""
    response = client.get("/api/v1/checklists/99999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_trip_checklists(client, auth_headers, db, test_trip, test_user):
    """Test listing all checklists for a trip."""
    # Create multiple checklists
    for i in range(3):
        checklist_create = ChecklistCreate(
            trip_id=test_trip.id,
            name=f"Checklist {i}",
            checklist_type=ChecklistType.GENERAL,
        )
        crud.create_checklist(db, checklist_create, user_id=test_user.id)

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/checklists", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3


def test_list_trip_checklists_with_type_filter(
    client, auth_headers, db, test_trip, test_user
):
    """Test listing checklists filtered by type."""
    # Create checklists with different types
    crud.create_checklist(
        db,
        ChecklistCreate(
            trip_id=test_trip.id,
            name="Pre-Departure",
            checklist_type=ChecklistType.PRE_DEPARTURE,
        ),
        user_id=test_user.id,
    )
    crud.create_checklist(
        db,
        ChecklistCreate(
            trip_id=test_trip.id,
            name="General",
            checklist_type=ChecklistType.GENERAL,
        ),
        user_id=test_user.id,
    )

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/checklists?checklist_type=pre_departure",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["checklist_type"] == "pre_departure"


# NOTE: UPDATE endpoint for checklists is not implemented in the router yet
# Uncomment these tests when the endpoint is added
# def test_update_checklist_owner(client, auth_headers, test_checklist):
#     """Test updating checklist as owner."""
#     update_data = {
#         "name": "Updated Checklist",
#         "description": "Updated description",
#     }
#
#     response = client.put(
#         f"/api/v1/checklists/{test_checklist.id}",
#         json=update_data,
#         headers=auth_headers,
#     )
#
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data["name"] == "Updated Checklist"
#     assert data["description"] == "Updated description"
#
#
# def test_update_checklist_unauthorized(client, test_checklist):
#     """Test updating checklist without authentication."""
#     response = client.put(
#         f"/api/v1/checklists/{test_checklist.id}", json={"name": "Updated"}
#     )
#
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_checklist_owner(client, auth_headers, test_checklist, db):
    """Test deleting checklist as owner."""
    response = client.delete(
        f"/api/v1/checklists/{test_checklist.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify soft delete
    db.refresh(test_checklist)
    assert test_checklist.deleted_at is not None


def test_delete_checklist_unauthorized(client, test_checklist):
    """Test deleting checklist without authentication."""
    response = client.delete(f"/api/v1/checklists/{test_checklist.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_checklist_item_success(
    client, auth_headers, test_checklist, checklist_item_data
):
    """Test creating a checklist item."""
    response = client.post(
        f"/api/v1/checklists/{test_checklist.id}/items",
        json=checklist_item_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == checklist_item_data["title"]
    assert data["priority"] == checklist_item_data["priority"]
    assert data["is_completed"] is False


def test_create_checklist_item_unauthorized(client, test_checklist, checklist_item_data):
    """Test creating a checklist item without authentication."""
    response = client.post(
        f"/api/v1/checklists/{test_checklist.id}/items", json=checklist_item_data
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_checklist_items(client, auth_headers, db, test_checklist):
    """Test getting all items for a checklist."""
    # Create multiple items
    for i in range(3):
        crud.create_checklist_item(
            db,
            test_checklist.id,
            ChecklistItemCreate(
                title=f"Item {i}",
                priority=Priority.MEDIUM,
            ),
        )

    response = client.get(
        f"/api/v1/checklists/{test_checklist.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) == 3


def test_update_checklist_item(client, auth_headers, test_checklist_item):
    """Test updating a checklist item."""
    update_data = {
        "title": "Updated item",
        "description": "Updated description",
        "priority": "critical",
    }

    response = client.put(
        f"/api/v1/checklist-items/{test_checklist_item.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated item"
    assert data["description"] == "Updated description"
    assert data["priority"] == "critical"


def test_update_checklist_item_unauthorized(client, test_checklist_item):
    """Test updating a checklist item without authentication."""
    response = client.put(
        f"/api/v1/checklist-items/{test_checklist_item.id}",
        json={"title": "Updated"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_checklist_item_not_found(client, auth_headers):
    """Test updating non-existent checklist item."""
    response = client.put(
        "/api/v1/checklist-items/99999",
        json={"title": "Updated"},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# NOTE: DELETE endpoint for checklist items is not implemented in the router yet
# Uncomment these tests when the endpoint is added
# def test_delete_checklist_item(client, auth_headers, test_checklist_item, db):
#     """Test deleting a checklist item."""
#     item_id = test_checklist_item.id
#
#     response = client.delete(
#         f"/api/v1/checklist-items/{item_id}", headers=auth_headers
#     )
#
#     assert response.status_code == status.HTTP_204_NO_CONTENT
#
#     # Verify hard delete
#     item = crud.get_checklist_item_by_id(db, item_id)
#     assert item is None
#
#
# def test_delete_checklist_item_unauthorized(client, test_checklist_item):
#     """Test deleting a checklist item without authentication."""
#     response = client.delete(f"/api/v1/checklist-items/{test_checklist_item.id}")
#
#     assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#
# def test_delete_checklist_item_not_found(client, auth_headers):
#     """Test deleting non-existent checklist item."""
#     response = client.delete("/api/v1/checklist-items/99999", headers=auth_headers)
#
#     assert response.status_code == status.HTTP_404_NOT_FOUND


def test_toggle_complete_status(client, auth_headers, test_checklist_item):
    """Test toggling completion status of a checklist item."""
    # Toggle to completed
    response = client.post(
        f"/api/v1/checklist-items/{test_checklist_item.id}/toggle-complete",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_completed"] is True
    assert data["completed_at"] is not None
    assert data["completed_by"] is not None

    # Toggle back to incomplete
    response = client.post(
        f"/api/v1/checklist-items/{test_checklist_item.id}/toggle-complete",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_completed"] is False
    assert data["completed_at"] is None
    assert data["completed_by"] is None


def test_toggle_complete_status_unauthorized(client, test_checklist_item):
    """Test toggling completion status without authentication."""
    response = client.post(
        f"/api/v1/checklist-items/{test_checklist_item.id}/toggle-complete"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_toggle_complete_status_not_found(client, auth_headers):
    """Test toggling completion status of non-existent item."""
    response = client.post(
        "/api/v1/checklist-items/99999/toggle-complete", headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_checklist_summary(client, auth_headers, db, test_checklist, test_user):
    """Test getting checklist summary."""
    # Create items with different priorities and completion statuses
    items_data = [
        (Priority.HIGH, True),
        (Priority.HIGH, False),
        (Priority.MEDIUM, True),
        (Priority.LOW, False),
    ]

    for priority, is_completed in items_data:
        item = crud.create_checklist_item(
            db,
            test_checklist.id,
            ChecklistItemCreate(
                title="Test item",
                priority=priority,
                due_date=date.today() + timedelta(days=7),
            ),
        )
        if is_completed:
            crud.toggle_completed(db, item, test_user.id)

    response = client.get(
        f"/api/v1/checklists/{test_checklist.id}/summary", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 4
    assert data["completed_items"] == 2
    assert data["percentage_completed"] == 50.0
    assert "by_priority" in data


def test_get_checklist_summary_unauthorized(client, test_checklist):
    """Test getting checklist summary without authentication."""
    response = client.get(f"/api/v1/checklists/{test_checklist.id}/summary")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_checklist_summary_with_overdue_items(
    client, auth_headers, db, test_checklist
):
    """Test getting summary with overdue items."""
    # Create overdue item
    crud.create_checklist_item(
        db,
        test_checklist.id,
        ChecklistItemCreate(
            title="Overdue item",
            due_date=date.today() - timedelta(days=2),
            priority=Priority.HIGH,
        ),
    )

    # Create future item
    crud.create_checklist_item(
        db,
        test_checklist.id,
        ChecklistItemCreate(
            title="Future item",
            due_date=date.today() + timedelta(days=7),
            priority=Priority.MEDIUM,
        ),
    )

    response = client.get(
        f"/api/v1/checklists/{test_checklist.id}/summary", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 2
    assert data["overdue_items"] == 1
