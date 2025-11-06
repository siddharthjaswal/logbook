# TripDay Entity

## Overview
The TripDay entity represents a single day in a trip's itinerary. Each day includes location details, activities, accommodations, transit information, and can be categorized by type (transit, sightseeing, leisure, etc.).

## Database Table: `trip_days`

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique trip day identifier |
| `trip_id` | BIGINT | FOREIGN KEY (trips.id), NOT NULL, ON DELETE CASCADE | Associated trip |
| `date` | DATE | NOT NULL | The date of this day |
| `day_number` | INTEGER | NOT NULL | Day number in trip sequence (1-indexed) |
| `day_type` | trip_day_type | DEFAULT 'mixed' | Type of day (enum) |
| `title` | VARCHAR(200) | NULLABLE | Optional title for the day |
| `place` | VARCHAR(200) | NOT NULL | Location/place name |
| `place_city` | VARCHAR(100) | NULLABLE | City name |
| `place_country` | VARCHAR(100) | NULLABLE | Country name |
| `timezone` | VARCHAR(50) | NOT NULL | Timezone for this location |
| `coordinates` | POINT | NULLABLE | Location coordinates (lat, lng) |
| `transit_mode` | transit_mode | NULLABLE | Mode of transit TO this location |
| `transit_details` | JSONB | DEFAULT '{}' | Transit booking details (flight number, train, etc.) |
| `arrival_time` | BIGINT | NULLABLE | Arrival time in Unix timestamp |
| `departure_time` | BIGINT | NULLABLE | Departure time in Unix timestamp |
| `accommodation_name` | VARCHAR(200) | NULLABLE | Hotel/accommodation name |
| `accommodation_address` | TEXT | NULLABLE | Accommodation address |
| `accommodation_checkin` | BIGINT | NULLABLE | Check-in time in Unix timestamp |
| `accommodation_checkout` | BIGINT | NULLABLE | Check-out time in Unix timestamp |
| `accommodation_confirmation` | VARCHAR(100) | NULLABLE | Booking confirmation number |
| `activities` | JSONB | DEFAULT '[]' | Planned activities for the day |
| `bookings` | JSONB | DEFAULT '[]' | Tour/activity bookings |
| `weather_forecast` | JSONB | NULLABLE | Weather data for the day |
| `notes` | TEXT | NULLABLE | Day-specific notes |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

### Enums

```sql
CREATE TYPE trip_day_type AS ENUM (
    'transit',        -- Travel day (flights, long trains, driving between cities)
    'sightseeing',    -- Visiting landmarks, attractions, guided tours
    'leisure',        -- Relaxing, unstructured time, beach day, pool day
    'activity',       -- Specific activities (hiking, diving, skiing, water sports)
    'cultural',       -- Museums, theaters, galleries, cultural experiences
    'adventure',      -- Outdoor activities, sports, adrenaline activities
    'culinary',       -- Food tours, cooking classes, restaurant hopping
    'shopping',       -- Shopping focused day, markets, boutiques
    'business',       -- Work-related (conferences, meetings, networking)
    'exploration',    -- Wandering, discovering neighborhoods, local life
    'rest',           -- Recovery day, sleep in, minimal plans
    'mixed'           -- Combination of multiple types
);

CREATE TYPE transit_mode AS ENUM (
    'flight',
    'train',
    'bus',
    'car',
    'boat',
    'ferry',
    'bike',
    'walk',
    'other'
);
```

### Constraints

```sql
-- Unique: One day per date per trip
ALTER TABLE trip_days ADD CONSTRAINT unique_trip_date UNIQUE (trip_id, date);

-- Day number must be positive
ALTER TABLE trip_days ADD CONSTRAINT positive_day_number CHECK (day_number > 0);
```

### Indexes

```sql
-- Primary lookups
CREATE INDEX idx_trip_days_trip_id ON trip_days(trip_id);
CREATE INDEX idx_trip_days_date ON trip_days(date);
CREATE INDEX idx_trip_days_day_number ON trip_days(trip_id, day_number);

-- Type filtering
CREATE INDEX idx_trip_days_type ON trip_days(day_type);

-- Location search
CREATE INDEX idx_trip_days_city_country ON trip_days(place_city, place_country);

-- JSONB indexes for activities and bookings
CREATE INDEX idx_trip_days_activities ON trip_days USING GIN(activities);
CREATE INDEX idx_trip_days_bookings ON trip_days USING GIN(bookings);
```

## Relationships

- **trip**: Many-to-One with Trip (CASCADE on delete)
- **expenses**: One-to-Many with Expense (expenses for this day)
- **photos**: One-to-Many with Photo (photos from this day)

## Business Rules

### Day Creation
1. Must belong to a trip
2. Date is required
3. Place is required (minimum: location name)
4. Timezone is required (defaults to trip timezone or UTC)
5. Day number is auto-calculated or specified

### Day Types
1. **transit**: Focus on transportation between locations
2. **sightseeing**: Visiting tourist attractions and landmarks
3. **leisure**: Relaxation and downtime
4. **activity**: Specific planned activities
5. **cultural**: Museums, theaters, cultural experiences
6. **adventure**: Outdoor and adventure sports
7. **culinary**: Food-related experiences
8. **shopping**: Shopping activities
9. **business**: Work-related activities
10. **exploration**: Unstructured discovery
11. **rest**: Recovery and rest day
12. **mixed**: Multiple activity types

### Transit Information
1. `transit_mode`: How you're traveling TO this location
2. `transit_details`: Booking details (JSONB structure)
   ```json
   {
     "flight_number": "AA1234",
     "airline": "American Airlines",
     "departure_airport": "JFK",
     "arrival_airport": "CDG",
     "booking_reference": "ABC123",
     "seat": "12A"
   }
   ```

### Accommodation
1. All accommodation fields are optional
2. Useful for multi-day stays at same location
3. Can link to expenses for accommodation costs
4. Check-in/out times in Unix timestamp

### Activities Structure
```json
[
  {
    "time": "09:00",
    "name": "Eiffel Tower Visit",
    "duration_hours": 2,
    "notes": "Book tickets online",
    "priority": "high",
    "cost": 25.00,
    "booking_url": "https://..."
  },
  {
    "time": "14:00",
    "name": "Louvre Museum",
    "duration_hours": 3,
    "notes": "Skip the line pass",
    "priority": "medium",
    "cost": 17.00
  }
]
```

### Bookings Structure
```json
[
  {
    "type": "tour",
    "name": "Paris Walking Tour",
    "confirmation": "ABC123",
    "cost": 50.00,
    "currency": "EUR",
    "time": "10:00",
    "duration_hours": 3,
    "provider": "Free Tours Paris",
    "status": "confirmed"
  }
]
```

### Weather Forecast
```json
{
  "temp_high": 75,
  "temp_low": 60,
  "condition": "partly_cloudy",
  "precipitation_chance": 20,
  "humidity": 65,
  "wind_speed": 10,
  "sunrise": "06:30",
  "sunset": "20:15"
}
```

### Timezone Handling
1. Each day has its own timezone (important for multi-timezone trips)
2. Arrival/departure times are in Unix timestamp (absolute time)
3. Display times should be converted to day's timezone
4. Example: Flight from NYC (EST) to Paris (CET) - day timezone is CET

### Auto-calculation
1. Trip's `countries_visited` and `cities_visited` are calculated from trip_days
2. Trip dates can be auto-updated from min/max trip_day dates

## API Endpoints

### TripDay CRUD
- `POST /trip_days/` - Create new trip day
- `GET /trip_days/?trip_id={id}` - List days for a trip
- `GET /trip_days/{day_id}` - Get single trip day
- `PUT /trip_days/{day_id}` - Update trip day
- `DELETE /trip_days/{day_id}` - Delete trip day

### Additional Operations
- `GET /trip_days/{day_id}/weather` - Fetch weather forecast (Phase 5)
- `POST /trip_days/{day_id}/activities` - Add activity
- `DELETE /trip_days/{day_id}/activities/{index}` - Remove activity

## Pydantic Schemas

### TripDayBase
```python
class TripDayBase(BaseModel):
    trip_id: int
    date: date
    day_number: int
    day_type: str = "mixed"
    title: Optional[str] = None

    # Location
    place: str
    place_city: Optional[str] = None
    place_country: Optional[str] = None
    timezone: str = "UTC"

    # Transit
    transit_mode: Optional[str] = None
    transit_details: Dict = {}
    arrival_time: Optional[int] = None
    departure_time: Optional[int] = None

    # Accommodation
    accommodation_name: Optional[str] = None
    accommodation_address: Optional[str] = None
    accommodation_checkin: Optional[int] = None
    accommodation_checkout: Optional[int] = None
    accommodation_confirmation: Optional[str] = None

    # Planning
    activities: List[Dict] = []
    bookings: List[Dict] = []

    # Notes
    notes: Optional[str] = None
```

### ActivitySchema
```python
class ActivitySchema(BaseModel):
    time: Optional[str] = None
    name: str
    duration_hours: Optional[float] = None
    notes: Optional[str] = None
    priority: Optional[str] = "medium"
    cost: Optional[Decimal] = None
    booking_url: Optional[str] = None
```

### BookingSchema
```python
class BookingSchema(BaseModel):
    type: str  # 'tour', 'activity', 'restaurant', 'ticket'
    name: str
    confirmation: Optional[str] = None
    cost: Optional[Decimal] = None
    currency: str = "USD"
    time: Optional[str] = None
    duration_hours: Optional[float] = None
    provider: Optional[str] = None
    status: str = "confirmed"  # 'pending', 'confirmed', 'cancelled'
```

### TripDayResponse
```python
class TripDayResponse(TripDayBase):
    id: int
    weather_forecast: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## Validation Rules

### Date Validation
```python
@validator('date')
def date_within_trip_range(cls, v, values):
    # Check that date falls within trip's start and end dates
    # (if trip dates are set)
    pass
```

### Day Number
```python
@validator('day_number')
def positive_day_number(cls, v):
    if v <= 0:
        raise ValueError('Day number must be positive')
    return v
```

### Activities Validation
```python
@validator('activities')
def validate_activities(cls, v):
    for activity in v:
        ActivitySchema(**activity)  # Validate each activity
    return v
```

## Security Considerations

1. **Access Control**: Check trip collaborator permissions
2. **Viewers**: Can only read trip days
3. **Editors**: Can create/update trip days
4. **Owners**: Full access including delete

## Use Cases

### Transit Day Example
```json
{
  "trip_id": 1,
  "date": "2024-06-01",
  "day_number": 1,
  "day_type": "transit",
  "title": "Travel to Paris",
  "place": "Charles de Gaulle Airport",
  "place_city": "Paris",
  "place_country": "France",
  "timezone": "Europe/Paris",
  "transit_mode": "flight",
  "transit_details": {
    "flight_number": "AF123",
    "airline": "Air France",
    "departure_airport": "JFK",
    "arrival_airport": "CDG"
  },
  "arrival_time": 1717225200,
  "accommodation_name": "Hotel Paris",
  "accommodation_checkin": 1717246800
}
```

### Sightseeing Day Example
```json
{
  "trip_id": 1,
  "date": "2024-06-02",
  "day_number": 2,
  "day_type": "sightseeing",
  "title": "Paris Landmarks",
  "place": "Paris City Center",
  "place_city": "Paris",
  "place_country": "France",
  "timezone": "Europe/Paris",
  "activities": [
    {
      "time": "09:00",
      "name": "Eiffel Tower",
      "duration_hours": 2,
      "cost": 25.00
    },
    {
      "time": "14:00",
      "name": "Louvre Museum",
      "duration_hours": 3,
      "cost": 17.00
    }
  ]
}
```

## Migration Notes

### Phase 1 MVP
- Core fields and CRUD operations
- Basic activity and booking support

### Phase 3 Enhancements
- Weather integration
- Advanced activity management
- Auto-calculation of trip destinations

### Future Considerations
- Real-time collaboration on day planning
- AI-suggested activities
- Integration with booking platforms
