"""
Comment model for trip discussions and collaboration.

Supports commenting on trips and trip entities, with nested replies,
user mentions, and soft delete functionality.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Comment(Base):
    """Comment model for trip discussions and collaboration."""

    __tablename__ = "comments"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)

    # Entity Association (optional - for commenting on specific trip entities)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)

    # Comment Content
    content = Column(Text, nullable=False)

    # User Mentions (stored as JSON array of user IDs for SQLite compatibility)
    mentions = Column(JSON, nullable=True, default=lambda: [])

    # Edit tracking
    is_edited = Column(Boolean, default=False, nullable=False)
    edited_at = Column(TIMESTAMP, nullable=True)

    # Soft Delete
    deleted_at = Column(TIMESTAMP, nullable=True, index=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="comments")
    user = relationship("User")

    # Self-referential relationship for nested replies
    parent = relationship("Comment", remote_side=[id], backref="replies")

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_comments_trip_entity', 'trip_id', 'entity_type', 'entity_id'),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, trip_id={self.trip_id}, user_id={self.user_id}, parent_id={self.parent_id})>"
