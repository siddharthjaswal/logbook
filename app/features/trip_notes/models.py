"""
TripNote model for notes and journals.

Notes can be associated with trips or specific trip days.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM, JSON

from app.core.database import Base
from app.shared.enums import NoteType


class TripNote(Base):
    """Trip note model for notes and journals."""

    __tablename__ = "trip_notes"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Note Details
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(
        ENUM(NoteType, name="note_type", create_type=True),
        default=NoteType.GENERAL,
        nullable=False,
        index=True
    )

    # Organization
    tags = Column(JSON, nullable=True)  # Array of tags
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)
    color = Column(String(7), nullable=True)  # Hex color code for UI (e.g., #FF5733)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(TIMESTAMP, nullable=True)  # Soft delete

    # Relationships
    trip = relationship("Trip", back_populates="notes")
    trip_day = relationship("TripDay", back_populates="notes")
    author = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<TripNote(id={self.id}, title='{self.title}', type='{self.note_type}')>"
