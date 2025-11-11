"""
Pydantic schemas for TripNote feature.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.shared.enums import NoteType


class TripNoteBase(BaseModel):
    """Base schema for TripNote."""
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    note_type: NoteType = NoteType.GENERAL
    tags: Optional[List[str]] = None
    is_pinned: bool = False
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

    class Config:
        from_attributes = True


class TripNoteCreate(BaseModel):
    """Schema for creating a TripNote."""
    trip_id: int = Field(..., gt=0)
    trip_day_id: Optional[int] = Field(None, gt=0)
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    note_type: NoteType = NoteType.GENERAL
    tags: Optional[List[str]] = None
    is_pinned: bool = False
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TripNoteUpdate(BaseModel):
    """Schema for updating a TripNote."""
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    note_type: Optional[NoteType] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TripNoteResponse(TripNoteBase):
    """Schema for TripNote response."""
    id: int
    trip_id: int
    trip_day_id: Optional[int]
    created_by: int
    created_at: datetime
    updated_at: datetime
