"""
CRUD operations for User feature.

These functions handle database operations for users.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.features.users.models import User
from app.features.users.schemas import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    """
    Get user by Google ID (for OAuth login).

    Args:
        db: Database session
        google_id: Google OAuth user ID

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(
        User.google_id == google_id,
        User.deleted_at.is_(None)
    ).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email.

    Args:
        db: Database session
        email: User email

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(
        User.email == email,
        User.deleted_at.is_(None)
    ).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username.

    Args:
        db: Database session
        username: Username

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(
        User.username == username,
        User.deleted_at.is_(None)
    ).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Create new user from Google OAuth data.

    Args:
        db: Database session
        user_in: UserCreate schema with user data

    Returns:
        Created User object
    """
    user = User(**user_in.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """
    Update user profile.

    Args:
        db: Database session
        user: User object to update
        user_in: UserUpdate schema with updated fields

    Returns:
        Updated User object
    """
    update_data = user_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def update_username(db: Session, user: User, username: str) -> User:
    """
    Update user's username.

    Args:
        db: Database session
        user: User object to update
        username: New username

    Returns:
        Updated User object
    """
    user.username = username
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: User) -> User:
    """
    Update user's last login timestamp.

    Args:
        db: Database session
        user: User object to update

    Returns:
        Updated User object
    """
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> User:
    """
    Soft delete user (sets deleted_at timestamp).

    Args:
        db: Database session
        user: User object to delete

    Returns:
        Deleted User object
    """
    user.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def check_username_available(db: Session, username: str, exclude_user_id: Optional[int] = None) -> bool:
    """
    Check if username is available.

    Args:
        db: Database session
        username: Username to check
        exclude_user_id: Optional user ID to exclude from check (for updating own username)

    Returns:
        True if username is available, False otherwise
    """
    query = db.query(User).filter(
        User.username == username,
        User.deleted_at.is_(None)
    )

    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)

    return query.first() is None


def check_email_available(db: Session, email: str) -> bool:
    """
    Check if email is available.

    Args:
        db: Database session
        email: Email to check

    Returns:
        True if email is available, False otherwise
    """
    return db.query(User).filter(
        User.email == email,
        User.deleted_at.is_(None)
    ).first() is None
