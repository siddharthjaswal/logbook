"""
Integration tests for Expense API endpoints.
"""

import pytest
from decimal import Decimal
from datetime import date
from fastapi import status
from app.features.trips import crud as trips_crud
from app.features.trips.schemas import TripCreate
from app.features.expenses import crud
from app.features.expenses.schemas import (
    ExpenseCreate,
    BudgetCategoryCreate,
    ExpenseSplitCreate,
)
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
    """Sample expense data for API testing."""
    return {
        "trip_id": test_trip.id,
        "description": "Sushi dinner",
        "category": "food_drink",
        "amount": "120.50",
        "currency": "USD",
        "expense_date": str(date.today()),
        "payment_method": "credit_card",
        "is_shared": False,
    }


@pytest.fixture
def test_expense(db, test_trip, test_user):
    """Create a test expense in the database."""
    expense_create = ExpenseCreate(
        trip_id=test_trip.id,
        description="Test Expense",
        category=ExpenseCategory.FOOD_DRINK,
        amount=Decimal("100.00"),
        currency="USD",
        expense_date=date.today(),
        payment_method=PaymentMethod.CASH,
    )
    return crud.create_expense(db, expense_create, user_id=test_user.id)


def test_create_expense_success(client, auth_headers, expense_data):
    """Test creating an expense."""
    response = client.post(
        "/api/v1/expenses", json=expense_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["description"] == expense_data["description"]
    assert data["category"] == expense_data["category"]
    assert data["id"] is not None


def test_create_expense_unauthorized(client, expense_data):
    """Test creating an expense without authentication."""
    response = client.post("/api/v1/expenses", json=expense_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_expense_multi_currency(client, auth_headers, expense_data):
    """Test creating an expense with multi-currency."""
    expense_data["original_amount"] = "10000"
    expense_data["original_currency"] = "JPY"
    expense_data["exchange_rate"] = "0.0091"

    response = client.post(
        "/api/v1/expenses", json=expense_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["original_amount"] == "10000.00"
    assert data["original_currency"] == "JPY"


def test_get_expense_by_id_owner(client, auth_headers, test_expense):
    """Test getting expense by ID as owner."""
    response = client.get(
        f"/api/v1/expenses/{test_expense.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_expense.id
    assert data["description"] == test_expense.description


def test_get_expense_unauthorized(client, test_expense):
    """Test getting expense without authentication."""
    response = client.get(f"/api/v1/expenses/{test_expense.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_expense_not_found(client, auth_headers):
    """Test getting non-existent expense."""
    response = client.get("/api/v1/expenses/99999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_trip_expenses(client, auth_headers, db, test_trip, test_user):
    """Test listing all expenses for a trip."""
    # Create multiple expenses
    for i in range(3):
        expense_create = ExpenseCreate(
            trip_id=test_trip.id,
            description=f"Expense {i}",
            category=ExpenseCategory.FOOD_DRINK,
            amount=Decimal("100.00"),
            currency="USD",
            expense_date=date.today(),
        )
        crud.create_expense(db, expense_create, user_id=test_user.id)

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/expenses", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3


def test_list_trip_expenses_with_category_filter(
    client, auth_headers, db, test_trip, test_user
):
    """Test listing expenses filtered by category."""
    # Create expenses with different categories
    crud.create_expense(
        db,
        ExpenseCreate(
            trip_id=test_trip.id,
            description="Food",
            category=ExpenseCategory.FOOD_DRINK,
            amount=Decimal("100.00"),
            currency="USD",
            expense_date=date.today(),
        ),
        user_id=test_user.id,
    )
    crud.create_expense(
        db,
        ExpenseCreate(
            trip_id=test_trip.id,
            description="Transport",
            category=ExpenseCategory.TRANSPORTATION,
            amount=Decimal("50.00"),
            currency="USD",
            expense_date=date.today(),
        ),
        user_id=test_user.id,
    )

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/expenses?category=food_drink",
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "food_drink"


def test_get_expense_summary(client, auth_headers, db, test_trip, test_user):
    """Test getting expense summary for a trip."""
    # Create expenses
    categories = [
        (ExpenseCategory.FOOD_DRINK, Decimal("120.50")),
        (ExpenseCategory.FOOD_DRINK, Decimal("80.00")),
        (ExpenseCategory.TRANSPORTATION, Decimal("50.00")),
    ]

    for category, amount in categories:
        crud.create_expense(
            db,
            ExpenseCreate(
                trip_id=test_trip.id,
                description="Expense",
                category=category,
                amount=amount,
                currency="USD",
                expense_date=date.today(),
            ),
            user_id=test_user.id,
        )

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/expenses/summary", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert float(data["total_expenses"]) == 250.50
    assert data["count"] == 3
    assert "by_category" in data


def test_update_expense_owner(client, auth_headers, test_expense):
    """Test updating expense as owner."""
    update_data = {
        "description": "Updated dinner",
        "amount": "150.00",
    }

    response = client.put(
        f"/api/v1/expenses/{test_expense.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["description"] == "Updated dinner"
    assert data["amount"] == "150.00"


def test_update_expense_unauthorized(client, test_expense):
    """Test updating expense without authentication."""
    response = client.put(
        f"/api/v1/expenses/{test_expense.id}", json={"description": "Updated"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_expense_owner(client, auth_headers, test_expense, db):
    """Test deleting expense as owner."""
    response = client.delete(
        f"/api/v1/expenses/{test_expense.id}", headers=auth_headers
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify soft delete
    db.refresh(test_expense)
    assert test_expense.deleted_at is not None


def test_delete_expense_unauthorized(client, test_expense):
    """Test deleting expense without authentication."""
    response = client.delete(f"/api/v1/expenses/{test_expense.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_expense_split(client, auth_headers, test_expense, test_user):
    """Test creating an expense split."""
    split_data = {
        "expense_id": test_expense.id,
        "user_id": test_user.id,
        "amount": "50.00",
        "percentage": "50.00",
    }

    response = client.post(
        f"/api/v1/expenses/{test_expense.id}/splits",
        json=split_data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["amount"] == "50.00"
    assert data["percentage"] == "50.00"
    assert data["is_settled"] is False


def test_get_expense_splits(client, auth_headers, db, test_expense, test_user):
    """Test getting all splits for an expense."""
    # Create splits
    for i in range(2):
        crud.create_expense_split(
            db,
            test_expense.id,
            ExpenseSplitCreate(
                user_id=test_user.id,
                amount=Decimal("50.00"),
            ),
        )

    response = client.get(
        f"/api/v1/expenses/{test_expense.id}/splits", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_create_budget_category(client, auth_headers, test_trip):
    """Test creating a budget category."""
    budget_data = {
        "category": "food_drink",
        "budgeted_amount": "500.00",
        "currency": "USD",
    }

    response = client.post(
        f"/api/v1/trips/{test_trip.id}/budget-categories", json=budget_data, headers=auth_headers
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["category"] == "food_drink"
    assert data["budgeted_amount"] == "500.00"


def test_get_budget_categories(client, auth_headers, db, test_trip):
    """Test getting budget categories for a trip."""
    # Create budget categories
    categories = [ExpenseCategory.FOOD_DRINK, ExpenseCategory.TRANSPORTATION]

    for category in categories:
        crud.create_budget_category(
            db,
            test_trip.id,
            BudgetCategoryCreate(
                category=category,
                budgeted_amount=Decimal("500.00"),
                currency="USD",
            ),
        )

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/budget-categories", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_get_budget_vs_actual(client, auth_headers, db, test_trip, test_user):
    """Test comparing budget vs actual spending."""
    # Create budget
    crud.create_budget_category(
        db,
        test_trip.id,
        BudgetCategoryCreate(
            category=ExpenseCategory.FOOD_DRINK,
            budgeted_amount=Decimal("500.00"),
            currency="USD",
        ),
    )

    # Create expenses
    for i in range(2):
        crud.create_expense(
            db,
            ExpenseCreate(
                trip_id=test_trip.id,
                description=f"Food {i}",
                category=ExpenseCategory.FOOD_DRINK,
                amount=Decimal("150.00"),
                currency="USD",
                expense_date=date.today(),
            ),
            user_id=test_user.id,
        )

    response = client.get(
        f"/api/v1/trips/{test_trip.id}/budget/vs-actual", headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "food_drink"
    assert float(data[0]["budgeted"]) == 500.00
    assert float(data[0]["actual"]) == 300.00
    assert float(data[0]["difference"]) == 200.00
