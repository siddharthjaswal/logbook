"""
Pydantic schemas for TripInvitation validation and serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

from app.shared.enums import MemberRole, InvitationStatus


class TripInvitationBase(BaseModel):
    """Base trip invitation schema with common fields."""

    invitee_email: EmailStr
    role: MemberRole = MemberRole.VIEWER
    message: Optional[str] = Field(None, max_length=1000)


class TripInvitationCreate(TripInvitationBase):
    """Schema for creating a new trip invitation."""

    trip_id: int


class TripInvitationUpdate(BaseModel):
    """Schema for updating a trip invitation (status only)."""

    status: InvitationStatus


class TripInvitationResponse(TripInvitationBase):
    """Schema for trip invitation response with all details."""

    id: int
    trip_id: int
    inviter_id: int
    invitee_id: Optional[int] = None
    status: InvitationStatus
    token: str
    expires_at: datetime
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested fields for better user experience
    inviter_name: Optional[str] = None
    trip_name: Optional[str] = None

    class Config:
        from_attributes = True


class TripInvitationPublic(BaseModel):
    """
    Limited trip invitation schema for public accept/decline endpoints.
    Only shows information necessary for the invitee to make a decision.
    """

    id: int
    trip_name: str
    inviter_name: str
    role: MemberRole
    message: Optional[str] = None
    expires_at: datetime
    status: InvitationStatus

    class Config:
        from_attributes = True
