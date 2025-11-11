"""
Pydantic schemas for Checklist feature.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from app.shared.enums import ChecklistType, Priority


class ChecklistItemBase(BaseModel):
    """Base schema for ChecklistItem."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    reminder_date: Optional[date] = None
    priority: Priority = Priority.MEDIUM
    order_index: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True


class ChecklistItemCreate(BaseModel):
    """Schema for creating a ChecklistItem."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    reminder_date: Optional[date] = None
    priority: Priority = Priority.MEDIUM


class ChecklistItemUpdate(BaseModel):
    """Schema for updating a ChecklistItem."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None
    reminder_date: Optional[date] = None
    priority: Optional[Priority] = None
    is_completed: Optional[bool] = None


class ChecklistItemResponse(ChecklistItemBase):
    """Schema for ChecklistItem response."""
    id: int
    checklist_id: int
    is_completed: bool
    completed_at: Optional[datetime]
    completed_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class ChecklistBase(BaseModel):
    """Base schema for Checklist."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    checklist_type: ChecklistType = ChecklistType.GENERAL

    class Config:
        from_attributes = True


class ChecklistCreate(BaseModel):
    """Schema for creating a Checklist."""
    trip_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    checklist_type: ChecklistType = ChecklistType.GENERAL


class ChecklistUpdate(BaseModel):
    """Schema for updating a Checklist."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    checklist_type: Optional[ChecklistType] = None


class ChecklistResponse(ChecklistBase):
    """Schema for Checklist response."""
    id: int
    trip_id: int
    created_by: int
    items: List[ChecklistItemResponse] = []
    created_at: datetime
    updated_at: datetime


class ChecklistSummary(BaseModel):
    """Schema for checklist summary."""
    total_items: int
    completed_items: int
    percentage_completed: float
    overdue_items: int
    by_priority: dict[str, dict[str, int]]  # priority -> {total, completed}
