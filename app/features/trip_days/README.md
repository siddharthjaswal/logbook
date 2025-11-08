# Trip Days Feature

## Overview
The Trip Days feature handles day-by-day itinerary planning for trips. Each day includes location details, activities, accommodations, transit information, and categorization by day type. This is where the detailed planning happens - what you'll do each day, where you'll stay, and how you'll get there.

## Current Implementation Status

### ✅ Completed
- [x] TripDay model with SQLAlchemy ORM
- [x] Database migration applied
- [x] Table created in PostgreSQL
- [x] Relationships with Trip
- [x] JSONB fields for flexible data (activities, bookings, transit_details)
- [x] Enums for day_type and transit_mode

### ⏳ In Progress / Not Started
- [ ] Pydantic schemas (TripDayCreate, TripDayUpdate, TripDayResponse)
- [ ] CRUD operations
- [ ] API router (`/trips/{trip_id}/days` endpoints)
- [ ] Activity templates and suggestions
- [ ] Weather API integration
- [ ] Tests (pytest + Bruno)

---

## Database Schema

### Table: `trip_days`

**Purpose**: Store detailed day-by-day itinerary for each trip, including location, activities, accommodations, and transit.

#### Primary Key
- `id` (BIGINT, auto-increment) - Unique day identifier

#### Trip Relationship

| Field | Type | Constraints | Purpose |
|-------|------|-------------|---------|
| `trip_id` | BIGINT | FOREIGN KEY (trips.id), NOT NULL, INDEXED | Parent trip - CASCADE delete |

**CASCADE Delete Behavior**:
- When trip is deleted → All its trip_days are deleted
- Makes sense: days don't exist without a trip
- No orphaned trip days in database

#### Day Information

| Field | Type | Nullable | Indexed | Purpose |
|-------|------|----------|---------|---------|
| `date` | DATE | NOT NULL | ✅ | The calendar date for this day |
| `day_number` | INTEGER | NOT NULL | - | Sequential day number (1, 2, 3, etc.) |
| `day_type` | ENUM (trip_day_type) | NOT NULL (default: MIXED) | ✅ | Category/theme of the day |
| `title` | VARCHAR(200) | YES | - | Optional day title (e.g., "Exploring Old Town") |

**Date vs Day Number**:
- **date**: Actual calendar date (2025-07-15)
- **day_number**: Relative to trip (Day 1, Day 2, etc.)
- Why both? Day number useful for "Day 3: Visit Louvre" regardless of actual date

**Day Type Enum** (12 types from app/shared/enums.py):
- `TRANSIT`: Travel day (flights, trains, long drives)
- `SIGHTSEEING`: Tourist attractions, landmarks
- `LEISURE`: Relaxation, beach, pool
- `ACTIVITY`: Specific activities (skiing, diving, hiking)
- `CULTURAL`: Museums, theaters, local events
- `ADVENTURE`: Outdoor adventures (rafting, trekking)
- `CULINARY`: Food tours, cooking classes, restaurant hopping
- `SHOPPING`: Shopping districts, markets
- `BUSINESS`: Business meetings, conferences
- `EXPLORATION`: Wandering, discovering neighborhoods
- `REST`: Rest day, recovery
- `MIXED`: Combination of multiple types (default)

**Use Cases**:
- Filter trips: "Show me trips with adventure days"
- UI customization: Different icons/colors for each type
- Statistics: "This trip has 3 cultural days, 2 adventure days"

**Unique Constraint**: `(trip_id, date)` - One entry per trip per date
```sql
CONSTRAINT uq_trip_date UNIQUE (trip_id, date)
```

#### Location

| Field | Type | Nullable | Indexed | Purpose |
|-------|------|----------|---------|---------|
| `place` | VARCHAR(200) | NOT NULL | - | Primary location name (e.g., "Paris", "Tokyo Shibuya") |
| `place_city` | VARCHAR(100) | YES | ✅ | City name (for aggregation, search) |
| `place_country` | VARCHAR(100) | YES | ✅ | Country name (for aggregation, search) |
| `timezone` | VARCHAR(50) | NOT NULL | - | Timezone for this location (e.g., "Europe/Paris") |

**Why separate place/city/country?**
- **place**: User-friendly display ("Shibuya District")
- **place_city**: Normalized for aggregation ("Tokyo")
- **place_country**: Normalized for aggregation ("Japan")
- Aggregation populates trip.countries_visited and trip.cities_visited

**Timezone importance**:
- Accurate time calculations for activities
- Important for international trips
- Example: Day starts in NYC (EST), ends in London (GMT)

**Future**: Add `coordinates` (PostGIS POINT) for map visualization

#### Transit (Travel TO this location)

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `transit_mode` | ENUM (transit_mode) | YES | How you're getting here (flight, train, etc.) |
| `transit_details` | JSONB | NOT NULL (default: {}) | Detailed transit information |
| `arrival_time` | BIGINT | YES | When you arrive (Unix timestamp milliseconds) |
| `departure_time` | BIGINT | YES | When you leave (Unix timestamp milliseconds) |

**Transit Mode Enum** (9 types):
- `FLIGHT`: Airplane
- `TRAIN`: Train, subway
- `BUS`: Bus, coach
- `CAR`: Rental car, personal vehicle
- `BOAT`: Boat, ship
- `FERRY`: Ferry
- `BIKE`: Bicycle
- `WALK`: Walking
- `OTHER`: Other modes

**Transit Details JSONB Structure**:
```json
{
  "flight_number": "UA123",
  "airline": "United Airlines",
  "departure_airport": "JFK",
  "arrival_airport": "NRT",
  "booking_reference": "ABC123",
  "seat": "12A",
  "terminal": "Terminal 1",
  "gate": "B22",
  "baggage_allowance": "2 bags, 23kg each",
  "notes": "Pre-booked meal: vegetarian"
}
```

**Train Example**:
```json
{
  "train_number": "Shinkansen Nozomi 1",
  "departure_station": "Tokyo Station",
  "arrival_station": "Kyoto Station",
  "car": "5",
  "seat": "12D",
  "booking_reference": "JR-456789",
  "jr_pass": true
}
```

**Why JSONB?**
- Flexible: Different transit modes need different fields
- Queryable: Can search `WHERE transit_details->>'airline' = 'United'`
- Scalable: Add new fields without schema changes

**Arrival/Departure Times**:
- Unix timestamps in milliseconds (13 digits)
- Example: 1720540800000 = July 9, 2024 10:00:00 UTC
- Combined with timezone for accurate local times

#### Accommodation

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `accommodation_name` | VARCHAR(200) | YES | Hotel/Airbnb/hostel name |
| `accommodation_address` | TEXT | YES | Full address |
| `accommodation_checkin` | BIGINT | YES | Check-in time (Unix timestamp) |
| `accommodation_checkout` | BIGINT | YES | Check-out time (Unix timestamp) |
| `accommodation_confirmation` | VARCHAR(100) | YES | Booking confirmation number |

**Use Cases**:
- Display: "Staying at Hotel XYZ"
- Itinerary PDF: Include confirmation numbers
- Map view: Show hotel location

**Example**:
```python
accommodation_name: "Park Hyatt Tokyo"
accommodation_address: "3-7-1-2 Nishi Shinjuku, Shinjuku-ku, Tokyo 163-1055, Japan"
accommodation_checkin: 1720540800000  # 3:00 PM local time
accommodation_checkout: 1720627200000  # 11:00 AM local time
accommodation_confirmation: "PH-789456123"
```

**Why nullable?**
- Not every day has accommodation (transit days, same hotel multi-day)
- Day trips don't need accommodation
- Can be added later

#### Activities

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `activities` | JSONB | [] | List of planned activities for the day |

**Activities JSONB Structure** (array of objects):
```json
[
  {
    "id": "uuid-1",
    "name": "Visit Louvre Museum",
    "type": "museum",
    "start_time": 1720544400000,
    "end_time": 1720558800000,
    "duration_minutes": 240,
    "location": {
      "name": "Louvre Museum",
      "address": "Rue de Rivoli, 75001 Paris",
      "coordinates": {"lat": 48.8606, "lng": 2.3376}
    },
    "booking": {
      "required": true,
      "status": "confirmed",
      "confirmation_number": "LV-123456",
      "price": {"amount": 17.00, "currency": "EUR"}
    },
    "notes": "Skip the line with pre-booked ticket. Must see: Mona Lisa, Venus de Milo",
    "url": "https://www.louvre.fr",
    "completed": false
  },
  {
    "id": "uuid-2",
    "name": "Dinner at Le Jules Verne",
    "type": "dining",
    "start_time": 1720638000000,
    "location": {
      "name": "Le Jules Verne",
      "address": "Eiffel Tower, 2nd floor, Paris"
    },
    "booking": {
      "required": true,
      "status": "pending",
      "reservation_name": "Smith",
      "party_size": 2
    },
    "notes": "Dress code: smart casual. Reserve for sunset"
  }
]
```

**Activity Types** (suggested categories):
- `museum`, `landmark`, `attraction`, `dining`, `shopping`, `activity`, `transportation`, `entertainment`, `nature`, `other`

**Why JSONB array?**
- Unlimited activities per day
- Each activity has rich metadata
- Can filter: "Days with dining activities"
- Can mark completed during trip

#### Bookings

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `bookings` | JSONB | [] | List of all bookings/reservations for the day |

**Bookings JSONB Structure**:
```json
[
  {
    "id": "uuid-1",
    "type": "tour",
    "name": "Full Day Mt. Fuji Tour",
    "provider": "Viator",
    "booking_reference": "VIA-789456",
    "status": "confirmed",
    "booking_date": "2024-06-15",
    "start_time": 1720497600000,
    "end_time": 1720540800000,
    "pickup_location": "Shinjuku Station West Exit",
    "dropoff_location": "Shinjuku Station",
    "price": {
      "amount": 15000,
      "currency": "JPY",
      "payment_status": "paid"
    },
    "participants": 2,
    "confirmation_email": "booking@viator.com",
    "cancellation_policy": "Free cancellation up to 24 hours before",
    "notes": "Bring jacket, weather can be cold at summit"
  },
  {
    "id": "uuid-2",
    "type": "restaurant",
    "name": "Sukiyabashi Jiro",
    "booking_reference": "JIRO-2024-07-10-001",
    "status": "confirmed",
    "time": 1720641600000,
    "party_size": 2,
    "price": {
      "amount": 40000,
      "currency": "JPY",
      "per_person": true
    },
    "notes": "Omakase only, no menu. Cash only!"
  }
]
```

**Booking Types**:
- `tour`, `activity`, `restaurant`, `show`, `transportation`, `accommodation`, `rental`, `other`

**Booking Status**:
- `pending`, `confirmed`, `cancelled`, `completed`

**Difference from Activities**:
- **Activities**: What you'll do (may or may not need booking)
- **Bookings**: Confirmed reservations with confirmation numbers
- Some overlap (tour is both activity and booking)

#### Weather

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `weather_forecast` | JSONB | YES | Weather forecast data |

**Weather JSONB Structure**:
```json
{
  "fetched_at": "2024-06-15T10:30:00Z",
  "source": "OpenWeatherMap",
  "temperature": {
    "min": 18,
    "max": 26,
    "unit": "celsius"
  },
  "conditions": "Partly cloudy",
  "precipitation": {
    "probability": 20,
    "amount": 0
  },
  "humidity": 65,
  "wind": {
    "speed": 12,
    "unit": "km/h"
  },
  "uv_index": 6,
  "sunrise": "06:24",
  "sunset": "20:15",
  "alerts": []
}
```

**Use Cases**:
- Packing suggestions: "Bring umbrella for Day 3"
- Activity planning: "Rainy day - indoor museum instead of hiking"
- Wardrobe planning: "Cold nights, bring jacket"

**Future**: Integrate with weather API to auto-fetch forecasts

#### Notes

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `notes` | TEXT | YES | Free-form notes for the day |

**Examples**:
- "Early start needed, 5am wake up for sunrise"
- "Laundry day - hotel has laundry service"
- "Rest day, no rush, sleep in"

#### Timestamps

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `created_at` | TIMESTAMP | now() | When day was created |
| `updated_at` | TIMESTAMP | now() (auto-update) | Last modification |

---

## Relationships

### Trip (Many-to-One)
```python
trip = relationship("Trip", back_populates="trip_days")
```

**Meaning**:
- Each trip_day belongs to exactly one trip
- One trip can have many trip_days
- Foreign key: `trip_id → trips.id`

**Cascade Behavior**:
- Trip deleted → All trip_days deleted (CASCADE)
- Cannot orphan trip days

---

## Indexes

### 1. Primary Key Index
```sql
CREATE INDEX ix_trip_days_id ON trip_days(id);
```
**Purpose**: Fast lookups by trip_day ID

### 2. Trip ID Index
```sql
CREATE INDEX ix_trip_days_trip_id ON trip_days(trip_id);
```
**Purpose**:
- Query: "Get all days for trip X"
- Most common query for trip_days
- Always used when displaying trip itinerary

### 3. Date Index
```sql
CREATE INDEX ix_trip_days_date ON trip_days(date);
```
**Purpose**:
- Query: "What am I doing on July 15?"
- Sort days chronologically
- Date range queries

### 4. Day Type Index
```sql
CREATE INDEX ix_trip_days_day_type ON trip_days(day_type);
```
**Purpose**:
- Query: "Show me all transit days"
- Filter: "Days with cultural activities"
- Statistics: "This trip has 5 sightseeing days"

### 5. Place City Index
```sql
CREATE INDEX ix_trip_days_place_city ON trip_days(place_city);
```
**Purpose**:
- Aggregation: Auto-update trip.cities_visited
- Query: "How many days in Tokyo?"
- Search: "Trips with days in Paris"

### 6. Place Country Index
```sql
CREATE INDEX ix_trip_days_place_country ON trip_days(place_country);
```
**Purpose**:
- Aggregation: Auto-update trip.countries_visited
- Query: "How many days in Japan?"
- Statistics: "5 days in France, 3 days in Italy"

---

## Business Rules

### 1. Trip Day Creation
- Must belong to a trip (`trip_id` required)
- Date and place are required
- Day number should be sequential (auto-calculated from date)
- Default day_type is MIXED

### 2. Date Uniqueness
- One trip can only have ONE entry per date
- Constraint: `UNIQUE (trip_id, date)`
- Prevents duplicate days in itinerary

### 3. Day Number Calculation
- Auto-calculated based on date relative to trip start
- Day 1 = trip.start_date_timestamp
- Day 2 = start_date + 1 day
- Can be manual if trip has flexible dates

### 4. Location Aggregation
- When trip_days are added/updated → update trip.countries_visited and trip.cities_visited
- Runs via trigger or background job
- Keeps trip-level location data in sync

### 5. Transit Logic
- Transit represents travel TO this location
- Day 1 usually has no transit (already at starting point)
- Day 2 transit = how you get from Day 1 to Day 2

### 6. JSONB Validation
- Activities: Must be array of objects with required fields (name, type)
- Bookings: Must be array of objects with booking_reference
- Transit details: Flexible structure, no strict validation
- Weather: Optional, auto-populated by system

### 7. Time Consistency
- All timestamps must match the day's timezone
- arrival_time/departure_time should be within the date bounds
- Activity times should be chronological

---

## API Endpoints (Planned)

### Trip Day CRUD
- `GET /trips/{trip_id}/days` - Get all days for a trip (sorted by date)
- `GET /trips/{trip_id}/days/{day_id}` - Get specific day
- `POST /trips/{trip_id}/days` - Add new day to trip
- `PUT /trips/{trip_id}/days/{day_id}` - Update day
- `DELETE /trips/{trip_id}/days/{day_id}` - Delete day
- `PATCH /trips/{trip_id}/days/{day_id}/day-type` - Update day type

### Bulk Operations
- `POST /trips/{trip_id}/days/bulk` - Add multiple days at once
- `PUT /trips/{trip_id}/days/reorder` - Reorder days (update day_number)

### Activities
- `POST /trips/{trip_id}/days/{day_id}/activities` - Add activity
- `PUT /trips/{trip_id}/days/{day_id}/activities/{activity_id}` - Update activity
- `DELETE /trips/{trip_id}/days/{day_id}/activities/{activity_id}` - Remove activity
- `PATCH /trips/{trip_id}/days/{day_id}/activities/{activity_id}/complete` - Mark completed

### Bookings
- `POST /trips/{trip_id}/days/{day_id}/bookings` - Add booking
- `PUT /trips/{trip_id}/days/{day_id}/bookings/{booking_id}` - Update booking
- `DELETE /trips/{trip_id}/days/{day_id}/bookings/{booking_id}` - Remove booking

### Weather
- `POST /trips/{trip_id}/days/{day_id}/weather/refresh` - Fetch latest weather forecast

---

## Pydantic Schemas (To Be Created)

### TripDayBase
```python
from datetime import date as DateType
from typing import List, Optional, Dict, Any

class TripDayBase(BaseModel):
    date: DateType
    day_number: int = Field(..., ge=1)
    day_type: TripDayType = TripDayType.MIXED
    title: Optional[str] = Field(None, max_length=200)

    # Location
    place: str = Field(..., max_length=200)
    place_city: Optional[str] = Field(None, max_length=100)
    place_country: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)

    # Transit
    transit_mode: Optional[TransitMode] = None
    transit_details: Dict[str, Any] = {}
    arrival_time: Optional[int] = None
    departure_time: Optional[int] = None

    # Accommodation
    accommodation_name: Optional[str] = Field(None, max_length=200)
    accommodation_address: Optional[str] = None
    accommodation_checkin: Optional[int] = None
    accommodation_checkout: Optional[int] = None
    accommodation_confirmation: Optional[str] = Field(None, max_length=100)

    # Planning
    activities: List[Dict[str, Any]] = []
    bookings: List[Dict[str, Any]] = []
    notes: Optional[str] = None
```

### TripDayCreate
```python
class TripDayCreate(TripDayBase):
    """Create new trip day."""
    pass
```

### TripDayUpdate
```python
class TripDayUpdate(BaseModel):
    """Update trip day - all fields optional."""
    date: Optional[DateType] = None
    day_number: Optional[int] = Field(None, ge=1)
    day_type: Optional[TripDayType] = None
    title: Optional[str] = Field(None, max_length=200)
    place: Optional[str] = Field(None, max_length=200)
    # ... all other fields optional
```

### TripDayResponse
```python
class TripDayResponse(TripDayBase):
    id: int
    trip_id: int
    weather_forecast: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### ActivitySchema
```python
class ActivitySchema(BaseModel):
    """Schema for activity within a trip day."""
    id: Optional[str] = None  # UUID
    name: str
    type: str  # activity, dining, museum, etc.
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    duration_minutes: Optional[int] = None
    location: Optional[Dict[str, Any]] = None
    booking: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    completed: bool = False
```

### BookingSchema
```python
class BookingSchema(BaseModel):
    """Schema for booking within a trip day."""
    id: Optional[str] = None  # UUID
    type: str  # tour, restaurant, show, etc.
    name: str
    provider: Optional[str] = None
    booking_reference: str
    status: str  # pending, confirmed, cancelled
    start_time: Optional[int] = None
    price: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
```

---

## CRUD Operations (To Be Created)

### get_trip_day_by_id
```python
def get_trip_day_by_id(db: Session, day_id: int) -> Optional[TripDay]:
    """Get trip day by ID."""
    return db.query(TripDay).filter(TripDay.id == day_id).first()
```

### get_trip_days_for_trip
```python
def get_trip_days_for_trip(
    db: Session,
    trip_id: int,
    order_by: str = "date"
) -> List[TripDay]:
    """Get all days for a trip, sorted by date."""
    query = db.query(TripDay).filter(TripDay.trip_id == trip_id)

    if order_by == "date":
        query = query.order_by(TripDay.date.asc())
    elif order_by == "day_number":
        query = query.order_by(TripDay.day_number.asc())

    return query.all()
```

### get_trip_day_by_date
```python
def get_trip_day_by_date(db: Session, trip_id: int, date: date) -> Optional[TripDay]:
    """Get trip day by trip and date."""
    return db.query(TripDay).filter(
        TripDay.trip_id == trip_id,
        TripDay.date == date
    ).first()
```

### create_trip_day
```python
def create_trip_day(db: Session, trip_id: int, day_in: TripDayCreate) -> TripDay:
    """Create new trip day."""
    day_data = day_in.dict()
    trip_day = TripDay(**day_data, trip_id=trip_id)
    db.add(trip_day)
    db.commit()
    db.refresh(trip_day)

    # Trigger location aggregation update
    update_trip_destinations(db, trip_id)

    return trip_day
```

### update_trip_day
```python
def update_trip_day(db: Session, trip_day: TripDay, day_in: TripDayUpdate) -> TripDay:
    """Update trip day."""
    update_data = day_in.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(trip_day, field, value)

    db.commit()
    db.refresh(trip_day)

    # If location changed, update trip destinations
    if 'place_city' in update_data or 'place_country' in update_data:
        update_trip_destinations(db, trip_day.trip_id)

    return trip_day
```

### delete_trip_day
```python
def delete_trip_day(db: Session, trip_day: TripDay) -> None:
    """Delete trip day (hard delete)."""
    trip_id = trip_day.trip_id
    db.delete(trip_day)
    db.commit()

    # Update trip destinations after deletion
    update_trip_destinations(db, trip_id)
```

### add_activity_to_day
```python
import uuid

def add_activity_to_day(
    db: Session,
    trip_day: TripDay,
    activity: ActivitySchema
) -> TripDay:
    """Add activity to trip day."""
    activity_data = activity.dict()

    # Generate UUID if not provided
    if not activity_data.get('id'):
        activity_data['id'] = str(uuid.uuid4())

    # Append to activities array
    activities = trip_day.activities.copy()
    activities.append(activity_data)
    trip_day.activities = activities

    db.commit()
    db.refresh(trip_day)
    return trip_day
```

### update_activity_in_day
```python
def update_activity_in_day(
    db: Session,
    trip_day: TripDay,
    activity_id: str,
    activity_update: ActivitySchema
) -> TripDay:
    """Update specific activity in trip day."""
    activities = trip_day.activities.copy()

    for i, act in enumerate(activities):
        if act.get('id') == activity_id:
            activities[i] = activity_update.dict()
            break

    trip_day.activities = activities
    db.commit()
    db.refresh(trip_day)
    return trip_day
```

### remove_activity_from_day
```python
def remove_activity_from_day(
    db: Session,
    trip_day: TripDay,
    activity_id: str
) -> TripDay:
    """Remove activity from trip day."""
    activities = [act for act in trip_day.activities if act.get('id') != activity_id]
    trip_day.activities = activities
    db.commit()
    db.refresh(trip_day)
    return trip_day
```

---

## Testing Strategy

### Unit Tests (pytest)
- Test trip day creation with required fields
- Test unique constraint (trip_id, date)
- Test JSONB field manipulation (activities, bookings)
- Test location aggregation (update trip destinations)
- Test day number calculation
- Test cascade delete when trip is deleted

### Integration Tests
- Test create trip day via API
- Test get all days for a trip (sorted by date)
- Test update trip day
- Test delete trip day
- Test add/update/remove activities
- Test add/update/remove bookings
- Test weather forecast refresh
- Test bulk day creation

### Bruno Collection
- `collection/trip-days/create-day.bru`
- `collection/trip-days/get-days.bru`
- `collection/trip-days/get-day.bru`
- `collection/trip-days/update-day.bru`
- `collection/trip-days/delete-day.bru`
- `collection/trip-days/add-activity.bru`
- `collection/trip-days/update-activity.bru`
- `collection/trip-days/add-booking.bru`

---

## Security Considerations

### 1. Permission Checks
- Only trip creator/collaborators can add/edit/delete days
- Public trips: days are viewable by anyone
- Private trips: days only viewable by creator/collaborators

### 2. JSONB Validation
- Validate activities and bookings structure
- Prevent malicious JSON injection
- Sanitize user input in notes field

### 3. Time Validation
- Validate timestamps are reasonable (not in distant past/future)
- Ensure arrival/departure times match the date
- Prevent negative durations

### 4. Date Validation
- Date must be within trip's start/end date range (if confirmed)
- Cannot create days for deleted trips
- Enforce unique constraint (trip_id, date)

---

## Future Enhancements

### Location Coordinates (PostGIS)
```python
from geoalchemy2 import Geometry
coordinates = Column(Geometry('POINT'), nullable=True)
# Enables: map visualization, route planning, distance calculations
```

### Activity Templates
- Pre-defined activity templates (e.g., "Visit Louvre" includes address, hours, pricing)
- Integration with attractions APIs (Google Places, Yelp)
- Auto-fill common activities

### Smart Suggestions
- "Top 10 things to do in Paris on July 15"
- Based on day_type, location, season
- User preferences and past trips

### Weather Integration
- Auto-fetch weather forecasts for upcoming days
- Alert if weather changes significantly
- Packing list suggestions based on weather

### Route Optimization
- Optimize daily activity order based on location
- Minimize travel time between activities
- "Best route to visit all activities today"

### Budget Tracking
- Track spending per day
- Compare budget vs actual
- Expense categorization

### Photo Attachments
- Attach photos to days/activities
- Create visual timeline
- Auto-organize by date taken

### Collaborative Editing
- Real-time updates when collaborators edit
- Activity assignments: "Who's booking this?"
- Comments and suggestions

### Export Formats
- Export day itinerary as PDF
- Export to Google Calendar
- Export to Apple Maps/Google Maps route

---

## Related Documentation

- [Trip Model Documentation](../trips/README.md)
- [User Model Documentation](../users/README.md)
- [Entity Documentation](../../../docs/entities/TRIP_DAY.md)
- [System Design](../../../SYSTEM_DESIGN.md)
