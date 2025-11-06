# Trip Entity

## Overview
The Trip entity represents a travel plan or completed trip. Trips can be private, unlisted, or public, and support collaboration between multiple users. Trips can span multiple destinations and support flexible date planning.

## Database Table: `trips`

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique trip identifier |
| `created_by` | BIGINT | FOREIGN KEY (users.id), NULLABLE | Original trip creator (can be NULL if user deleted) |
| `name` | VARCHAR(200) | NOT NULL | Trip name/title |
| `description` | TEXT | NULLABLE | Detailed trip description |
| `cover_photo_url` | TEXT | NULLABLE | URL to trip cover photo |
| `start_date_timestamp` | BIGINT | NULLABLE | Trip start time in Unix timestamp (NULL for flexible dates) |
| `start_timezone` | VARCHAR(50) | DEFAULT 'UTC' | Timezone for trip start |
| `end_date_timestamp` | BIGINT | NULLABLE | Trip end time in Unix timestamp (NULL for flexible dates) |
| `end_timezone` | VARCHAR(50) | DEFAULT 'UTC' | Timezone for trip end |
| `dates_confirmed` | BOOLEAN | DEFAULT FALSE | Whether dates are confirmed or tentative |
| `planned_start_year` | INTEGER | NULLABLE | Tentative start year (for flexible planning) |
| `planned_start_month` | INTEGER | NULLABLE | Tentative start month (1-12) |
| `planned_start_week` | VARCHAR(10) | NULLABLE | Tentative week (e.g., 'week1', 'week2') |
| `planned_duration_days` | INTEGER | NULLABLE | Planned duration in days |
| `date_flexibility` | VARCHAR(50) | NULLABLE | Flexibility level: 'exact', 'week', 'month', 'season', 'year' |
| `flexible_date_notes` | TEXT | NULLABLE | Notes about date flexibility |
| `primary_destination_country` | VARCHAR(100) | NULLABLE | Main destination country |
| `primary_destination_city` | VARCHAR(100) | NULLABLE | Main destination city |
| `primary_destination_coordinates` | POINT | NULLABLE | Primary destination coordinates (lat, lng) |
| `countries_visited` | TEXT[] | DEFAULT '{}' | Array of all countries in itinerary |
| `cities_visited` | TEXT[] | DEFAULT '{}' | Array of all cities in itinerary |
| `trip_type` | VARCHAR(20) | DEFAULT 'single_destination' | Type: 'single_destination', 'multi_city', 'multi_country', 'road_trip', 'cruise', 'round_trip' |
| `status` | trip_status | DEFAULT 'planning' | Trip status (enum) |
| `visibility` | VARCHAR(20) | DEFAULT 'private' | Visibility: 'private', 'unlisted', 'public' |
| `is_featured` | BOOLEAN | DEFAULT FALSE | Featured trip flag (for public discovery) |
| `budget_total` | NUMERIC(12, 2) | NULLABLE | Total trip budget |
| `currency` | VARCHAR(3) | DEFAULT 'USD' | Budget currency code |
| `views_count` | INTEGER | DEFAULT 0 | Number of views (public trips) |
| `clones_count` | INTEGER | DEFAULT 0 | Number of clones/forks |
| `likes_count` | INTEGER | DEFAULT 0 | Number of likes |
| `tags` | TEXT[] | DEFAULT '{}' | Array of tags for categorization |
| `notes` | TEXT | NULLABLE | General trip notes |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Trip creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |
| `deleted_at` | TIMESTAMP | NULLABLE | Soft delete timestamp |

### Enums

```sql
CREATE TYPE trip_status AS ENUM (
    'planning',      -- Trip is being planned
    'upcoming',      -- Trip is confirmed and upcoming
    'in_progress',   -- Trip is currently happening
    'completed',     -- Trip has been completed
    'cancelled'      -- Trip was cancelled
);
```

### Indexes

```sql
-- Primary lookups
CREATE INDEX idx_trips_created_by ON trips(created_by) WHERE deleted_at IS NULL;
CREATE INDEX idx_trips_status ON trips(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_trips_visibility ON trips(visibility) WHERE deleted_at IS NULL;

-- Date-based queries
CREATE INDEX idx_trips_start_date ON trips(start_date_timestamp) WHERE deleted_at IS NULL;
CREATE INDEX idx_trips_end_date ON trips(end_date_timestamp) WHERE deleted_at IS NULL;

-- Location-based search (GIN indexes for arrays)
CREATE INDEX idx_trips_countries_visited ON trips USING GIN(countries_visited);
CREATE INDEX idx_trips_cities_visited ON trips USING GIN(cities_visited);

-- Tags search
CREATE INDEX idx_trips_tags ON trips USING GIN(tags);

-- Public trip discovery
CREATE INDEX idx_trips_public_featured ON trips(is_featured, views_count)
    WHERE visibility = 'public' AND deleted_at IS NULL;

-- Soft delete
CREATE INDEX idx_trips_deleted_at ON trips(deleted_at) WHERE deleted_at IS NULL;
```

## Relationships

- **created_by**: Many-to-One with User (creator, can be NULL)
- **collaborators**: Many-to-Many with User via trip_collaborators
- **trip_days**: One-to-Many with TripDay
- **expenses**: One-to-Many with Expense
- **photos**: One-to-Many with Photo
- **notes**: One-to-Many with Note

## Business Rules

### Trip Creation
1. Trip must have a name
2. Dates are optional (support flexible planning)
3. If dates are provided, end_date must be >= start_date
4. Default status is 'planning'
5. Default visibility is 'private'

### Date Handling
1. **Exact Dates**: Set `start_date_timestamp` and `end_date_timestamp`
2. **Flexible Dates**: Use `planned_start_year`, `planned_start_month`, `planned_duration_days`
3. **Date Confirmation**: Set `dates_confirmed = TRUE` when finalized
4. Dates can be updated from trip_days (auto-calculation)

### Destinations
1. `primary_destination_*`: Main destination for display/filtering
2. `countries_visited` and `cities_visited`: Complete list (auto-calculated from trip_days)
3. `trip_type`: Automatically determined from number of destinations

### Visibility Levels
1. **private**: Only collaborators can see
2. **unlisted**: Anyone with link can see (not in public discovery)
3. **public**: Listed in public discovery, can be cloned

### Collaboration
1. Created by user becomes first owner
2. Other users can be invited as owner/editor/viewer
3. Multiple owners allowed
4. If creator deletes account:
   - Public/unlisted trips: `created_by = NULL`, trip persists
   - Private trips: Deleted if no other owners exist

### Engagement (Public Trips)
1. `views_count`: Auto-increment on each view
2. `likes_count`: Users can like/unlike
3. `clones_count`: Incremented when someone clones trip
4. `is_featured`: Manually set by admins for discovery

## API Endpoints

### Trip CRUD
- `POST /trips/` - Create new trip
- `GET /trips/` - List user's trips (with filters)
- `GET /trips/{trip_id}` - Get single trip
- `PUT /trips/{trip_id}` - Update trip
- `DELETE /trips/{trip_id}` - Delete trip (soft delete)

### Public Discovery
- `GET /trips/public` - Browse public trips
- `POST /trips/{trip_id}/like` - Like/unlike trip
- `POST /trips/{trip_id}/clone` - Clone public trip

### Trip Management
- `GET /trips/{trip_id}/summary` - Get trip statistics
- `POST /trips/{trip_id}/calculate-destinations` - Auto-calculate destinations from trip_days

## Pydantic Schemas

### TripBase
```python
class TripBase(BaseModel):
    name: str
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None

    # Exact dates (optional)
    start_date_timestamp: Optional[int] = None
    start_timezone: str = "UTC"
    end_date_timestamp: Optional[int] = None
    end_timezone: str = "UTC"

    # Flexible dates
    dates_confirmed: bool = False
    planned_start_year: Optional[int] = None
    planned_start_month: Optional[int] = None
    planned_duration_days: Optional[int] = None
    date_flexibility: Optional[str] = None
    flexible_date_notes: Optional[str] = None

    # Destinations
    primary_destination_country: Optional[str] = None
    primary_destination_city: Optional[str] = None

    # Other fields
    trip_type: str = "single_destination"
    status: str = "planning"
    visibility: str = "private"
    budget_total: Optional[Decimal] = None
    currency: str = "USD"
    tags: List[str] = []
    notes: Optional[str] = None
```

### TripCreate
```python
class TripCreate(TripBase):
    pass
```

### TripUpdate
```python
class TripUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    # ... all fields optional for partial updates
```

### TripResponse
```python
class TripResponse(TripBase):
    id: int
    created_by: Optional[int]
    countries_visited: List[str]
    cities_visited: List[str]
    views_count: int
    clones_count: int
    likes_count: int
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    # Include collaborators
    collaborators: List[TripCollaboratorResponse] = []

    class Config:
        from_attributes = True
```

## Validation Rules

### Dates
```python
@validator('end_date_timestamp')
def end_date_after_start(cls, v, values):
    if v and values.get('start_date_timestamp'):
        if v < values['start_date_timestamp']:
            raise ValueError('End date must be after start date')
    return v
```

### Planned Month
```python
@validator('planned_start_month')
def valid_month(cls, v):
    if v and (v < 1 or v > 12):
        raise ValueError('Month must be between 1 and 12')
    return v
```

### Visibility
```python
@validator('visibility')
def valid_visibility(cls, v):
    if v not in ['private', 'unlisted', 'public']:
        raise ValueError('Invalid visibility level')
    return v
```

## Security Considerations

1. **Access Control**: Check collaborator role before allowing modifications
2. **Public Trips**: Anyone can view, only collaborators can edit
3. **Private Trips**: Only collaborators can view
4. **Cloning**: Only public trips can be cloned
5. **Data Privacy**: Don't expose collaborator details in public trip listings

## Migration Notes

### Phase 1 MVP
- All core fields included
- Collaborator functionality (Phase 2)
- Public discovery and cloning (Phase 2)

### Future Enhancements
- Trip templates
- Recommended itineraries
- AI trip planning
- Weather integration
- Budget tracking integration with expenses
