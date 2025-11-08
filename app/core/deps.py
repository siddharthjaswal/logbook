"""
Shared dependencies for dependency injection.

These are used across multiple features via FastAPI's Depends().
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token

# OAuth2 scheme for JWT token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Optional OAuth2 scheme (doesn't raise exception if no token)
oauth2_scheme_optional = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.

    Usage:
        @router.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    Yields:
        Database session that will be closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_id(
    token: str = Depends(oauth2_scheme)
) -> int:
    """
    Dependency to get current authenticated user ID from JWT token.

    Args:
        token: JWT access token from Authorization header

    Returns:
        User ID from token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Dependency to get current authenticated user object.

    Args:
        db: Database session
        user_id: User ID from JWT token

    Returns:
        User object from database

    Raises:
        HTTPException: If user not found
    """
    # Import here to avoid circular imports
    from app.features.users.crud import get_user_by_id

    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Dependency to get current active user.

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user object

    Raises:
        HTTPException: If user is inactive or deleted
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deleted"
        )

    return current_user


async def get_current_active_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
):
    """
    Dependency to get current active user (optional).
    Returns None if no valid token is provided instead of raising an exception.

    Args:
        credentials: HTTP authorization credentials (optional)
        db: Database session

    Returns:
        Active user object or None if not authenticated
    """
    if credentials is None:
        return None

    try:
        # Decode token
        payload = decode_access_token(credentials.credentials)
        if payload is None:
            return None

        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None

        # Import here to avoid circular imports
        from app.features.users.crud import get_user_by_id

        # Get user from database
        user = get_user_by_id(db, user_id)
        if user is None or not user.is_active or user.deleted_at is not None:
            return None

        return user

    except Exception:
        # If anything fails, just return None (unauthenticated)
        return None
