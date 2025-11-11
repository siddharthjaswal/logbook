# Implementation Plan: Expenses & Budget Tracking + Notes & Packing Lists

**Date:** November 9, 2025
**Features:**
- Expenses & Budget Tracking
- Notes & Packing Lists

---

## Phase 1: Expenses & Budget Tracking

### Overview
Build comprehensive expense tracking system that works with existing cost fields while adding categorization, splitting, and budget comparison features.

### Database Models

#### 1. **Expense Model**
```python
class Expense(Base):
    """
    Individual expense entry.
    Can be linked to specific entities (accommodation, transit, activity, booking)
    or standalone.
    """
    __tablename__ = "expenses"

    id: int (PK)
    trip_id: int (FK -> trips.id, required)
    trip_day_id: int (FK -> trip_days.id, optional)

    # Link to existing entities (optional)
    accommodation_id: int (FK, optional)
    transit_id: int (FK, optional)
    activity_id: int (FK, optional)
    booking_id: int (FK, optional)

    # Expense details
    category: ExpenseCategory (enum, required)
    description: str (required)
    amount: Decimal (required)
    original_amount: Decimal (optional, if different currency)
    currency: str (required, default: trip currency)
    original_currency: str (optional)
    exchange_rate: Decimal (optional)

    # Payment details
    payment_method: PaymentMethod (enum, optional)
    paid_by_user_id: int (FK -> users.id, required)
    is_shared: bool (default: False)

    # Date/time
    expense_date: date (required)
    expense_time: time (optional)

    # Metadata
    receipt_url: str (optional, for Phase D later)
    notes: str (optional)
    tags: JSON/Array (optional)

    created_at: timestamp
    updated_at: timestamp
    deleted_at: timestamp (soft delete)

    # Relationships
    trip: relationship
    trip_day: relationship
    paid_by: relationship (User)
    splits: relationship (ExpenseSplit)
```

#### 2. **ExpenseSplit Model**
```python
class ExpenseSplit(Base):
    """
    For splitting expenses among multiple travelers.
    """
    __tablename__ = "expense_splits"

    id: int (PK)
    expense_id: int (FK -> expenses.id, required)
    user_id: int (FK -> users.id, required)

    # Split details
    amount: Decimal (required)
    percentage: Decimal (optional)
    is_settled: bool (default: False)
    settled_at: timestamp (optional)

    created_at: timestamp

    # Relationships
    expense: relationship
    user: relationship
```

#### 3. **BudgetCategory Model**
```python
class BudgetCategory(Base):
    """
    Budget allocation by category for a trip.
    """
    __tablename__ = "budget_categories"

    id: int (PK)
    trip_id: int (FK -> trips.id, required)

    category: ExpenseCategory (enum, required)
    budgeted_amount: Decimal (required)
    currency: str (required, default: trip currency)

    notes: str (optional)

    created_at: timestamp
    updated_at: timestamp

    # Relationships
    trip: relationship
```

### Enums

```python
class ExpenseCategory(str, Enum):
    ACCOMMODATION = "accommodation"
    TRANSPORTATION = "transportation"
    FOOD_DRINK = "food_drink"
    ACTIVITIES = "activities"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    INSURANCE = "insurance"
    VISAS_FEES = "visas_fees"
    GEAR_EQUIPMENT = "gear_equipment"
    COMMUNICATIONS = "communications"
    TIPS_GRATUITIES = "tips_gratuities"
    EMERGENCY = "emergency"
    OTHER = "other"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    DIGITAL_WALLET = "digital_wallet"  # Apple Pay, Google Pay, etc.
    BANK_TRANSFER = "bank_transfer"
    TRAVELER_CHECK = "traveler_check"
    OTHER = "other"
```

### API Endpoints

#### Expenses
```
POST   /api/v1/expenses                        - Create expense
GET    /api/v1/expenses/{id}                   - Get expense by ID
PUT    /api/v1/expenses/{id}                   - Update expense
DELETE /api/v1/expenses/{id}                   - Delete expense

GET    /api/v1/trips/{trip_id}/expenses        - List trip expenses
  Query params:
    - category: filter by category
    - start_date, end_date: date range
    - paid_by: filter by payer
    - is_shared: filter shared expenses
    - skip, limit: pagination

GET    /api/v1/trip-days/{day_id}/expenses     - List day expenses

# Link existing entity to expense
POST   /api/v1/expenses/{id}/link-accommodation/{acc_id}
POST   /api/v1/expenses/{id}/link-transit/{transit_id}
POST   /api/v1/expenses/{id}/link-activity/{activity_id}
POST   /api/v1/expenses/{id}/link-booking/{booking_id}

# Analytics
GET    /api/v1/trips/{trip_id}/expenses/summary
  Returns: total spent, by category, by currency, vs budget

GET    /api/v1/trips/{trip_id}/expenses/by-category
  Returns: breakdown by expense category

GET    /api/v1/trips/{trip_id}/expenses/by-day
  Returns: daily spending chart data

GET    /api/v1/trips/{trip_id}/expenses/by-user
  Returns: who paid what
```

#### Expense Splits
```
POST   /api/v1/expenses/{expense_id}/splits     - Add split
PUT    /api/v1/expense-splits/{id}              - Update split
DELETE /api/v1/expense-splits/{id}              - Remove split
POST   /api/v1/expense-splits/{id}/settle       - Mark as settled

GET    /api/v1/trips/{trip_id}/splits/balances  - Who owes whom
  Returns: settlement suggestions
```

#### Budget Categories
```
POST   /api/v1/trips/{trip_id}/budget-categories    - Set category budget
GET    /api/v1/trips/{trip_id}/budget-categories    - List budgets
PUT    /api/v1/budget-categories/{id}               - Update budget
DELETE /api/v1/budget-categories/{id}               - Delete budget

GET    /api/v1/trips/{trip_id}/budget/vs-actual     - Budget comparison
  Returns: budgeted vs actual for each category
```

### Features to Implement

1. ✅ **Basic Expense Tracking**
   - CRUD operations
   - Link to existing entities
   - Categories and payment methods

2. ✅ **Expense Splitting**
   - Split among travelers
   - Track who owes whom
   - Settlement tracking

3. ✅ **Budget Management**
   - Set budgets by category
   - Track actual vs budgeted
   - Warning when over budget

4. ✅ **Reporting & Analytics**
   - Total spent by category
   - Daily spending trends
   - Currency breakdown
   - Budget vs actual comparison

5. 🔄 **Currency Handling** (Phase 1.5)
   - Store original currency
   - Manual exchange rate entry
   - Convert to trip currency for totals

6. 🔜 **Advanced Features** (Future)
   - Automatic currency conversion (external API)
   - Receipt photo uploads
   - Export to CSV/Excel

---

## Phase 2: Notes & Packing Lists

### Overview
Add note-taking and packing list functionality to help travelers organize their trip planning.

### Database Models

#### 1. **TripNote Model**
```python
class TripNote(Base):
    """
    Notes and journals for trips.
    Can be trip-level or day-level.
    """
    __tablename__ = "trip_notes"

    id: int (PK)
    trip_id: int (FK -> trips.id, required)
    trip_day_id: int (FK -> trip_days.id, optional)
    created_by: int (FK -> users.id, required)

    # Note details
    title: str (optional)
    content: text (required)
    note_type: NoteType (enum, default: GENERAL)

    # Organization
    tags: JSON/Array (optional)
    is_pinned: bool (default: False)
    color: str (optional, for UI categorization)

    # Metadata
    created_at: timestamp
    updated_at: timestamp
    deleted_at: timestamp (soft delete)

    # Relationships
    trip: relationship
    trip_day: relationship
    author: relationship (User)
```

#### 2. **PackingList Model**
```python
class PackingList(Base):
    """
    Packing list container for a trip.
    """
    __tablename__ = "packing_lists"

    id: int (PK)
    trip_id: int (FK -> trips.id, required)
    created_by: int (FK -> users.id, required)

    name: str (required, e.g., "Main Luggage", "Carry-on", "Personal Items")
    description: str (optional)

    created_at: timestamp
    updated_at: timestamp
    deleted_at: timestamp (soft delete)

    # Relationships
    trip: relationship
    items: relationship (PackingItem)
    creator: relationship (User)
```

#### 3. **PackingItem Model**
```python
class PackingItem(Base):
    """
    Individual item in a packing list.
    """
    __tablename__ = "packing_items"

    id: int (PK)
    packing_list_id: int (FK -> packing_lists.id, required)

    # Item details
    name: str (required)
    category: PackingCategory (enum, required)
    quantity: int (default: 1)

    # Status
    is_packed: bool (default: False)
    packed_at: timestamp (optional)

    # Organization
    notes: str (optional)
    priority: Priority (enum, default: MEDIUM)
    order_index: int (for custom sorting)

    created_at: timestamp
    updated_at: timestamp

    # Relationships
    packing_list: relationship
```

#### 4. **Checklist Model**
```python
class Checklist(Base):
    """
    Pre-departure and general checklists.
    """
    __tablename__ = "checklists"

    id: int (PK)
    trip_id: int (FK -> trips.id, required)
    created_by: int (FK -> users.id, required)

    name: str (required, e.g., "Pre-Departure", "Booking Confirmations")
    description: str (optional)
    checklist_type: ChecklistType (enum, default: GENERAL)

    created_at: timestamp
    updated_at: timestamp
    deleted_at: timestamp (soft delete)

    # Relationships
    trip: relationship
    items: relationship (ChecklistItem)
    creator: relationship (User)
```

#### 5. **ChecklistItem Model**
```python
class ChecklistItem(Base):
    """
    Individual checklist task.
    """
    __tablename__ = "checklist_items"

    id: int (PK)
    checklist_id: int (FK -> checklists.id, required)

    # Item details
    title: str (required)
    description: str (optional)

    # Status
    is_completed: bool (default: False)
    completed_at: timestamp (optional)
    completed_by: int (FK -> users.id, optional)

    # Scheduling
    due_date: date (optional)
    reminder_date: date (optional)

    # Organization
    priority: Priority (enum, default: MEDIUM)
    order_index: int (for custom sorting)

    created_at: timestamp
    updated_at: timestamp

    # Relationships
    checklist: relationship
    completed_by_user: relationship (User)
```

### Enums

```python
class NoteType(str, Enum):
    GENERAL = "general"
    JOURNAL = "journal"
    PLANNING = "planning"
    IMPORTANT = "important"
    TIPS = "tips"
    MEMORIES = "memories"

class PackingCategory(str, Enum):
    CLOTHING = "clothing"
    TOILETRIES = "toiletries"
    ELECTRONICS = "electronics"
    DOCUMENTS = "documents"
    MEDICATIONS = "medications"
    ACCESSORIES = "accessories"
    ENTERTAINMENT = "entertainment"
    SPORTS_GEAR = "sports_gear"
    CAMPING_GEAR = "camping_gear"
    BABY_ITEMS = "baby_items"
    FOOD_SNACKS = "food_snacks"
    OTHER = "other"

class ChecklistType(str, Enum):
    PRE_DEPARTURE = "pre_departure"
    BOOKING_CONFIRMATIONS = "booking_confirmations"
    DOCUMENTS = "documents"
    SHOPPING = "shopping"
    GENERAL = "general"
    CUSTOM = "custom"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

### API Endpoints

#### Trip Notes
```
POST   /api/v1/trip-notes                      - Create note
GET    /api/v1/trip-notes/{id}                 - Get note
PUT    /api/v1/trip-notes/{id}                 - Update note
DELETE /api/v1/trip-notes/{id}                 - Delete note

GET    /api/v1/trips/{trip_id}/notes           - List trip notes
  Query params:
    - trip_day_id: filter by day
    - note_type: filter by type
    - tags: filter by tags
    - is_pinned: show pinned only

GET    /api/v1/trip-days/{day_id}/notes        - List day notes
POST   /api/v1/trip-notes/{id}/pin             - Pin/unpin note
```

#### Packing Lists
```
POST   /api/v1/packing-lists                   - Create packing list
GET    /api/v1/packing-lists/{id}              - Get list
PUT    /api/v1/packing-lists/{id}              - Update list
DELETE /api/v1/packing-lists/{id}              - Delete list

GET    /api/v1/trips/{trip_id}/packing-lists   - List all packing lists

# Items
POST   /api/v1/packing-lists/{list_id}/items   - Add item
PUT    /api/v1/packing-items/{id}              - Update item
DELETE /api/v1/packing-items/{id}              - Delete item
POST   /api/v1/packing-items/{id}/pack         - Mark as packed
POST   /api/v1/packing-items/{id}/unpack       - Mark as not packed
POST   /api/v1/packing-items/reorder           - Reorder items

GET    /api/v1/packing-lists/{list_id}/summary
  Returns: total items, packed count, by category
```

#### Checklists
```
POST   /api/v1/checklists                      - Create checklist
GET    /api/v1/checklists/{id}                 - Get checklist
PUT    /api/v1/checklists/{id}                 - Update checklist
DELETE /api/v1/checklists/{id}                 - Delete checklist

GET    /api/v1/trips/{trip_id}/checklists      - List trip checklists
  Query params:
    - checklist_type: filter by type

# Items
POST   /api/v1/checklists/{list_id}/items      - Add item
PUT    /api/v1/checklist-items/{id}            - Update item
DELETE /api/v1/checklist-items/{id}            - Delete item
POST   /api/v1/checklist-items/{id}/complete   - Mark complete
POST   /api/v1/checklist-items/{id}/uncomplete - Mark incomplete
POST   /api/v1/checklist-items/reorder         - Reorder items

GET    /api/v1/checklists/{list_id}/summary
  Returns: total items, completed count, overdue count
```

### Features to Implement

1. ✅ **Trip Notes**
   - Create, read, update, delete notes
   - Associate with trip or specific days
   - Note types and tagging
   - Pin important notes

2. ✅ **Packing Lists**
   - Multiple lists per trip (luggage, carry-on, etc.)
   - Categorized items
   - Pack/unpack tracking
   - Progress summary

3. ✅ **Checklists**
   - Pre-departure checklists
   - Task completion tracking
   - Due dates and priorities
   - Reorderable items

4. 🔜 **Templates** (Future)
   - Common packing list templates
   - Pre-departure checklist templates
   - Share templates with community

---

## Implementation Order

### Recommended Sequence:

**Phase 1A: Expenses Core** (Day 1-2)
1. Create Expense model, schemas, CRUD
2. Add ExpenseCategory and PaymentMethod enums
3. Implement basic endpoints
4. Write tests

**Phase 1B: Expense Analytics** (Day 2-3)
1. Add summary/reporting endpoints
2. Budget comparison logic
3. Category breakdowns
4. Write tests

**Phase 1C: Expense Splitting** (Day 3-4)
1. Create ExpenseSplit model
2. Implement split endpoints
3. Balance calculation logic
4. Write tests

**Phase 1D: Budget Categories** (Day 4-5)
1. Create BudgetCategory model
2. Implement budget management
3. Budget vs actual comparison
4. Write tests

**Phase 2A: Notes** (Day 5-6)
1. Create TripNote model
2. Implement CRUD endpoints
3. Pinning and tagging
4. Write tests

**Phase 2B: Packing Lists** (Day 6-7)
1. Create PackingList and PackingItem models
2. Implement list management
3. Pack/unpack functionality
4. Write tests

**Phase 2C: Checklists** (Day 7-8)
1. Create Checklist and ChecklistItem models
2. Implement checklist management
3. Completion tracking
4. Write tests

**Phase 3: Integration & Polish** (Day 8-9)
1. Bruno collections for all endpoints
2. Update documentation
3. Integration tests
4. Performance optimization

---

## Database Migrations

Will need Alembic migrations for:
1. `expenses` table
2. `expense_splits` table
3. `budget_categories` table
4. `trip_notes` table
5. `packing_lists` table
6. `packing_items` table
7. `checklists` table
8. `checklist_items` table

---

## Estimated Scope

**Expenses & Budget Tracking:**
- Models: 3
- Enums: 2
- Endpoints: ~25
- Tests: ~40-50
- Lines of code: ~2,000

**Notes & Packing Lists:**
- Models: 5
- Enums: 4
- Endpoints: ~30
- Tests: ~45-55
- Lines of code: ~2,200

**Total:**
- Models: 8
- Endpoints: ~55
- Tests: ~85-105
- Lines of code: ~4,200

---

## Questions to Consider

1. **Currency Conversion:** Should we integrate with a currency API for automatic conversion, or keep it manual for Phase 1?

2. **Shared Expenses:** Do we need to handle non-user travelers (e.g., friends not on the platform)?

3. **Packing Templates:** Should we provide default templates, or let users create from scratch?

4. **Permissions:** Should trip collaborators (future feature) be able to add expenses/notes, or owner only?

5. **Notifications:** Should we add reminders for checklist items with due dates?

---

## Success Criteria

### Expenses & Budget Tracking
- ✅ Track all trip expenses with categorization
- ✅ Split expenses among travelers
- ✅ Compare actual spending to budget
- ✅ View spending analytics (by category, day, user)
- ✅ Support multiple currencies
- ✅ 100% test coverage

### Notes & Packing Lists
- ✅ Add notes at trip and day level
- ✅ Create multiple packing lists
- ✅ Track packing progress
- ✅ Manage pre-departure checklists
- ✅ Organize with categories and priorities
- ✅ 100% test coverage

---

## Ready to Start?

Would you like me to:
1. **Start with Expenses** (Phase 1A) and build sequentially?
2. **Implement both features in parallel** (faster but more complex)?
3. **Plan more details** before implementing?
4. **Adjust the scope** (add/remove features)?
