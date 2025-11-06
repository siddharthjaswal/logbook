"""
Shared pagination utilities.
"""

from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    skip: int = 0
    limit: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "skip": 0,
                "limit": 100
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    class Config:
        from_attributes = True
