"""
CRUD operations for Trip Members feature.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional, List

from app.features.trip_members.models import TripMember
from app.features.trip_members.schemas import TripMemberCreate, TripMemberUpdate
from app.shared.enums import MemberRole


# ROLE HIERARCHY HELPER
def _role_hierarchy_value(role: MemberRole) -> int:
    """
    Get numeric value for role hierarchy comparison.
    Higher number = more permissions.

    Args:
        role: The member role

    Returns:
        int: Numeric value (Owner=3, Editor=2, Viewer=1)
    """
    hierarchy = {
        MemberRole.OWNER: 3,
        MemberRole.EDITOR: 2,
        MemberRole.VIEWER: 1
    }
    return hierarchy.get(role, 0)


# CREATE OPERATIONS

def create_member(
    db: Session,
    trip_id: int,
    user_id: int,
    role: MemberRole,
    invited_by: Optional[int] = None
) -> TripMember:
    """
    Add a new member to a trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user to add as member
        role: Role to assign to the member
        invited_by: Optional ID of the user who invited this member

    Returns:
        TripMember: The created trip member

    Raises:
        IntegrityError: If the user is already a member of the trip
    """
    member = TripMember(
        trip_id=trip_id,
        user_id=user_id,
        role=role,
        invited_by=invited_by
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


# READ OPERATIONS

def get_member_by_id(db: Session, member_id: int) -> Optional[TripMember]:
    """
    Get a trip member by their ID.

    Args:
        db: Database session
        member_id: ID of the trip member

    Returns:
        Optional[TripMember]: The trip member if found, None otherwise
    """
    return db.query(TripMember).filter(
        TripMember.id == member_id
    ).first()


def get_member(db: Session, trip_id: int, user_id: int) -> Optional[TripMember]:
    """
    Get a specific member by trip and user ID.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user

    Returns:
        Optional[TripMember]: The trip member if found, None otherwise
    """
    return db.query(TripMember).filter(
        and_(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id
        )
    ).first()


def get_trip_members(
    db: Session,
    trip_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[TripMember]:
    """
    Get all members of a trip with pagination.

    Args:
        db: Database session
        trip_id: ID of the trip
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        List[TripMember]: List of trip members
    """
    return db.query(TripMember).filter(
        TripMember.trip_id == trip_id
    ).order_by(
        TripMember.joined_at.asc()
    ).offset(skip).limit(limit).all()


def get_trip_members_with_users(
    db: Session,
    trip_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[TripMember]:
    """
    Get all members of a trip with their user data preloaded.

    Args:
        db: Database session
        trip_id: ID of the trip
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        List[TripMember]: List of trip members with user relationships loaded
    """
    return db.query(TripMember).options(
        joinedload(TripMember.user),
        joinedload(TripMember.inviter)
    ).filter(
        TripMember.trip_id == trip_id
    ).order_by(
        TripMember.joined_at.asc()
    ).offset(skip).limit(limit).all()


def get_user_trips(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[TripMember]:
    """
    Get all trips that a user is a member of.

    Args:
        db: Database session
        user_id: ID of the user
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        List[TripMember]: List of trip memberships for the user
    """
    return db.query(TripMember).options(
        joinedload(TripMember.trip)
    ).filter(
        TripMember.user_id == user_id
    ).order_by(
        TripMember.joined_at.desc()
    ).offset(skip).limit(limit).all()


# UPDATE OPERATIONS

def update_member_role(db: Session, member: TripMember, role: MemberRole) -> TripMember:
    """
    Update a member's role in a trip.

    Args:
        db: Database session
        member: The trip member to update
        role: New role to assign

    Returns:
        TripMember: The updated trip member
    """
    member.role = role
    db.commit()
    db.refresh(member)
    return member


# DELETE OPERATIONS

def remove_member(db: Session, member: TripMember) -> None:
    """
    Remove a member from a trip.

    Args:
        db: Database session
        member: The trip member to remove
    """
    db.delete(member)
    db.commit()


# PERMISSION CHECK OPERATIONS

def check_member_permission(
    db: Session,
    trip_id: int,
    user_id: int,
    required_role: MemberRole
) -> bool:
    """
    Check if a user has the required role or higher for a trip.
    Uses role hierarchy: Owner > Editor > Viewer

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user
        required_role: Minimum required role

    Returns:
        bool: True if user has required role or higher, False otherwise

    Examples:
        - User with OWNER role passes check for EDITOR requirement (True)
        - User with VIEWER role fails check for EDITOR requirement (False)
        - User with EDITOR role passes check for EDITOR requirement (True)
    """
    member = get_member(db, trip_id, user_id)

    if not member:
        return False

    user_role_value = _role_hierarchy_value(member.role)
    required_role_value = _role_hierarchy_value(required_role)

    return user_role_value >= required_role_value


def is_trip_owner(db: Session, trip_id: int, user_id: int) -> bool:
    """
    Check if a user is the owner of a trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user

    Returns:
        bool: True if user is trip owner, False otherwise
    """
    member = get_member(db, trip_id, user_id)
    return member is not None and member.role == MemberRole.OWNER


def is_trip_member(db: Session, trip_id: int, user_id: int) -> bool:
    """
    Check if a user is a member of a trip (any role).

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user

    Returns:
        bool: True if user is a member of the trip, False otherwise
    """
    member = get_member(db, trip_id, user_id)
    return member is not None


def has_edit_permission(db: Session, trip_id: int, user_id: int) -> bool:
    """
    Check if a user has edit permissions (Editor or Owner) for a trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user

    Returns:
        bool: True if user can edit the trip, False otherwise
    """
    return check_member_permission(db, trip_id, user_id, MemberRole.EDITOR)


def has_view_permission(db: Session, trip_id: int, user_id: int) -> bool:
    """
    Check if a user has view permissions (any role) for a trip.

    Args:
        db: Database session
        trip_id: ID of the trip
        user_id: ID of the user

    Returns:
        bool: True if user can view the trip, False otherwise
    """
    return check_member_permission(db, trip_id, user_id, MemberRole.VIEWER)


# UTILITY OPERATIONS

def count_trip_members(db: Session, trip_id: int) -> int:
    """
    Count the total number of members in a trip.

    Args:
        db: Database session
        trip_id: ID of the trip

    Returns:
        int: Number of members in the trip
    """
    return db.query(TripMember).filter(
        TripMember.trip_id == trip_id
    ).count()


def get_trip_owners(db: Session, trip_id: int) -> List[TripMember]:
    """
    Get all owners of a trip.

    Args:
        db: Database session
        trip_id: ID of the trip

    Returns:
        List[TripMember]: List of trip members with OWNER role
    """
    return db.query(TripMember).filter(
        and_(
            TripMember.trip_id == trip_id,
            TripMember.role == MemberRole.OWNER
        )
    ).all()


def get_members_by_role(db: Session, trip_id: int, role: MemberRole) -> List[TripMember]:
    """
    Get all members of a trip with a specific role.

    Args:
        db: Database session
        trip_id: ID of the trip
        role: Role to filter by

    Returns:
        List[TripMember]: List of trip members with the specified role
    """
    return db.query(TripMember).filter(
        and_(
            TripMember.trip_id == trip_id,
            TripMember.role == role
        )
    ).order_by(TripMember.joined_at.asc()).all()
