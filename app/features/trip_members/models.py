"""
Trip Members data models.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.shared.enums import MemberRole


class TripMember(Base):
    """Trip member representing a user's membership in a trip."""
    
    __tablename__ = "trip_members"
    
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(MemberRole), nullable=False, default=MemberRole.VIEWER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    trip = relationship("Trip", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="trip_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('trip_id', 'user_id', name='uq_trip_member'),
    )
    
    def __repr__(self):
        return f"<TripMember trip_id={self.trip_id} user_id={self.user_id} role={self.role}>"
