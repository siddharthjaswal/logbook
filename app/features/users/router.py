"""
API router for User endpoints.

Handles user profile management (authentication handled in auth feature).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.users.schemas import UserResponse, UserUpdate, UsernameUpdate
from app.features.users import crud

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile.

    Returns:
        Current user profile data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user's profile.

    Args:
        user_update: Updated user data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user profile

    Raises:
        HTTPException 400: If username is already taken
    """
    # If username is being updated, check availability
    if user_update.username is not None:
        if not crud.check_username_available(db, user_update.username, exclude_user_id=current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken"
            )

    updated_user = crud.update_user(db, current_user, user_update)
    return updated_user


@router.patch("/me/username", response_model=UserResponse)
async def update_my_username(
    username_update: UsernameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user's username.

    Args:
        username_update: New username
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user profile

    Raises:
        HTTPException 400: If username is already taken
    """
    # Check if username is available
    if not crud.check_username_available(db, username_update.username, exclude_user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )

    updated_user = crud.update_username(db, current_user, username_update.username)
    return updated_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete current user's account (soft delete).

    The account will be marked as deleted but not removed from database.
    User data can be recovered within 30 days.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        204 No Content
    """
    crud.delete_user(db, current_user)
    return None
