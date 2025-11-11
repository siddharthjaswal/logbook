"""
Pydantic schemas for ActivityLog validation and serialization.

These schemas are used for API request/response validation and
help maintain an audit trail of trip activities and changes.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.shared.enums import ActivityLogType


class ActivityLogBase(BaseModel):
    """Base activity log schema with common fields."""

    activity_type: ActivityLogType
    entity_type: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[int] = None
    description: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class ActivityLogCreate(BaseModel):
    """Schema for creating a new activity log."""

    trip_id: int
    user_id: int
    activity_type: ActivityLogType
    entity_type: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[int] = None
    description: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class ActivityLogResponse(BaseModel):
    """Schema for activity log response with user details."""

    id: int
    trip_id: int
    user_id: Optional[int]
    activity_type: ActivityLogType
    entity_type: Optional[str]
    entity_id: Optional[int]
    description: str
    activity_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime

    # Nested user information (from relationship)
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_user(cls, activity_log):
        """Create response from ORM model with user details."""
        data = {
            "id": activity_log.id,
            "trip_id": activity_log.trip_id,
            "user_id": activity_log.user_id,
            "activity_type": activity_log.activity_type,
            "entity_type": activity_log.entity_type,
            "entity_id": activity_log.entity_id,
            "description": activity_log.description,
            "activity_metadata": activity_log.activity_metadata or {},
            "created_at": activity_log.created_at,
            "user_name": None,
            "user_email": None
        }

        # Add user details if relationship is loaded
        if activity_log.user:
            user = activity_log.user
            # Build full name from first_name and last_name
            if user.first_name and user.last_name:
                data["user_name"] = f"{user.first_name} {user.last_name}"
            elif user.first_name:
                data["user_name"] = user.first_name
            elif user.username:
                data["user_name"] = user.username
            else:
                data["user_name"] = "Unknown User"

            data["user_email"] = user.email

        return cls(**data)
