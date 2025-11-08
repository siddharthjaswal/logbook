"""
Unit tests for User CRUD operations.

Tests the database operations for users without involving the API layer.
"""

import pytest
from datetime import datetime

from app.features.users.crud import (
    get_user_by_id,
    get_user_by_google_id,
    get_user_by_email,
    get_user_by_username,
    create_user,
    update_user,
    update_username,
    delete_user,
    check_username_available,
    check_email_available,
)
from app.features.users.schemas import UserCreate, UserUpdate


def test_create_user(db, test_user_data):
    """Test creating a new user."""
    user_create = UserCreate(**test_user_data)
    user = create_user(db, user_create)

    assert user.id is not None
    assert user.email == test_user_data["email"]
    assert user.google_id == test_user_data["google_id"]
    assert user.email_verified is True
    assert user.is_active is True
    assert user.deleted_at is None


def test_get_user_by_id(db, test_user):
    """Test retrieving user by ID."""
    user = get_user_by_id(db, test_user.id)

    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


def test_get_user_by_id_not_found(db):
    """Test retrieving non-existent user by ID returns None."""
    user = get_user_by_id(db, 99999)
    assert user is None


def test_get_user_by_google_id(db, test_user):
    """Test retrieving user by Google ID."""
    user = get_user_by_google_id(db, test_user.google_id)

    assert user is not None
    assert user.id == test_user.id
    assert user.google_id == test_user.google_id


def test_get_user_by_email(db, test_user):
    """Test retrieving user by email."""
    user = get_user_by_email(db, test_user.email)

    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


def test_get_user_by_username(db, test_user_data):
    """Test retrieving user by username."""
    # Create user with username
    test_user_data["username"] = "testusername"
    user_create = UserCreate(**test_user_data)
    created_user = create_user(db, user_create)

    # Retrieve by username
    user = get_user_by_username(db, "testusername")

    assert user is not None
    assert user.id == created_user.id
    assert user.username == "testusername"


def test_update_user(db, test_user):
    """Test updating user profile."""
    update_data = UserUpdate(
        first_name="Updated",
        last_name="Name",
        bio="Updated bio",
        default_currency="EUR"
    )

    updated_user = update_user(db, test_user, update_data)

    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.bio == "Updated bio"
    assert updated_user.default_currency == "EUR"


def test_update_user_partial(db, test_user):
    """Test partial update of user (only some fields)."""
    original_email = test_user.email

    update_data = UserUpdate(bio="Just updating bio")
    updated_user = update_user(db, test_user, update_data)

    assert updated_user.bio == "Just updating bio"
    assert updated_user.email == original_email  # Unchanged


def test_update_username(db, test_user):
    """Test updating username."""
    new_username = "newusername"
    updated_user = update_username(db, test_user, new_username)

    assert updated_user.username == new_username


def test_delete_user(db, test_user):
    """Test soft delete of user."""
    deleted_user = delete_user(db, test_user)

    assert deleted_user.deleted_at is not None
    assert isinstance(deleted_user.deleted_at, datetime)

    # Verify user is not returned in normal queries
    user = get_user_by_id(db, test_user.id)
    assert user is None


def test_check_username_available(db, test_user_data):
    """Test checking username availability."""
    # Username is available
    assert check_username_available(db, "availableusername") is True

    # Create user with username
    test_user_data["username"] = "takenusername"
    user_create = UserCreate(**test_user_data)
    create_user(db, user_create)

    # Username is taken
    assert check_username_available(db, "takenusername") is False


def test_check_username_available_exclude_self(db, test_user):
    """Test checking username availability excluding current user."""
    # Update user to have a username
    update_username(db, test_user, "myusername")

    # Check if same username is available excluding this user
    # (should return True because we're excluding the user who has it)
    assert check_username_available(db, "myusername", exclude_user_id=test_user.id) is True


def test_check_email_available(db, test_user):
    """Test checking email availability."""
    # Email is taken
    assert check_email_available(db, test_user.email) is False

    # Email is available
    assert check_email_available(db, "available@example.com") is True


def test_deleted_user_not_found(db, test_user):
    """Test that deleted users are not returned in queries."""
    # Delete the user
    delete_user(db, test_user)

    # All getter methods should return None
    assert get_user_by_id(db, test_user.id) is None
    assert get_user_by_google_id(db, test_user.google_id) is None
    assert get_user_by_email(db, test_user.email) is None

    # Email and username should become available again
    assert check_email_available(db, test_user.email) is True
