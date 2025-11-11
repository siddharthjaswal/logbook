"""
CRUD operations for PackingList feature.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from decimal import Decimal

from app.features.packing_lists.models import PackingList, PackingItem
from app.features.packing_lists.schemas import (
    PackingListCreate, PackingListUpdate,
    PackingItemCreate, PackingItemUpdate
)


# PACKING LIST CRUD

def create_packing_list(db: Session, list_in: PackingListCreate, user_id: int) -> PackingList:
    """Create a new packing list."""
    packing_list = PackingList(**list_in.model_dump(mode='python'), created_by=user_id)
    db.add(packing_list)
    db.commit()
    db.refresh(packing_list)
    return packing_list


def get_packing_list_by_id(db: Session, list_id: int) -> Optional[PackingList]:
    """Get a packing list by ID."""
    return db.query(PackingList).filter(
        PackingList.id == list_id,
        PackingList.deleted_at.is_(None)
    ).first()


def get_packing_lists_by_trip(db: Session, trip_id: int) -> List[PackingList]:
    """Get all packing lists for a trip."""
    return db.query(PackingList).filter(
        PackingList.trip_id == trip_id,
        PackingList.deleted_at.is_(None)
    ).all()


def update_packing_list(db: Session, packing_list: PackingList, list_in: PackingListUpdate) -> PackingList:
    """Update a packing list."""
    update_data = list_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(packing_list, field, value)
    db.commit()
    db.refresh(packing_list)
    return packing_list


def delete_packing_list(db: Session, packing_list: PackingList) -> None:
    """Soft delete a packing list."""
    packing_list.deleted_at = func.now()
    db.commit()


# PACKING ITEM CRUD

def create_packing_item(db: Session, list_id: int, item_in: PackingItemCreate) -> PackingItem:
    """Create a new packing item."""
    item = PackingItem(packing_list_id=list_id, **item_in.model_dump(mode='python'))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_packing_item_by_id(db: Session, item_id: int) -> Optional[PackingItem]:
    """Get a packing item by ID."""
    return db.query(PackingItem).filter(PackingItem.id == item_id).first()


def update_packing_item(db: Session, item: PackingItem, item_in: PackingItemUpdate) -> PackingItem:
    """Update a packing item."""
    update_data = item_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_packing_item(db: Session, item: PackingItem) -> None:
    """Delete a packing item."""
    db.delete(item)
    db.commit()


def toggle_packed(db: Session, item: PackingItem) -> PackingItem:
    """Toggle packed status of an item."""
    item.is_packed = not item.is_packed
    if item.is_packed:
        item.packed_at = func.now()
    else:
        item.packed_at = None
    db.commit()
    db.refresh(item)
    return item


def get_packing_list_summary(db: Session, list_id: int) -> dict:
    """Get summary for a packing list."""
    items = db.query(PackingItem).filter(PackingItem.packing_list_id == list_id).all()

    total = len(items)
    packed = sum(1 for i in items if i.is_packed)
    percentage = (packed / total * 100) if total > 0 else 0

    by_category = {}
    for item in items:
        cat = item.category.value
        if cat not in by_category:
            by_category[cat] = {"total": 0, "packed": 0}
        by_category[cat]["total"] += 1
        if item.is_packed:
            by_category[cat]["packed"] += 1

    return {
        "total_items": total,
        "packed_items": packed,
        "percentage_packed": round(percentage, 2),
        "by_category": by_category
    }
