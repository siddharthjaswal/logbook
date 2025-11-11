"""
Pydantic schemas for Expense feature.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.shared.enums import ExpenseCategory, PaymentMethod


class ExpenseBase(BaseModel):
    """Base schema for Expense."""
    description: str = Field(..., min_length=1, max_length=500)
    category: ExpenseCategory
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    original_amount: Optional[Decimal] = Field(None, gt=0)
    original_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    exchange_rate: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    is_shared: bool = False
    expense_date: date
    expense_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

    class Config:
        from_attributes = True


class ExpenseCreate(BaseModel):
    """Schema for creating an Expense."""
    trip_id: int = Field(..., gt=0)
    trip_day_id: Optional[int] = Field(None, gt=0)
    accommodation_id: Optional[int] = Field(None, gt=0)
    transit_id: Optional[int] = Field(None, gt=0)
    activity_id: Optional[int] = Field(None, gt=0)
    booking_id: Optional[int] = Field(None, gt=0)

    description: str = Field(..., min_length=1, max_length=500)
    category: ExpenseCategory
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    original_amount: Optional[Decimal] = Field(None, gt=0)
    original_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    exchange_rate: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    is_shared: bool = False
    expense_date: date
    expense_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ExpenseUpdate(BaseModel):
    """Schema for updating an Expense."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[ExpenseCategory] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    original_amount: Optional[Decimal] = Field(None, gt=0)
    original_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    exchange_rate: Optional[Decimal] = Field(None, gt=0)
    payment_method: Optional[PaymentMethod] = None
    is_shared: Optional[bool] = None
    expense_date: Optional[date] = None
    expense_time: Optional[str] = Field(None, pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ExpenseResponse(ExpenseBase):
    """Schema for Expense response."""
    id: int
    trip_id: int
    trip_day_id: Optional[int]
    paid_by_user_id: int
    accommodation_id: Optional[int]
    transit_id: Optional[int]
    activity_id: Optional[int]
    booking_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class ExpenseSplitCreate(BaseModel):
    """Schema for creating an ExpenseSplit."""
    user_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)


class ExpenseSplitUpdate(BaseModel):
    """Schema for updating an ExpenseSplit."""
    amount: Optional[Decimal] = Field(None, gt=0)
    percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_settled: Optional[bool] = None


class ExpenseSplitResponse(BaseModel):
    """Schema for ExpenseSplit response."""
    id: int
    expense_id: int
    user_id: int
    amount: Decimal
    percentage: Optional[Decimal]
    is_settled: bool
    settled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetCategoryCreate(BaseModel):
    """Schema for creating a BudgetCategory."""
    category: ExpenseCategory
    budgeted_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None


class BudgetCategoryUpdate(BaseModel):
    """Schema for updating a BudgetCategory."""
    budgeted_amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    notes: Optional[str] = None


class BudgetCategoryResponse(BaseModel):
    """Schema for BudgetCategory response."""
    id: int
    trip_id: int
    category: ExpenseCategory
    budgeted_amount: Decimal
    currency: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseSummary(BaseModel):
    """Schema for expense summary/analytics."""
    total_expenses: Decimal
    currency: str
    by_category: dict[str, Decimal]
    by_payment_method: dict[str, Decimal]
    count: int


class BudgetVsActual(BaseModel):
    """Schema for budget vs actual comparison."""
    category: ExpenseCategory
    budgeted: Decimal
    actual: Decimal
    difference: Decimal
    percentage_used: Decimal
