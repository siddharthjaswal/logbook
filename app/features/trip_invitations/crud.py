"""
CRUD operations for TripInvitation model.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.features.trip_invitations.models import TripInvitation
from app.features.trip_members.models import TripMember
from app.shared.enums import MemberRole, InvitationStatus


def create_invitation(
    db: Session,
    trip_id: int,
    inviter_id: int,
    invitee_email: str,
    role: MemberRole,
    message: Optional[str] = None
) -> TripInvitation:
    """
    Create a new trip invitation with a secure token and expiry date.

    Args:
        db: Database session
        trip_id: ID of the trip
        inviter_id: ID of the user sending the invitation
        invitee_email: Email address of the invitee
        role: Role to assign to the invitee
        message: Optional message from the inviter

    Returns:
        Created TripInvitation object
    """
    # Generate secure token
    token = secrets.token_urlsafe(32)

    # Set expiry to 7 days from now
    expires_at = datetime.utcnow() + timedelta(days=7)

    invitation = TripInvitation(
        trip_id=trip_id,
        inviter_id=inviter_id,
        invitee_email=invitee_email.lower(),
        role=role,
        status=InvitationStatus.PENDING,
        token=token,
        message=message,
        expires_at=expires_at
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def get_invitation_by_id(db: Session, invitation_id: int) -> Optional[TripInvitation]:
    """
    Get a trip invitation by its ID.

    Args:
        db: Database session
        invitation_id: ID of the invitation

    Returns:
        TripInvitation object or None if not found
    """
    return db.query(TripInvitation).filter(TripInvitation.id == invitation_id).first()


def get_invitation_by_token(db: Session, token: str) -> Optional[TripInvitation]:
    """
    Get a trip invitation by its token.

    Args:
        db: Database session
        token: Invitation token

    Returns:
        TripInvitation object or None if not found
    """
    return db.query(TripInvitation).filter(TripInvitation.token == token).first()


def get_trip_invitations(
    db: Session,
    trip_id: int,
    status: Optional[InvitationStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TripInvitation]:
    """
    Get all invitations for a trip, optionally filtered by status.

    Args:
        db: Database session
        trip_id: ID of the trip
        status: Optional status filter
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of TripInvitation objects
    """
    query = db.query(TripInvitation).filter(TripInvitation.trip_id == trip_id)

    if status:
        query = query.filter(TripInvitation.status == status)

    return query.order_by(TripInvitation.created_at.desc()).offset(skip).limit(limit).all()


def get_user_invitations(db: Session, user_email: str) -> List[TripInvitation]:
    """
    Get all invitations for a user by email address.

    Args:
        db: Database session
        user_email: Email address of the user

    Returns:
        List of TripInvitation objects
    """
    return db.query(TripInvitation).filter(
        TripInvitation.invitee_email == user_email.lower(),
        TripInvitation.status == InvitationStatus.PENDING
    ).order_by(TripInvitation.created_at.desc()).all()


def accept_invitation(
    db: Session,
    invitation: TripInvitation,
    user_id: int
) -> TripInvitation:
    """
    Accept a trip invitation and create a trip member.

    Args:
        db: Database session
        invitation: TripInvitation object to accept
        user_id: ID of the user accepting the invitation

    Returns:
        Updated TripInvitation object

    Raises:
        ValueError: If invitation is expired or not pending
    """
    # Check if invitation is expired
    if invitation.expires_at < datetime.utcnow():
        raise ValueError("Invitation has expired")

    # Check if invitation is pending
    if invitation.status != InvitationStatus.PENDING:
        raise ValueError(f"Invitation is not pending (status: {invitation.status})")

    # Create trip member
    trip_member = TripMember(
        trip_id=invitation.trip_id,
        user_id=user_id,
        role=invitation.role,
        invited_by=invitation.inviter_id
    )
    db.add(trip_member)

    # Update invitation
    invitation.status = InvitationStatus.ACCEPTED
    invitation.invitee_id = user_id
    invitation.responded_at = datetime.utcnow()

    db.commit()
    db.refresh(invitation)
    return invitation


def decline_invitation(db: Session, invitation: TripInvitation) -> TripInvitation:
    """
    Decline a trip invitation.

    Args:
        db: Database session
        invitation: TripInvitation object to decline

    Returns:
        Updated TripInvitation object

    Raises:
        ValueError: If invitation is not pending
    """
    # Check if invitation is pending
    if invitation.status != InvitationStatus.PENDING:
        raise ValueError(f"Invitation is not pending (status: {invitation.status})")

    # Update invitation
    invitation.status = InvitationStatus.DECLINED
    invitation.responded_at = datetime.utcnow()

    db.commit()
    db.refresh(invitation)
    return invitation


def cancel_invitation(db: Session, invitation: TripInvitation) -> TripInvitation:
    """
    Cancel a trip invitation (by sender).

    Args:
        db: Database session
        invitation: TripInvitation object to cancel

    Returns:
        Updated TripInvitation object

    Raises:
        ValueError: If invitation is not pending
    """
    # Check if invitation is pending
    if invitation.status != InvitationStatus.PENDING:
        raise ValueError(f"Invitation is not pending (status: {invitation.status})")

    # Update invitation
    invitation.status = InvitationStatus.CANCELLED

    db.commit()
    db.refresh(invitation)
    return invitation


def expire_invitations(db: Session) -> int:
    """
    Mark expired invitations (where expires_at < now and status=PENDING).

    Args:
        db: Database session

    Returns:
        Number of invitations marked as expired
    """
    now = datetime.utcnow()

    result = db.query(TripInvitation).filter(
        and_(
            TripInvitation.status == InvitationStatus.PENDING,
            TripInvitation.expires_at < now
        )
    ).update(
        {
            TripInvitation.status: InvitationStatus.EXPIRED,
            TripInvitation.updated_at: now
        },
        synchronize_session=False
    )

    db.commit()
    return result
