"""
API routes for Expense feature.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.expenses import crud
from app.features.expenses.schemas import *
from app.shared.enums import ExpenseCategory

router = APIRouter()


# EXPENSE ENDPOINTS

@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new expense."""
    return crud.create_expense(db, expense_in, current_user.id)


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get expense by ID."""
    expense = crud.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an expense."""
    expense = crud.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return crud.update_expense(db, expense, expense_in)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an expense."""
    expense = crud.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    crud.delete_expense(db, expense)


@router.get("/trips/{trip_id}/expenses", response_model=List[ExpenseResponse])
async def get_trip_expenses(
    trip_id: int,
    category: Optional[ExpenseCategory] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all expenses for a trip."""
    return crud.get_expenses_by_trip(db, trip_id, category, start_date, end_date, skip, limit)


@router.get("/trips/{trip_id}/expenses/summary")
async def get_expense_summary(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get expense summary for a trip."""
    return crud.get_expense_summary(db, trip_id)


# BUDGET ENDPOINTS

@router.post("/trips/{trip_id}/budget-categories", response_model=BudgetCategoryResponse)
async def create_budget_category(
    trip_id: int,
    budget_in: BudgetCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a budget category."""
    return crud.create_budget_category(db, trip_id, budget_in)


@router.get("/trips/{trip_id}/budget-categories", response_model=List[BudgetCategoryResponse])
async def get_budget_categories(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all budget categories for a trip."""
    return crud.get_budget_categories(db, trip_id)


@router.get("/trips/{trip_id}/budget/vs-actual")
async def get_budget_vs_actual(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get budget vs actual comparison."""
    return crud.get_budget_vs_actual(db, trip_id)


# EXPENSE SPLIT ENDPOINTS

@router.post("/expenses/{expense_id}/splits", response_model=ExpenseSplitResponse)
async def create_expense_split(
    expense_id: int,
    split_in: ExpenseSplitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create an expense split."""
    return crud.create_expense_split(db, expense_id, split_in)
