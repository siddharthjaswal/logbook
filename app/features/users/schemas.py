"""
Pydantic schemas for User feature.

These schemas are used for API request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base User schema with common fields."""

    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None

    # Preferences
    default_currency: str = Field(default="USD", min_length=3, max_length=3)
    unit_system: str = Field(default="metric", max_length=10)  # metric | imperial
    date_format: str = Field(default="YYYY-MM-DD", max_length=20)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)


class UserCreate(UserBase):
    """Schema for creating a new user (from Google OAuth)."""

    google_id: str = Field(..., max_length=255)
    email_verified: bool = True
    profile_photo_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user profile (all fields optional)."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None

    # Preferences
    default_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    unit_system: Optional[str] = Field(None, max_length=10)  # metric | imperial
    date_format: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)


class UsernameUpdate(BaseModel):
    """Schema for updating username only."""

    username: str = Field(..., min_length=3, max_length=50)


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data like google_id)."""

    id: int
    email_verified: bool
    profile_photo_url: Optional[str]
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True  # Allows creating from ORM models


class UserPublicResponse(BaseModel):
    """Limited user info for public display (e.g., trip creator)."""

    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    profile_photo_url: Optional[str]

    class Config:
        from_attributes = True
