"""
API routes for TripNote feature.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.trip_notes import crud
from app.features.trip_notes.schemas import *

router = APIRouter()


@router.post("/trip-notes", response_model=TripNoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_in: TripNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new trip note."""
    return crud.create_trip_note(db, note_in, current_user.id)


@router.get("/trip-notes/{note_id}", response_model=TripNoteResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get note by ID."""
    note = crud.get_trip_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/trip-notes/{note_id}", response_model=TripNoteResponse)
def update_note(
    note_id: int,
    note_in: TripNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a note."""
    note = crud.get_trip_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return crud.update_trip_note(db, note, note_in)


@router.delete("/trip-notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a note."""
    note = crud.get_trip_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    crud.delete_trip_note(db, note)


@router.get("/trips/{trip_id}/notes", response_model=List[TripNoteResponse])
def get_trip_notes(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all notes for a trip."""
    return crud.get_trip_notes_by_trip(db, trip_id)


@router.post("/trip-notes/{note_id}/pin", response_model=TripNoteResponse)
def toggle_pin_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle pin status of a note."""
    note = crud.get_trip_note_by_id(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return crud.toggle_pin(db, note)
