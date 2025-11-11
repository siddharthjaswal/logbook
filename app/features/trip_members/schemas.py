"""
Pydantic schemas for Trip Members feature.
"""

from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.shared.enums import MemberRole

if TYPE_CHECKING:
    from app.features.users.schemas import UserPublicResponse


class TripMemberBase(BaseModel):
    """Base schema for Trip Member."""
    role: MemberRole = Field(..., description="Role of the member in the trip")

    class Config:
        from_attributes = True


class TripMemberCreate(BaseModel):
    """Schema for creating a Trip Member."""
    trip_id: int = Field(..., gt=0, description="ID of the trip")
    user_id: int = Field(..., gt=0, description="ID of the user to add as member")
    role: MemberRole = Field(default=MemberRole.VIEWER, description="Role of the member")
    invited_by: Optional[int] = Field(None, gt=0, description="ID of the user who invited this member")


class TripMemberUpdate(BaseModel):
    """Schema for updating a Trip Member (only role can be updated)."""
    role: MemberRole = Field(..., description="Updated role of the member")


class TripMemberResponse(TripMemberBase):
    """Schema for Trip Member response with basic user info."""
    id: int
    trip_id: int
    user_id: int
    joined_at: datetime
    invited_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    # Nested user information (from relationships)
    user_email: Optional[str] = Field(None, description="Email of the member")
    user_name: Optional[str] = Field(None, description="Full name of the member")

    class Config:
        from_attributes = True


class TripMemberWithUser(TripMemberResponse):
    """Schema for Trip Member response with full user object."""
    user: Optional["UserPublicResponse"] = Field(None, description="Full user object")

    class Config:
        from_attributes = True
