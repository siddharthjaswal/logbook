"""
Unit tests for Expense CRUD operations.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from app.features.expenses import crud
from app.features.expenses.schemas import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseSplitCreate,
    BudgetCategoryCreate,
)
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.shared.enums import (
    ExpenseCategory,
    PaymentMethod,
    TripType,
    TripStatus,
    TripVisibility,
)


@pytest.fixture
def test_trip(db, test_user):
    """Create a test trip for expense tests."""
    trip_create = TripCreate(
        name="Test Trip",
        primary_destination_country="Japan",
        trip_type=TripType.SINGLE_DESTINATION,
        status=TripStatus.PLANNING,
        visibility=TripVisibility.PRIVATE,
        currency="USD",
    )
    return trips_crud.create_trip(db, trip_create, user_id=test_user.id)


@pytest.fixture
def expense_data(test_trip, test_user):
    """Sample expense data for testing."""
    return {
        "trip_id": test_trip.id,
        "description": "Sushi dinner",
        "category": ExpenseCategory.FOOD_DRINK,
        "amount": Decimal("120.50"),
        "currency": "USD",
        "expense_date": date.today(),
        "payment_method": PaymentMethod.CREDIT_CARD,
        "is_shared": False,
    }


@pytest.fixture
def test_expense(db, expense_data, test_user):
    """Create a test expense in the database."""
    expense_create = ExpenseCreate(**expense_data)
    return crud.create_expense(db, expense_create, user_id=test_user.id)


def test_create_expense(db, expense_data, test_user):
    """Test creating an expense."""
    expense_create = ExpenseCreate(**expense_data)
    expense = crud.create_expense(db, expense_create, user_id=test_user.id)

    assert expense.id is not None
    assert expense.description == expense_data["description"]
    assert expense.category == ExpenseCategory.FOOD_DRINK
    assert expense.amount == Decimal("120.50")
    assert expense.currency == "USD"
    assert expense.paid_by_user_id == test_user.id
    assert expense.deleted_at is None


def test_create_expense_with_multi_currency(db, expense_data, test_user):
    """Test creating an expense with multi-currency support."""
    expense_data["original_amount"] = Decimal("10000")
    expense_data["original_currency"] = "JPY"
    expense_data["exchange_rate"] = Decimal("0.0091")

    expense_create = ExpenseCreate(**expense_data)
    expense = crud.create_expense(db, expense_create, user_id=test_user.id)

    assert expense.original_amount == Decimal("10000")
    assert expense.original_currency == "JPY"
    assert expense.exchange_rate == Decimal("0.0091")
    assert expense.amount == Decimal("120.50")  # USD equivalent


def test_get_expense_by_id(db, test_expense):
    """Test getting an expense by ID."""
    expense = crud.get_expense_by_id(db, test_expense.id)

    assert expense is not None
    assert expense.id == test_expense.id
    assert expense.description == test_expense.description


def test_get_expense_by_id_not_found(db):
    """Test getting non-existent expense returns None."""
    expense = crud.get_expense_by_id(db, 99999)
    assert expense is None


def test_get_expenses_by_trip(db, test_trip, expense_data, test_user):
    """Test getting all expenses for a trip."""
    # Create multiple expenses
    for i in range(3):
        data = expense_data.copy()
        data["description"] = f"Expense {i}"
        expense_create = ExpenseCreate(**data)
        crud.create_expense(db, expense_create, user_id=test_user.id)

    expenses = crud.get_expenses_by_trip(db, test_trip.id)

    assert len(expenses) == 3
    assert all(expense.trip_id == test_trip.id for expense in expenses)


def test_get_expenses_by_trip_with_category_filter(db, test_trip, expense_data, test_user):
    """Test getting expenses filtered by category."""
    # Create expenses with different categories
    food_data = expense_data.copy()
    food_data["category"] = ExpenseCategory.FOOD_DRINK
    crud.create_expense(db, ExpenseCreate(**food_data), user_id=test_user.id)

    transport_data = expense_data.copy()
    transport_data["category"] = ExpenseCategory.TRANSPORTATION
    crud.create_expense(db, ExpenseCreate(**transport_data), user_id=test_user.id)

    food_expenses = crud.get_expenses_by_trip(
        db, test_trip.id, category=ExpenseCategory.FOOD_DRINK
    )

    assert len(food_expenses) == 1
    assert food_expenses[0].category == ExpenseCategory.FOOD_DRINK


def test_update_expense(db, test_expense):
    """Test updating an expense."""
    expense_update = ExpenseUpdate(
        description="Updated dinner",
        amount=Decimal("150.00"),
        payment_method=PaymentMethod.CASH,
    )

    updated_expense = crud.update_expense(db, test_expense, expense_update)

    assert updated_expense.description == "Updated dinner"
    assert updated_expense.amount == Decimal("150.00")
    assert updated_expense.payment_method == PaymentMethod.CASH
    # Original fields should remain unchanged
    assert updated_expense.category == test_expense.category


def test_delete_expense(db, test_expense):
    """Test soft deleting an expense."""
    crud.delete_expense(db, test_expense)

    assert test_expense.deleted_at is not None

    # Deleted expense should not be returned
    expense = crud.get_expense_by_id(db, test_expense.id)
    assert expense is None


def test_get_expense_summary(db, test_trip, expense_data, test_user):
    """Test getting expense summary for a trip."""
    # Create expenses with different categories
    categories = [
        (ExpenseCategory.FOOD_DRINK, Decimal("120.50")),
        (ExpenseCategory.FOOD_DRINK, Decimal("80.00")),
        (ExpenseCategory.TRANSPORTATION, Decimal("50.00")),
    ]

    for category, amount in categories:
        data = expense_data.copy()
        data["category"] = category
        data["amount"] = amount
        crud.create_expense(db, ExpenseCreate(**data), user_id=test_user.id)

    summary = crud.get_expense_summary(db, test_trip.id)

    assert summary["total_expenses"] == Decimal("250.50")
    assert summary["by_category"][ExpenseCategory.FOOD_DRINK.value] == Decimal("200.50")
    assert summary["by_category"][ExpenseCategory.TRANSPORTATION.value] == Decimal("50.00")
    assert summary["count"] == 3


def test_create_expense_split(db, test_expense, test_user):
    """Test creating an expense split."""
    split_data = {
        "user_id": test_user.id,
        "amount": Decimal("60.25"),
        "percentage": Decimal("50.00"),
    }

    split_create = ExpenseSplitCreate(**split_data)
    split = crud.create_expense_split(db, test_expense.id, split_create)

    assert split.id is not None
    assert split.expense_id == test_expense.id
    assert split.user_id == test_user.id
    assert split.amount == Decimal("60.25")
    assert split.percentage == Decimal("50.00")
    assert split.is_settled is False


def test_get_expense_splits(db, test_expense, test_user):
    """Test getting all splits for an expense."""
    # Create multiple splits
    for i in range(2):
        split_data = {
            "user_id": test_user.id,
            "amount": Decimal("60.25"),
        }
        crud.create_expense_split(db, test_expense.id, ExpenseSplitCreate(**split_data))

    splits = crud.get_expense_splits(db, test_expense.id)

    assert len(splits) == 2
    assert all(split.expense_id == test_expense.id for split in splits)


def test_settle_expense_split(db, test_expense, test_user):
    """Test settling an expense split."""
    split_data = {
        "user_id": test_user.id,
        "amount": Decimal("60.25"),
    }
    split = crud.create_expense_split(db, test_expense.id, ExpenseSplitCreate(**split_data))

    settled_split = crud.settle_expense_split(db, split.id)

    assert settled_split.is_settled is True
    assert settled_split.settled_at is not None


def test_create_budget_category(db, test_trip):
    """Test creating a budget category."""
    budget_data = {
        "category": ExpenseCategory.FOOD_DRINK,
        "budgeted_amount": Decimal("500.00"),
        "currency": "USD",
    }

    budget_create = BudgetCategoryCreate(**budget_data)
    budget = crud.create_budget_category(db, test_trip.id, budget_create)

    assert budget.id is not None
    assert budget.trip_id == test_trip.id
    assert budget.category == ExpenseCategory.FOOD_DRINK
    assert budget.budgeted_amount == Decimal("500.00")
    assert budget.currency == "USD"


def test_get_budget_categories(db, test_trip):
    """Test getting all budget categories for a trip."""
    # Create budget categories
    categories = [ExpenseCategory.FOOD_DRINK, ExpenseCategory.TRANSPORTATION]

    for category in categories:
        budget_data = {
            "category": category,
            "budgeted_amount": Decimal("500.00"),
            "currency": "USD",
        }
        crud.create_budget_category(db, test_trip.id, BudgetCategoryCreate(**budget_data))

    budgets = crud.get_budget_categories(db, test_trip.id)

    assert len(budgets) == 2
    assert all(budget.trip_id == test_trip.id for budget in budgets)


def test_get_budget_vs_actual(db, test_trip, expense_data, test_user):
    """Test comparing budget vs actual spending."""
    # Create budget
    budget_data = {
        "category": ExpenseCategory.FOOD_DRINK,
        "budgeted_amount": Decimal("500.00"),
        "currency": "USD",
    }
    crud.create_budget_category(db, test_trip.id, BudgetCategoryCreate(**budget_data))

    # Create expenses
    for i in range(2):
        data = expense_data.copy()
        data["category"] = ExpenseCategory.FOOD_DRINK
        data["amount"] = Decimal("150.00")
        crud.create_expense(db, ExpenseCreate(**data), user_id=test_user.id)

    comparison = crud.get_budget_vs_actual(db, test_trip.id)

    assert len(comparison) == 1
    assert comparison[0]["category"] == ExpenseCategory.FOOD_DRINK.value
    assert comparison[0]["budgeted"] == Decimal("500.00")
    assert comparison[0]["actual"] == Decimal("300.00")
    assert comparison[0]["difference"] == Decimal("200.00")
    assert comparison[0]["percentage_used"] == Decimal("60.00")


def test_check_expense_ownership_owner(test_expense, test_user):
    """Test checking ownership when user owns the expense."""
    is_owner = crud.check_expense_ownership(test_expense, test_user.id)
    assert is_owner is True


def test_check_expense_ownership_not_owner(test_expense):
    """Test checking ownership when user doesn't own the expense."""
    is_owner = crud.check_expense_ownership(test_expense, 99999)
    assert is_owner is False
