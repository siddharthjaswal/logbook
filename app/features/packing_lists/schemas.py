"""
Pydantic schemas for PackingList feature.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.shared.enums import PackingCategory, Priority


class PackingItemBase(BaseModel):
    """Base schema for PackingItem."""
    name: str = Field(..., min_length=1, max_length=200)
    category: PackingCategory
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    order_index: int = Field(default=0, ge=0)

    class Config:
        from_attributes = True


class PackingItemCreate(BaseModel):
    """Schema for creating a PackingItem."""
    name: str = Field(..., min_length=1, max_length=200)
    category: PackingCategory
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None
    priority: Priority = Priority.MEDIUM


class PackingItemUpdate(BaseModel):
    """Schema for updating a PackingItem."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[PackingCategory] = None
    quantity: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None
    priority: Optional[Priority] = None
    is_packed: Optional[bool] = None


class PackingItemResponse(PackingItemBase):
    """Schema for PackingItem response."""
    id: int
    packing_list_id: int
    is_packed: bool
    packed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PackingListBase(BaseModel):
    """Base schema for PackingList."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PackingListCreate(BaseModel):
    """Schema for creating a PackingList."""
    trip_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PackingListUpdate(BaseModel):
    """Schema for updating a PackingList."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class PackingListResponse(PackingListBase):
    """Schema for PackingList response."""
    id: int
    trip_id: int
    created_by: int
    items: List[PackingItemResponse] = []
    created_at: datetime
    updated_at: datetime


class PackingListSummary(BaseModel):
    """Schema for packing list summary."""
    total_items: int
    packed_items: int
    percentage_packed: float
    by_category: dict[str, dict[str, int]]  # category -> {total, packed}
