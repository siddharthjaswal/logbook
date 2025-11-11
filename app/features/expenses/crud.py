"""
CRUD operations for Expense feature.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from datetime import date
from decimal import Decimal

from app.features.expenses.models import Expense, ExpenseSplit, BudgetCategory
from app.features.expenses.schemas import (
    ExpenseCreate, ExpenseUpdate,
    ExpenseSplitCreate, ExpenseSplitUpdate,
    BudgetCategoryCreate, BudgetCategoryUpdate
)
from app.shared.enums import ExpenseCategory


# EXPENSE CRUD

def check_expense_ownership(expense: Expense, user_id: int) -> bool:
    """Check if a user owns an expense."""
    return expense.paid_by_user_id == user_id


def create_expense(db: Session, expense_in: ExpenseCreate, user_id: int) -> Expense:
    """Create a new expense."""
    data = expense_in.model_dump(mode='python')
    expense = Expense(**data, paid_by_user_id=user_id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expense_by_id(db: Session, expense_id: int) -> Optional[Expense]:
    """Get an expense by ID."""
    return db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.deleted_at.is_(None)
    ).first()


def get_expenses_by_trip(
    db: Session,
    trip_id: int,
    category: Optional[ExpenseCategory] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Expense]:
    """Get all expenses for a trip with optional filters."""
    query = db.query(Expense).filter(
        Expense.trip_id == trip_id,
        Expense.deleted_at.is_(None)
    )

    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)

    return query.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()


def update_expense(db: Session, expense: Expense, expense_in: ExpenseUpdate) -> Expense:
    """Update an expense."""
    update_data = expense_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: Expense) -> None:
    """Soft delete an expense."""
    expense.deleted_at = func.now()
    db.commit()


def get_expense_summary(db: Session, trip_id: int) -> dict:
    """Get expense summary for a trip."""
    expenses = db.query(Expense).filter(
        Expense.trip_id == trip_id,
        Expense.deleted_at.is_(None)
    ).all()

    total = sum(e.amount for e in expenses)
    by_category = {}
    for e in expenses:
        cat = e.category.value
        by_category[cat] = by_category.get(cat, Decimal(0)) + e.amount

    return {
        "total_expenses": total,
        "by_category": by_category,
        "count": len(expenses)
    }


# EXPENSE SPLIT CRUD

def create_expense_split(db: Session, expense_id: int, split_in: ExpenseSplitCreate) -> ExpenseSplit:
    """Create an expense split."""
    split = ExpenseSplit(expense_id=expense_id, **split_in.model_dump(mode='python'))
    db.add(split)
    db.commit()
    db.refresh(split)
    return split


def get_expense_splits(db: Session, expense_id: int) -> List[ExpenseSplit]:
    """Get all splits for an expense."""
    return db.query(ExpenseSplit).filter(
        ExpenseSplit.expense_id == expense_id
    ).all()


def settle_expense_split(db: Session, split_id: int) -> ExpenseSplit:
    """Mark an expense split as settled."""
    split = db.query(ExpenseSplit).filter(ExpenseSplit.id == split_id).first()
    if split:
        split.is_settled = True
        split.settled_at = func.now()
        db.commit()
        db.refresh(split)
    return split


def update_expense_split(db: Session, split: ExpenseSplit, split_in: ExpenseSplitUpdate) -> ExpenseSplit:
    """Update an expense split."""
    update_data = split_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(split, field, value)
    db.commit()
    db.refresh(split)
    return split


def delete_expense_split(db: Session, split: ExpenseSplit) -> None:
    """Delete an expense split."""
    db.delete(split)
    db.commit()


# BUDGET CATEGORY CRUD

def create_budget_category(db: Session, trip_id: int, budget_in: BudgetCategoryCreate) -> BudgetCategory:
    """Create a budget category."""
    budget = BudgetCategory(trip_id=trip_id, **budget_in.model_dump(mode='python'))
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budget_categories(db: Session, trip_id: int) -> List[BudgetCategory]:
    """Get all budget categories for a trip."""
    return db.query(BudgetCategory).filter(BudgetCategory.trip_id == trip_id).all()


def update_budget_category(db: Session, budget: BudgetCategory, budget_in: BudgetCategoryUpdate) -> BudgetCategory:
    """Update a budget category."""
    update_data = budget_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget_category(db: Session, budget: BudgetCategory) -> None:
    """Delete a budget category."""
    db.delete(budget)
    db.commit()


def get_budget_vs_actual(db: Session, trip_id: int) -> List[dict]:
    """Get budget vs actual comparison."""
    budgets = get_budget_categories(db, trip_id)
    expenses = db.query(Expense).filter(
        Expense.trip_id == trip_id,
        Expense.deleted_at.is_(None)
    ).all()

    # Calculate actual by category
    actual_by_category = {}
    for e in expenses:
        cat = e.category
        actual_by_category[cat] = actual_by_category.get(cat, Decimal(0)) + e.amount

    # Compare budget vs actual
    comparison = []
    for budget in budgets:
        actual = actual_by_category.get(budget.category, Decimal(0))
        difference = budget.budgeted_amount - actual
        percentage = (actual / budget.budgeted_amount * 100) if budget.budgeted_amount > 0 else 0

        comparison.append({
            "category": budget.category,
            "budgeted": budget.budgeted_amount,
            "actual": actual,
            "difference": difference,
            "percentage_used": percentage
        })

    return comparison
