"""
API router for Authentication endpoints.

Handles Google OAuth login, token refresh, and logout.
"""

import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.deps import get_db, get_current_active_user
from app.core.security import decode_refresh_token, create_access_token
from app.core.config import settings
from app.features.auth.oauth import oauth
from app.features.auth.schemas import (
    GoogleUserInfo,
    GoogleIdTokenRequest,
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

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Thread pool for running blocking Google API calls asynchronously
executor = ThreadPoolExecutor(max_workers=4)


@router.post("/google", response_model=AuthUserResponse)
async def google_id_token_login(
    token_request: GoogleIdTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google ID token (for Android/iOS apps).

    This endpoint accepts a Google ID token from mobile apps,
    verifies it with Google, creates/updates the user, and returns JWT tokens.

    Args:
        token_request: Request containing Google ID token
        db: Database session

    Returns:
        AuthUserResponse with access token, refresh token, and user info

    Raises:
        HTTPException 400: If ID token verification fails
    """
    logger.info("🔐 Received Google ID token authentication request")
    logger.info(f"📝 ID Token (first 50 chars): {token_request.idToken[:50]}...")

    try:
        # Verify the ID token with Google (run in thread pool to avoid blocking)
        logger.info("🔍 Verifying ID token with Google...")
        loop = asyncio.get_event_loop()

        # Add timeout to prevent hanging indefinitely
        try:
            idinfo = await asyncio.wait_for(
                loop.run_in_executor(
                    executor,
                    lambda: id_token.verify_oauth2_token(
                        token_request.idToken,
                        google_requests.Request(),
                        settings.GOOGLE_OAUTH_CLIENT_ID
                    )
                ),
                timeout=10.0  # 10 second timeout for Google verification
            )
        except asyncio.TimeoutError:
            logger.error("❌ Google token verification timed out after 10 seconds")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Google authentication service timed out. Please try again."
            )

        logger.info(f"✅ ID token verified successfully")
        logger.info(f"👤 User email: {idinfo.get('email')}")
        logger.info(f"📧 Email verified: {idinfo.get('email_verified')}")

        # Verify the token is for our app
        if idinfo['aud'] not in [settings.GOOGLE_OAUTH_CLIENT_ID, settings.GOOGLE_OAUTH_WEB_CLIENT_ID]:
            logger.error(f"❌ Invalid audience: {idinfo['aud']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token audience"
            )

        # Parse Google user info
        google_user = GoogleUserInfo(
            id=idinfo.get("sub"),
            email=idinfo.get("email"),
            verified_email=idinfo.get("email_verified", False),
            name=idinfo.get("name"),
            given_name=idinfo.get("given_name"),
            family_name=idinfo.get("family_name"),
            picture=idinfo.get("picture"),
            locale=idinfo.get("locale"),
        )

        logger.info(f"📋 Parsed Google user info: {google_user.email}")

        # Get or create user in database
        logger.info("💾 Getting or creating user in database...")
        user = get_or_create_user_from_google(db, google_user)
        logger.info(f"✅ User retrieved/created: ID={user.id}, Email={user.email}")

        # Generate JWT tokens
        logger.info("🎟️  Generating JWT tokens...")
        tokens = generate_tokens_for_user(user)
        logger.info("✅ JWT tokens generated successfully")

        # Create response with tokens and user data
        response = create_auth_response(user, tokens)
        logger.info(f"🎉 Authentication successful for user: {user.email}")

        return response

    except ValueError as e:
        # Invalid token
        logger.error(f"❌ ID token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error during authentication: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


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
