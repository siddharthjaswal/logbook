"""
Pydantic schemas for Authentication feature.

These schemas are used for OAuth flow and token management.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    """Response when user logs in successfully."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires


class TokenRefreshRequest(BaseModel):
    """Request body for refreshing access token."""

    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Response when refreshing access token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GoogleUserInfo(BaseModel):
    """User information from Google OAuth."""

    id: str  # Google user ID
    email: EmailStr
    verified_email: bool
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None  # Profile photo URL
    locale: Optional[str] = None


class GoogleIdTokenRequest(BaseModel):
    """Request body for Google ID token authentication (Android/iOS)."""

    idToken: str  # Google ID token from Android/iOS app


class AuthUserResponse(BaseModel):
    """
    Combined response after successful authentication.

    Includes both tokens and user information.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict  # UserResponse from users.schemas
