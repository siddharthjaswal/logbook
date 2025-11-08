# Trips Feature

## Overview
The Trips feature is the core of the Logbook application, handling travel planning, itinerary management, and trip sharing. Trips support flexible date planning, multiple destinations, collaboration (Phase 2), and public sharing.

## Current Implementation Status

### ✅ Completed
- [x] Trip model with SQLAlchemy ORM
- [x] Database migration applied
- [x] Table created in PostgreSQL
- [x] Relationships with User and TripDay

### ⏳ In Progress / Not Started
- [ ] Pydantic schemas (TripCreate, TripUpdate, TripResponse)
- [ ] CRUD operations
- [ ] API router (`/trips` endpoints)
- [ ] Public trip discovery endpoints
- [ ] Trip cloning functionality
- [ ] Tests (pytest + Bruno)

---

## Database Schema

### Table: `trips`

**Purpose**: Store travel itineraries with flexible planning, multi-destination support, and public sharing capabilities.

#### Primary Key
- `id` (BIGINT, auto-increment) - Unique trip identifier

#### Creator Relationship

| Field | Type | Constraints | Purpose |
|-------|------|-------------|---------|
| `created_by` | BIGINT | FOREIGN KEY (users.id), NULL, INDEXED | Trip creator - SET NULL if user deleted |

**Why NULL?**
- Public trips persist even if creator deletes their account
- Prevents data loss when users leave the platform
- Creator attribution is preserved in trip metadata

**Why SET NULL on delete?**
- Discussed in previous session: "User deleted → trips exist without creator"
- Public trips should remain accessible to community
- Private trips owned by deleted user are handled separately

#### Basic Information

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `name` | VARCHAR(200) | NOT NULL | Trip title (e.g., "Summer in Europe", "Japan Cherry Blossom Tour") |
| `description` | TEXT | YES | Detailed trip description, overview, highlights |
| `cover_photo_url` | TEXT | YES | Hero image URL for trip (user-uploaded or default) |

**Design Notes:**
- **name**: Required for every trip, used in search and listings
- **description**: Optional, supports Markdown formatting in UI
- **cover_photo_url**: Optional, can be auto-selected from trip_days photos

#### Dates - Exact Timestamps (Confirmed Trips)

| Field | Type | Nullable | Indexed | Purpose |
|-------|------|----------|---------|---------|
| `start_date_timestamp` | BIGINT | YES | ✅ | Trip start date as Unix timestamp (milliseconds) |
| `start_timezone` | VARCHAR(50) | NOT NULL (default: UTC) | - | Timezone for start date (e.g., "America/New_York") |
| `end_date_timestamp` | BIGINT | YES | ✅ | Trip end date as Unix timestamp (milliseconds) |
| `end_timezone` | VARCHAR(50) | NOT NULL (default: UTC) | - | Timezone for end date |

**Why nullable timestamps?**
- Supports "someday" trips without fixed dates
- Users can plan trips in early stages without commitment
- Transitions from flexible → exact when dates confirmed

**Why separate timezones?**
- Trip might start in NYC (EST) and end in Tokyo (JST)
- Accurate time calculations across time zones
- Important for multi-city trips

**Why BigInt (milliseconds)?**
- Stores Unix timestamp in milliseconds (13 digits)
- Supports precise time for flight/train schedules
- Example: 1704067200000 = January 1, 2024 00:00:00 UTC

#### Flexible/Tentative Dates (Planning Stage)

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `dates_confirmed` | BOOLEAN | NOT NULL (default: FALSE) | Whether exact dates are finalized |
| `planned_start_year` | INTEGER | YES | Target year (e.g., 2025) |
| `planned_start_month` | INTEGER | YES | Target month (1-12) |
| `planned_start_week` | VARCHAR(10) | YES | Target week ('week1', 'week2', 'week3', 'week4') |
| `planned_duration_days` | INTEGER | YES | Estimated trip length in days |
| `date_flexibility` | VARCHAR(50) | YES | How flexible dates are (enum: EXACT, PLUS_MINUS_FEW_DAYS, ANYTIME_IN_MONTH, ANYTIME_IN_SEASON) |
| `flexible_date_notes` | TEXT | YES | Free-text notes about date constraints |

**Use Case Examples:**

**Scenario 1**: Flexible Summer Trip
```
dates_confirmed: false
planned_start_year: 2025
planned_start_month: 7
planned_duration_days: 14
date_flexibility: "ANYTIME_IN_MONTH"
flexible_date_notes: "Avoiding July 4th weekend, prefer mid-month"
```

**Scenario 2**: Exact Holiday Trip
```
dates_confirmed: true
start_date_timestamp: 1735689600000  # Dec 31, 2024
end_date_timestamp: 1736467200000    # Jan 9, 2025
planned_duration_days: 10
```

**Scenario 3**: "Someday" Dream Trip
```
dates_confirmed: false
planned_start_year: 2026
date_flexibility: "ANYTIME_IN_SEASON"
flexible_date_notes: "Cherry blossom season in Japan (late March - early April)"
```

**Why this complexity?**
- User request: "what if the user has no start or end date but a thought of number of days"
- Supports early-stage trip planning
- Helps with budget estimation and destination research
- Can search for "trips in Summer 2025" even without exact dates

#### Location - Primary Destination

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `primary_destination_country` | VARCHAR(100) | YES | Main destination country (e.g., "France") |
| `primary_destination_city` | VARCHAR(100) | YES | Main destination city (e.g., "Paris") |

**Why separate from countries_visited/cities_visited?**
- For search and filtering: "Show me trips to Japan"
- For trip cards: "Primary: Tokyo, Japan + 3 more cities"
- Multi-destination trip (France + Italy) might have primary_destination = "France"

**Future**: Add `primary_destination_coordinates` (PostGIS POINT) for map clustering

#### All Destinations (Auto-calculated from TripDays)

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `countries_visited` | ARRAY(TEXT) | [] | List of all countries in the trip |
| `cities_visited` | ARRAY(TEXT) | [] | List of all cities in the trip |

**Example**:
```python
countries_visited: ["France", "Italy", "Switzerland"]
cities_visited: ["Paris", "Lyon", "Milan", "Venice", "Zurich"]
```

**How it works**:
- Backend aggregates from trip_days.place_country and trip_days.place_city
- Auto-updated when trip days are added/removed
- Used for search: "Find trips that visit Rome"
- Used for stats: "This trip covers 3 countries, 5 cities"

**Why arrays?**
- PostgreSQL ARRAY type is performant and queryable
- Can use `@>` operator: `WHERE countries_visited @> ARRAY['Japan']`
- GIN index support for fast searching

#### Trip Type Classification

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `trip_type` | VARCHAR(20) | 'single_destination' | Type of trip |

**Enum Values** (from app/shared/enums.py):
- `SINGLE_DESTINATION`: One city/region (e.g., "Week in Paris")
- `MULTI_CITY`: Multiple cities in one country (e.g., "Tokyo → Kyoto → Osaka")
- `MULTI_COUNTRY`: Multiple countries (e.g., "Europe backpacking")
- `ROUND_TRIP`: Circular route, return to start (e.g., "Iceland Ring Road")
- `ROAD_TRIP`: Car/vehicle-based journey
- `CRUISE`: Cruise ship itinerary
- `BACKPACKING`: Budget/hostel travel
- `BUSINESS`: Business trip with leisure

**Why classify?**
- Better search filters: "Show me backpacking trips"
- UI customization: Road trips show map routes
- Recommendations: "Users who liked road trips also liked..."

#### Status & Visibility

| Field | Type | Default | Indexed | Purpose |
|-------|------|---------|---------|---------|
| `status` | ENUM (trip_status) | PLANNING | ✅ | Current trip status |
| `visibility` | VARCHAR(20) | PRIVATE | ✅ | Who can see this trip |
| `is_featured` | BOOLEAN | FALSE | - | Admin-curated featured trips |

**Status Enum Values**:
- `PLANNING`: Trip is being planned, dates not confirmed
- `UPCOMING`: Dates confirmed, trip is scheduled for future
- `IN_PROGRESS`: Trip is currently happening
- `COMPLETED`: Trip has finished
- `CANCELLED`: Trip was cancelled

**Status Transitions**:
```
PLANNING → UPCOMING (when dates_confirmed = true and start_date in future)
UPCOMING → IN_PROGRESS (when current_date >= start_date)
IN_PROGRESS → COMPLETED (when current_date > end_date)
Any status → CANCELLED (user action)
```

**Visibility Values** (from app/shared/enums.py):
- `PRIVATE`: Only creator and collaborators can see
- `UNLISTED`: Anyone with link can see, not in public listings
- `PUBLIC`: Visible in public trip discovery, search results

**is_featured**:
- Admin can mark exceptional public trips as featured
- Featured trips shown on homepage, recommendation feeds
- Criteria: High quality, good photos, detailed itinerary

#### Budget

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `budget_total` | DECIMAL(12, 2) | YES | Total trip budget |
| `currency` | VARCHAR(3) | NOT NULL (default: USD) | Currency code (ISO 4217) |

**Examples**:
- `budget_total: 3500.00, currency: "USD"` = $3,500 trip
- `budget_total: 450000.00, currency: "JPY"` = ¥450,000 trip

**Why DECIMAL(12, 2)?**
- 12 digits total: supports up to 999,999,999.99 (billion-dollar trips!)
- 2 decimal places: accurate to cents/paise
- Fixed precision avoids floating-point errors

**Why separate currency?**
- Users from different countries use different currencies
- Inherited from user.default_currency when trip created
- Can convert for display but store in original currency

**Future**: Add `budget_breakdown` JSONB for per-category budgets (flights, hotels, food, etc.)

#### Engagement Metrics (Public Trips)

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `views_count` | INTEGER | 0 | Number of times trip was viewed |
| `clones_count` | INTEGER | 0 | Number of times trip was cloned/copied |
| `likes_count` | INTEGER | 0 | Number of users who liked this trip |

**Use Cases**:
- **views_count**: Track popularity, show "trending" trips
- **clones_count**: Most useful/inspiring trips, viral itineraries
- **likes_count**: Community favorites, user bookmarks

**How they increment**:
- Views: Incremented when trip detail page is loaded (once per user session)
- Clones: Incremented when user copies this trip to their account
- Likes: Toggle feature, users can like/unlike

**Privacy**:
- Only tracked for PUBLIC trips
- PRIVATE/UNLISTED trips always show 0

#### Metadata

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `tags` | ARRAY(TEXT) | [] | Searchable tags/categories |
| `notes` | TEXT | NULL | Private notes (only visible to creator/collaborators) |

**Tags Examples**:
```python
tags: ["beach", "family-friendly", "budget", "summer", "europe"]
```

**How tags work**:
- User-generated or auto-suggested
- Used for search and filtering
- Can be categorized: activity tags, season tags, vibe tags
- Support full-text search: `WHERE 'beach' = ANY(tags)`

**Notes**:
- Private scratchpad for trip planning
- Not shown in public trips
- Could include: packing lists, budget notes, contacts

#### Timestamps

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `created_at` | TIMESTAMP | now() | When trip was created |
| `updated_at` | TIMESTAMP | now() (auto-update) | Last modification time |

**Use Cases**:
- **created_at**: Sort by "newest trips", user analytics
- **updated_at**: Cache invalidation, "recently updated" feed
- Auto-updated by PostgreSQL trigger on any column change

#### Soft Delete

| Field | Type | Indexed | Purpose |
|-------|------|---------|---------|
| `deleted_at` | TIMESTAMP (NULL) | ✅ | Soft delete timestamp |

**Soft Delete Strategy**:
- When user deletes trip, set `deleted_at = now()`
- Queries filter `WHERE deleted_at IS NULL` by default
- Allows 30-day recovery period: "Restore deleted trip?"
- Cleanup job permanently deletes after 30 days
- Cascade deletes all trip_days (they're deleted immediately via CASCADE)

**Why indexed?**
- Fast filtering: `WHERE deleted_at IS NULL`
- Efficient cleanup queries: `WHERE deleted_at < now() - interval '30 days'`

---

## Relationships

### User (Many-to-One)
```python
creator = relationship("User", back_populates="trips", foreign_keys=[created_by])
```

**Meaning**:
- Each trip has one creator (the user who made it)
- One user can create many trips
- Foreign key: `created_by → users.id`

**Cascade Behavior**:
- User deleted → `created_by` is SET NULL
- Trip persists without creator (public trips remain accessible)
- Private trips of deleted users are hidden (deleted_at set by application logic)

### TripDays (One-to-Many)
```python
trip_days = relationship("TripDay", back_populates="trip", cascade="all, delete-orphan")
```

**Meaning**:
- One trip has many days (day-by-day itinerary)
- Each trip_day belongs to exactly one trip
- Foreign key: `trip_days.trip_id → trips.id`

**Cascade Behavior**:
- Trip deleted → All trip_days are deleted (CASCADE)
- When trip is soft-deleted → trip_days remain (for recovery)
- When trip is permanently deleted → trip_days deleted from database

### Trip Collaborators (Phase 2)
```python
# collaborators = relationship("TripCollaborator", back_populates="trip")
```

**Future**: Many-to-Many relationship via `trip_collaborators` junction table
- Trip can have multiple collaborators
- User can collaborate on multiple trips
- Different roles: owner, editor, viewer

---

## Indexes

### 1. Primary Key Index
```sql
CREATE INDEX ix_trips_id ON trips(id);
```
**Purpose**: Fast lookups by trip ID (every query uses this)

### 2. Creator Index
```sql
CREATE INDEX ix_trips_created_by ON trips(created_by);
```
**Purpose**:
- Query: "Get all trips created by user X"
- User profile: "Show my trips"
- Analytics: "How many trips did this user create?"

### 3. Start Date Index
```sql
CREATE INDEX ix_trips_start_date_timestamp ON trips(start_date_timestamp);
```
**Purpose**:
- Query: "Trips starting in next 30 days"
- Status transitions: UPCOMING → IN_PROGRESS
- Calendar views, timeline sorting

### 4. End Date Index
```sql
CREATE INDEX ix_trips_end_date_timestamp ON trips(end_date_timestamp);
```
**Purpose**:
- Query: "Trips ending this week"
- Status transitions: IN_PROGRESS → COMPLETED
- Trip duration calculations

### 5. Status Index
```sql
CREATE INDEX ix_trips_status ON trips(status);
```
**Purpose**:
- Query: "Show all PLANNING trips"
- Dashboard: "Upcoming trips", "Completed trips"
- Very selective filter (only 5 possible values)

### 6. Visibility Index
```sql
CREATE INDEX ix_trips_visibility ON trips(visibility);
```
**Purpose**:
- Query: "Get all PUBLIC trips for discovery"
- Privacy filter: exclude PRIVATE trips from search
- Very selective (only 3 values)

### 7. Soft Delete Index
```sql
CREATE INDEX ix_trips_deleted_at ON trips(deleted_at);
```
**Purpose**:
- Fast filtering: `WHERE deleted_at IS NULL` (active trips)
- Cleanup queries: Find trips deleted >30 days ago
- Most queries use this filter

**Composite Index Consideration** (Future optimization):
```sql
CREATE INDEX ix_trips_visibility_status_deleted
ON trips(visibility, status, deleted_at)
WHERE deleted_at IS NULL;
```
- Covers most common query: public, active trips
- Partial index saves space

---

## Business Rules

### 1. Trip Creation
- Creator must be authenticated user
- Only `name` is required initially
- Dates can be added later (flexible planning)
- Defaults: status=PLANNING, visibility=PRIVATE

### 2. Date Validation
- If `dates_confirmed = true`, must have `start_date_timestamp` and `end_date_timestamp`
- `end_date` must be >= `start_date`
- If flexible dates: must have at least `planned_start_year` OR `planned_duration_days`

### 3. Visibility Rules
- **PRIVATE**: Only creator and collaborators (Phase 2) can view
- **UNLISTED**: Anyone with direct link can view, but not in public listings
- **PUBLIC**: Visible in search, discovery, explore pages

### 4. Status Transitions
- **PLANNING → UPCOMING**: User sets `dates_confirmed = true` with future dates
- **UPCOMING → IN_PROGRESS**: Automated when `current_date >= start_date`
- **IN_PROGRESS → COMPLETED**: Automated when `current_date > end_date`
- **Any → CANCELLED**: User action only

### 5. Auto-calculated Fields
- `countries_visited` and `cities_visited` auto-update when trip_days change
- `updated_at` auto-updates on any field change
- `views_count`, `clones_count`, `likes_count` only for PUBLIC trips

### 6. Deletion Rules
- **Soft delete**: Set `deleted_at`, hide from queries
- **Recovery period**: 30 days
- **Permanent delete**: After 30 days, remove from database
- **Trip days**: Cascade deleted when trip permanently deleted

---

## API Endpoints (Planned)

### Trip CRUD
- `POST /trips` - Create new trip
- `GET /trips/{trip_id}` - Get trip by ID (check permissions)
- `PUT /trips/{trip_id}` - Update trip (creator only)
- `DELETE /trips/{trip_id}` - Soft delete trip (creator only)
- `PATCH /trips/{trip_id}/status` - Update trip status

### My Trips
- `GET /trips/me` - Get all trips created by current user
- `GET /trips/me/status/{status}` - Filter by status (planning, upcoming, etc.)

### Public Discovery
- `GET /trips/public` - Discover public trips (paginated, filtered)
- `GET /trips/featured` - Get featured trips
- `GET /trips/search?q={query}` - Search trips by name, tags, destinations

### Trip Engagement
- `POST /trips/{trip_id}/like` - Like a public trip
- `DELETE /trips/{trip_id}/like` - Unlike a trip
- `POST /trips/{trip_id}/clone` - Clone trip to my account (increment clones_count)
- `POST /trips/{trip_id}/view` - Record a view (increment views_count)

### Trip Days (nested)
- `GET /trips/{trip_id}/days` - Get all days for a trip
- `POST /trips/{trip_id}/days` - Add day to trip
- (See trip_days/README.md for full CRUD)

---

## Pydantic Schemas (To Be Created)

### TripBase
```python
class TripBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None

    # Exact dates
    start_date_timestamp: Optional[int] = None
    start_timezone: str = "UTC"
    end_date_timestamp: Optional[int] = None
    end_timezone: str = "UTC"

    # Flexible dates
    dates_confirmed: bool = False
    planned_start_year: Optional[int] = None
    planned_start_month: Optional[int] = Field(None, ge=1, le=12)
    planned_start_week: Optional[str] = None
    planned_duration_days: Optional[int] = Field(None, gt=0)
    date_flexibility: Optional[str] = None
    flexible_date_notes: Optional[str] = None

    # Location
    primary_destination_country: Optional[str] = None
    primary_destination_city: Optional[str] = None

    # Classification
    trip_type: str = TripType.SINGLE_DESTINATION.value
    visibility: str = TripVisibility.PRIVATE.value

    # Budget
    budget_total: Optional[Decimal] = None
    currency: str = "USD"

    # Metadata
    tags: List[str] = []
    notes: Optional[str] = None
```

### TripCreate
```python
class TripCreate(TripBase):
    """Create new trip - only name required."""
    pass
```

### TripUpdate
```python
class TripUpdate(BaseModel):
    """Update trip - all fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None
    # ... all other fields optional
```

### TripResponse
```python
class TripResponse(TripBase):
    id: int
    created_by: Optional[int]
    status: TripStatus

    # Auto-calculated
    countries_visited: List[str]
    cities_visited: List[str]

    # Engagement
    views_count: int
    clones_count: int
    likes_count: int
    is_featured: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### TripPublicResponse
```python
class TripPublicResponse(BaseModel):
    """Limited fields for public trip listings."""
    id: int
    name: str
    description: Optional[str]
    cover_photo_url: Optional[str]
    primary_destination_country: Optional[str]
    primary_destination_city: Optional[str]
    countries_visited: List[str]
    trip_type: str
    status: TripStatus
    tags: List[str]
    views_count: int
    clones_count: int
    likes_count: int
    is_featured: bool
    created_at: datetime

    # Exclude: created_by, notes, budget (privacy)
```

---

## CRUD Operations (To Be Created)

### get_trip_by_id
```python
def get_trip_by_id(db: Session, trip_id: int, include_deleted: bool = False) -> Optional[Trip]:
    """Get trip by ID."""
    query = db.query(Trip).filter(Trip.id == trip_id)
    if not include_deleted:
        query = query.filter(Trip.deleted_at.is_(None))
    return query.first()
```

### get_trips_by_user
```python
def get_trips_by_user(
    db: Session,
    user_id: int,
    status: Optional[TripStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Trip]:
    """Get all trips created by a user."""
    query = db.query(Trip).filter(
        Trip.created_by == user_id,
        Trip.deleted_at.is_(None)
    )
    if status:
        query = query.filter(Trip.status == status)
    return query.offset(skip).limit(limit).all()
```

### get_public_trips
```python
def get_public_trips(
    db: Session,
    country: Optional[str] = None,
    trip_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    skip: int = 0,
    limit: int = 20
) -> List[Trip]:
    """Discover public trips with filters."""
    query = db.query(Trip).filter(
        Trip.visibility == TripVisibility.PUBLIC.value,
        Trip.deleted_at.is_(None)
    )

    if country:
        query = query.filter(Trip.countries_visited.contains([country]))
    if trip_type:
        query = query.filter(Trip.trip_type == trip_type)
    if tags:
        query = query.filter(Trip.tags.overlap(tags))

    return query.order_by(Trip.created_at.desc()).offset(skip).limit(limit).all()
```

### create_trip
```python
def create_trip(db: Session, trip_in: TripCreate, user_id: int) -> Trip:
    """Create new trip."""
    trip_data = trip_in.dict()
    trip = Trip(**trip_data, created_by=user_id)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip
```

### update_trip
```python
def update_trip(db: Session, trip: Trip, trip_in: TripUpdate) -> Trip:
    """Update trip."""
    update_data = trip_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    db.commit()
    db.refresh(trip)
    return trip
```

### delete_trip (soft)
```python
def delete_trip(db: Session, trip: Trip) -> Trip:
    """Soft delete trip."""
    trip.deleted_at = datetime.utcnow()
    db.commit()
    return trip
```

### update_trip_destinations
```python
def update_trip_destinations(db: Session, trip_id: int) -> Trip:
    """Auto-update countries_visited and cities_visited from trip_days."""
    trip = get_trip_by_id(db, trip_id)

    countries = set()
    cities = set()

    for day in trip.trip_days:
        if day.place_country:
            countries.add(day.place_country)
        if day.place_city:
            cities.add(day.place_city)

    trip.countries_visited = list(countries)
    trip.cities_visited = list(cities)
    db.commit()
    db.refresh(trip)
    return trip
```

### increment_view_count
```python
def increment_view_count(db: Session, trip_id: int) -> None:
    """Increment views counter (only for public trips)."""
    db.execute(
        text("UPDATE trips SET views_count = views_count + 1 WHERE id = :trip_id AND visibility = 'public'"),
        {"trip_id": trip_id}
    )
    db.commit()
```

---

## Testing Strategy

### Unit Tests (pytest)
- Test trip creation with required fields only
- Test trip creation with all optional fields
- Test flexible date validation
- Test exact date validation (end >= start)
- Test status transitions
- Test auto-update of countries_visited/cities_visited
- Test soft delete
- Test visibility permissions

### Integration Tests
- Test create trip via API (authenticated user)
- Test get trip by ID (check permissions)
- Test update trip (creator only)
- Test delete trip (soft delete, then verify hidden)
- Test public trip discovery with filters
- Test trip cloning
- Test engagement metrics (views, likes, clones)

### Bruno Collection
- `collection/trips/create-trip.bru`
- `collection/trips/get-trip.bru`
- `collection/trips/update-trip.bru`
- `collection/trips/delete-trip.bru`
- `collection/trips/my-trips.bru`
- `collection/trips/public-trips.bru`
- `collection/trips/search-trips.bru`
- `collection/trips/like-trip.bru`
- `collection/trips/clone-trip.bru`

---

## Security Considerations

### 1. Permission Checks
- Only creator can update/delete their trips
- Public trips viewable by anyone
- Private trips only viewable by creator (+ collaborators in Phase 2)
- Unlisted trips viewable by anyone with link

### 2. Data Privacy
- Don't expose `created_by` user details in public trips
- Don't expose `notes` field in public responses
- Budget information optional to share

### 3. Input Validation
- Validate date ranges (end >= start)
- Validate month (1-12), year (reasonable range)
- Validate trip_type, visibility, status (use enums)
- Sanitize tags and notes (prevent XSS)

### 4. Rate Limiting
- Limit trip creation (e.g., 10 trips per hour)
- Limit public trip queries (prevent scraping)
- Limit engagement actions (prevent spam likes/clones)

### 5. Soft Delete Protection
- Ensure all queries filter `deleted_at IS NULL`
- Prevent undelete by non-creator
- Cleanup job runs with admin privileges

---

## Future Enhancements

### Trip Collaboration (Phase 2)
```python
# Add these relationships:
collaborators = relationship("TripCollaborator", back_populates="trip")
# Supports: owner, editor, viewer roles
```

### Location Coordinates (PostGIS)
```python
from geoalchemy2 import Geometry
primary_destination_coordinates = Column(Geometry('POINT'), nullable=True)
# Enables: map clustering, distance searches, route visualization
```

### Budget Breakdown
```python
budget_breakdown = Column(JSONB, nullable=True)
# Example: {"flights": 1200, "hotels": 1500, "food": 600, "activities": 400}
```

### Trip Templates
- Allow users to create trips from templates
- "2-week Japan itinerary template"
- Clone and customize

### Trip Recommendations
- "Users who liked this trip also liked..."
- Based on: trip_type, countries_visited, tags
- Collaborative filtering

### Trip Insights
- "You've visited 15 countries across 42 trips"
- "Your average trip length: 8.5 days"
- Spending patterns, favorite destinations

### Trip Export
- Export trip as PDF itinerary
- Export as Google Calendar events
- Export as ICS file

---

## Related Documentation

- [User Model Documentation](../users/README.md)
- [TripDay Model Documentation](../trip_days/README.md)
- [Entity Documentation](../../../docs/entities/TRIP.md)
- [System Design](../../../SYSTEM_DESIGN.md)
- [Authentication Feature](../auth/README.md)
