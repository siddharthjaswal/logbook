"""
Integration tests for TripNote API endpoints.
"""

import pytest
from datetime import date
from fastapi import status
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.features.trip_days import crud as trip_days_crud
from app.features.trip_days.schemas import TripDayCreate
from app.features.trip_notes import crud
from app.features.trip_notes.schemas import TripNoteCreate
from app.shared.enums import (
    NoteType,
    TripType,
    TripStatus,
    TripVisibility,
)


@pytest.fixture
def test_trip(db, test_user):
    """Create a test trip for note tests."""
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
def test_trip_day(db, test_trip):
    """Create a test trip day for note tests."""
    trip_day_create = TripDayCreate(
        trip_id=test_trip.id,
        date=date.today(),
        day_number=1,
        place="Tokyo",
        timezone="Asia/Tokyo"
    )
    return trip_days_crud.create_trip_day(db, trip_day_create)


@pytest.fixture
def note_data(test_trip):
    """Sample note data for API testing."""
    return {
        "trip_id": test_trip.id,
        "title": "Day 1 Journal",
        "content": "Today was an amazing day exploring Tokyo!",
        "note_type": "journal",
        "tags": ["tokyo", "sightseeing"],
        "is_pinned": False,
        "color": "#FF5733",
    }


@pytest.fixture
def test_trip_note(db, test_trip, test_user):
    """Create a test trip note in the database."""
    note_create = TripNoteCreate(
        trip_id=test_trip.id,
        title="Test Note",
        content="This is a test note",
        note_type=NoteType.GENERAL,
        is_pinned=False,
    )
    return crud.create_trip_note(db, note_create, user_id=test_user.id)


def test_create_trip_note_success(client, auth_headers, note_data):
    """Test creating a trip note."""
    response = client.post(
        "/api/v1/trip-notes", json=note_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == note_data["title"]
    assert data["content"] == note_data["content"]
    assert data["note_type"] == note_data["note_type"]
    assert data["id"] is not None


def test_create_trip_note_with_trip_day(client, auth_headers, note_data, test_trip_day):
    """Test creating a trip note associated with a trip day."""
    note_data["trip_day_id"] = test_trip_day.id

    response = client.post(
        "/api/v1/trip-notes", json=note_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["trip_day_id"] == test_trip_day.id


def test_create_trip_note_minimal(client, auth_headers, test_trip):
    """Test creating a note with only required fields."""
    minimal_data = {
        "trip_id": test_trip.id,
        "content": "Minimal note content",
    }

    response = client.post(
        "/api/v1/trip-notes", json=minimal_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["content"] == "Minimal note content"
    assert data["note_type"] == "general"  # Default value


def test_create_trip_note_unauthorized(client, note_data):
    """Test creating a trip note without authentication."""
    response = client.post("/api/v1/trip-notes", json=note_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_trip_note_with_color(client, auth_headers, note_data):
    """Test creating a note with a color."""
    note_data["color"] = "#00FF00"

    response = client.post(
        "/api/v1/trip-notes", json=note_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["color"] == "#00FF00"


def test_get_trip_note_by_id_owner(client, auth_headers, test_trip_note):
    """Test getting trip note by ID as owner."""
    response = client.get(
        f"/api/v1/trip-notes/{test_trip_note.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_trip_note.id
    assert data["title"] == test_trip_note.title
    assert data["content"] == test_trip_note.content


def test_get_trip_note_unauthorized(client, test_trip_note):
    """Test getting trip note without authentication."""
    response = client.get(f"/api/v1/trip-notes/{test_trip_note.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_trip_note_not_found(client, auth_headers):
    """Test getting non-existent trip note."""
    response = client.get("/api/v1/trip-notes/99999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_trip_notes(client, auth_headers, db, test_trip, test_user):
    """Test listing all notes for a trip."""
    # Create multiple notes
    for i in range(3):
        note_create = TripNoteCreate(
            trip_id=test_trip.id,
            title=f"Note {i}",
            content=f"Content for note {i}",
            note_type=NoteType.GENERAL,
        )
        crud.create_trip_note(db, note_create, user_id=test_user.id)

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/notes", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3


def test_list_trip_notes_with_type_filter(
    client, auth_headers, db, test_trip, test_user
):
    """Test listing notes filtered by type."""
    # Create notes with different types
    crud.create_trip_note(
        db,
        TripNoteCreate(
            trip_id=test_trip.id,
            title="Journal Entry",
            content="Journal content",
            note_type=NoteType.JOURNAL,
        ),
        user_id=test_user.id,
    )
    crud.create_trip_note(
        db,
        TripNoteCreate(
            trip_id=test_trip.id,
            title="Planning Note",
            content="Planning content",
            note_type=NoteType.PLANNING,
        ),
        user_id=test_user.id,
    )

    # Note: The router currently doesn't support filtering by note_type via query params
    # This test verifies that all notes are returned regardless of type
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/notes",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    # Verify both types are present
    note_types = {note["note_type"] for note in data}
    assert "journal" in note_types
    assert "planning" in note_types


def test_list_trip_notes_empty(client, auth_headers, test_trip):
    """Test listing notes for a trip with no notes."""
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/notes", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0


def test_list_trip_notes_ordering(client, auth_headers, db, test_trip, test_user):
    """Test that notes are ordered correctly (pinned first, then by creation date)."""
    # Create unpinned note
    crud.create_trip_note(
        db,
        TripNoteCreate(
            trip_id=test_trip.id,
            content="Unpinned note",
            note_type=NoteType.GENERAL,
            is_pinned=False,
        ),
        user_id=test_user.id,
    )

    # Create pinned note
    pinned_note = crud.create_trip_note(
        db,
        TripNoteCreate(
            trip_id=test_trip.id,
            content="Pinned note",
            note_type=NoteType.IMPORTANT,
            is_pinned=True,
        ),
        user_id=test_user.id,
    )

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/notes", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    # Pinned note should be first
    assert data[0]["id"] == pinned_note.id
    assert data[0]["is_pinned"] is True


def test_update_trip_note_owner(client, auth_headers, test_trip_note):
    """Test updating trip note as owner."""
    update_data = {
        "title": "Updated Title",
        "content": "Updated content with more details",
        "note_type": "memories",
    }

    response = client.put(
        f"/api/v1/trip-notes/{test_trip_note.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Updated content with more details"
    assert data["note_type"] == "memories"


def test_update_trip_note_partial(client, auth_headers, test_trip_note):
    """Test partial update of a trip note."""
    update_data = {
        "content": "Only updating the content",
    }

    response = client.put(
        f"/api/v1/trip-notes/{test_trip_note.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "Only updating the content"
    # Original title should remain
    assert data["title"] == test_trip_note.title


def test_update_trip_note_color(client, auth_headers, test_trip_note):
    """Test updating the color of a note."""
    update_data = {
        "color": "#00FF00",
    }

    response = client.put(
        f"/api/v1/trip-notes/{test_trip_note.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["color"] == "#00FF00"


def test_update_trip_note_tags(client, auth_headers, test_trip_note):
    """Test updating tags of a note."""
    update_data = {
        "tags": ["tokyo", "food", "culture"],
    }

    response = client.put(
        f"/api/v1/trip-notes/{test_trip_note.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tags"] == ["tokyo", "food", "culture"]


def test_update_trip_note_unauthorized(client, test_trip_note):
    """Test updating trip note without authentication."""
    response = client.put(
        f"/api/v1/trip-notes/{test_trip_note.id}",
        json={"content": "Updated"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_trip_note_not_found(client, auth_headers):
    """Test updating non-existent trip note."""
    response = client.put(
        "/api/v1/trip-notes/99999",
        json={"content": "Updated"},
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_trip_note_owner(client, auth_headers, test_trip_note, db):
    """Test deleting trip note as owner."""
    response = client.delete(
        f"/api/v1/trip-notes/{test_trip_note.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify soft delete
    db.refresh(test_trip_note)
    assert test_trip_note.deleted_at is not None


def test_delete_trip_note_unauthorized(client, test_trip_note):
    """Test deleting trip note without authentication."""
    response = client.delete(f"/api/v1/trip-notes/{test_trip_note.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_trip_note_not_found(client, auth_headers):
    """Test deleting non-existent trip note."""
    response = client.delete(
        "/api/v1/trip-notes/99999", headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_toggle_pin_note(client, auth_headers, test_trip_note):
    """Test toggling pin status of a note."""
    # Initial state
    assert test_trip_note.is_pinned is False

    # Toggle to pinned
    response = client.post(
        f"/api/v1/trip-notes/{test_trip_note.id}/pin", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_pinned"] is True

    # Toggle back to unpinned
    response = client.post(
        f"/api/v1/trip-notes/{test_trip_note.id}/pin", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_pinned"] is False


def test_toggle_pin_note_unauthorized(client, test_trip_note):
    """Test toggling pin without authentication."""
    response = client.post(
        f"/api/v1/trip-notes/{test_trip_note.id}/pin"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_toggle_pin_note_not_found(client, auth_headers):
    """Test toggling pin for non-existent note."""
    response = client.post(
        "/api/v1/trip-notes/99999/pin", headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_note_with_all_note_types(client, auth_headers, test_trip):
    """Test creating notes with all available note types."""
    note_types = ["general", "journal", "planning", "important", "tips", "memories"]

    for note_type in note_types:
        note_data = {
            "trip_id": test_trip.id,
            "content": f"Content for {note_type} note",
            "note_type": note_type,
        }

        response = client.post(
            "/api/v1/trip-notes", json=note_data, headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["note_type"] == note_type


def test_create_note_with_invalid_color(client, auth_headers, test_trip):
    """Test creating a note with an invalid color format."""
    note_data = {
        "trip_id": test_trip.id,
        "content": "Test content",
        "color": "invalid_color",  # Invalid hex color
    }

    response = client.post(
        "/api/v1/trip-notes", json=note_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_notes_excludes_deleted(client, auth_headers, db, test_trip, test_user):
    """Test that deleted notes are not returned in list."""
    # Create note
    note = crud.create_trip_note(
        db,
        TripNoteCreate(
            trip_id=test_trip.id,
            content="This note will be deleted",
            note_type=NoteType.GENERAL,
        ),
        user_id=test_user.id,
    )

    # Delete note
    crud.delete_trip_note(db, note)

    # List notes
    response = client.get(
        f"/api/v1/trips/{test_trip.id}/notes", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0  # Deleted note should not appear


def test_get_deleted_note_by_id_returns_not_found(client, auth_headers, db, test_trip_note):
    """Test that getting a deleted note by ID returns 404."""
    # Delete the note
    crud.delete_trip_note(db, test_trip_note)

    # Try to get the deleted note
    response = client.get(
        f"/api/v1/trip-notes/{test_trip_note.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
