"""
CRUD operations for TripNote feature.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.features.trip_notes.models import TripNote
from app.features.trip_notes.schemas import TripNoteCreate, TripNoteUpdate
from app.shared.enums import NoteType


def create_trip_note(db: Session, note_in: TripNoteCreate, user_id: int) -> TripNote:
    """Create a new trip note."""
    note = TripNote(**note_in.model_dump(mode='python'), created_by=user_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_trip_note_by_id(db: Session, note_id: int) -> Optional[TripNote]:
    """Get a trip note by ID."""
    return db.query(TripNote).filter(
        TripNote.id == note_id,
        TripNote.deleted_at.is_(None)
    ).first()


def get_trip_notes_by_trip(
    db: Session,
    trip_id: int,
    trip_day_id: Optional[int] = None,
    note_type: Optional[NoteType] = None,
    is_pinned: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TripNote]:
    """Get all notes for a trip with optional filters."""
    query = db.query(TripNote).filter(
        TripNote.trip_id == trip_id,
        TripNote.deleted_at.is_(None)
    )

    if trip_day_id:
        query = query.filter(TripNote.trip_day_id == trip_day_id)
    if note_type:
        query = query.filter(TripNote.note_type == note_type)
    if is_pinned is not None:
        query = query.filter(TripNote.is_pinned == is_pinned)

    return query.order_by(
        TripNote.is_pinned.desc(),
        TripNote.created_at.desc()
    ).offset(skip).limit(limit).all()


def update_trip_note(db: Session, note: TripNote, note_in: TripNoteUpdate) -> TripNote:
    """Update a trip note."""
    update_data = note_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


def delete_trip_note(db: Session, note: TripNote) -> None:
    """Soft delete a trip note."""
    note.deleted_at = func.now()
    db.commit()


def toggle_pin(db: Session, note: TripNote) -> TripNote:
    """Toggle pin status of a note."""
    note.is_pinned = not note.is_pinned
    db.commit()
    db.refresh(note)
    return note
