"""
API routes for Trip Invitations feature.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.trip_invitations import crud, schemas
from app.features.trip_members import crud as member_crud
from app.features.activity_logs import crud as activity_crud
from app.core.permissions import check_trip_permission
from app.shared.enums import MemberRole, InvitationStatus, ActivityLogType

router = APIRouter()


@router.post("/trips/{trip_id}/invitations", response_model=schemas.TripInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    trip_id: int,
    invitation_data: schemas.TripInvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Send an invitation to join a trip (owner/editor only)."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.EDITOR)
    
    invitation = crud.create_invitation(
        db, trip_id, current_user.id, 
        invitation_data.invitee_email, 
        invitation_data.role,
        invitation_data.message
    )
    
    # Log activity
    activity_crud.log_member_added(
        db, trip_id, current_user.id,
        invitation_data.invitee_email,
        invitation_data.role.value
    )
    
    return invitation


@router.get("/trips/{trip_id}/invitations", response_model=List[schemas.TripInvitationResponse])
async def list_trip_invitations(
    trip_id: int,
    status: Optional[InvitationStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all invitations for a trip (owner/editor only)."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.EDITOR)
    return crud.get_trip_invitations(db, trip_id, status, skip, limit)


@router.delete("/trips/{trip_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    trip_id: int,
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Cancel an invitation (owner/editor only)."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.EDITOR)
    
    invitation = crud.get_invitation_by_id(db, invitation_id)
    if not invitation or invitation.trip_id != trip_id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    try:
        crud.cancel_invitation(db, invitation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invitations/{token}/accept", response_model=schemas.TripInvitationPublic)
async def accept_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Accept an invitation (public endpoint)."""
    invitation = crud.get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    try:
        invitation = crud.accept_invitation(db, invitation, current_user.id)
        
        # Log activity
        activity_crud.log_member_added(
            db, invitation.trip_id, current_user.id,
            current_user.email, invitation.role.value
        )
        
        return invitation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invitations/{token}/decline", response_model=schemas.TripInvitationPublic)
async def decline_invitation(
    token: str,
    db: Session = Depends(get_db)
):
    """Decline an invitation (public endpoint, no auth required)."""
    invitation = crud.get_invitation_by_token(db, token)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    try:
        return crud.decline_invitation(db, invitation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/me/invitations", response_model=List[schemas.TripInvitationPublic])
async def my_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get my pending invitations."""
    return crud.get_user_invitations(db, current_user.email)
