"""
API routes for Activity Logs feature.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.activity_logs import crud, schemas
from app.core.permissions import check_trip_permission
from app.shared.enums import MemberRole, ActivityLogType

router = APIRouter()


@router.get("/trips/{trip_id}/activity", response_model=List[schemas.ActivityLogResponse])
async def get_trip_activity(
    trip_id: int,
    activity_type: Optional[ActivityLogType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get activity feed for a trip."""
    check_trip_permission(db, trip_id, current_user.id, MemberRole.VIEWER)
    return crud.get_activity_logs(db, trip_id, activity_type, skip, limit)
