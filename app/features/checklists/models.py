"""
Checklist models for trip task management.

Includes:
- Checklist: Container for checklist items
- ChecklistItem: Individual tasks/checklist items
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.core.database import Base
from app.shared.enums import ChecklistType, Priority


class Checklist(Base):
    """Checklist model for trip task lists."""

    __tablename__ = "checklists"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Checklist Details
    name = Column(String(200), nullable=False)  # e.g., "Pre-Departure", "Booking Confirmations"
    description = Column(Text, nullable=True)
    checklist_type = Column(
        ENUM(ChecklistType, name="checklist_type", create_type=True),
        default=ChecklistType.GENERAL,
        nullable=False,
        index=True
    )

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(TIMESTAMP, nullable=True)  # Soft delete

    # Relationships
    trip = relationship("Trip", back_populates="checklists")
    items = relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Checklist(id={self.id}, name='{self.name}', type='{self.checklist_type}')>"


class ChecklistItem(Base):
    """Checklist item model for individual tasks."""

    __tablename__ = "checklist_items"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    checklist_id = Column(Integer, ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False, index=True)

    # Item Details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    completed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Scheduling
    due_date = Column(Date, nullable=True, index=True)
    reminder_date = Column(Date, nullable=True)

    # Organization
    priority = Column(
        ENUM(Priority, name="priority", create_type=False),  # Reuse existing enum
        default=Priority.MEDIUM,
        nullable=False
    )
    order_index = Column(Integer, default=0, nullable=False)  # For custom sorting

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    checklist = relationship("Checklist", back_populates="items")
    completed_by_user = relationship("User", foreign_keys=[completed_by])

    def __repr__(self):
        return f"<ChecklistItem(id={self.id}, title='{self.title}', completed={self.is_completed})>"
