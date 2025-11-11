# API Refactoring - December 2024

## Overview

Major API refactoring to improve user experience by eliminating the need to manually create or know trip_day_ids before creating related entities. **All 4 features (Accommodations, Transits, Activities, Bookings) now auto-create trip days** when provided with trip_id + dates.

## What Changed

### Before (Old API)
- Users had to provide `trip_day_id` for all entities
- Required creating trip_days first OR knowing their IDs
- Multi-day accommodations required multiple API calls
- Poor UX for simple operations

### After (New API)
- Users provide `trip_id` + date(s)
- Backend automatically finds or creates trip_days
- Multi-day accommodations in single API call
- Cleaner, more intuitive API

---

## 1. Accommodations API

### Old Request Format
```json
POST /api/v1/accommodations
{
  "trip_day_id": 1,
  "accommodation_type": "whole_day",
  "name": "Park Hyatt Tokyo",
  "cost": 450.00,
  "currency": "USD"
}
```

### ✅ New Request Format
```json
POST /api/v1/accommodations
{
  "trip_id": 1,
  "check_in_date": "2024-06-01",
  "check_out_date": "2024-06-03",
  "name": "Park Hyatt Tokyo",
  "cost": 450.00,
  "currency": "USD"
}
```

### Key Changes
- **Removed**: `trip_day_id`, `accommodation_type`, `display_order`
- **Added**: `trip_id`, `check_in_date`, `check_out_date`
- **Behavior**: Auto-creates trip days for date range
- **Response**: Returns **array** of accommodations (one per night)
  - Day 1: CHECK_IN
  - Day 2: WHOLE_DAY
  - Day 3: CHECK_OUT

### Required Fields
- `trip_id` (int)
- `check_in_date` (YYYY-MM-DD)
- `check_out_date` (YYYY-MM-DD)
- `name` (string)

---

## 2. Transits API

### Old Request Format
```json
POST /api/v1/transits
{
  "trip_day_id": 1,
  "transit_mode": "flight",
  "carrier": "United Airlines",
  "from_location": "SFO",
  "to_location": "NRT"
}
```

### ✅ New Request Format
```json
POST /api/v1/transits
{
  "trip_id": 1,
  "transit_date": "2024-06-01",
  "transit_mode": "flight",
  "carrier": "United Airlines",
  "from_location": "SFO",
  "to_location": "NRT"
}
```

### Key Changes
- **Removed**: `trip_day_id`, `display_order`
- **Added**: `trip_id`, `transit_date`
- **Behavior**: Auto-creates trip day if doesn't exist
- **Response**: Single transit object

### Required Fields
- `trip_id` (int)
- `transit_date` (YYYY-MM-DD)
- `transit_mode` (enum: flight, train, bus, car, etc.)

### Important Note
Field renamed from `date` to `transit_date` to avoid Python name collision with `datetime.date`.

---

## 3. Activities API

### Old Request Format
```json
POST /api/v1/activities
{
  "trip_day_id": 2,
  "name": "Visit Meiji Shrine",
  "activity_type": "cultural",
  "time": "09:00"
}
```

### ✅ New Request Format
```json
POST /api/v1/activities
{
  "trip_id": 1,
  "activity_date": "2024-06-02",
  "name": "Visit Meiji Shrine",
  "activity_type": "cultural",
  "time": "09:00"
}
```

### Key Changes
- **Removed**: `trip_day_id`, `display_order`
- **Added**: `trip_id`, `activity_date`
- **Behavior**: Auto-creates trip day if doesn't exist
- **Response**: Single activity object

### Required Fields
- `trip_id` (int)
- `activity_date` (YYYY-MM-DD)
- `name` (string)

---

## 4. Bookings API

### Old Request Format
```json
POST /api/v1/bookings
{
  "trip_day_id": 1,
  "activity_id": null,
  "booking_type": "tour",
  "name": "Tokyo City Tour"
}
```

### ✅ New Request Format
```json
POST /api/v1/bookings
{
  "trip_id": 1,
  "event_date": "2024-06-01",
  "activity_id": null,
  "booking_type": "tour",
  "name": "Tokyo City Tour"
}
```

### Key Changes
- **Removed**: `trip_day_id`
- **Added**: `trip_id`, `event_date`
- **Behavior**: Auto-creates trip day if doesn't exist
- **Response**: Single booking object
- **Note**: `activity_id` remains optional for linking to specific activities

### Required Fields
- `trip_id` (int)
- `event_date` (YYYY-MM-DD)
- `name` (string)

---

## Backend Implementation

### Auto Trip Day Creation Logic

All 4 features now use the same pattern:

```python
def create_entity(db: Session, entity_in: EntityCreate):
    # Find existing trip day for this date
    trip_day = trip_days_crud.get_trip_day_by_trip_and_date(
        db, entity_in.trip_id, entity_in.date
    )

    # Auto-create if doesn't exist
    if not trip_day:
        trip_day_in = TripDayCreate(
            trip_id=entity_in.trip_id,
            date=entity_in.date,
            day_number=_get_next_day_number(db, entity_in.trip_id, entity_in.date),
            place="TBD",
            timezone="UTC"
        )
        trip_day = trip_days_crud.create_trip_day(db, trip_day_in)

    # Create entity with trip_day_id
    entity = Entity(trip_day_id=trip_day.id, **entity_data)
    db.add(entity)
    db.commit()
    return entity
```

### Day Number Assignment

When auto-creating trip days, the system intelligently assigns day_number based on existing trip days:
- If date is after all existing days: `max(day_number) + 1`
- If date is before all existing days: `min(day_number)`
- If date is in the middle: `previous_day_number + 1`

---

## Breaking Changes

### For Frontend Clients

1. **Update Request Bodies**
   - Accommodations: Send `trip_id + check_in_date + check_out_date` instead of `trip_day_id`
   - Transits: Send `trip_id + transit_date` instead of `trip_day_id`
   - Activities: Send `trip_id + activity_date` instead of `trip_day_id`
   - Bookings: Send `trip_id + event_date` instead of `trip_day_id`

2. **Handle Response Changes**
   - Accommodations now returns **array** instead of single object
   - All other endpoints still return single object

3. **Remove Trip Day Pre-Creation Logic**
   - No longer need to create trip days before adding entities
   - System handles this automatically

### Database Schema
- **No changes** - Database structure remains the same
- All tables still use `trip_day_id` foreign keys
- Only the API layer changed

---

## Migration Guide

### Step 1: Update Request Formation
```javascript
// OLD
const response = await api.post('/accommodations', {
  trip_day_id: selectedTripDayId,
  accommodation_type: 'whole_day',
  name: hotelName,
  ...
});

// NEW
const response = await api.post('/accommodations', {
  trip_id: currentTripId,
  check_in_date: checkInDate,    // "2024-06-01"
  check_out_date: checkOutDate,  // "2024-06-03"
  name: hotelName,
  ...
});
```

### Step 2: Handle Array Response (Accommodations Only)
```javascript
// OLD
const accommodation = response.data;
console.log(accommodation.id);

// NEW
const accommodations = response.data;  // Now an array!
accommodations.forEach(acc => console.log(acc.id));
```

### Step 3: Remove Trip Day Creation Code
```javascript
// OLD - No longer needed!
const tripDay = await api.post('/trip-days', {
  trip_id: tripId,
  date: activityDate,
  ...
});
const activity = await api.post('/activities', {
  trip_day_id: tripDay.id,
  ...
});

// NEW - Direct creation!
const activity = await api.post('/activities', {
  trip_id: tripId,
  activity_date: activityDate,
  ...
});
```

---

## Benefits

### For Frontend
✅ **Simpler API calls** - Less data to manage
✅ **Fewer requests** - No need to create trip days first
✅ **Better UX** - Users provide intuitive dates
✅ **Atomic operations** - Entities and trip days created together

### For Backend
✅ **Consistent pattern** - All 4 features work the same way
✅ **Auto-management** - Trip days created as needed
✅ **Cleaner code** - Logic encapsulated in CRUD layer
✅ **Backward compatible DB** - No schema migrations needed

---

## Testing

All features have comprehensive test coverage:
- ✅ Accommodations: 15 tests passing
- ✅ Transits: 5 tests passing
- ✅ Activities: 5 tests passing
- ✅ Bookings: 5 tests passing
- **Total: 30 tests passing**

### Test Example
```python
def test_create_transit(db: Session, test_trip):
    """Test creating a transit (auto-creates trip day)."""
    transit_in = TransitCreate(
        trip_id=test_trip.id,
        transit_date=date(2024, 6, 1),  # New API!
        transit_mode=TransitMode.FLIGHT,
        carrier="United Airlines",
        ...
    )
    transit = crud.create_transit(db, transit_in)

    assert transit.id is not None
    assert transit.transit_mode == TransitMode.FLIGHT
```

---

## Bruno Collection Updates

Example Bruno requests have been updated in:
- `collection/accommodations/Create Accommodation - Park Hyatt Tokyo.bru`
- `collection/transits/Create Transit - International Flight.bru`
- `collection/activities/Create Activity - Meiji Shrine.bru`
- `collection/bookings/Create Booking - Hotel.bru`

All updated files include:
- ✅ New request format
- ✅ Updated field names
- ✅ Comprehensive documentation
- ✅ Usage examples

---

## Timeline

- **Completed**: December 2024
- **All Endpoints**: Production ready
- **Documentation**: Updated
- **Tests**: Passing

## Questions?

For questions about this refactoring, contact the development team or refer to:
- Feature README files in `app/features/*/README.md`
- Bruno collection examples in `collection/*/`
- Test files in `tests/features/*/test_crud.py`
