"""
Integration tests for User API endpoints.

Tests the API layer including authentication, validation, and error handling.
"""

import pytest
from fastapi import status


def test_get_my_profile_success(client, test_user, auth_headers):
    """Test getting current user's profile."""
    response = client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["first_name"] == test_user.first_name
    assert data["is_active"] is True
    assert "google_id" not in data  # Should not expose google_id


def test_get_my_profile_unauthorized(client):
    """Test getting profile without authentication."""
    response = client.get("/api/v1/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


def test_get_my_profile_invalid_token(client):
    """Test getting profile with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_my_profile_success(client, test_user, auth_headers):
    """Test updating current user's profile."""
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "bio": "My new bio",
        "default_currency": "EUR",
        "timezone": "Europe/Paris"
    }

    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["bio"] == "My new bio"
    assert data["default_currency"] == "EUR"
    assert data["timezone"] == "Europe/Paris"


def test_update_my_profile_partial(client, test_user, auth_headers):
    """Test partial update of profile."""
    original_email = test_user.email

    update_data = {"bio": "Just updating bio"}

    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["bio"] == "Just updating bio"
    assert data["email"] == original_email  # Unchanged


def test_update_my_profile_username_taken(client, test_user, db, test_user_data, auth_headers):
    """Test updating username to one that's already taken."""
    # Create another user with a specific username
    from app.features.users.crud import create_user
    from app.features.users.schemas import UserCreate

    other_user_data = test_user_data.copy()
    other_user_data["google_id"] = "other_google_id"
    other_user_data["email"] = "other@example.com"
    other_user_data["username"] = "takenusername"

    other_user_create = UserCreate(**other_user_data)
    create_user(db, other_user_create)

    # Try to update current user's username to the taken one
    update_data = {"username": "takenusername"}

    response = client.put(
        "/api/v1/users/me",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already taken" in response.json()["detail"].lower()


def test_update_my_profile_unauthorized(client):
    """Test updating profile without authentication."""
    update_data = {"first_name": "Updated"}

    response = client.put("/api/v1/users/me", json=update_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_my_username_success(client, test_user, auth_headers):
    """Test updating username."""
    update_data = {"username": "newusername"}

    response = client.patch(
        "/api/v1/users/me/username",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "newusername"


def test_update_my_username_taken(client, test_user, db, test_user_data, auth_headers):
    """Test updating username to one that's already taken."""
    # Create another user with a specific username
    from app.features.users.crud import create_user
    from app.features.users.schemas import UserCreate

    other_user_data = test_user_data.copy()
    other_user_data["google_id"] = "other_google_id"
    other_user_data["email"] = "other@example.com"
    other_user_data["username"] = "takenusername"

    other_user_create = UserCreate(**other_user_data)
    create_user(db, other_user_create)

    # Try to update to the taken username
    update_data = {"username": "takenusername"}

    response = client.patch(
        "/api/v1/users/me/username",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already taken" in response.json()["detail"].lower()


def test_update_my_username_validation_error(client, auth_headers):
    """Test updating username with invalid data."""
    # Username too short (less than 3 chars)
    update_data = {"username": "ab"}

    response = client.patch(
        "/api/v1/users/me/username",
        headers=auth_headers,
        json=update_data
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_delete_my_account_success(client, test_user, db, auth_headers):
    """Test soft deleting current user's account."""
    response = client.delete("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify user is soft deleted
    from app.features.users.crud import get_user_by_id
    deleted_user = get_user_by_id(db, test_user.id)
    assert deleted_user is None  # Not returned because deleted_at is set


def test_delete_my_account_unauthorized(client):
    """Test deleting account without authentication."""
    response = client.delete("/api/v1/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_inactive_user_forbidden(client, test_user, db, auth_headers):
    """Test that inactive users are forbidden from accessing endpoints."""
    # Deactivate the user
    test_user.is_active = False
    db.commit()

    response = client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "inactive" in response.json()["detail"].lower()


def test_deleted_user_forbidden(client, test_user, db):
    """Test that deleted users cannot authenticate."""
    from app.core.security import create_access_token
    from app.features.users.crud import delete_user

    # Create auth headers before deleting
    access_token = create_access_token(data={"sub": test_user.id})
    headers = {"Authorization": f"Bearer {access_token}"}

    # Soft delete the user
    delete_user(db, test_user)

    # Try to access endpoint with token from deleted user
    response = client.get("/api/v1/users/me", headers=headers)

    # Should return 404 because user not found (deleted)
    assert response.status_code == status.HTTP_404_NOT_FOUND
