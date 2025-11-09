# Bookings Feature

The Bookings feature manages reservations, confirmations, and bookings for trips. Bookings can be associated with trip days, activities, or both, providing flexible reservation tracking.

## Overview

Bookings track all your reservations including accommodations, restaurants, tours, transportation, and more. They provide a centralized way to manage confirmation numbers, costs, and booking details.

### Key Features

- **Flexible Association**: Can belong to trip days, activities, or both
- **9 Booking Types**: Accommodation, restaurant, tour, transportation, etc.
- **Confirmation Tracking**: Store confirmation numbers and references
- **Multi-Currency Support**: Track costs in any currency
- **Status Management**: Track pending, confirmed, completed, cancelled states
- **Search by Confirmation**: Quick lookup by confirmation number
- **Cost Aggregation**: Sum booking costs per trip day
- **Contact Information**: Store provider phone/email for easy reference

## Database Schema

### Table: `bookings`

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Auto-incrementing primary key |
| `trip_day_id` | Integer (FK) | Reference to trip_days (nullable, CASCADE delete) |
| `activity_id` | Integer (FK) | Reference to activities (nullable, CASCADE delete) |
| `booking_type` | Enum | Type of booking (default: OTHER) |
| `name` | String(200) | Booking name (required) |
| `provider` | String(200) | Service provider name |
| `confirmation_number` | String(100) | Confirmation/reservation number |
| `booking_reference` | String(100) | Additional reference number |
| `cost` | Decimal(10,2) | Booking cost |
| `currency` | String(3) | ISO currency code (default: USD) |
| `booking_date` | Date | Date of the booking/reservation |
| `booking_time` | String(5) | Time in HH:MM format (24-hour) |
| `location` | String(200) | Location name |
| `location_address` | Text | Full address |
| `contact_phone` | String(50) | Provider contact phone |
| `contact_email` | String(255) | Provider contact email |
| `booking_url` | Text | URL to booking confirmation/management |
| `status` | Enum | Booking status (default: PENDING) |
| `notes` | Text | Additional notes |
| `created_at` | Timestamp | Creation timestamp |
| `updated_at` | Timestamp | Last update timestamp |

### Indexes

- `id` (primary key)
- `trip_day_id` (foreign key)
- `activity_id` (foreign key)
- `booking_type` (for filtering)
- `confirmation_number` (for search)

### Relationships

- **Belongs to**: `TripDay` (many-to-one, optional)
- **Belongs to**: `Activity` (many-to-one, optional)

**Note**: A booking must have at least one of `trip_day_id` or `activity_id`.

## Enums

### BookingType

```python
ACCOMMODATION = "accommodation"  # Hotels, hostels, vacation rentals
RESTAURANT = "restaurant"        # Dining reservations
TOUR = "tour"                    # Guided tours, experiences
TRANSPORTATION = "transportation" # Flights, trains, buses, car rentals
ENTERTAINMENT = "entertainment"  # Shows, concerts, events
ATTRACTION = "attraction"        # Theme parks, museums (ticketed)
SERVICE = "service"              # Spa, guides, photography
RENTAL = "rental"                # Equipment, vehicles, gear
OTHER = "other"                  # Anything else
```

### BookingStatus

```python
PENDING = "pending"        # Booking initiated but not confirmed
CONFIRMED = "confirmed"    # Booking has been confirmed
COMPLETED = "completed"    # Service has been used/completed
CANCELLED = "cancelled"    # Booking was cancelled
```

## API Endpoints

All endpoints require authentication via `Authorization: Bearer <token>` header.

### Create Booking

```http
POST /api/v1/bookings/
Content-Type: application/json

{
  "trip_day_id": 1,
  "booking_type": "accommodation",
  "name": "Park Hyatt Tokyo",
  "provider": "Hyatt Hotels",
  "confirmation_number": "HYT123456789",
  "booking_reference": "RES-2025-001",
  "cost": 45000,
  "currency": "JPY",
  "booking_date": "2025-01-01",
  "booking_time": "15:00",
  "location": "Park Hyatt Tokyo",
  "location_address": "3-7-1-2 Nishi Shinjuku, Shinjuku-ku, Tokyo 163-1055",
  "contact_phone": "+81-3-5322-1234",
  "contact_email": "tokyo.park@hyatt.com",
  "booking_url": "https://www.hyatt.com/reservation/HYT123456789",
  "status": "confirmed",
  "notes": "Check-in: 3PM. Late checkout requested."
}
```

**Response**: `201 Created`
```json
{
  "id": 1,
  "trip_day_id": 1,
  "activity_id": null,
  "booking_type": "accommodation",
  "name": "Park Hyatt Tokyo",
  "provider": "Hyatt Hotels",
  "confirmation_number": "HYT123456789",
  "booking_reference": "RES-2025-001",
  "cost": 45000.0,
  "currency": "JPY",
  "booking_date": "2025-01-01",
  "booking_time": "15:00",
  "location": "Park Hyatt Tokyo",
  "location_address": "3-7-1-2 Nishi Shinjuku, Shinjuku-ku, Tokyo 163-1055",
  "contact_phone": "+81-3-5322-1234",
  "contact_email": "tokyo.park@hyatt.com",
  "booking_url": "https://www.hyatt.com/reservation/HYT123456789",
  "status": "confirmed",
  "notes": "Check-in: 3PM. Late checkout requested.",
  "created_at": 1704672000,
  "updated_at": 1704672000
}
```

### List Bookings by Trip Day

```http
GET /api/v1/bookings/trip-day/{trip_day_id}?skip=0&limit=100&booking_type=restaurant&booking_status=confirmed
```

**Query Parameters**:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 100, max: 100)
- `booking_type` (optional): Filter by BookingType enum
- `booking_status` (optional): Filter by BookingStatus enum

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "trip_day_id": 1,
    "activity_id": null,
    "booking_type": "restaurant",
    "name": "Sukiyabashi Jiro",
    "confirmation_number": "JIRO20250103",
    "booking_date": "2025-01-03",
    "booking_time": "18:00",
    "cost": 40000.0,
    "currency": "JPY",
    "status": "confirmed"
  }
]
```

### List Bookings by Activity

```http
GET /api/v1/bookings/activity/{activity_id}?skip=0&limit=100
```

**Response**: `200 OK` (same format as trip day listing)

### Get Booking by ID

```http
GET /api/v1/bookings/{booking_id}
```

**Response**: `200 OK` (same as create response)

### Get Booking by Confirmation Number

```http
GET /api/v1/bookings/confirmation/{confirmation_number}
```

**Response**: `200 OK` (same as create response)

**Example**:
```bash
GET /api/v1/bookings/confirmation/HYT123456789
```

### Update Booking

```http
PUT /api/v1/bookings/{booking_id}
Content-Type: application/json

{
  "status": "completed",
  "notes": "Checked out. Excellent service and room."
}
```

**Response**: `200 OK` (full booking object with updates)

### Delete Booking

```http
DELETE /api/v1/bookings/{booking_id}
```

**Response**: `204 No Content`

### Get Bookings Cost

```http
GET /api/v1/bookings/trip-day/{trip_day_id}/cost?currency=JPY
```

**Response**: `200 OK`
```json
{
  "trip_day_id": 1,
  "currency": "JPY",
  "total_cost": 85000.0
}
```

## Access Control

All booking endpoints verify:
1. User is authenticated
2. User owns the trip (checked via trip_day or activity relationship)

**Authorization Errors**:
- `400 Bad Request`: Missing both trip_day_id and activity_id on create
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User doesn't own the trip
- `404 Not Found`: Trip day, activity, or booking doesn't exist

## Usage Examples

### Booking a Multi-Day Accommodation

```python
# Day 1: Check-in
booking1 = {
    "trip_day_id": 1,
    "booking_type": "accommodation",
    "name": "Park Hyatt Tokyo",
    "provider": "Hyatt Hotels",
    "confirmation_number": "HYT123456789",
    "cost": 45000,
    "currency": "JPY",
    "booking_date": "2025-01-01",
    "booking_time": "15:00",
    "status": "confirmed"
}

# Day 2: Same hotel (reference only, no cost)
booking2 = {
    "trip_day_id": 2,
    "booking_type": "accommodation",
    "name": "Park Hyatt Tokyo (Night 2)",
    "confirmation_number": "HYT123456789",
    "status": "confirmed",
    "notes": "Same reservation as Day 1"
}
```

### Restaurant Reservation for an Activity

```python
# Create activity first
activity = {
    "trip_day_id": 3,
    "name": "Tokyo Food Tour",
    "activity_type": "dining",
    "time": "18:00",
    "duration": 3.0
}
# Response: {"id": 5, ...}

# Book restaurant for the tour
booking = {
    "activity_id": 5,  # Link to the food tour activity
    "booking_type": "restaurant",
    "name": "Sukiyabashi Jiro",
    "confirmation_number": "JIRO20250103",
    "cost": 40000,
    "currency": "JPY",
    "booking_date": "2025-01-03",
    "booking_time": "18:30",
    "status": "confirmed"
}
```

### Tracking Transportation

```python
# Flight booking
flight = {
    "trip_day_id": 1,
    "booking_type": "transportation",
    "name": "Tokyo Haneda to Hotel",
    "provider": "Narita Express",
    "confirmation_number": "NEX-2025-001",
    "cost": 3250,
    "currency": "JPY",
    "booking_date": "2025-01-01",
    "booking_time": "14:00",
    "location": "Narita Airport",
    "contact_phone": "+81-50-2016-1603",
    "status": "confirmed"
}
```

### Finding a Booking

```bash
# Quick lookup by confirmation number
GET /api/v1/bookings/confirmation/HYT123456789

# Filter by type
GET /api/v1/bookings/trip-day/1?booking_type=restaurant

# Filter by status
GET /api/v1/bookings/trip-day/1?booking_status=pending
```

## Booking Workflows

### Standard Workflow

1. **PENDING**: Initial booking request made
2. **CONFIRMED**: Provider confirms the reservation
3. **COMPLETED**: Service has been used
4. (Optional) **CANCELLED**: Booking was cancelled

### Status Updates

```python
# Make initial booking
POST /api/v1/bookings/
{
    "booking_type": "restaurant",
    "name": "Dinner Reservation",
    "status": "pending",
    ...
}

# Receive confirmation
PUT /api/v1/bookings/1
{
    "status": "confirmed",
    "confirmation_number": "REST123",
    "notes": "Confirmed for 7:00 PM, table for 2"
}

# After dining
PUT /api/v1/bookings/1
{
    "status": "completed",
    "notes": "Excellent meal. Recommend the tasting menu."
}
```

## Association Patterns

### Trip Day Only

Use when the booking applies to the whole day:
```python
{
    "trip_day_id": 1,
    "activity_id": null,
    "booking_type": "accommodation",
    ...
}
```

### Activity Only

Use when the booking is specific to an activity:
```python
{
    "trip_day_id": null,
    "activity_id": 5,
    "booking_type": "tour",
    ...
}
```

### Both Trip Day and Activity

Use when you want the booking to show in both contexts:
```python
{
    "trip_day_id": 3,
    "activity_id": 8,
    "booking_type": "attraction",
    ...
}
```

## Related Features

- **TripDays**: Can associate bookings with specific days
- **Activities**: Can link bookings to specific activities
- **Trips**: Grand-parent feature for authorization

## CRUD Operations

All CRUD operations are in `app/features/bookings/crud.py`:

- `create_booking()` - Create new booking
- `get_booking_by_id()` - Get single booking
- `get_bookings_by_trip_day()` - List by trip day
- `get_bookings_by_activity()` - List by activity
- `get_bookings_by_trip()` - List across entire trip
- `get_bookings_by_type()` - Filter by type
- `get_bookings_by_status()` - Filter by status
- `get_booking_by_confirmation()` - Search by confirmation number
- `update_booking()` - Update booking
- `delete_booking()` - Delete booking
- `get_booking_count()` - Count bookings
- `get_total_booking_cost_by_trip_day()` - Sum costs by currency

## Best Practices

1. **Always include confirmation numbers**: Critical for trip management
2. **Store provider contact info**: Helpful when you need to make changes
3. **Use booking_url for easy access**: Quick links to manage reservations
4. **Track costs accurately**: Helps with budget management
5. **Update status as you go**: PENDING → CONFIRMED → COMPLETED workflow
6. **Use notes for important details**: Cancellation policies, special requests, etc.
7. **Associate correctly**: Choose trip_day, activity, or both based on context
8. **Use booking_reference for secondary IDs**: Some providers have multiple reference numbers
9. **Include booking_date and booking_time**: Helps with chronological organization

## Common Queries

### All Confirmed Bookings for a Trip Day

```bash
GET /api/v1/bookings/trip-day/1?booking_status=confirmed
```

### All Restaurant Reservations

```bash
GET /api/v1/bookings/trip-day/3?booking_type=restaurant
```

### Total Cost of Bookings

```bash
GET /api/v1/bookings/trip-day/1/cost?currency=JPY
```

### Find Specific Booking

```bash
GET /api/v1/bookings/confirmation/HYT123456789
```

### Pending Bookings (Need Follow-up)

```bash
GET /api/v1/bookings/trip-day/2?booking_status=pending
```

## Integration with Activities

Bookings can enhance activities with detailed reservation information:

```python
# 1. Create the activity
activity = {
    "trip_day_id": 3,
    "name": "Tokyo DisneySea",
    "activity_type": "entertainment",
    "time": "09:00",
    "duration": 8.0,
    "cost": 8900,
    "currency": "JPY"
}
# Response: {"id": 10, ...}

# 2. Add booking for the tickets
booking = {
    "activity_id": 10,
    "trip_day_id": 3,  # Also associate with the day
    "booking_type": "attraction",
    "name": "Tokyo DisneySea Tickets",
    "provider": "Disney",
    "confirmation_number": "TDS-2025-123456",
    "cost": 8900,
    "currency": "JPY",
    "booking_date": "2025-01-03",
    "booking_time": "09:00",
    "booking_url": "https://www.tokyodisneyresort.jp/en/booking/...",
    "status": "confirmed",
    "notes": "E-tickets. Show QR code at entrance."
}
```

## Migration

This feature was added in migration `f376b0e51c77_add_activities_and_bookings_tables.py`.

To create the table:
```bash
alembic upgrade head
```

To rollback (removes bookings table):
```bash
alembic downgrade -1
```

## Error Handling

### Validation Errors

```json
{
  "detail": "Must provide either trip_day_id or activity_id"
}
```

### Not Found

```json
{
  "detail": "Booking not found"
}
```

### Unauthorized

```json
{
  "detail": "Not authorized to add bookings to this trip"
}
```
