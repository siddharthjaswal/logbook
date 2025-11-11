"""
TripInvitation model for managing trip collaboration invitations.

Handles inviting users to collaborate on trips with specific roles.
Supports both registered users and email invitations.
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ENUM

from app.core.database import Base
from app.shared.enums import MemberRole, InvitationStatus


class TripInvitation(Base):
    """TripInvitation model for managing trip collaboration invitations."""

    __tablename__ = "trip_invitations"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invitee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Invitation Details
    invitee_email = Column(String(255), nullable=False, index=True)
    role = Column(
        ENUM(MemberRole, name="member_role", create_type=False),
        default=MemberRole.VIEWER,
        nullable=False
    )
    status = Column(
        ENUM(InvitationStatus, name="invitation_status", create_type=True),
        default=InvitationStatus.PENDING,
        nullable=False,
        index=True
    )

    # Token for invitation link
    token = Column(String(255), unique=True, nullable=False, index=True)

    # Optional message from inviter
    message = Column(Text, nullable=True)

    # Expiration and Response tracking
    expires_at = Column(TIMESTAMP, nullable=False)
    responded_at = Column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id])
    invitee = relationship("User", foreign_keys=[invitee_id])

    def __repr__(self):
        return f"<TripInvitation(id={self.id}, trip_id={self.trip_id}, invitee_email='{self.invitee_email}', status='{self.status}')>"
