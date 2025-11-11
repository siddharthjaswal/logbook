# Accommodations Feature

The Accommodations feature manages lodging and accommodation bookings for trip days. Unlike the previous single-accommodation design, this feature supports **multiple accommodations per day**, enabling realistic scenarios like hotel changes, early checkouts, and late check-ins.

## Overview

- **Model**: `Accommodation` - Stores accommodation details with type classification
- **Router**: `/api/v1/accommodations` - RESTful API endpoints
- **Features**:
  - Multiple accommodations per trip day
  - Three accommodation types: CHECK_IN, WHOLE_DAY, CHECK_OUT
  - Confirmation number lookup
  - Cost tracking and aggregation
  - Custom ordering with `display_order`
  - GPS coordinates for mapping
  - Comprehensive booking details

## Accommodation Types

The `AccommodationType` enum enables precise tracking of accommodation timing:

| Type | Use Case | Example |
|------|----------|---------|
| `CHECK_IN` | Arrival day with check-in | Flying into Tokyo, checking into hotel in the evening |
| `WHOLE_DAY` | Full day stay | Regular day staying at the same hotel |
| `CHECK_OUT` | Departure day with checkout | Checking out of Tokyo hotel to travel to Kyoto |

**Multi-Accommodation Day Example:**
```
Day 5: Tokyo → Kyoto
1. CHECK_OUT from Park Hyatt Tokyo (morning)
2. CHECK_IN to Ritz-Carlton Kyoto (evening)
```

## Database Schema

### Accommodation Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `trip_day_id` | Integer | Foreign key to trip_days (CASCADE delete) |
| `accommodation_type` | AccommodationType | CHECK_IN, WHOLE_DAY, or CHECK_OUT |
| `check_in_time` | Integer | Unix timestamp for check-in |
| `check_out_time` | Integer | Unix timestamp for checkout |
| `name` | String(200) | Hotel/accommodation name (required) |
| `address` | Text | Full address |
| `latitude` | Decimal(10,8) | GPS latitude |
| `longitude` | Decimal(11,8) | GPS longitude |
| `confirmation_number` | String(100) | Booking confirmation (indexed) |
| `booking_url` | Text | Link to booking details |
| `cost` | Decimal(10,2) | Accommodation cost |
| `currency` | String(3) | ISO currency code (default: USD) |
| `contact_phone` | String(50) | Hotel phone number |
| `contact_email` | String(255) | Hotel email |
| `room_type` | String(100) | Room category/type |
| `notes` | Text | Additional notes |
| `display_order` | Integer | Custom ordering (default: 0) |
| `created_at` | Timestamp | Creation timestamp |
| `updated_at` | Timestamp | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key on `trip_day_id`
- Index on `accommodation_type`
- Index on `confirmation_number`

**Relationships:**
- `trip_day`: Many-to-one relationship with TripDay (CASCADE delete)

## API Endpoints

### 1. Create Accommodation
**POST** `/api/v1/accommodations`

Creates a new accommodation for a trip day.

**Request Body:**
```json
{
  "trip_day_id": 1,
  "accommodation_type": "whole_day",
  "check_in_time": 1704096000,
  "check_out_time": null,
  "name": "Park Hyatt Tokyo",
  "address": "3-7-1-2 Nishi Shinjuku, Shinjuku-ku, Tokyo 163-1055, Japan",
  "latitude": 35.6852,
  "longitude": 139.6917,
  "confirmation_number": "HYATT123456",
  "booking_url": "https://www.hyatt.com/...",
  "cost": 450.00,
  "currency": "USD",
  "contact_phone": "+81-3-5322-1234",
  "contact_email": "tokyo.park@hyatt.com",
  "room_type": "Deluxe King Room",
  "notes": "Request high floor with city view",
  "display_order": 0
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "trip_day_id": 1,
  "accommodation_type": "whole_day",
  "name": "Park Hyatt Tokyo",
  "cost": 450.00,
  "currency": "USD",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### 2. List Accommodations by Trip Day
**GET** `/api/v1/accommodations/trip-day/{trip_day_id}`

Retrieves all accommodations for a specific trip day.

**Query Parameters:**
- `skip` (integer): Records to skip for pagination (default: 0)
- `limit` (integer): Max records to return, 1-100 (default: 100)
- `accommodation_type` (optional): Filter by type (check_in, whole_day, check_out)

**Example:** `GET /api/v1/accommodations/trip-day/5?accommodation_type=check_in`

**Response:** `200 OK`
```json
[
  {
    "id": 3,
    "trip_day_id": 5,
    "accommodation_type": "check_in",
    "check_in_time": 1704470400,
    "name": "Ritz-Carlton Kyoto",
    "cost": 650.00,
    "display_order": 1
  }
]
```

### 3. Get Accommodation by ID
**GET** `/api/v1/accommodations/{accommodation_id}`

Retrieves a specific accommodation.

**Response:** `200 OK` - Full accommodation details

### 4. Get Accommodation by Confirmation Number
**GET** `/api/v1/accommodations/confirmation/{confirmation_number}`

Look up accommodation using booking confirmation.

**Example:** `GET /api/v1/accommodations/confirmation/HYATT123456`

**Response:** `200 OK` - Full accommodation details

### 5. Update Accommodation
**PUT** `/api/v1/accommodations/{accommodation_id}`

Updates an accommodation. All fields are optional.

**Request Body:**
```json
{
  "room_type": "Park Suite",
  "cost": 850.00,
  "notes": "Upgraded to suite. Late checkout confirmed at 2pm."
}
```

**Response:** `200 OK` - Updated accommodation

### 6. Delete Accommodation
**DELETE** `/api/v1/accommodations/{accommodation_id}`

Permanently deletes an accommodation.

**Response:** `204 No Content`

### 7. Reorder Accommodations
**POST** `/api/v1/accommodations/trip-day/{trip_day_id}/reorder`

Reorder accommodations by providing IDs in desired sequence.

**Request Body:**
```json
[1, 3, 2]
```

**Response:** `200 OK` - Array of accommodations with updated display_order

### 8. Get Accommodations Cost
**GET** `/api/v1/accommodations/trip-day/{trip_day_id}/cost`

Calculate total accommodation cost for a trip day.

**Query Parameters:**
- `currency` (string): Currency code to filter by (default: USD)

**Example:** `GET /api/v1/accommodations/trip-day/1/cost?currency=USD`

**Response:** `200 OK`
```json
{
  "trip_day_id": 1,
  "currency": "USD",
  "total_cost": 450.00
}
```

## Usage Examples

### Example 1: Simple Single-Day Stay
```json
POST /api/v1/accommodations
{
  "trip_day_id": 2,
  "accommodation_type": "whole_day",
  "name": "Park Hyatt Tokyo",
  "cost": 450.00,
  "currency": "USD"
}
```

### Example 2: Multi-Accommodation Day (Hotel Change)
```json
// Morning: Check out from Tokyo hotel
POST /api/v1/accommodations
{
  "trip_day_id": 5,
  "accommodation_type": "check_out",
  "check_out_time": 1704441600,
  "name": "Park Hyatt Tokyo",
  "cost": 0,
  "display_order": 0
}

// Evening: Check in to Kyoto hotel
POST /api/v1/accommodations
{
  "trip_day_id": 5,
  "accommodation_type": "check_in",
  "check_in_time": 1704470400,
  "name": "Ritz-Carlton Kyoto",
  "cost": 650.00,
  "currency": "USD",
  "display_order": 1
}
```

### Example 3: Arrival Day
```json
POST /api/v1/accommodations
{
  "trip_day_id": 1,
  "accommodation_type": "check_in",
  "check_in_time": 1704110400,
  "name": "Park Hyatt Tokyo",
  "cost": 450.00,
  "notes": "Arriving from SFO. Late check-in expected around 5pm."
}
```

### Example 4: Filtering by Type
```bash
# Get all checkouts for a trip day
GET /api/v1/accommodations/trip-day/5?accommodation_type=check_out

# Get all check-ins for a trip day
GET /api/v1/accommodations/trip-day/5?accommodation_type=check_in
```

## Common Workflows

### Workflow 1: Hotel Change During Trip
1. Create CHECK_OUT accommodation for morning departure
2. Create CHECK_IN accommodation for evening arrival
3. Use `display_order` to ensure correct sequence
4. Both accommodations on same trip_day_id

### Workflow 2: Extended Stay
1. Create CHECK_IN on arrival day
2. Create WHOLE_DAY for each full day
3. Create CHECK_OUT on departure day

### Workflow 3: Cost Tracking
```bash
# Get total accommodation cost for specific day
GET /api/v1/accommodations/trip-day/5/cost?currency=USD

# Response: { "total_cost": 650.00 }
```

### Workflow 4: Confirmation Lookup
```bash
# Quick lookup from booking email
GET /api/v1/accommodations/confirmation/HYATT123456
```

## Best Practices

### 1. Accommodation Types
- **CHECK_IN**: Use for days when you're arriving and checking in
- **WHOLE_DAY**: Use for regular days with no check-in/out activity
- **CHECK_OUT**: Use for days when you're leaving/checking out
- **Hotel changes**: Use both CHECK_OUT and CHECK_IN on the same day

### 2. Timing
- Store times as **Unix timestamps** (seconds since epoch)
- Times represent local time at the accommodation location
- Use `check_in_time` and `check_out_time` for precise tracking
- Null values acceptable if exact times unknown

### 3. Display Order
- Set `display_order` for custom sequencing
- Lower numbers appear first
- Default is 0
- Useful for multi-accommodation days to control order

### 4. Cost Tracking
- Store costs in original booking currency
- Use `currency` field (ISO 4217 codes: USD, JPY, EUR, etc.)
- Cost aggregation filters by currency
- For multi-currency trips, query each currency separately

### 5. GPS Coordinates
- Use standard decimal degrees format
- Latitude: -90 to 90 (North/South)
- Longitude: -180 to 180 (East/West)
- Enables mapping and location-based features

### 6. Confirmation Numbers
- Always store booking confirmations
- Indexed for fast lookup
- Essential for check-in and customer service
- Can be used to find accommodation across trips

### 7. Contact Information
- Store hotel phone and email
- Useful for emergencies and changes
- Include country codes for international numbers

## Error Handling

| Status Code | Scenario |
|-------------|----------|
| `400 Bad Request` | Invalid data (missing required fields, invalid types) |
| `401 Unauthorized` | Missing or invalid authentication token |
| `403 Forbidden` | User doesn't own the trip |
| `404 Not Found` | Trip day or accommodation not found |
| `422 Unprocessable Entity` | Validation errors (invalid enum values, constraints) |

## Validation Rules

- `name`: Required, 1-200 characters
- `trip_day_id`: Required, must exist
- `accommodation_type`: Must be check_in, whole_day, or check_out
- `currency`: 3 characters (ISO 4217)
- `latitude`: -90 to 90
- `longitude`: -180 to 180
- `cost`: >= 0
- `display_order`: >= 0

## Database Queries

The CRUD layer provides optimized queries:

```python
# Get accommodations ordered by display_order and check-in time
accommodations = get_accommodations_by_trip_day(db, trip_day_id=5)

# Filter by type
checkins = get_accommodations_by_type(db, trip_day_id=5,
                                      accommodation_type=AccommodationType.CHECK_IN)

# Find by confirmation
accommodation = get_accommodation_by_confirmation(db, "HYATT123456")

# Calculate costs
total = get_total_cost_by_trip_day(db, trip_day_id=5, currency="USD")
```

## Integration with Other Features

- **Trip Days**: Each accommodation belongs to exactly one trip day
- **Activities**: Accommodations provide location context for daily activities
- **Transits**: CHECK_IN/CHECK_OUT types coordinate with arrival/departure transits
- **Cost Tracking**: Aggregates with activities and transits for total trip cost

## Migration Notes

This feature replaces the old single-accommodation fields on `trip_days`:
- ❌ Removed: `accommodation_name`, `accommodation_address`, `accommodation_checkin`, `accommodation_checkout`, `accommodation_confirmation`
- ✅ New: Separate `accommodations` table with full relationship support

Benefits:
- Multiple accommodations per day
- Better data normalization
- Enhanced search capabilities
- Richer booking details
- Proper CASCADE deletion
