# Transits Feature

The Transits feature manages transportation and movement during trip days. Unlike the previous single-transit JSON design, this feature supports **multiple transits per day**, enabling realistic multi-leg journeys with comprehensive timezone tracking for international travel.

## Overview

- **Model**: `Transit` - Stores transit details with timezone support
- **Router**: `/api/v1/transits` - RESTful API endpoints
- **Features**:
  - Multiple transits per trip day
  - **Timezone tracking**: Separate departure and arrival timezones
  - Nine transit modes: flight, train, bus, car, boat, ferry, bike, walk, other
  - Complete booking details (confirmation, ticket, seat, gate, terminal)
  - Route tracking with GPS coordinates
  - Cost tracking and aggregation
  - Custom ordering with `display_order`

## Transit Modes

The `TransitMode` enum supports all common transportation types:

| Mode | Use Cases | Example |
|------|-----------|---------|
| `FLIGHT` | Commercial flights, private planes | United UA838, ANA NH21 |
| `TRAIN` | Trains, subways, light rail | Shinkansen, Amtrak, Eurostar |
| `BUS` | Buses, coaches | Airport shuttle, intercity bus |
| `CAR` | Cars, taxis, rideshare | Uber, Lyft, rental car, taxi |
| `BOAT` | Boats, ships, cruises | Ferry, water taxi, yacht |
| `FERRY` | Scheduled ferry services | Staten Island Ferry |
| `BIKE` | Bicycles, e-bikes | Bike rental, personal bike |
| `WALK` | Walking, hiking | Hotel to restaurant |
| `OTHER` | Other transportation | Helicopter, tram, cable car |

## Database Schema

### Transit Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `trip_day_id` | Integer | Foreign key to trip_days (CASCADE delete) |
| `transit_mode` | TransitMode | Type of transportation (required) |
| `carrier` | String(200) | Airline, train company, bus line, etc. |
| `flight_number` | String(50) | Flight/train/bus number |
| `from_location` | String(200) | Departure location name |
| `to_location` | String(200) | Arrival location name |
| `from_latitude` | Decimal(10,8) | Departure GPS latitude |
| `from_longitude` | Decimal(11,8) | Departure GPS longitude |
| `to_latitude` | Decimal(10,8) | Arrival GPS latitude |
| `to_longitude` | Decimal(11,8) | Arrival GPS longitude |
| `departure_time` | Integer | Unix timestamp for departure |
| `arrival_time` | Integer | Unix timestamp for arrival |
| **`departure_timezone`** | **String(50)** | **IANA timezone at departure** |
| **`arrival_timezone`** | **String(50)** | **IANA timezone at arrival** |
| `duration_minutes` | Integer | Transit duration in minutes |
| `confirmation_number` | String(100) | Booking confirmation (indexed) |
| `ticket_number` | String(100) | E-ticket or ticket number |
| `seat` | String(50) | Seat assignment |
| `gate` | String(20) | Departure gate |
| `terminal` | String(50) | Airport/station terminal |
| `booking_class` | String(50) | Economy, Business, First, etc. |
| `cost` | Decimal(10,2) | Transit cost |
| `currency` | String(3) | ISO currency code (default: USD) |
| `notes` | Text | Additional notes |
| `display_order` | Integer | Custom ordering (default: 0) |
| `created_at` | Timestamp | Creation timestamp |
| `updated_at` | Timestamp | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key on `trip_day_id`
- Index on `transit_mode`
- Index on `confirmation_number`

**Relationships:**
- `trip_day`: Many-to-one relationship with TripDay (CASCADE delete)

## Timezone Handling

### Why Separate Timezones?

International travel often crosses timezone boundaries. Separate `departure_timezone` and `arrival_timezone` fields enable:

1. **Accurate local time display**: Show departure in departure timezone, arrival in arrival timezone
2. **Proper duration calculations**: Account for timezone changes
3. **Calendar integration**: Schedule correctly in different timezones
4. **User experience**: Display times as travelers would see them

### IANA Timezone Format

Use standard IANA timezone names:
- ✅ `"America/Los_Angeles"` (not "PST" or "PDT")
- ✅ `"Asia/Tokyo"` (not "JST")
- ✅ `"Europe/Paris"` (not "CET")

### Example: International Flight

```json
{
  "from_location": "San Francisco (SFO)",
  "to_location": "Tokyo Narita (NRT)",
  "departure_time": 1704067200,
  "arrival_time": 1704110400,
  "departure_timezone": "America/Los_Angeles",
  "arrival_timezone": "Asia/Tokyo"
}
```

Client apps can convert Unix timestamps using timezone info:
- Departure: Show 1704067200 as local time in America/Los_Angeles
- Arrival: Show 1704110400 as local time in Asia/Tokyo

## API Endpoints

### 1. Create Transit
**POST** `/api/v1/transits`

Creates a new transit for a trip day.

**Request Body (International Flight Example):**
```json
{
  "trip_day_id": 1,
  "transit_mode": "flight",
  "carrier": "United Airlines",
  "flight_number": "UA838",
  "from_location": "San Francisco International Airport (SFO)",
  "to_location": "Tokyo Narita Airport (NRT)",
  "from_latitude": 37.6213,
  "from_longitude": -122.3790,
  "to_latitude": 35.7720,
  "to_longitude": 140.3929,
  "departure_time": 1704067200,
  "arrival_time": 1704110400,
  "departure_timezone": "America/Los_Angeles",
  "arrival_timezone": "Asia/Tokyo",
  "duration_minutes": 660,
  "confirmation_number": "UA456ABC",
  "ticket_number": "UA016-9876543210",
  "seat": "32K",
  "gate": "G92",
  "terminal": "Terminal 3",
  "booking_class": "Economy",
  "cost": 850.00,
  "currency": "USD",
  "notes": "International flight crosses date line."
}
```

**Response:** `201 Created` - Full transit details with ID

### 2. List Transits by Trip Day
**GET** `/api/v1/transits/trip-day/{trip_day_id}`

Retrieves all transits for a specific trip day.

**Query Parameters:**
- `skip` (integer): Records to skip for pagination (default: 0)
- `limit` (integer): Max records to return, 1-100 (default: 100)
- `transit_mode` (optional): Filter by mode (flight, train, bus, etc.)

**Example:** `GET /api/v1/transits/trip-day/5?transit_mode=train`

**Response:** `200 OK`
```json
[
  {
    "id": 2,
    "trip_day_id": 5,
    "transit_mode": "train",
    "carrier": "JR Central",
    "flight_number": "Nozomi 225",
    "from_location": "Tokyo Station",
    "to_location": "Kyoto Station",
    "departure_time": 1704441600,
    "arrival_time": 1704450000,
    "departure_timezone": "Asia/Tokyo",
    "arrival_timezone": "Asia/Tokyo",
    "duration_minutes": 140,
    "display_order": 1
  }
]
```

### 3. Get Transit by ID
**GET** `/api/v1/transits/{transit_id}`

Retrieves a specific transit.

**Response:** `200 OK` - Full transit details

### 4. Get Transit by Confirmation Number
**GET** `/api/v1/transits/confirmation/{confirmation_number}`

Look up transit using booking confirmation.

**Example:** `GET /api/v1/transits/confirmation/ANA123XYZ`

**Response:** `200 OK` - Full transit details

### 5. Update Transit
**PUT** `/api/v1/transits/{transit_id}`

Updates a transit. All fields are optional.

**Request Body (Gate Change Example):**
```json
{
  "seat": "14B",
  "gate": "G15",
  "booking_class": "Premium Economy",
  "cost": 250.00,
  "notes": "Upgraded to premium economy. Gate changed from G12 to G15."
}
```

**Response:** `200 OK` - Updated transit

### 6. Delete Transit
**DELETE** `/api/v1/transits/{transit_id}`

Permanently deletes a transit.

**Response:** `204 No Content`

### 7. Reorder Transits
**POST** `/api/v1/transits/trip-day/{trip_day_id}/reorder`

Reorder transits by providing IDs in desired sequence.

**Request Body:**
```json
[4, 2, 3]
```

**Response:** `200 OK` - Array of transits with updated display_order

### 8. Get Transits Cost
**GET** `/api/v1/transits/trip-day/{trip_day_id}/cost`

Calculate total transit cost for a trip day.

**Query Parameters:**
- `currency` (string): Currency code to filter by (default: USD)

**Example:** `GET /api/v1/transits/trip-day/5/cost?currency=USD`

**Response:** `200 OK`
```json
{
  "trip_day_id": 5,
  "currency": "USD",
  "total_cost": 390.00
}
```

## Usage Examples

### Example 1: International Flight
```json
POST /api/v1/transits
{
  "trip_day_id": 1,
  "transit_mode": "flight",
  "carrier": "United Airlines",
  "flight_number": "UA838",
  "from_location": "San Francisco (SFO)",
  "to_location": "Tokyo Narita (NRT)",
  "departure_time": 1704067200,
  "arrival_time": 1704110400,
  "departure_timezone": "America/Los_Angeles",
  "arrival_timezone": "Asia/Tokyo",
  "duration_minutes": 660,
  "confirmation_number": "UA456ABC",
  "seat": "32K",
  "cost": 850.00,
  "currency": "USD"
}
```

### Example 2: Multi-Leg Journey (Same Day)
```json
// 1. Taxi from hotel to station
POST /api/v1/transits
{
  "trip_day_id": 5,
  "transit_mode": "car",
  "carrier": "Tokyo Taxi",
  "from_location": "Park Hyatt Tokyo",
  "to_location": "Tokyo Station",
  "departure_time": 1704438000,
  "arrival_time": 1704440400,
  "departure_timezone": "Asia/Tokyo",
  "arrival_timezone": "Asia/Tokyo",
  "cost": 30.00,
  "display_order": 0
}

// 2. Shinkansen to Kyoto
POST /api/v1/transits
{
  "trip_day_id": 5,
  "transit_mode": "train",
  "carrier": "JR Central",
  "flight_number": "Nozomi 225",
  "from_location": "Tokyo Station",
  "to_location": "Kyoto Station",
  "departure_time": 1704441600,
  "arrival_time": 1704450000,
  "departure_timezone": "Asia/Tokyo",
  "arrival_timezone": "Asia/Tokyo",
  "duration_minutes": 140,
  "seat": "Car 7, Seat 11D",
  "cost": 140.00,
  "display_order": 1
}

// 3. Walk to hotel
POST /api/v1/transits
{
  "trip_day_id": 5,
  "transit_mode": "walk",
  "from_location": "Kyoto Station",
  "to_location": "Ritz-Carlton Kyoto",
  "departure_time": 1704450600,
  "arrival_time": 1704451800,
  "departure_timezone": "Asia/Tokyo",
  "arrival_timezone": "Asia/Tokyo",
  "duration_minutes": 20,
  "display_order": 2
}
```

### Example 3: Train Journey
```json
POST /api/v1/transits
{
  "trip_day_id": 3,
  "transit_mode": "train",
  "carrier": "Amtrak",
  "flight_number": "Acela 2150",
  "from_location": "New York Penn Station",
  "to_location": "Washington Union Station",
  "departure_time": 1704297600,
  "arrival_time": 1704308400,
  "departure_timezone": "America/New_York",
  "arrival_timezone": "America/New_York",
  "duration_minutes": 180,
  "seat": "Car 3, Seat 12A",
  "booking_class": "Business Class",
  "cost": 220.00,
  "currency": "USD"
}
```

### Example 4: Simple Taxi Ride
```json
POST /api/v1/transits
{
  "trip_day_id": 1,
  "transit_mode": "car",
  "carrier": "Uber",
  "from_location": "Tokyo Narita Airport",
  "to_location": "Park Hyatt Tokyo",
  "departure_time": 1704121200,
  "arrival_time": 1704126600,
  "departure_timezone": "Asia/Tokyo",
  "arrival_timezone": "Asia/Tokyo",
  "cost": 250.00,
  "currency": "USD"
}
```

## Common Workflows

### Workflow 1: Multi-Leg Journey Planning
1. Create each transit segment separately
2. Set `display_order` to control sequence (0, 1, 2, ...)
3. Use consistent trip_day_id for same-day transits
4. Include timezones for each segment

### Workflow 2: International Flight Booking
1. Set `transit_mode` to "flight"
2. Include carrier and flight_number
3. **Critical**: Set both `departure_timezone` and `arrival_timezone`
4. Store confirmation_number for check-in
5. Add seat, gate, terminal when available

### Workflow 3: Cost Tracking
```bash
# Get total transit cost for specific day
GET /api/v1/transits/trip-day/5/cost?currency=USD

# Calculate multi-leg journey cost
# Response: { "total_cost": 390.00 }
# = Taxi (30) + Shinkansen (140) + Walk (0) + other segments
```

### Workflow 4: Confirmation Lookup
```bash
# Quick flight lookup from booking email
GET /api/v1/transits/confirmation/UA456ABC

# Returns full transit details including departure/arrival times
```

### Workflow 5: Transit Updates
```bash
# Update seat assignment after online check-in
PUT /api/v1/transits/1
{
  "seat": "15F",
  "gate": "B23"
}

# Update due to delay
PUT /api/v1/transits/1
{
  "departure_time": 1704070800,  # New time
  "notes": "Flight delayed 1 hour due to weather"
}
```

## Best Practices

### 1. Transit Modes
- **FLIGHT**: Use for all air travel (commercial, charter, private)
- **TRAIN**: Includes subways, light rail, high-speed rail
- **CAR**: Use for taxis, Uber, Lyft, rental cars, personal cars
- **WALK**: Don't forget short walks between locations!
- Choose most specific mode available

### 2. Timezone Handling
- **Always include timezones** for accurate time display
- Use IANA timezone names (e.g., "America/Los_Angeles")
- Set departure_timezone = arrival_timezone for domestic travel
- For international: Different timezones reflect reality
- Store times as Unix timestamps (UTC internally)

### 3. Multi-Leg Journeys
- Create separate transit for each segment
- Use `display_order` for custom sequencing
- Order typically matches chronological order
- All segments on same `trip_day_id`

### 4. Booking Details
- Always store `confirmation_number` if available
- Add `ticket_number` for e-tickets
- Update `seat`, `gate`, `terminal` as info becomes available
- Use `booking_class` for upgrades/downgrades

### 5. GPS Coordinates
- Store coordinates for both departure and arrival
- Enables mapping, distance calculations, route visualization
- Latitude: -90 to 90, Longitude: -180 to 180
- Not required but highly recommended

### 6. Cost Tracking
- Store in original booking currency
- Use standard ISO 4217 codes (USD, JPY, EUR, etc.)
- Cost aggregation filters by currency
- For multi-currency, query each separately

### 7. Display Order
- Set explicitly for multi-transit days
- Lower numbers appear first (0, 1, 2, ...)
- Default is 0
- Can reorder later with reorder endpoint

### 8. Flight-Specific Fields
- `carrier`: Airline name (United Airlines, ANA, etc.)
- `flight_number`: Flight code (UA838, NH21)
- `seat`: Seat assignment with row and letter
- `gate`: Departure gate
- `terminal`: Airport terminal
- `booking_class`: Economy, Premium Economy, Business, First

### 9. Train-Specific Fields
- `carrier`: Railway company (JR Central, Amtrak, Eurostar)
- `flight_number`: Can be used for train number/name
- `seat`: Car and seat (e.g., "Car 7, Seat 11D")
- `booking_class`: Ordinary, Green Car, First Class, etc.

## Error Handling

| Status Code | Scenario |
|-------------|----------|
| `400 Bad Request` | Invalid data (missing required fields, invalid types) |
| `401 Unauthorized` | Missing or invalid authentication token |
| `403 Forbidden` | User doesn't own the trip |
| `404 Not Found` | Trip day or transit not found |
| `422 Unprocessable Entity` | Validation errors (invalid enum, constraints) |

## Validation Rules

- `trip_day_id`: Required, must exist
- `transit_mode`: Required, must be valid TransitMode enum value
- `carrier`: 0-200 characters
- `flight_number`: 0-50 characters
- `from_location`, `to_location`: 0-200 characters
- `from_latitude`, `to_latitude`: -90 to 90
- `from_longitude`, `to_longitude`: -180 to 180
- `departure_timezone`, `arrival_timezone`: 0-50 characters (IANA format)
- `duration_minutes`: >= 0
- `currency`: 3 characters (ISO 4217)
- `cost`: >= 0
- `display_order`: >= 0

## Database Queries

The CRUD layer provides optimized queries:

```python
# Get transits ordered by display_order and departure_time
transits = get_transits_by_trip_day(db, trip_day_id=5)

# Filter by mode
flights = get_transits_by_mode(db, trip_day_id=1,
                               transit_mode=TransitMode.FLIGHT)

# Find by confirmation
transit = get_transit_by_confirmation(db, "UA456ABC")

# Calculate costs
total = get_total_cost_by_trip_day(db, trip_day_id=5, currency="USD")
```

## Integration with Other Features

- **Trip Days**: Each transit belongs to exactly one trip day
- **Accommodations**: Coordinate arrival/departure transits with CHECK_IN/CHECK_OUT
- **Activities**: Transit times affect activity scheduling
- **Cost Tracking**: Aggregates with accommodations and activities for total trip cost
- **Mapping**: GPS coordinates enable route visualization

## Migration Notes

This feature replaces the old single-transit JSON design on `trip_days`:
- ❌ Removed: `transit_mode`, `transit_details` (JSON), `arrival_time`, `departure_time`
- ✅ New: Separate `transits` table with full relationship support

Benefits:
- **Multiple transits per day** (critical for real-world travel)
- **Timezone tracking** (essential for international travel)
- Better data normalization
- Enhanced search capabilities
- Richer booking details
- Proper CASCADE deletion
- Structured data instead of JSON blob

## Real-World Scenarios

### Scenario 1: Simple Flight
```
Day 1: Fly Tokyo to Osaka
- Single FLIGHT transit
- Same timezone (Asia/Tokyo)
```

### Scenario 2: International Arrival
```
Day 1: Arrive in Tokyo from San Francisco
- FLIGHT: SFO → NRT (crosses timezones!)
- CAR: Airport → Hotel
```

### Scenario 3: Complex Multi-City Travel
```
Day 5: Tokyo to Kyoto
- CAR: Hotel → Tokyo Station
- TRAIN: Tokyo → Kyoto (Shinkansen)
- WALK: Kyoto Station → Hotel
```

### Scenario 4: Multi-Modal Journey
```
Day 3: Island Hopping
- CAR: Hotel → Ferry Terminal
- FERRY: Main Island → Small Island
- BIKE: Ferry Port → Beach
- WALK: Beach → Restaurant
```

All scenarios fully supported with proper sequencing, timing, and cost tracking!
