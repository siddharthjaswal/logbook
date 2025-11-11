"""
API routes for PackingList feature.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.features.users.models import User
from app.features.packing_lists import crud
from app.features.packing_lists.schemas import *

router = APIRouter()


# PACKING LIST ENDPOINTS

@router.post("/packing-lists", response_model=PackingListResponse, status_code=status.HTTP_201_CREATED)
async def create_packing_list(
    list_in: PackingListCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new packing list."""
    return crud.create_packing_list(db, list_in, current_user.id)


@router.get("/packing-lists/{list_id}", response_model=PackingListResponse)
async def get_packing_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get packing list by ID."""
    packing_list = crud.get_packing_list_by_id(db, list_id)
    if not packing_list:
        raise HTTPException(status_code=404, detail="Packing list not found")
    return packing_list


@router.get("/trips/{trip_id}/packing-lists", response_model=List[PackingListResponse])
async def get_trip_packing_lists(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all packing lists for a trip."""
    return crud.get_packing_lists_by_trip(db, trip_id)


@router.delete("/packing-lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_packing_list(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a packing list."""
    packing_list = crud.get_packing_list_by_id(db, list_id)
    if not packing_list:
        raise HTTPException(status_code=404, detail="Packing list not found")
    crud.delete_packing_list(db, packing_list)


# PACKING ITEM ENDPOINTS

@router.post("/packing-lists/{list_id}/items", response_model=PackingItemResponse)
async def create_packing_item(
    list_id: int,
    item_in: PackingItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add an item to a packing list."""
    return crud.create_packing_item(db, list_id, item_in)


@router.put("/packing-items/{item_id}", response_model=PackingItemResponse)
async def update_packing_item(
    item_id: int,
    item_in: PackingItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a packing item."""
    item = crud.get_packing_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Packing item not found")
    return crud.update_packing_item(db, item, item_in)


@router.post("/packing-items/{item_id}/toggle-pack", response_model=PackingItemResponse)
async def toggle_packed_status(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle packed status of an item."""
    item = crud.get_packing_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Packing item not found")
    return crud.toggle_packed(db, item)


@router.get("/packing-lists/{list_id}/summary")
async def get_list_summary(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get summary for a packing list."""
    return crud.get_packing_list_summary(db, list_id)
