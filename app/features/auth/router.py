"""
API router for Authentication endpoints.

Handles Google OAuth login, token refresh, and logout.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.core.security import decode_refresh_token, create_access_token
from app.core.config import settings
from app.features.auth.oauth import oauth
from app.features.auth.schemas import (
    GoogleUserInfo,
    AuthUserResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from app.features.auth.service import (
    get_or_create_user_from_google,
    generate_tokens_for_user,
    create_auth_response,
)
from app.features.users.crud import get_user_by_id
from app.features.users.schemas import UserResponse

router = APIRouter()


@router.get("/google")
async def google_login(request: Request):
    """
    Initiate Google OAuth flow.

    Redirects user to Google's OAuth consent screen.

    Args:
        request: FastAPI request object (needed for authlib)

    Returns:
        Redirect to Google OAuth
    """
    # Build redirect URI for OAuth callback
    redirect_uri = request.url_for("google_callback")

    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.

    Exchanges authorization code for access token,
    fetches user info from Google, creates/updates user,
    and returns JWT tokens.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        AuthUserResponse with access token, refresh token, and user info

    Raises:
        HTTPException 400: If OAuth flow fails
    """
    try:
        # Exchange authorization code for access token
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google: {str(e)}"
        )

    # Get user info from Google
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google"
        )

    # Parse Google user info
    google_user = GoogleUserInfo(
        id=user_info.get("sub"),
        email=user_info.get("email"),
        verified_email=user_info.get("email_verified", False),
        name=user_info.get("name"),
        given_name=user_info.get("given_name"),
        family_name=user_info.get("family_name"),
        picture=user_info.get("picture"),
        locale=user_info.get("locale"),
    )

    # Get or create user in database
    user = get_or_create_user_from_google(db, google_user)

    # Generate JWT tokens
    tokens = generate_tokens_for_user(user)

    # Create response with tokens and user data
    return create_auth_response(user, tokens)


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Args:
        refresh_request: Request with refresh token
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException 401: If refresh token is invalid
        HTTPException 404: If user not found
    """
    # Decode refresh token
    payload = decode_refresh_token(refresh_request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user ID from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Get user from database
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Generate new access token
    access_token = create_access_token(data={"sub": user.id})

    return TokenRefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user = Depends(get_current_active_user)):
    """
    Logout user.

    Note: With stateless JWT tokens, logout is primarily client-side
    (clearing tokens from storage). This endpoint exists for consistency
    and potential future server-side token blacklisting.

    Args:
        current_user: Current authenticated user

    Returns:
        204 No Content
    """
    # In stateless JWT implementation, logout happens client-side
    # Client should delete access and refresh tokens

    # Future enhancement: Add token to blacklist/revocation list
    return None


@router.get("/me", response_model=UserResponse)
async def get_authenticated_user(current_user = Depends(get_current_active_user)):
    """
    Get current authenticated user.

    Same as GET /users/me but in auth context.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user profile
    """
    return current_user
