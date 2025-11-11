"""
API routes for Checklist feature.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.checklists import crud
from app.features.checklists.schemas import *
from app.shared.enums import ChecklistType

router = APIRouter()


# CHECKLIST ENDPOINTS

@router.post("/checklists", response_model=ChecklistResponse, status_code=status.HTTP_201_CREATED)
async def create_checklist(
    checklist_in: ChecklistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new checklist."""
    return crud.create_checklist(db, checklist_in, current_user.id)


@router.get("/checklists/{checklist_id}", response_model=ChecklistResponse)
async def get_checklist(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get checklist by ID."""
    checklist = crud.get_checklist_by_id(db, checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return checklist


@router.get("/trips/{trip_id}/checklists", response_model=List[ChecklistResponse])
async def get_trip_checklists(
    trip_id: int,
    checklist_type: Optional[ChecklistType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all checklists for a trip."""
    return crud.get_checklists_by_trip(db, trip_id, checklist_type=checklist_type)


@router.delete("/checklists/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a checklist."""
    checklist = crud.get_checklist_by_id(db, checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    crud.delete_checklist(db, checklist)


# CHECKLIST ITEM ENDPOINTS

@router.post("/checklists/{checklist_id}/items", response_model=ChecklistItemResponse)
async def create_checklist_item(
    checklist_id: int,
    item_in: ChecklistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add an item to a checklist."""
    return crud.create_checklist_item(db, checklist_id, item_in)


@router.put("/checklist-items/{item_id}", response_model=ChecklistItemResponse)
async def update_checklist_item(
    item_id: int,
    item_in: ChecklistItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a checklist item."""
    item = crud.get_checklist_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return crud.update_checklist_item(db, item, item_in)


@router.post("/checklist-items/{item_id}/toggle-complete", response_model=ChecklistItemResponse)
async def toggle_completed_status(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle completed status of a checklist item."""
    item = crud.get_checklist_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return crud.toggle_completed(db, item, current_user.id)


@router.get("/checklists/{checklist_id}/summary")
async def get_checklist_summary(
    checklist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get summary for a checklist."""
    return crud.get_checklist_summary(db, checklist_id)
