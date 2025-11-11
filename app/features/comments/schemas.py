"""
Pydantic schemas for Comment feature.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CommentBase(BaseModel):
    """Base schema for Comment."""
    content: str = Field(..., min_length=1)
    entity_type: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[int] = Field(None, gt=0)
    parent_id: Optional[int] = Field(None, gt=0)

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    """Schema for creating a Comment."""
    trip_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1)
    entity_type: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[int] = Field(None, gt=0)
    parent_id: Optional[int] = Field(None, gt=0)


class CommentUpdate(BaseModel):
    """Schema for updating a Comment."""
    content: str = Field(..., min_length=1)


class CommentResponse(CommentBase):
    """Schema for Comment response."""
    id: int
    trip_id: int
    user_id: Optional[int]
    entity_type: Optional[str]
    entity_id: Optional[int]
    parent_id: Optional[int]
    content: str
    mentions: Optional[List[int]] = []
    is_edited: bool
    edited_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Nested user information
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    # Reply count for top-level comments
    reply_count: int = 0
