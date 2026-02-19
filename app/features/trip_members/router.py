"""
API routes for Trip Members feature.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.trip_members import crud, schemas
from app.core.permissions import check_trip_permission
from app.shared.enums import MemberRole

router = APIRouter()


@router.get("/trips/{trip_id}/members", response_model=List[schemas.TripMemberResponse])
async def list_trip_members(
    trip_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all members of a trip."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.VIEWER)
    members = crud.get_trip_members_with_users(db, trip_id, skip, limit)
    for m in members:
        if m.user:
            name = None
            if getattr(m.user, 'first_name', None):
                name = f"{m.user.first_name} {m.user.last_name or ''}".strip()
            if not name:
                name = getattr(m.user, 'username', None)
            m.user_email = getattr(m.user, 'email', None)
            m.user_name = name
            m.user_avatar = getattr(m.user, 'profile_photo_url', None)
    return members


@router.post("/trips/{trip_id}/members", response_model=schemas.TripMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_trip_member(
    trip_id: int,
    member_data: schemas.TripMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a member to a trip (owner only)."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.OWNER)
    
    # Check if user is already a member
    existing = crud.get_member(db, trip_id, member_data.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this trip"
        )
    
    return crud.create_member(db, trip_id, member_data.user_id, member_data.role, current_user.id)


@router.put("/trips/{trip_id}/members/{user_id}", response_model=schemas.TripMemberResponse)
async def update_member_role(
    trip_id: int,
    user_id: int,
    update_data: schemas.TripMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a member's role (owner only)."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.OWNER)
    
    member = crud.get_member(db, trip_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    return crud.update_member_role(db, member, update_data.role)


@router.delete("/trips/{trip_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_trip_member(
    trip_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a member from a trip (owner only)."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.OWNER)
    
    member = crud.get_member(db, trip_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if trying to remove the last owner
    if member.role == MemberRole.OWNER:
        owners = crud.get_members_by_role(db, trip_id, MemberRole.OWNER)
        if len(owners) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner from the trip"
            )
    
    crud.remove_member(db, member)


@router.post("/trips/{trip_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Leave a trip (for non-owners or if not the last owner)."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.VIEWER)
    
    member = crud.get_member(db, trip_id, current_user.id)
    if not member:
        raise HTTPException(status_code=404, detail="You are not a member of this trip")
    
    # Check if trying to leave as the last owner
    if member.role == MemberRole.OWNER:
        owners = crud.get_members_by_role(db, trip_id, MemberRole.OWNER)
        if len(owners) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave trip as the last owner. Transfer ownership or delete the trip."
            )
    
    crud.remove_member(db, member)
