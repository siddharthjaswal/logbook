"""
API routes for Comments feature.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.comments import crud, schemas
from app.features.activity_logs import crud as activity_crud
from app.core.permissions import check_trip_permission
from app.shared.enums import MemberRole, ActivityLogType

router = APIRouter()


@router.post("/trips/{trip_id}/comments", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    trip_id: int,
    comment_data: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a comment to a trip or trip entity."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.VIEWER)
    
    comment = crud.create_comment(
        db, trip_id, current_user.id, comment_data.content,
        comment_data.entity_type, comment_data.entity_id, comment_data.parent_id
    )
    
    # Log activity
    activity_crud.create_activity_log(
        db, trip_id, current_user.id,
        ActivityLogType.COMMENT_ADDED,
        f"Added a comment",
        "comment", comment.id
    )
    
    return comment


@router.get("/trips/{trip_id}/comments", response_model=List[schemas.CommentResponse])
def list_trip_comments(
    trip_id: int,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List comments for a trip or specific entity."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.VIEWER)
    return crud.get_comments(db, trip_id, entity_type, entity_id, skip, limit)


@router.get("/comments/{comment_id}/replies", response_model=List[schemas.CommentResponse])
def get_comment_replies(
    comment_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get replies to a comment."""
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check user has access to the trip
    check_trip_permission(db, comment.trip_id, current_user.id, MemberRole.VIEWER)
    
    return crud.get_comment_replies(db, comment_id, skip, limit)


@router.put("/comments/{comment_id}", response_model=schemas.CommentResponse)
def update_comment(
    comment_id: int,
    update_data: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Edit a comment (owner only)."""
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check ownership
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )
    
    return crud.update_comment(db, comment, update_data.content)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a comment (owner or trip owner only)."""
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user owns the comment or is trip owner
    is_owner = comment.user_id == current_user.id
    is_trip_owner = check_trip_permission(db, comment.trip_id, current_user.id, MemberRole.OWNER)
    
    if not (is_owner or is_trip_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments or if you're the trip owner"
        )
    
    crud.delete_comment(db, comment)
