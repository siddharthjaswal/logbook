"""
Authentication service for Google OAuth.

Handles OAuth flow, user creation/login, and token management.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.features.users.models import User
from app.features.users.crud import (
    get_user_by_google_id,
    create_user,
    update_last_login,
)
from app.features.users.schemas import UserCreate
from app.features.auth.schemas import GoogleUserInfo, AuthUserResponse


def get_or_create_user_from_google(db: Session, google_user: GoogleUserInfo) -> User:
    """
    Get existing user or create new user from Google OAuth data.

    Args:
        db: Database session
        google_user: User information from Google

    Returns:
        User object (existing or newly created)
    """
    # Check if user exists by Google ID
    user = get_user_by_google_id(db, google_user.id)

    if user:
        # Existing user: Update last login timestamp
        user = update_last_login(db, user)
        return user
    else:
        # New user: Create from Google data
        user_create = UserCreate(
            google_id=google_user.id,
            email=google_user.email,
            email_verified=google_user.verified_email,
            first_name=google_user.given_name,
            last_name=google_user.family_name,
            profile_photo_url=google_user.picture,
        )
        return create_user(db, user_create)


def generate_tokens_for_user(user: User) -> dict:
    """
    Generate access and refresh tokens for a user.

    Args:
        user: User object

    Returns:
        Dictionary with access_token, refresh_token, token_type, expires_in
    """
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
    }


def create_auth_response(user: User, tokens: dict) -> AuthUserResponse:
    """
    Create authentication response with tokens and user data.

    Args:
        user: User object
        tokens: Dictionary with token data

    Returns:
        AuthUserResponse with tokens and user info
    """
    from app.features.users.schemas import UserResponse

    user_response = UserResponse.model_validate(user)

    return AuthUserResponse(
        **tokens,
        user=user_response.model_dump()
    )
