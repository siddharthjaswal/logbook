"""
Packing list models for trip packing organization.

Includes:
- PackingList: Container for packing items
- PackingItem: Individual items to pack
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.core.database import Base
from app.shared.enums import PackingCategory, Priority


class PackingList(Base):
    """Packing list model for organizing items to pack."""

    __tablename__ = "packing_lists"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # List Details
    name = Column(String(200), nullable=False)  # e.g., "Main Luggage", "Carry-on"
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(TIMESTAMP, nullable=True)  # Soft delete

    # Relationships
    trip = relationship("Trip", back_populates="packing_lists")
    items = relationship("PackingItem", back_populates="packing_list", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<PackingList(id={self.id}, name='{self.name}', trip_id={self.trip_id})>"


class PackingItem(Base):
    """Packing item model for individual items in a packing list."""

    __tablename__ = "packing_items"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Key
    packing_list_id = Column(Integer, ForeignKey("packing_lists.id", ondelete="CASCADE"), nullable=False, index=True)

    # Item Details
    name = Column(String(200), nullable=False)
    category = Column(
        ENUM(PackingCategory, name="packing_category", create_type=True),
        nullable=False,
        index=True
    )
    quantity = Column(Integer, default=1, nullable=False)

    # Status
    is_packed = Column(Boolean, default=False, nullable=False, index=True)
    packed_at = Column(TIMESTAMP, nullable=True)

    # Organization
    notes = Column(Text, nullable=True)
    priority = Column(
        ENUM(Priority, name="priority", create_type=True),
        default=Priority.MEDIUM,
        nullable=False
    )
    order_index = Column(Integer, default=0, nullable=False)  # For custom sorting

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    packing_list = relationship("PackingList", back_populates="items")

    def __repr__(self):
        return f"<PackingItem(id={self.id}, name='{self.name}', packed={self.is_packed})>"
