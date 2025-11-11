"""
Permission checking utilities for trip collaboration.

Provides decorators and utility functions to enforce role-based access control
for trip resources.
"""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.trip_members import crud as member_crud
from app.shared.enums import MemberRole


class PermissionError(HTTPException):
    """Custom exception for permission-related errors."""
    
    def __init__(self, detail: str = "You don't have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class TripNotFoundError(HTTPException):
    """Exception for when trip doesn't exist."""
    
    def __init__(self, trip_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found or you don't have access to it"
        )


def check_trip_permission(
    db: Session,
    trip_id: int,
    user_id: int,
    required_role: MemberRole = MemberRole.VIEWER
) -> bool:
    """
    Check if user has required permission level for a trip.
    
    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user
        required_role: Minimum required role (default: VIEWER)
        
    Returns:
        bool: True if user has required permission
        
    Raises:
        TripNotFoundError: If trip doesn't exist or user is not a member
        PermissionError: If user doesn't have required role
    """
    # Check if user is a member of the trip
    member = member_crud.get_member(db, trip_id, user_id)
    
    if not member:
        raise TripNotFoundError(trip_id)
    
    # Check if user has required role
    has_permission = member_crud.check_member_permission(
        db, trip_id, user_id, required_role
    )
    
    if not has_permission:
        raise PermissionError(
            f"You need {required_role.value} role or higher to perform this action"
        )
    
    return True


def require_trip_permission(required_role: MemberRole = MemberRole.VIEWER):
    """
    Decorator to enforce trip permissions on route handlers.
    
    The route must have a 'trip_id' parameter (path or query).
    
    Args:
        required_role: Minimum required role (default: VIEWER)
        
    Example:
        @router.get("/trips/{trip_id}/details")
        @require_trip_permission(MemberRole.VIEWER)
        async def get_trip_details(trip_id: int, ...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            db: Session = kwargs.get('db')
            current_user: User = kwargs.get('current_user')
            trip_id: int = kwargs.get('trip_id')
            
            if not all([db, current_user, trip_id]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies for permission check"
                )
            
            # Check permission
            check_trip_permission(db, trip_id, current_user.id, required_role)
            
            # Call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_trip_owner(func: Callable):
    """
    Decorator to enforce OWNER permission on route handlers.
    
    Shortcut for @require_trip_permission(MemberRole.OWNER)
    """
    return require_trip_permission(MemberRole.OWNER)(func)


def require_trip_editor(func: Callable):
    """
    Decorator to enforce EDITOR permission on route handlers.
    
    Shortcut for @require_trip_permission(MemberRole.EDITOR)
    """
    return require_trip_permission(MemberRole.EDITOR)(func)


def require_trip_member(func: Callable):
    """
    Decorator to enforce any member access (VIEWER+) on route handlers.
    
    Shortcut for @require_trip_permission(MemberRole.VIEWER)
    """
    return require_trip_permission(MemberRole.VIEWER)(func)


# Dependency functions for FastAPI dependency injection
async def get_trip_permission(
    trip_id: int,
    required_role: MemberRole = MemberRole.VIEWER,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> bool:
    """
    FastAPI dependency to check trip permissions.
    
    Usage:
        @router.get("/trips/{trip_id}/details")
        async def get_trip(
            trip_id: int,
            _: bool = Depends(get_trip_permission)
        ):
            ...
    """
    return check_trip_permission(db, trip_id, current_user.id, required_role)


def require_owner_permission(trip_id: int):
    """Factory function for owner permission dependency."""
    async def check(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ) -> bool:
        return check_trip_permission(db, trip_id, current_user.id, MemberRole.OWNER)
    return check


def require_editor_permission(trip_id: int):
    """Factory function for editor permission dependency."""
    async def check(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ) -> bool:
        return check_trip_permission(db, trip_id, current_user.id, MemberRole.EDITOR)
    return check


def require_member_access(trip_id: int):
    """Factory function for member access dependency."""
    async def check(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
    ) -> bool:
        return check_trip_permission(db, trip_id, current_user.id, MemberRole.VIEWER)
    return check
