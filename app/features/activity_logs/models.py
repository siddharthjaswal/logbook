"""
ActivityLog model for tracking trip activities and changes.

Maintains an audit trail of all actions performed on a trip
for collaboration transparency and history tracking.
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.core.database import Base
from app.shared.enums import ActivityLogType


class ActivityLog(Base):
    """ActivityLog model for tracking trip activities and changes."""

    __tablename__ = "activity_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Activity Details
    activity_type = Column(
        ENUM(ActivityLogType, name="activity_log_type", create_type=True),
        nullable=False,
        index=True
    )
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=False)

    # Additional metadata stored as JSON
    activity_metadata = Column(JSON, nullable=True, default=lambda: {})

    # Timestamp
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, index=True)

    # Relationships
    trip = relationship("Trip", back_populates="activity_logs")
    user = relationship("User")

    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_activity_logs_trip_created', 'trip_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, trip_id={self.trip_id}, activity_type='{self.activity_type}', created_at='{self.created_at}')>"
