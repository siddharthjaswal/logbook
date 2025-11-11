"""
CRUD operations for Comment feature.
"""

import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.features.comments.models import Comment
from app.features.users.models import User


def extract_mentions(content: str) -> List[str]:
    """
    Extract @username patterns from content using regex.

    Returns list of usernames (without the @ symbol).
    """
    # Match @username patterns (alphanumeric and underscores)
    pattern = r'@(\w+)'
    matches = re.findall(pattern, content)
    # Return unique usernames
    return list(set(matches))


def create_comment(
    db: Session,
    trip_id: int,
    user_id: int,
    content: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    parent_id: Optional[int] = None
) -> Comment:
    """
    Create a new comment.

    Automatically extracts mentions from content and looks up user IDs.
    """
    # Extract mentions from content
    mentioned_usernames = extract_mentions(content)

    # Look up user IDs for mentioned usernames
    mentioned_user_ids = []
    if mentioned_usernames:
        mentioned_users = db.query(User.id).filter(
            User.username.in_(mentioned_usernames),
            User.deleted_at.is_(None),
            User.is_active.is_(True)
        ).all()
        mentioned_user_ids = [user.id for user in mentioned_users]

    # Create comment
    comment = Comment(
        trip_id=trip_id,
        user_id=user_id,
        content=content,
        entity_type=entity_type,
        entity_id=entity_id,
        parent_id=parent_id,
        mentions=mentioned_user_ids if mentioned_user_ids else []
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comment_by_id(db: Session, comment_id: int) -> Optional[Comment]:
    """
    Get a single comment by ID.

    Excludes soft deleted comments.
    """
    return db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.deleted_at.is_(None)
    ).first()


def get_comments(
    db: Session,
    trip_id: int,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Comment]:
    """
    Get comments for a trip or specific entity.

    Returns only top-level comments (parent_id is NULL) ordered by created_at DESC.
    Filters out soft deleted comments.
    """
    query = db.query(Comment).filter(
        Comment.trip_id == trip_id,
        Comment.parent_id.is_(None),
        Comment.deleted_at.is_(None)
    )

    # Optional filtering by entity
    if entity_type:
        query = query.filter(Comment.entity_type == entity_type)
    if entity_id:
        query = query.filter(Comment.entity_id == entity_id)

    return query.order_by(
        Comment.created_at.desc()
    ).offset(skip).limit(limit).all()


def get_comment_replies(
    db: Session,
    parent_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Comment]:
    """
    Get replies to a specific comment.

    Returns comments ordered by created_at ASC (oldest first).
    Filters out soft deleted comments.
    """
    return db.query(Comment).filter(
        Comment.parent_id == parent_id,
        Comment.deleted_at.is_(None)
    ).order_by(
        Comment.created_at.asc()
    ).offset(skip).limit(limit).all()


def update_comment(db: Session, comment: Comment, content: str) -> Comment:
    """
    Update a comment's content.

    Sets is_edited=True and edited_at to current timestamp.
    Re-extracts mentions from the updated content.
    """
    # Extract mentions from updated content
    mentioned_usernames = extract_mentions(content)

    # Look up user IDs for mentioned usernames
    mentioned_user_ids = []
    if mentioned_usernames:
        mentioned_users = db.query(User.id).filter(
            User.username.in_(mentioned_usernames),
            User.deleted_at.is_(None),
            User.is_active.is_(True)
        ).all()
        mentioned_user_ids = [user.id for user in mentioned_users]

    # Update comment
    comment.content = content
    comment.mentions = mentioned_user_ids if mentioned_user_ids else []
    comment.is_edited = True
    comment.edited_at = func.now()

    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    """
    Soft delete a comment.

    Sets deleted_at to current timestamp.
    """
    comment.deleted_at = func.now()
    db.commit()


def check_comment_ownership(db: Session, comment_id: int, user_id: int) -> bool:
    """
    Check if a user owns a specific comment.

    Returns True if the user is the owner, False otherwise.
    """
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.user_id == user_id,
        Comment.deleted_at.is_(None)
    ).first()

    return comment is not None


def get_reply_count(db: Session, comment_id: int) -> int:
    """
    Get the count of replies for a specific comment.

    Excludes soft deleted replies.
    """
    return db.query(func.count(Comment.id)).filter(
        Comment.parent_id == comment_id,
        Comment.deleted_at.is_(None)
    ).scalar()
