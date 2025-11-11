"""
CRUD operations for Checklist feature.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date

from app.features.checklists.models import Checklist, ChecklistItem
from app.features.checklists.schemas import (
    ChecklistCreate, ChecklistUpdate,
    ChecklistItemCreate, ChecklistItemUpdate
)
from app.shared.enums import ChecklistType


# CHECKLIST CRUD

def create_checklist(db: Session, checklist_in: ChecklistCreate, user_id: int) -> Checklist:
    """Create a new checklist."""
    checklist = Checklist(**checklist_in.model_dump(mode='python'), created_by=user_id)
    db.add(checklist)
    db.commit()
    db.refresh(checklist)
    return checklist


def get_checklist_by_id(db: Session, checklist_id: int) -> Optional[Checklist]:
    """Get a checklist by ID."""
    return db.query(Checklist).filter(
        Checklist.id == checklist_id,
        Checklist.deleted_at.is_(None)
    ).first()


def get_checklists_by_trip(
    db: Session,
    trip_id: int,
    checklist_type: Optional[ChecklistType] = None
) -> List[Checklist]:
    """Get all checklists for a trip."""
    query = db.query(Checklist).filter(
        Checklist.trip_id == trip_id,
        Checklist.deleted_at.is_(None)
    )

    if checklist_type:
        query = query.filter(Checklist.checklist_type == checklist_type)

    return query.all()


def update_checklist(db: Session, checklist: Checklist, checklist_in: ChecklistUpdate) -> Checklist:
    """Update a checklist."""
    update_data = checklist_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(checklist, field, value)
    db.commit()
    db.refresh(checklist)
    return checklist


def delete_checklist(db: Session, checklist: Checklist) -> None:
    """Soft delete a checklist."""
    checklist.deleted_at = func.now()
    db.commit()


# CHECKLIST ITEM CRUD

def create_checklist_item(db: Session, checklist_id: int, item_in: ChecklistItemCreate) -> ChecklistItem:
    """Create a new checklist item."""
    item = ChecklistItem(checklist_id=checklist_id, **item_in.model_dump(mode='python'))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_checklist_item_by_id(db: Session, item_id: int) -> Optional[ChecklistItem]:
    """Get a checklist item by ID."""
    return db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()


def update_checklist_item(db: Session, item: ChecklistItem, item_in: ChecklistItemUpdate) -> ChecklistItem:
    """Update a checklist item."""
    update_data = item_in.model_dump(mode='python', exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_checklist_item(db: Session, item: ChecklistItem) -> None:
    """Delete a checklist item."""
    db.delete(item)
    db.commit()


def toggle_completed(db: Session, item: ChecklistItem, user_id: int) -> ChecklistItem:
    """Toggle completed status of a checklist item."""
    item.is_completed = not item.is_completed
    if item.is_completed:
        item.completed_at = func.now()
        item.completed_by = user_id
    else:
        item.completed_at = None
        item.completed_by = None
    db.commit()
    db.refresh(item)
    return item


def get_checklist_summary(db: Session, checklist_id: int) -> dict:
    """Get summary for a checklist."""
    items = db.query(ChecklistItem).filter(ChecklistItem.checklist_id == checklist_id).all()

    total = len(items)
    completed = sum(1 for i in items if i.is_completed)
    percentage = (completed / total * 100) if total > 0 else 0

    # Count overdue items
    today = date.today()
    overdue = sum(1 for i in items if not i.is_completed and i.due_date and i.due_date < today)

    by_priority = {}
    for item in items:
        priority = item.priority.value
        if priority not in by_priority:
            by_priority[priority] = {"total": 0, "completed": 0}
        by_priority[priority]["total"] += 1
        if item.is_completed:
            by_priority[priority]["completed"] += 1

    return {
        "total_items": total,
        "completed_items": completed,
        "percentage_completed": round(percentage, 2),
        "overdue_items": overdue,
        "by_priority": by_priority
    }
