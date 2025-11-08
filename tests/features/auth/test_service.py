"""
Unit tests for Auth service functions.

Tests user creation from Google OAuth and token generation.
"""

import pytest
from app.features.auth.schemas import GoogleUserInfo
from app.features.auth.service import (
    get_or_create_user_from_google,
    generate_tokens_for_user,
    create_auth_response,
)
from app.features.users.crud import get_user_by_google_id


def test_create_new_user_from_google(db):
    """Test creating a new user from Google OAuth data."""
    google_user = GoogleUserInfo(
        id="google_123456",
        email="newuser@example.com",
        verified_email=True,
        given_name="New",
        family_name="User",
        picture="https://example.com/photo.jpg",
    )

    user = get_or_create_user_from_google(db, google_user)

    assert user is not None
    assert user.google_id == "google_123456"
    assert user.email == "newuser@example.com"
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.email_verified is True
    assert user.profile_photo_url == "https://example.com/photo.jpg"


def test_get_existing_user_from_google(db, test_user):
    """Test getting an existing user from Google OAuth data."""
    google_user = GoogleUserInfo(
        id=test_user.google_id,
        email=test_user.email,
        verified_email=True,
        given_name="Updated",
        family_name="Name",
    )

    user = get_or_create_user_from_google(db, google_user)

    # Should return existing user
    assert user.id == test_user.id
    assert user.google_id == test_user.google_id

    # Should update last_login_at
    assert user.last_login_at is not None


def test_get_existing_user_updates_last_login(db, test_user):
    """Test that logging in updates last_login_at timestamp."""
    original_last_login = test_user.last_login_at

    google_user = GoogleUserInfo(
        id=test_user.google_id,
        email=test_user.email,
        verified_email=True,
    )

    user = get_or_create_user_from_google(db, google_user)

    # last_login_at should be updated
    if original_last_login:
        assert user.last_login_at > original_last_login
    else:
        assert user.last_login_at is not None


def test_generate_tokens_for_user(test_user):
    """Test generating access and refresh tokens for a user."""
    tokens = generate_tokens_for_user(test_user)

    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 1800  # 30 minutes * 60 seconds

    # Tokens should be non-empty strings
    assert isinstance(tokens["access_token"], str)
    assert len(tokens["access_token"]) > 0
    assert isinstance(tokens["refresh_token"], str)
    assert len(tokens["refresh_token"]) > 0


def test_create_auth_response(test_user):
    """Test creating auth response with tokens and user data."""
    tokens = generate_tokens_for_user(test_user)
    response = create_auth_response(test_user, tokens)

    assert response.access_token == tokens["access_token"]
    assert response.refresh_token == tokens["refresh_token"]
    assert response.token_type == "bearer"
    assert response.expires_in == 1800

    # User data should be included
    assert response.user["id"] == test_user.id
    assert response.user["email"] == test_user.email


def test_google_user_without_names(db):
    """Test creating user when Google doesn't provide names."""
    google_user = GoogleUserInfo(
        id="google_no_names",
        email="nonames@example.com",
        verified_email=True,
        given_name=None,
        family_name=None,
    )

    user = get_or_create_user_from_google(db, google_user)

    assert user is not None
    assert user.email == "nonames@example.com"
    assert user.first_name is None
    assert user.last_name is None
