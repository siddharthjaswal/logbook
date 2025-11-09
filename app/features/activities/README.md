# Activities Feature

The Activities feature allows users to manage individual activities within their trip days. Each activity can include timing, location, cost, booking information, and more.

## Overview

Activities are granular events or tasks that make up a trip day. They provide detailed planning and tracking for everything from sightseeing to dining experiences.

### Key Features

- **Flexible Activity Types**: 11 different types (sightseeing, dining, adventure, cultural, etc.)
- **Time Management**: Track start time and duration (supports decimal hours)
- **Location Tracking**: Store addresses with optional lat/lng coordinates
- **Cost Tracking**: Multi-currency support with aggregation
- **Status Management**: Track planning, booking, completion, and cancellation
- **Custom Ordering**: Reorder activities within a day using display_order
- **Booking Integration**: Link to confirmation numbers and booking URLs

## Database Schema

### Table: `activities`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-incrementing primary key |
| `trip_day_id` | Integer (FK) | Reference to trip_days table (CASCADE delete) |
| `name` | String(200) | Activity name (required) |
| `activity_type` | Enum | Type of activity (default: OTHER) |
| `time` | String(5) | Start time in HH:MM format (24-hour) |
| `duration` | Decimal(4,2) | Duration in hours (e.g., 1.5 = 90 minutes) |
| `location` | String(200) | Location name |
| `location_address` | Text | Full address |
| `latitude` | Decimal(10,8) | GPS latitude |
| `longitude` | Decimal(11,8) | GPS longitude |
| `cost` | Decimal(10,2) | Cost amount |
| `currency` | String(3) | ISO currency code (default: USD) |
| `booking_required` | Boolean | Whether booking is needed (default: false) |
| `confirmation_number` | String(100) | Booking confirmation number |
| `booking_url` | Text | URL to booking/tickets |
| `contact_phone` | String(50) | Contact phone number |
| `contact_email` | String(255) | Contact email address |
| `status` | Enum | Activity status (default: PLANNED) |
| `notes` | Text | Additional notes |
| `display_order` | Integer | Custom ordering within trip day (default: 0) |
| `created_at` | Timestamp | Creation timestamp |
| `updated_at` | Timestamp | Last update timestamp |

### Indexes

- `id` (primary key)
- `trip_day_id` (foreign key)
- `activity_type` (for filtering)
- `status` (for filtering)

### Relationships

- **Belongs to**: `TripDay` (many-to-one)
- **Has many**: `Booking` (one-to-many, cascade delete)

## Enums

### ActivityType

```python
SIGHTSEEING = "sightseeing"      # Museums, landmarks, viewpoints
DINING = "dining"                # Restaurants, cafes, food tours
ADVENTURE = "adventure"          # Hiking, sports, extreme activities
CULTURAL = "cultural"            # Shows, performances, cultural experiences
ENTERTAINMENT = "entertainment"  # Movies, concerts, nightlife
SHOPPING = "shopping"            # Markets, malls, boutiques
RELAXATION = "relaxation"        # Spa, beach, parks
TRANSPORTATION = "transportation" # Getting from place to place
ACCOMMODATION = "accommodation"  # Check-in/check-out activities
BUSINESS = "business"            # Meetings, conferences
OTHER = "other"                  # Anything else
```

### ActivityStatus

```python
PLANNED = "planned"      # Activity is planned but not booked
BOOKED = "booked"        # Activity has been booked/confirmed
COMPLETED = "completed"  # Activity has been done
CANCELLED = "cancelled"  # Activity was cancelled
```

## API Endpoints

All endpoints require authentication via `Authorization: Bearer <token>` header.

### Create Activity

```http
POST /api/v1/activities/
Content-Type: application/json

{
  "trip_day_id": 1,
  "name": "Meiji Shrine Visit",
  "activity_type": "cultural",
  "time": "09:00",
  "duration": 2.0,
  "location": "Meiji Shrine",
  "location_address": "1-1 Yoyogikamizonocho, Shibuya City, Tokyo 151-8557, Japan",
  "latitude": 35.6764,
  "longitude": 139.6993,
  "cost": 0,
  "currency": "JPY",
  "booking_required": false,
  "status": "planned",
  "notes": "Quiet and peaceful in the morning. Free admission.",
  "display_order": 0
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "trip_day_id": 1,
  "name": "Meiji Shrine Visit",
  "activity_type": "cultural",
  "time": "09:00",
  "duration": 2.0,
  "location": "Meiji Shrine",
  "location_address": "1-1 Yoyogikamizonocho, Shibuya City, Tokyo 151-8557, Japan",
  "latitude": 35.6764,
  "longitude": 139.6993,
  "cost": 0.0,
  "currency": "JPY",
  "booking_required": false,
  "confirmation_number": null,
  "booking_url": null,
  "contact_phone": null,
  "contact_email": null,
  "status": "planned",
  "notes": "Quiet and peaceful in the morning. Free admission.",
  "display_order": 0,
  "created_at": 1704672000,
  "updated_at": 1704672000
}
```

### List Activities by Trip Day

```http
GET /api/v1/activities/trip-day/{trip_day_id}?skip=0&limit=100&activity_type=cultural&activity_status=planned
```

**Query Parameters**:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 100, max: 100)
- `activity_type` (optional): Filter by ActivityType enum
- `activity_status` (optional): Filter by ActivityStatus enum

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "trip_day_id": 1,
    "activity_type": "cultural",
    "name": "Meiji Shrine Visit",
    "time": "09:00",
    "duration": 2.0,
    "cost": 0.0,
    "currency": "JPY",
    "status": "planned",
    "location": "Meiji Shrine"
  }
]
```

### Get Activity by ID

```http
GET /api/v1/activities/{activity_id}
```

**Response**: `200 OK` (same as create response)

### Update Activity

```http
PUT /api/v1/activities/{activity_id}
Content-Type: application/json

{
  "status": "booked",
  "confirmation_number": "SHRINE123",
  "notes": "Confirmed booking for guided tour"
}
```

**Response**: `200 OK` (full activity object with updates)

### Delete Activity

```http
DELETE /api/v1/activities/{activity_id}
```

**Response**: `204 No Content`

### Reorder Activities

```http
POST /api/v1/activities/trip-day/{trip_day_id}/reorder
Content-Type: application/json

[3, 1, 2]  // Array of activity IDs in desired order
```

**Response**: `200 OK`
```json
[
  {
    "id": 3,
    "display_order": 0,
    ...
  },
  {
    "id": 1,
    "display_order": 1,
    ...
  },
  {
    "id": 2,
    "display_order": 2,
    ...
  }
]
```

### Get Activities Cost

```http
GET /api/v1/activities/trip-day/{trip_day_id}/cost?currency=JPY
```

**Response**: `200 OK`
```json
{
  "trip_day_id": 1,
  "currency": "JPY",
  "total_cost": 15000.0
}
```

## Access Control

All activity endpoints verify:
1. User is authenticated
2. User owns the trip that contains the trip day

**Authorization Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User doesn't own the trip
- `404 Not Found`: Trip day or activity doesn't exist

## Usage Examples

### Planning a Sightseeing Day

```python
# Create morning activity
activity1 = {
    "trip_day_id": 1,
    "name": "Tokyo Tower",
    "activity_type": "sightseeing",
    "time": "09:00",
    "duration": 1.5,
    "cost": 1200,
    "currency": "JPY",
    "display_order": 0
}

# Create lunch
activity2 = {
    "trip_day_id": 1,
    "name": "Sushi Restaurant",
    "activity_type": "dining",
    "time": "12:00",
    "duration": 1.0,
    "cost": 3000,
    "currency": "JPY",
    "booking_required": true,
    "display_order": 1
}

# Create afternoon activity
activity3 = {
    "trip_day_id": 1,
    "name": "Senso-ji Temple",
    "activity_type": "cultural",
    "time": "14:00",
    "duration": 2.0,
    "cost": 0,
    "currency": "JPY",
    "display_order": 2
}
```

### Filtering Activities

```bash
# Get all dining activities
GET /api/v1/activities/trip-day/1?activity_type=dining

# Get all booked activities
GET /api/v1/activities/trip-day/1?activity_status=booked

# Get completed cultural activities
GET /api/v1/activities/trip-day/1?activity_type=cultural&activity_status=completed
```

## Related Features

- **TripDays**: Parent feature that contains activities
- **Bookings**: Can be associated with activities for detailed reservation tracking
- **Trips**: Grand-parent feature for authorization

## CRUD Operations

All CRUD operations are in `app/features/activities/crud.py`:

- `create_activity()` - Create new activity
- `get_activity_by_id()` - Get single activity
- `get_activities_by_trip_day()` - List with pagination
- `get_activities_by_trip()` - List across all days
- `get_activities_by_type()` - Filter by type
- `get_activities_by_status()` - Filter by status
- `update_activity()` - Update activity
- `delete_activity()` - Delete activity
- `get_activity_count()` - Count activities
- `reorder_activities()` - Update display order
- `get_total_cost_by_trip_day()` - Sum costs by currency

## Best Practices

1. **Use display_order for chronological ordering**: Don't rely on time alone, as some activities may not have times
2. **Set booking_required early**: Helps with planning and tracking what needs to be reserved
3. **Use decimal duration**: 0.5 for 30 minutes, 1.5 for 90 minutes, 2.5 for 2.5 hours
4. **Include location coordinates when possible**: Enables mapping and distance calculations
5. **Update status as you progress**: PLANNED → BOOKED → COMPLETED workflow
6. **Use notes for important details**: Dress codes, reservation names, special instructions
7. **Track costs accurately**: Helps with budget management via cost aggregation endpoint

## Migration

This feature was added in migration `f376b0e51c77_add_activities_and_bookings_tables.py`.

To create the table:
```bash
alembic upgrade head
```

To rollback (removes activities table):
```bash
alembic downgrade -1
```
