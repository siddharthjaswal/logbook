"""
Unit tests for TripNote CRUD operations.
"""

import pytest
from datetime import datetime
from app.features.trip_notes import crud
from app.features.trip_notes.schemas import (
    TripNoteCreate,
    TripNoteUpdate,
)
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.features.trip_days import crud as trip_days_crud
from app.features.trip_days.schemas import TripDayCreate
from app.shared.enums import (
    NoteType,
    TripType,
    TripStatus,
    TripVisibility,
)
from datetime import date


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
def note_data(test_trip, test_user):
    """Sample note data for testing."""
    return {
        "trip_id": test_trip.id,
        "title": "Day 1 Journal",
        "content": "Today was an amazing day exploring Tokyo!",
        "note_type": NoteType.JOURNAL,
        "tags": ["tokyo", "sightseeing"],
        "is_pinned": False,
        "color": "#FF5733",
    }


@pytest.fixture
def test_trip_note(db, note_data, test_user):
    """Create a test trip note in the database."""
    note_create = TripNoteCreate(**note_data)
    return crud.create_trip_note(db, note_create, user_id=test_user.id)


def test_create_trip_note(db, note_data, test_user):
    """Test creating a trip note."""
    note_create = TripNoteCreate(**note_data)
    note = crud.create_trip_note(db, note_create, user_id=test_user.id)

    assert note.id is not None
    assert note.title == note_data["title"]
    assert note.content == note_data["content"]
    assert note.note_type == NoteType.JOURNAL
    assert note.tags == ["tokyo", "sightseeing"]
    assert note.is_pinned is False
    assert note.color == "#FF5733"
    assert note.created_by == test_user.id
    assert note.deleted_at is None


def test_create_trip_note_with_trip_day(db, note_data, test_trip_day, test_user):
    """Test creating a trip note associated with a trip day."""
    note_data["trip_day_id"] = test_trip_day.id

    note_create = TripNoteCreate(**note_data)
    note = crud.create_trip_note(db, note_create, user_id=test_user.id)

    assert note.id is not None
    assert note.trip_day_id == test_trip_day.id
    assert note.content == note_data["content"]


def test_get_trip_note_by_id(db, test_trip_note):
    """Test getting a trip note by ID."""
    note = crud.get_trip_note_by_id(db, test_trip_note.id)

    assert note is not None
    assert note.id == test_trip_note.id
    assert note.title == test_trip_note.title
    assert note.content == test_trip_note.content


def test_get_trip_note_by_id_not_found(db):
    """Test getting non-existent note returns None."""
    note = crud.get_trip_note_by_id(db, 99999)
    assert note is None


def test_get_trip_notes_by_trip(db, test_trip, note_data, test_user):
    """Test getting all notes for a trip."""
    # Create multiple notes
    for i in range(3):
        data = note_data.copy()
        data["title"] = f"Note {i}"
        data["content"] = f"Content for note {i}"
        note_create = TripNoteCreate(**data)
        crud.create_trip_note(db, note_create, user_id=test_user.id)

    notes = crud.get_trip_notes_by_trip(db, test_trip.id)

    assert len(notes) == 3
    assert all(note.trip_id == test_trip.id for note in notes)


def test_get_trip_notes_by_trip_with_type_filter(db, test_trip, note_data, test_user):
    """Test getting notes filtered by type."""
    # Create notes with different types
    journal_data = note_data.copy()
    journal_data["note_type"] = NoteType.JOURNAL
    crud.create_trip_note(db, TripNoteCreate(**journal_data), user_id=test_user.id)

    planning_data = note_data.copy()
    planning_data["note_type"] = NoteType.PLANNING
    planning_data["content"] = "Planning content"
    crud.create_trip_note(db, TripNoteCreate(**planning_data), user_id=test_user.id)

    journal_notes = crud.get_trip_notes_by_trip(
        db, test_trip.id, note_type=NoteType.JOURNAL
    )

    assert len(journal_notes) == 1
    assert journal_notes[0].note_type == NoteType.JOURNAL


def test_get_trip_notes_by_trip_with_trip_day_filter(db, test_trip, test_trip_day, note_data, test_user):
    """Test getting notes filtered by trip day."""
    # Create note with trip day
    day_note_data = note_data.copy()
    day_note_data["trip_day_id"] = test_trip_day.id
    crud.create_trip_note(db, TripNoteCreate(**day_note_data), user_id=test_user.id)

    # Create note without trip day
    general_note_data = note_data.copy()
    general_note_data["content"] = "General note"
    crud.create_trip_note(db, TripNoteCreate(**general_note_data), user_id=test_user.id)

    day_notes = crud.get_trip_notes_by_trip(
        db, test_trip.id, trip_day_id=test_trip_day.id
    )

    assert len(day_notes) == 1
    assert day_notes[0].trip_day_id == test_trip_day.id


def test_get_trip_notes_with_pinned_filter(db, test_trip, note_data, test_user):
    """Test getting notes filtered by pinned status."""
    # Create pinned note
    pinned_data = note_data.copy()
    pinned_data["is_pinned"] = True
    crud.create_trip_note(db, TripNoteCreate(**pinned_data), user_id=test_user.id)

    # Create unpinned note
    unpinned_data = note_data.copy()
    unpinned_data["is_pinned"] = False
    unpinned_data["content"] = "Unpinned note"
    crud.create_trip_note(db, TripNoteCreate(**unpinned_data), user_id=test_user.id)

    pinned_notes = crud.get_trip_notes_by_trip(
        db, test_trip.id, is_pinned=True
    )

    assert len(pinned_notes) == 1
    assert pinned_notes[0].is_pinned is True


def test_update_trip_note(db, test_trip_note):
    """Test updating a trip note."""
    note_update = TripNoteUpdate(
        title="Updated Journal Entry",
        content="Updated content with more details",
        note_type=NoteType.MEMORIES,
        color="#00FF00",
    )

    updated_note = crud.update_trip_note(db, test_trip_note, note_update)

    assert updated_note.title == "Updated Journal Entry"
    assert updated_note.content == "Updated content with more details"
    assert updated_note.note_type == NoteType.MEMORIES
    assert updated_note.color == "#00FF00"
    # Original fields should remain unchanged
    assert updated_note.trip_id == test_trip_note.trip_id


def test_update_trip_note_partial(db, test_trip_note):
    """Test partial update of a trip note."""
    original_title = test_trip_note.title

    note_update = TripNoteUpdate(
        content="Only updating the content"
    )

    updated_note = crud.update_trip_note(db, test_trip_note, note_update)

    assert updated_note.content == "Only updating the content"
    assert updated_note.title == original_title  # Should remain unchanged


def test_delete_trip_note(db, test_trip_note):
    """Test soft deleting a trip note."""
    crud.delete_trip_note(db, test_trip_note)

    assert test_trip_note.deleted_at is not None

    # Deleted note should not be returned
    note = crud.get_trip_note_by_id(db, test_trip_note.id)
    assert note is None


def test_toggle_pin(db, test_trip_note):
    """Test toggling pin status of a note."""
    # Initial state
    assert test_trip_note.is_pinned is False

    # Toggle to pinned
    updated_note = crud.toggle_pin(db, test_trip_note)
    assert updated_note.is_pinned is True

    # Toggle back to unpinned
    updated_note = crud.toggle_pin(db, test_trip_note)
    assert updated_note.is_pinned is False


def test_get_trip_notes_ordering(db, test_trip, note_data, test_user):
    """Test that notes are ordered by pinned status and creation date."""
    # Create unpinned note (older)
    unpinned_data = note_data.copy()
    unpinned_data["is_pinned"] = False
    unpinned_data["content"] = "Older unpinned note"
    crud.create_trip_note(db, TripNoteCreate(**unpinned_data), user_id=test_user.id)

    # Create pinned note
    pinned_data = note_data.copy()
    pinned_data["is_pinned"] = True
    pinned_data["content"] = "Pinned note"
    pinned_note = crud.create_trip_note(db, TripNoteCreate(**pinned_data), user_id=test_user.id)

    # Create another unpinned note (newer)
    unpinned_data2 = note_data.copy()
    unpinned_data2["is_pinned"] = False
    unpinned_data2["content"] = "Newer unpinned note"
    crud.create_trip_note(db, TripNoteCreate(**unpinned_data2), user_id=test_user.id)

    notes = crud.get_trip_notes_by_trip(db, test_trip.id)

    # Pinned note should be first
    assert notes[0].is_pinned is True
    assert notes[0].id == pinned_note.id

    # Other notes should be ordered by creation date (newest first)
    assert notes[1].is_pinned is False
    assert notes[2].is_pinned is False


def test_create_note_without_optional_fields(db, test_trip, test_user):
    """Test creating a note with only required fields."""
    minimal_data = {
        "trip_id": test_trip.id,
        "content": "Minimal note content",
    }

    note_create = TripNoteCreate(**minimal_data)
    note = crud.create_trip_note(db, note_create, user_id=test_user.id)

    assert note.id is not None
    assert note.content == "Minimal note content"
    assert note.title is None
    assert note.note_type == NoteType.GENERAL  # Default value
    assert note.tags is None
    assert note.is_pinned is False  # Default value
    assert note.color is None


def test_update_note_tags(db, test_trip_note):
    """Test updating tags of a note."""
    note_update = TripNoteUpdate(
        tags=["tokyo", "food", "culture", "temples"]
    )

    updated_note = crud.update_trip_note(db, test_trip_note, note_update)

    assert updated_note.tags == ["tokyo", "food", "culture", "temples"]
