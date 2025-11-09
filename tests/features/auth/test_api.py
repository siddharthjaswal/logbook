"""
Integration tests for Auth API endpoints.

Tests token refresh, logout, and authenticated user retrieval.
"""

import pytest
from fastapi import status
from app.core.security import create_refresh_token, create_access_token


def test_refresh_token_success(client, test_user):
    """Test refreshing access token with valid refresh token."""
    # Create a valid refresh token
    refresh_token = create_refresh_token(data={"sub": test_user.id})

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 604800


def test_refresh_token_invalid(client):
    """Test refreshing with invalid refresh token."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid" in response.json()["detail"].lower()


def test_refresh_token_access_token_rejected(client, test_user):
    """Test that access token cannot be used as refresh token."""
    # Try to use access token as refresh token (should fail)
    access_token = create_access_token(data={"sub": test_user.id})

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_refresh_token_user_not_found(client):
    """Test refreshing token for non-existent user."""
    # Create refresh token with non-existent user ID
    refresh_token = create_refresh_token(data={"sub": 99999})

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_refresh_token_inactive_user(client, test_user, db):
    """Test refreshing token for inactive user."""
    # Deactivate the user
    test_user.is_active = False
    db.commit()

    # Create refresh token
    refresh_token = create_refresh_token(data={"sub": test_user.id})

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "inactive" in response.json()["detail"].lower()


def test_logout_success(client, test_user, auth_headers):
    """Test logout with valid authentication."""
    response = client.post("/api/v1/auth/logout", headers=auth_headers)

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_logout_unauthorized(client):
    """Test logout without authentication."""
    response = client.post("/api/v1/auth/logout")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_via_auth_endpoint(client, test_user, auth_headers):
    """Test getting current user via /auth/me endpoint."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication."""
    response = client.get("/api/v1/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
