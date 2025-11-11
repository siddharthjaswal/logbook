"""
User model for authentication and user management.

Users authenticate via Google OAuth and can create trips,
collaborate on trips, and interact with public trips.
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model with Google OAuth authentication."""

    __tablename__ = "users"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # OAuth Authentication (Google only for MVP)
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=True, nullable=False)

    # Optional username (can be set after signup)
    username = Column(String(50), unique=True, nullable=True, index=True)

    # Profile (populated from Google)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    profile_photo_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)

    # Preferences
    default_currency = Column(String(3), default="USD", nullable=False)
    date_format = Column(String(20), default="YYYY-MM-DD", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)

    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(TIMESTAMP, nullable=True)

    # Soft Delete
    deleted_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    trips = relationship("Trip", back_populates="creator", foreign_keys="[Trip.created_by]")
    trip_memberships = relationship("TripMember", back_populates="user", foreign_keys="[TripMember.user_id]")  # Phase 2

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
