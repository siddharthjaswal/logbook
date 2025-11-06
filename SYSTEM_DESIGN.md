# System Design Document
## Logbook - Travel Planning & Tracking Backend

**Version:** 1.0
**Last Updated:** 2025-11-05
**Status:** Design Phase

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Database Design](#2-database-design)
3. [API Design Patterns](#3-api-design-patterns)
4. [Authentication & Authorization](#4-authentication--authorization)
5. [File Storage Architecture](#5-file-storage-architecture)
6. [Caching Strategy](#6-caching-strategy)
7. [Error Handling & Validation](#7-error-handling--validation)
8. [Performance & Scalability](#8-performance--scalability)
9. [Security Considerations](#9-security-considerations)
10. [Technology Stack Decisions](#10-technology-stack-decisions)
11. [Data Flow Diagrams](#11-data-flow-diagrams)
12. [Deployment Architecture](#12-deployment-architecture)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────┐
│   Clients   │
│ (Web/Mobile)│
└──────┬──────┘
       │ HTTPS
       ↓
┌──────────────────────────────────────┐
│         Load Balancer / CDN          │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│         API Gateway / NGINX          │
│      (Rate Limiting, SSL, CORS)      │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│      FastAPI Application Layer       │
│  ┌────────────────────────────────┐  │
│  │  Auth Middleware (JWT)         │  │
│  ├────────────────────────────────┤  │
│  │  Route Handlers                │  │
│  ├────────────────────────────────┤  │
│  │  Business Logic Layer          │  │
│  ├────────────────────────────────┤  │
│  │  Data Access Layer (CRUD)      │  │
│  └────────────────────────────────┘  │
└──────┬───────────────┬───────────────┘
       │               │
       ↓               ↓
┌─────────────┐  ┌──────────────┐
│  PostgreSQL │  │  Redis Cache │
│  (Primary)  │  │  & Sessions  │
└─────────────┘  └──────────────┘
       │
       ↓
┌─────────────┐
│  Celery     │
│  Workers    │
│  (Async)    │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────┐
│  External Services              │
│  • AWS S3 (File Storage)        │
│  • SendGrid (Email)             │
│  • Currency API                 │
│  • Weather API (Future)         │
└─────────────────────────────────┘
```

### 1.2 Architectural Patterns

#### Layered Architecture
```
┌────────────────────────────────────┐
│     Presentation Layer (API)       │  FastAPI Routes
├────────────────────────────────────┤
│     Business Logic Layer           │  Services & Validators
├────────────────────────────────────┤
│     Data Access Layer              │  CRUD Operations
├────────────────────────────────────┤
│     Database Layer                 │  PostgreSQL + SQLAlchemy
└────────────────────────────────────┘
```

**Benefits:**
- Clear separation of concerns
- Easy to test each layer independently
- Maintainable and scalable
- Standard pattern for REST APIs

#### Design Patterns Used

1. **Repository Pattern** (Data Access Layer)
   - Abstracts database operations
   - Makes database swapping easier
   - Simplifies testing with mocks

2. **Dependency Injection** (FastAPI Native)
   - Database sessions injected per request
   - Current user injected after auth
   - Clean and testable code

3. **Factory Pattern** (For complex object creation)
   - Trip creation with defaults
   - User registration with validation

4. **Strategy Pattern** (For file storage)
   - Local storage for development
   - S3 storage for production
   - Easy to swap implementations

---

## 2. Database Design

### 2.1 Database Choice: PostgreSQL

**Decision: PostgreSQL over SQLite for production**

| Criteria | SQLite | PostgreSQL | Decision |
|----------|--------|------------|----------|
| Concurrency | Limited (file locking) | Excellent (MVCC) | ✅ PostgreSQL |
| Data Size | Limited (~140 TB) | Unlimited | ✅ PostgreSQL |
| Network Access | No | Yes | ✅ PostgreSQL |
| JSON Support | Basic | Advanced (JSONB) | ✅ PostgreSQL |
| Full-Text Search | Basic | Advanced | ✅ PostgreSQL |
| Transactions | Yes | Advanced | ✅ PostgreSQL |
| Replication | Manual | Built-in | ✅ PostgreSQL |
| Performance | Fast for simple | Better for complex | ✅ PostgreSQL |

**Recommendation:** Use SQLite for development, PostgreSQL for production.

### 2.2 Complete Database Schema

#### Core Entities Detailed Design

---

### **Entity: Users**

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,

    -- OAuth Authentication (Google only for MVP)
    google_id VARCHAR(255) NOT NULL UNIQUE,  -- Google user ID
    email VARCHAR(255) NOT NULL UNIQUE,      -- From Google (always verified)
    email_verified BOOLEAN DEFAULT TRUE,     -- Google handles verification

    -- Optional username (can be set after signup)
    username VARCHAR(50) UNIQUE,

    -- Profile (populated from Google)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_photo_url TEXT,  -- From Google profile picture
    bio TEXT,

    -- Preferences
    default_currency VARCHAR(3) DEFAULT 'USD',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',

    -- Account Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    -- Soft Delete
    deleted_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;
```

**Design Decisions:**
- `BIGSERIAL` for future-proof IDs (supports billions of records)
- **Google OAuth only** (no password storage, more secure)
- `google_id` as OAuth identifier (unique, indexed)
- Email from Google (always verified, no email verification flow needed)
- `email_verified` always TRUE (Google handles verification)
- Profile fields populated from Google profile (name, photo)
- Optional username (can be set by user after signup for display/URL)
- Soft delete with `deleted_at` to preserve data integrity
- Timezone-aware timestamps for global users
- No password fields (OAuth-only authentication)

---

### **Entity: Trips**

```sql
CREATE TYPE trip_status AS ENUM ('planning', 'ongoing', 'completed', 'cancelled');

CREATE TABLE trips (
    id BIGSERIAL PRIMARY KEY,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    -- Note: created_by tracks original creator (can be NULL if user deleted)
    -- Trip persists even if creator leaves - see trip_collaborators for active members
    -- Public trips remain accessible even after creator deletion

    -- Basic Info
    name VARCHAR(200) NOT NULL,
    description TEXT,
    cover_photo_url TEXT,

    -- Dates (flexible for planning stage)
    start_date_timestamp BIGINT,           -- Exact start time (NULL if flexible)
    start_timezone VARCHAR(50) DEFAULT 'UTC',
    end_date_timestamp BIGINT,             -- Exact end time (NULL if flexible)
    end_timezone VARCHAR(50) DEFAULT 'UTC',

    -- Flexible/tentative dates (for planning stage)
    dates_confirmed BOOLEAN DEFAULT FALSE, -- Are dates locked in?
    planned_start_year INTEGER,            -- e.g., 2025
    planned_start_month INTEGER,           -- 1-12 (e.g., January = 1)
    planned_start_week VARCHAR(10),        -- 'first', 'second', 'third', 'fourth', 'last'
    planned_duration_days INTEGER,         -- e.g., 5 days

    -- Flexible date description (user-friendly)
    date_flexibility VARCHAR(50),          -- 'exact', 'flexible', 'month', 'quarter', 'year'
    flexible_date_notes TEXT,              -- "Sometime in January, preferably first 2 weeks"

    -- Location (for search/filtering/display)
    primary_destination_country VARCHAR(100), -- Main/first destination
    primary_destination_city VARCHAR(100),    -- Main/first city
    primary_destination_coordinates POINT,    -- Main destination coordinates

    -- All destinations visited (calculated from trip_days or user-provided)
    countries_visited TEXT[], -- ['France', 'Italy', 'Spain']
    cities_visited TEXT[],    -- ['Paris', 'Rome', 'Barcelona']

    -- Trip type classification
    trip_type VARCHAR(20) DEFAULT 'single_destination', -- single_destination, multi_city, multi_country, regional, global

    -- Status & Visibility
    status trip_status DEFAULT 'planning',
    visibility VARCHAR(20) DEFAULT 'private', -- private, unlisted, public
    is_featured BOOLEAN DEFAULT FALSE, -- Featured in public gallery

    -- Budget
    budget_total NUMERIC(12, 2),
    currency VARCHAR(3) DEFAULT 'USD',

    -- Metadata
    tags TEXT[], -- Array of tags for categorization
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_dates CHECK (
        (start_date_timestamp IS NULL AND end_date_timestamp IS NULL) OR
        (start_date_timestamp IS NOT NULL AND end_date_timestamp IS NOT NULL AND end_date_timestamp >= start_date_timestamp)
    ),
    CONSTRAINT valid_budget CHECK (budget_total IS NULL OR budget_total >= 0),
    CONSTRAINT valid_planned_month CHECK (planned_start_month IS NULL OR (planned_start_month >= 1 AND planned_start_month <= 12)),
    CONSTRAINT valid_duration CHECK (planned_duration_days IS NULL OR planned_duration_days > 0)
);

-- Indexes
CREATE INDEX idx_trips_created_by ON trips(created_by);
CREATE INDEX idx_trips_status ON trips(status);
CREATE INDEX idx_trips_visibility ON trips(visibility);
CREATE INDEX idx_trips_type ON trips(trip_type);
CREATE INDEX idx_trips_dates ON trips(start_date_timestamp, end_date_timestamp);
CREATE INDEX idx_trips_dates_confirmed ON trips(dates_confirmed);
CREATE INDEX idx_trips_planned_dates ON trips(planned_start_year, planned_start_month);
CREATE INDEX idx_trips_primary_destination ON trips(primary_destination_country, primary_destination_city);
CREATE INDEX idx_trips_tags ON trips USING GIN(tags); -- For array searches

-- GIN indexes for multi-destination searches
CREATE INDEX idx_trips_countries_visited ON trips USING GIN(countries_visited);
CREATE INDEX idx_trips_cities_visited ON trips USING GIN(cities_visited);

-- Composite indexes for public trip queries
CREATE INDEX idx_trips_public_featured ON trips(visibility, is_featured)
    WHERE visibility = 'public' AND deleted_at IS NULL;
CREATE INDEX idx_trips_public_destination ON trips(visibility, primary_destination_country, primary_destination_city)
    WHERE visibility = 'public' AND deleted_at IS NULL;
CREATE INDEX idx_trips_public_views ON trips(visibility, views_count DESC)
    WHERE visibility = 'public' AND deleted_at IS NULL;
```

**Design Decisions:**
- `created_by` tracks original creator (can be NULL if user deleted)
- `ON DELETE SET NULL` - trip persists even if creator deleted (especially for public trips)
- `visibility` enum: private (collaborators only), unlisted (link sharing), public (discoverable)
- `is_featured` flag for curated public trips in gallery
- **Flexible date support**:
  - Exact dates: `start/end_date_timestamp` (when confirmed)
  - Flexible dates: `planned_start_year/month` + `planned_duration_days`
  - `dates_confirmed` flag indicates planning vs confirmed stage
  - `date_flexibility` describes how flexible ('exact', 'flexible', 'month', 'quarter')
  - Supports common scenarios: "5 days in January", "2 weeks in summer", "TBD"
  - Constraint: Either both timestamps NULL or both NOT NULL
- **Multi-destination support**:
  - `primary_destination_*` fields for main/first destination (display, search)
  - `countries_visited`, `cities_visited` arrays for all destinations
  - `trip_type` classification (single_destination, multi_city, multi_country, etc.)
  - Auto-calculated from trip_days or user-provided
  - GIN indexes for efficient "contains" queries (e.g., trips visiting France)
- **Timezone handling**:
  - Unix timestamps (absolute time, no ambiguity)
  - Separate timezone fields for start/end (local interpretation)
  - start_timezone = "where the trip starts" (usually home/departure city)
  - end_timezone = "where the trip ends" (final destination)
  - Each trip_day has its own timezone (handles timezone changes)
  - IANA timezone format (e.g., 'America/New_York', 'Asia/Tokyo')
- `ENUM` for status to enforce valid states
- `NUMERIC(12,2)` for budget to avoid floating point errors
- PostgreSQL `POINT` type for coordinates (can upgrade to PostGIS)
- `TEXT[]` array for flexible tagging
- Composite indexes for common query patterns

---

### **Flexible Date Model**

Travel planning happens in stages. Users often know **where** and **how long** before they know **exactly when**.

#### The Problem: Rigid Dates

Current travel apps often require exact dates, but reality is:
- "I want to visit Paris for 5 days in January" (no exact dates yet)
- "Planning 2 weeks in Europe, summer 2025" (flexible)
- "Weekend getaway to Barcelona, sometime in March" (TBD)

#### The Solution: Support Both Exact AND Flexible Dates

```sql
-- Exact dates (when confirmed)
start_date_timestamp: 1735689600  -- Jan 1, 2025
end_date_timestamp: 1736121600    -- Jan 6, 2025
dates_confirmed: TRUE

-- OR Flexible dates (planning stage)
start_date_timestamp: NULL
end_date_timestamp: NULL
dates_confirmed: FALSE
planned_start_year: 2025
planned_start_month: 1            -- January
planned_duration_days: 5
date_flexibility: 'month'
flexible_date_notes: 'Preferably first 2 weeks of January'
```

---

#### Real-World Examples

**Example 1: Exact Dates (Confirmed)**
```sql
Trip: "Paris New Year"
start_date_timestamp: 1735689600      -- Jan 1, 2025, 00:00 UTC
end_date_timestamp: 1735948800        -- Jan 4, 2025, 00:00 UTC
dates_confirmed: TRUE
date_flexibility: 'exact'
planned_duration_days: 3              -- Calculated from timestamps

-- Display: "Jan 1-4, 2025" ✅
```

**Example 2: Flexible Month**
```sql
Trip: "Paris Winter Trip"
start_date_timestamp: NULL
end_date_timestamp: NULL
dates_confirmed: FALSE
planned_start_year: 2025
planned_start_month: 1                -- January
planned_duration_days: 5
date_flexibility: 'month'
flexible_date_notes: 'Flexible within January, avoiding New Year'

-- Display: "January 2025 • 5 days" 📅
```

**Example 3: Flexible Week**
```sql
Trip: "Barcelona Weekend"
start_date_timestamp: NULL
dates_confirmed: FALSE
planned_start_year: 2025
planned_start_month: 3                -- March
planned_start_week: 'second'          -- Second week
planned_duration_days: 3
date_flexibility: 'flexible'

-- Display: "2nd week of March 2025 • 3 days" 📅
```

**Example 4: Flexible Quarter**
```sql
Trip: "Southeast Asia Adventure"
start_date_timestamp: NULL
dates_confirmed: FALSE
planned_start_year: 2025
planned_start_month: NULL             -- Not specific month
planned_duration_days: 21
date_flexibility: 'quarter'
flexible_date_notes: 'Q1 2025 - January, February, or March'

-- Display: "Q1 2025 • 3 weeks" 📅
```

**Example 5: Someday/TBD**
```sql
Trip: "Australia Dream Trip"
start_date_timestamp: NULL
dates_confirmed: FALSE
planned_start_year: 2026
planned_duration_days: 14
date_flexibility: 'year'
flexible_date_notes: 'Someday in 2026, need to save up first'

-- Display: "2026 • 2 weeks" 📅
```

---

#### Date Flexibility Levels

```sql
CREATE TYPE date_flexibility AS ENUM (
    'exact',      -- Dates locked in
    'flexible',   -- Within specific week/month
    'month',      -- Flexible within a month
    'quarter',    -- Q1, Q2, Q3, Q4
    'year',       -- Sometime this year
    'tbd'         -- To be determined
);
```

| Flexibility | Has Exact Dates? | Has Month? | Use Case |
|-------------|------------------|------------|----------|
| **exact** | ✅ Yes | ✅ Yes | Flights booked |
| **flexible** | ❌ No | ✅ Yes | "First week of Jan" |
| **month** | ❌ No | ✅ Yes | "Sometime in January" |
| **quarter** | ❌ No | ❌ No | "Q1 2025" |
| **year** | ❌ No | ❌ No | "Someday in 2025" |
| **tbd** | ❌ No | ❌ No | "Eventually..." |

---

#### User Journey: Planning → Confirmed

**Stage 1: Initial Idea**
```sql
-- User creates trip
name: "Paris Adventure"
planned_start_year: 2025
planned_start_month: 6               -- June
planned_duration_days: 7
dates_confirmed: FALSE
date_flexibility: 'month'
status: 'planning'
```

**Stage 2: Narrow Down Dates**
```sql
-- User updates trip
planned_start_week: 'second'         -- Second week of June
date_flexibility: 'flexible'
flexible_date_notes: 'June 8-15 or June 9-16'
```

**Stage 3: Dates Confirmed**
```sql
-- User books flights, locks dates
start_date_timestamp: 1749600000     -- June 9, 2025
end_date_timestamp: 1750204800       -- June 16, 2025
start_timezone: 'America/New_York'
end_timezone: 'Europe/Paris'
dates_confirmed: TRUE
date_flexibility: 'exact'
status: 'planning'                   -- Still planning details
```

**Stage 4: Trip Happening**
```sql
status: 'ongoing'                    -- User on the trip!
```

**Stage 5: Trip Completed**
```sql
status: 'completed'                  -- Memories saved
```

---

#### Display Logic

**Frontend Display Helper:**
```python
def format_trip_dates(trip, user_timezone=None):
    """Format trip dates based on confirmation status."""

    # Exact dates confirmed
    if trip.dates_confirmed and trip.start_date_timestamp:
        start = format_timestamp(trip.start_date_timestamp, trip.start_timezone)
        end = format_timestamp(trip.end_date_timestamp, trip.end_timezone)
        return f"{start} - {end}"

    # Flexible dates
    else:
        parts = []

        # Week specificity
        if trip.planned_start_week:
            week_text = {
                'first': '1st week',
                'second': '2nd week',
                'third': '3rd week',
                'fourth': '4th week',
                'last': 'last week'
            }[trip.planned_start_week]
            parts.append(week_text + ' of')

        # Month specificity
        if trip.planned_start_month:
            month_name = calendar.month_name[trip.planned_start_month]
            parts.append(month_name)
        elif trip.date_flexibility == 'quarter':
            quarter = (trip.planned_start_month - 1) // 3 + 1 if trip.planned_start_month else '?'
            parts.append(f"Q{quarter}")

        # Year
        if trip.planned_start_year:
            parts.append(str(trip.planned_start_year))

        # Duration
        if trip.planned_duration_days:
            if trip.planned_duration_days == 1:
                duration = "1 day"
            elif trip.planned_duration_days < 7:
                duration = f"{trip.planned_duration_days} days"
            elif trip.planned_duration_days % 7 == 0:
                weeks = trip.planned_duration_days // 7
                duration = f"{weeks} {'week' if weeks == 1 else 'weeks'}"
            else:
                duration = f"{trip.planned_duration_days} days"
            parts.append('•')
            parts.append(duration)

        return ' '.join(parts)

# Examples:
# "2nd week of January 2025 • 5 days"
# "June 2025 • 2 weeks"
# "Q1 2025 • 21 days"
# "2026 • 2 weeks"
```

---

#### Search & Filter by Flexible Dates

**Query: "Trips planned for January 2025"**
```sql
SELECT * FROM trips
WHERE (
    -- Exact dates in January 2025
    (dates_confirmed = TRUE
     AND start_date_timestamp >= 1735689600  -- Jan 1, 2025
     AND start_date_timestamp < 1738368000)  -- Feb 1, 2025
    OR
    -- Flexible dates targeting January 2025
    (dates_confirmed = FALSE
     AND planned_start_year = 2025
     AND planned_start_month = 1)
);
```

**Query: "Trips in planning stage"**
```sql
SELECT * FROM trips
WHERE dates_confirmed = FALSE
  AND status = 'planning'
ORDER BY planned_start_year, planned_start_month;
```

**Query: "Trips with confirmed dates"**
```sql
SELECT * FROM trips
WHERE dates_confirmed = TRUE
  AND status IN ('planning', 'ongoing')
ORDER BY start_date_timestamp;
```

---

#### Benefits of Flexible Dates

✅ **Real planning workflow**: Matches how people actually plan trips
✅ **Early ideation**: Start planning before booking
✅ **Gradual refinement**: Narrow down dates over time
✅ **Public discovery**: "January 2025 trips" works for both exact and flexible
✅ **Trip status tracking**: Clear distinction between ideas vs booked trips
✅ **No forced precision**: Don't require exact dates unnecessarily

---

#### Business Logic: Confirming Dates

```python
async def confirm_trip_dates(
    trip_id: int,
    start_date: datetime,
    end_date: datetime,
    start_timezone: str,
    end_timezone: str,
    db: Session
):
    """
    User confirms exact dates for their trip.
    Transition from flexible to confirmed.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    # Calculate duration
    duration_seconds = end_date.timestamp() - start_date.timestamp()
    duration_days = int(duration_seconds / 86400)

    # Update trip
    trip.start_date_timestamp = int(start_date.timestamp())
    trip.end_date_timestamp = int(end_date.timestamp())
    trip.start_timezone = start_timezone
    trip.end_timezone = end_timezone
    trip.dates_confirmed = True
    trip.date_flexibility = 'exact'
    trip.planned_duration_days = duration_days

    db.commit()
    return trip
```

---

#### Alternative Approaches Considered

❌ **Option 1: Always require exact dates**
- Problem: Forces users to pick arbitrary dates during planning
- Result: Bad UX, inaccurate data

❌ **Option 2: Store as string "January 2025"**
- Problem: Can't query/filter efficiently
- Result: No sorting, no date-based searches

❌ **Option 3: Separate "planned_trips" table**
- Problem: Duplication, complex migrations when dates confirmed
- Result: Overkill

✅ **Our Approach: Nullable timestamps + flexible fields**
- Simple, flexible, queryable
- Matches real user workflow
- Single source of truth

---

### **Multi-Destination Model**

Most trips visit **multiple locations**. How do we represent "Europe Backpacking" that visits Paris, Rome, and Barcelona?

#### The Approach: Primary + All Destinations

```sql
trips:
  -- Primary destination (for display/filtering)
  primary_destination_country: 'France'
  primary_destination_city: 'Paris'

  -- All destinations visited (for complete search)
  countries_visited: ['France', 'Italy', 'Spain']
  cities_visited: ['Paris', 'Rome', 'Barcelona']

  -- Trip type classification
  trip_type: 'multi_country'
```

#### Why Both Primary AND All Destinations?

**1. Primary Destination = User-Facing**
- Trip cards: "**Paris** and 2 other cities"
- Search: "Trips to **France**"
- Display: Easy to show main destination

**2. All Destinations = Complete Search**
- Find: "All trips visiting Italy" (even if Italy isn't primary)
- Browse: "Multi-country trips in Europe"
- Analytics: "Most popular country combinations"

#### Real-World Examples

**Example 1: Single Destination Trip**
```sql
Trip: "Tokyo Adventure" (7 days in Tokyo)

primary_destination_country: 'Japan'
primary_destination_city: 'Tokyo'
countries_visited: ['Japan']
cities_visited: ['Tokyo']
trip_type: 'single_destination'
```

**Example 2: Multi-City Trip (Same Country)**
```sql
Trip: "Italian Tour" (Rome → Florence → Venice)

primary_destination_country: 'Italy'
primary_destination_city: 'Rome'  -- First/main city
countries_visited: ['Italy']
cities_visited: ['Rome', 'Florence', 'Venice']
trip_type: 'multi_city'
```

**Example 3: Multi-Country Trip**
```sql
Trip: "Europe Backpacking" (France → Italy → Spain)

primary_destination_country: 'France'  -- First country
primary_destination_city: 'Paris'      -- First city
countries_visited: ['France', 'Italy', 'Spain']
cities_visited: ['Paris', 'Rome', 'Barcelona']
trip_type: 'multi_country'
```

**Example 4: Regional Trip**
```sql
Trip: "Southeast Asia Adventure" (Thailand → Vietnam → Cambodia)

primary_destination_country: 'Thailand'
primary_destination_city: 'Bangkok'
countries_visited: ['Thailand', 'Vietnam', 'Cambodia']
cities_visited: ['Bangkok', 'Ho Chi Minh City', 'Siem Reap']
trip_type: 'regional'
```

**Example 5: Global Trip**
```sql
Trip: "Around the World" (USA → Europe → Asia → Australia)

primary_destination_country: 'USA'  -- Starting point
primary_destination_city: 'New York'
countries_visited: ['USA', 'France', 'Japan', 'Australia', ...]
cities_visited: ['New York', 'Paris', 'Tokyo', 'Sydney', ...]
trip_type: 'global'
```

#### Trip Type Classification

```sql
CREATE TYPE trip_type AS ENUM (
    'single_destination',  -- One city/area
    'multi_city',          -- Multiple cities, one country
    'multi_country',       -- Multiple countries, one region
    'regional',            -- Cross-regional (e.g., Southeast Asia, Western Europe)
    'global'               -- Multiple continents
);
```

| Type | Definition | Example |
|------|------------|---------|
| **single_destination** | One city/area | "Paris 5 Days" |
| **multi_city** | 2+ cities, 1 country | "Italy: Rome, Florence, Venice" |
| **multi_country** | 2+ countries, 1 region | "Spain & Portugal" |
| **regional** | Multiple countries, cross-regional | "Southeast Asia: Thailand, Vietnam, Cambodia" |
| **global** | Multiple continents | "Around the World: USA, Europe, Asia" |

#### Auto-Calculation from trip_days

```python
def calculate_destinations(trip_id: int, db: Session):
    """
    Auto-calculate destination fields from trip_days.
    Called after trip_days are added/updated.
    """
    # Get all days for trip, ordered chronologically
    days = db.query(TripDay).filter(
        TripDay.trip_id == trip_id
    ).order_by(TripDay.date).all()

    if not days:
        return

    # Extract unique countries and cities (preserve order)
    countries = []
    cities = []
    for day in days:
        if day.place_country and day.place_country not in countries:
            countries.append(day.place_country)
        if day.place_city and day.place_city not in cities:
            cities.append(day.place_city)

    # Primary = first destination
    primary_country = countries[0] if countries else None
    primary_city = cities[0] if cities else None

    # Classify trip type
    trip_type = classify_trip_type(countries, cities)

    # Update trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    trip.primary_destination_country = primary_country
    trip.primary_destination_city = primary_city
    trip.countries_visited = countries
    trip.cities_visited = cities
    trip.trip_type = trip_type
    db.commit()

def classify_trip_type(countries: list, cities: list) -> str:
    """Classify trip based on destinations."""
    if len(countries) == 1 and len(cities) == 1:
        return 'single_destination'
    elif len(countries) == 1 and len(cities) > 1:
        return 'multi_city'
    elif len(countries) <= 3:
        return 'multi_country'
    elif len(countries) <= 6:
        return 'regional'
    else:
        return 'global'
```

#### Search Queries Enabled

**1. Find trips to specific country (primary OR visited)**
```sql
-- Trips where France is primary destination
SELECT * FROM trips WHERE primary_destination_country = 'France';

-- Trips that visit France (even if not primary)
SELECT * FROM trips WHERE 'France' = ANY(countries_visited);

-- Combined: Trips related to France
SELECT * FROM trips
WHERE primary_destination_country = 'France'
   OR 'France' = ANY(countries_visited);
```

**2. Find multi-country trips**
```sql
SELECT * FROM trips
WHERE trip_type IN ('multi_country', 'regional', 'global');
```

**3. Find trips visiting multiple specific countries**
```sql
-- Trips visiting both France AND Italy
SELECT * FROM trips
WHERE countries_visited @> ARRAY['France', 'Italy'];
```

**4. Browse by city**
```sql
-- All trips to Paris
SELECT * FROM trips WHERE 'Paris' = ANY(cities_visited);
```

#### User Experience Benefits

**Trip Cards/Display:**
```
[Trip Card]
Europe Adventure
📍 Paris, France + 2 more cities
🗓️ 10 days • Multi-country
```

**Search Results:**
```
Search: "France"
Results:
✓ "Paris Weekend" (primary: France)
✓ "Europe Tour" (visits: France, Italy, Spain)
✓ "French Riviera" (primary: France)
```

**Filters:**
```
Destination Type:
☐ Single destination
☑ Multi-city
☑ Multi-country
☐ Regional
☐ Global
```

#### Benefits of This Approach

✅ **Accurate**: Captures all destinations visited
✅ **Searchable**: Can find trips by any destination (not just primary)
✅ **User-friendly**: Shows primary destination prominently
✅ **Efficient**: GIN indexes make array searches fast
✅ **Flexible**: User can override auto-calculation
✅ **Analytics-ready**: Easy to query trip patterns

#### Alternative Approaches Considered

❌ **Option 1: Single destination only**
```sql
destination_country: 'France'  -- Loses Italy, Spain!
```
- Problem: Can't represent multi-destination trips

❌ **Option 2: Comma-separated string**
```sql
destinations: 'France, Italy, Spain'
```
- Problem: Can't query efficiently, string parsing required

❌ **Option 3: Separate destinations table**
```sql
trip_destinations:
  trip_id, country, city, order
```
- Problem: Overkill, extra joins, slower queries
- When to use: If destinations become complex (duration per city, etc.)

✅ **Our Approach: Primary + Arrays**
- Simple, fast, covers all use cases

---

### **Timezone Handling Strategy**

Travel apps face a unique challenge: **trips span multiple timezones**. A flight from NYC to Tokyo crosses 13 hours of timezone difference. Here's how we handle it:

#### The Approach: Hybrid Timestamp + Timezone

```sql
trips:
  start_date_timestamp: 1735689600  -- Unix timestamp (absolute)
  start_timezone: 'America/New_York' -- Local context
  end_date_timestamp: 1737504000
  end_timezone: 'Asia/Tokyo'

trip_days:
  date: '2025-01-05'                -- Calendar date
  timezone: 'Europe/Paris'          -- That day's timezone
  arrival_time: 1735740000          -- Absolute timestamp
  departure_time: 1735790000
```

#### Why This Works

**1. Unix Timestamps = Absolute Time**
- No ambiguity: `1735689600` is exactly one moment in time globally
- Easy comparison: `timestamp1 > timestamp2` always works
- Math operations: Calculate duration, sort chronologically

**2. Timezone Fields = Human Interpretation**
- Display: "Trip starts January 1, 2025 at 9:00 AM **EST**"
- Context: User knows which local time zone
- Flexibility: Each day can have different timezone

**3. Real-World Example**

```
Trip: NYC → Paris → Tokyo (10 days)

trips table:
  start_date_timestamp: 1735689600  (Jan 1, 2025, 00:00:00)
  start_timezone: 'America/New_York' (EST, UTC-5)
  end_date_timestamp: 1736553600    (Jan 11, 2025, 00:00:00)
  end_timezone: 'Asia/Tokyo'        (JST, UTC+9)

trip_days:
  Day 1: date=2025-01-01, timezone='America/New_York'   (NYC)
  Day 2: date=2025-01-02, timezone='America/New_York'   (Flight to Paris)
  Day 3: date=2025-01-03, timezone='Europe/Paris'       (Arrived Paris)
  Day 4: date=2025-01-04, timezone='Europe/Paris'       (Paris)
  Day 5: date=2025-01-05, timezone='Europe/Paris'       (Paris)
  Day 6: date=2025-01-06, timezone='Europe/Paris'       (Flight to Tokyo)
  Day 7: date=2025-01-07, timezone='Asia/Tokyo'         (Arrived Tokyo)
  Day 8: date=2025-01-08, timezone='Asia/Tokyo'         (Tokyo)
  Day 9: date=2025-01-09, timezone='Asia/Tokyo'         (Tokyo)
  Day 10: date=2025-01-10, timezone='Asia/Tokyo'        (Tokyo)
```

#### Handling Edge Cases

**Case 1: Flight Crossing Midnight**
```
Depart NYC: Jan 1, 11:30 PM EST
Arrive Paris: Jan 2, 12:45 PM CET (next day!)

Day 1 (Jan 1):
  timezone: 'America/New_York'
  departure_time: 1735783800  (Jan 1, 23:30 EST)

Day 2 (Jan 2):
  timezone: 'Europe/Paris'
  arrival_time: 1735825500    (Jan 2, 12:45 CET)
```

**Case 2: Flight Crossing Date Line**
```
Depart Los Angeles: Jan 5, 10:00 PM PST
Arrive Sydney: Jan 7, 7:00 AM AEDT (skip Jan 6!)

Day 1 (Jan 5):
  timezone: 'America/Los_Angeles'
  departure_time: 1736146800

Day 2 (Jan 7):  // Note: Jan 6 doesn't exist for traveler!
  timezone: 'Australia/Sydney'
  arrival_time: 1736200800
```

**Case 3: Validation**
```python
# When creating/updating trip_days
def validate_trip_day(trip_day, trip):
    # Convert trip bounds to UTC for comparison
    trip_start_utc = trip.start_date_timestamp
    trip_end_utc = trip.end_date_timestamp

    # Convert day's date to UTC using its timezone
    day_start_utc = convert_to_utc(trip_day.date, trip_day.timezone)

    # Validate day falls within trip
    if not (trip_start_utc <= day_start_utc <= trip_end_utc):
        raise ValidationException(
            "Day must fall within trip dates",
            f"Day {trip_day.date} ({trip_day.timezone}) outside trip range"
        )
```

#### Display Logic

**Frontend Display:**
```python
# Display trip start to user
def format_trip_start(trip, user_timezone):
    # Convert to user's preferred timezone for display
    local_time = convert_timestamp(
        trip.start_date_timestamp,
        from_tz=trip.start_timezone,
        to_tz=user_timezone
    )
    return f"{local_time} ({trip.start_timezone})"

# Example output:
# "January 1, 2025, 9:00 AM EST"
# Or if user is in California:
# "January 1, 2025, 6:00 AM PST (9:00 AM EST)"
```

#### Benefits of This Approach

✅ **Accurate**: Unix timestamps are absolute, no timezone math errors
✅ **Flexible**: Each day has its own timezone (handles timezone changes)
✅ **User-friendly**: Display in local context
✅ **Sortable**: Easy to query/sort trips chronologically
✅ **Validated**: Can enforce days fall within trip bounds
✅ **International**: IANA timezone database (handles DST automatically)

#### Alternative Approaches Considered

❌ **Option 1: Store everything in UTC**
- Problem: Loses local context ("9 AM departure" vs "14:00 UTC")
- Difficult to display meaningfully to users

❌ **Option 2: Store dates as strings with timezone**
- Problem: Can't easily compare/sort
- Math operations require parsing

❌ **Option 3: Use PostgreSQL TIMESTAMPTZ**
- Problem: Stores in UTC, loses original timezone info
- Can't differentiate "9 AM EST" vs "9 AM PST" if both stored as UTC

✅ **Our Approach: Hybrid**
- Unix timestamp (absolute time) + timezone (local context)
- Best of both worlds!

---

### **Entity: TripCollaborators** (NEW - Many-to-Many Relationship)

```sql
CREATE TYPE collaborator_role AS ENUM ('owner', 'editor', 'viewer');

CREATE TABLE trip_collaborators (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role collaborator_role NOT NULL DEFAULT 'viewer',

    -- Invitation tracking
    invited_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    invitation_status VARCHAR(20) DEFAULT 'accepted', -- pending, accepted, declined

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(trip_id, user_id) -- User can only be added once per trip
);

-- Function to handle user deletion and trip ownership
CREATE OR REPLACE FUNCTION handle_user_deletion_for_trips()
RETURNS TRIGGER AS $$
DECLARE
    affected_trip RECORD;
    remaining_owners INT;
    next_editor BIGINT;
BEGIN
    -- For each trip where deleted user was an owner
    FOR affected_trip IN
        SELECT DISTINCT tc.trip_id, t.visibility
        FROM trip_collaborators tc
        JOIN trips t ON tc.trip_id = t.id
        WHERE tc.user_id = OLD.id AND tc.role = 'owner'
    LOOP
        -- Count remaining owners after this deletion
        SELECT COUNT(*) INTO remaining_owners
        FROM trip_collaborators
        WHERE trip_id = affected_trip.trip_id
          AND role = 'owner'
          AND user_id != OLD.id;

        -- If no owners will remain
        IF remaining_owners = 0 THEN
            -- If trip is public, promote first editor to owner
            IF affected_trip.visibility = 'public' THEN
                SELECT user_id INTO next_editor
                FROM trip_collaborators
                WHERE trip_id = affected_trip.trip_id
                  AND role = 'editor'
                  AND user_id != OLD.id
                ORDER BY created_at ASC
                LIMIT 1;

                IF next_editor IS NOT NULL THEN
                    UPDATE trip_collaborators
                    SET role = 'owner'
                    WHERE trip_id = affected_trip.trip_id
                      AND user_id = next_editor;
                END IF;
            -- If trip is private and no owners remain, delete it
            ELSIF affected_trip.visibility = 'private' THEN
                DELETE FROM trips WHERE id = affected_trip.trip_id;
            END IF;
        END IF;
    END LOOP;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_deletion_trip_ownership_trigger
    BEFORE DELETE ON users
    FOR EACH ROW
    EXECUTE FUNCTION handle_user_deletion_for_trips();

-- Indexes
CREATE INDEX idx_trip_collaborators_trip_id ON trip_collaborators(trip_id);
CREATE INDEX idx_trip_collaborators_user_id ON trip_collaborators(user_id);
CREATE INDEX idx_trip_collaborators_role ON trip_collaborators(trip_id, role);
CREATE INDEX idx_trip_collaborators_pending ON trip_collaborators(user_id, invitation_status)
    WHERE invitation_status = 'pending';
```

**Collaborator Roles:**

| Role | Permissions |
|------|-------------|
| **owner** | Full control: edit trip, add/remove collaborators, delete trip |
| **editor** | Edit trip details, add expenses/photos/notes, edit days |
| **viewer** | View-only access, can add personal notes (future feature) |

**Design Decisions:**
- Creator automatically becomes 'owner' via trigger or application logic
- Multiple 'owners' allowed (e.g., both partners in a couple)
- Invitation system built-in for future feature
- `UNIQUE(trip_id, user_id)` prevents duplicate memberships
- User deletion handling:
  - **Private trips**: Deleted if last owner leaves
  - **Public trips**: First editor promoted to owner (trip persists)
  - **Unlisted trips**: Same as public (trip persists)
- Trip data remains accessible based on visibility setting

**Trigger to Auto-Add Creator as Owner:**
```sql
CREATE OR REPLACE FUNCTION add_trip_creator_as_owner()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO trip_collaborators (trip_id, user_id, role, invitation_status)
    VALUES (NEW.id, NEW.created_by, 'owner', 'accepted');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trip_creator_owner_trigger
    AFTER INSERT ON trips
    FOR EACH ROW
    EXECUTE FUNCTION add_trip_creator_as_owner();
```

---

### **Trip Visibility Model: Open Source Trips**

Logbook supports **three visibility levels** for trips, enabling users to share their travel itineraries with the world.

#### Visibility Levels

```sql
CREATE TYPE trip_visibility AS ENUM ('private', 'unlisted', 'public');
```

| Visibility | Who Can View | Discoverable | Use Case |
|------------|-------------|--------------|----------|
| **private** | Only collaborators | No | Personal/family trips |
| **unlisted** | Anyone with link | No | Share with specific friends |
| **public** | Everyone | Yes | Community contribution, inspiration |

#### Public Trip Features

**1. Public Trip Gallery**
```sql
-- Get featured public trips
SELECT * FROM trips
WHERE visibility = 'public'
  AND is_featured = TRUE
  AND deleted_at IS NULL
ORDER BY created_at DESC;

-- Browse public trips by destination
SELECT * FROM trips
WHERE visibility = 'public'
  AND destination_country = 'France'
  AND deleted_at IS NULL;
```

**2. Trip Cloning (Fork)**
Users can "clone" public trips to create their own version:
```sql
-- Clone trip creates new trip with same structure
-- but user becomes owner of cloned trip
INSERT INTO trips (created_by, name, description, ...)
SELECT new_user_id, CONCAT(name, ' (Copy)'), description, ...
FROM trips WHERE id = source_trip_id;
```

**3. Trip Statistics & Analytics**
```sql
-- Add to trips table for public engagement
ALTER TABLE trips ADD COLUMN views_count INTEGER DEFAULT 0;
ALTER TABLE trips ADD COLUMN clones_count INTEGER DEFAULT 0;
ALTER TABLE trips ADD COLUMN likes_count INTEGER DEFAULT 0;

-- Track trip views
CREATE TABLE trip_views (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    viewer_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    viewer_ip_address INET,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trip_views_trip_id ON trip_views(trip_id);
CREATE INDEX idx_trip_views_user_id ON trip_views(viewer_user_id);
CREATE INDEX idx_trip_views_ip ON trip_views(viewer_ip_address);
CREATE INDEX idx_trip_views_date ON trip_views(viewed_at);

-- Track trip likes
CREATE TABLE trip_likes (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trip_id, user_id)
);

CREATE INDEX idx_trip_likes_trip_id ON trip_likes(trip_id);
CREATE INDEX idx_trip_likes_user_id ON trip_likes(user_id);
```

**4. Public Trip Comments (Optional - Future Phase)**
```sql
CREATE TABLE trip_comments (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_comment_id BIGINT REFERENCES trip_comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);
```

#### Authorization for Public Trips

```python
def check_trip_view_access(trip_id: int, current_user: User | None, db: Session):
    """
    Check if user can view trip based on visibility.
    Returns trip if authorized, raises 403/404 if not.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Public trips - anyone can view
    if trip.visibility == 'public':
        # Increment view counter
        trip.views_count += 1
        db.commit()
        return trip

    # Unlisted trips - anyone with link can view
    if trip.visibility == 'unlisted':
        return trip

    # Private trips - only collaborators
    if trip.visibility == 'private':
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")

        is_collaborator = db.query(TripCollaborator).filter(
            TripCollaborator.trip_id == trip_id,
            TripCollaborator.user_id == current_user.id
        ).first()

        if not is_collaborator:
            raise HTTPException(status_code=403, detail="Access denied")

        return trip
```

#### Public Trip API Endpoints

```
# Browse public trips
GET    /trips/public
Query: ?destination=France&tags=adventure&sort=-views_count&page=1
Response: Paginated list of public trips

# Get featured trips
GET    /trips/featured
Response: Curated list of featured public trips

# Search public trips
GET    /trips/search?q=europe+backpacking
Response: Search results with relevance ranking

# Clone public trip
POST   /trips/{trip_id}/clone
Response: New trip (copy) owned by current user

# Like public trip
POST   /trips/{trip_id}/like
DELETE /trips/{trip_id}/like

# Get trip statistics
GET    /trips/{trip_id}/stats
Response: { views, clones, likes, created_at, collaborators_count }

# Get trending trips
GET    /trips/trending
Query: ?period=week&limit=10
Response: Top trips by views/clones/likes
```

#### Benefits of Open Source Trips

✅ **Community Contribution**: Users help others plan similar trips
✅ **Travel Inspiration**: Browse real itineraries from travelers
✅ **Trip Templates**: Clone and customize existing trips
✅ **Reputation System**: Users gain recognition for helpful itineraries
✅ **Social Proof**: Popular trips validated by community engagement
✅ **Knowledge Sharing**: Learn from others' experiences and budgets

---

### **Entity: TripDays**

```sql
CREATE TYPE transit_mode AS ENUM (
    'flight', 'train', 'bus', 'car', 'boat',
    'walk', 'bicycle', 'motorcycle', 'other'
);

CREATE TYPE trip_day_type AS ENUM (
    'transit',        -- Travel day (flights, long trains, driving)
    'sightseeing',    -- Visiting landmarks, attractions, tours
    'leisure',        -- Relaxing, unstructured, beach day
    'activity',       -- Specific activities (hiking, diving, skiing)
    'cultural',       -- Museums, theaters, galleries, cultural experiences
    'adventure',      -- Outdoor activities, sports, adrenaline
    'culinary',       -- Food tours, cooking classes, restaurant hopping
    'shopping',       -- Shopping focused day
    'business',       -- Work-related (conferences, meetings)
    'exploration',    -- Wandering, discovering neighborhoods
    'rest',           -- Recovery day, sleep in, minimal plans
    'mixed'           -- Combination of multiple types
);

CREATE TABLE trip_days (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,

    -- Day Info
    date DATE NOT NULL,
    day_number INTEGER NOT NULL, -- Calculated: 1, 2, 3...
    day_type trip_day_type DEFAULT 'mixed',
    title VARCHAR(200),

    -- Location
    place VARCHAR(200) NOT NULL,        -- Display name (e.g., "Eiffel Tower, Paris")
    place_city VARCHAR(100),            -- Structured: City name
    place_country VARCHAR(100),         -- Structured: Country name
    timezone VARCHAR(50) NOT NULL,      -- IANA timezone for this location
    coordinates POINT,                  -- Lat/long coordinates

    -- Transit (Travel TO this location)
    transit_mode transit_mode,
    transit_details JSONB, -- Flexible structure for different transit types
    arrival_time BIGINT,
    departure_time BIGINT,

    -- Accommodation
    accommodation_name VARCHAR(200),
    accommodation_address TEXT,
    accommodation_checkin BIGINT,
    accommodation_checkout BIGINT,
    accommodation_confirmation VARCHAR(100),

    -- Planning
    activities JSONB, -- Array of activity objects
    bookings JSONB, -- Array of booking references
    weather_forecast JSONB,

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(trip_id, date),
    CONSTRAINT valid_day_number CHECK (day_number > 0),
    CONSTRAINT valid_times CHECK (
        arrival_time IS NULL OR departure_time IS NULL OR
        departure_time >= arrival_time
    )
);

-- Indexes
CREATE INDEX idx_trip_days_trip_id ON trip_days(trip_id);
CREATE INDEX idx_trip_days_date ON trip_days(date);
CREATE INDEX idx_trip_days_trip_date ON trip_days(trip_id, date);
CREATE INDEX idx_trip_days_trip_day_number ON trip_days(trip_id, day_number);
CREATE INDEX idx_trip_days_day_type ON trip_days(day_type);
CREATE INDEX idx_trip_days_trip_type ON trip_days(trip_id, day_type);
CREATE INDEX idx_trip_days_location ON trip_days(place_country, place_city);
CREATE INDEX idx_trip_days_activities ON trip_days USING GIN(activities);
```

**Design Decisions:**
- `DATE` type for day date (simpler than timestamp for day-level)
- `day_number` auto-calculated for easy ordering
- **Day type classification**:
  - `day_type` enum categorizes the day's primary purpose
  - 12 types covering all travel scenarios (transit, sightseeing, leisure, etc.)
  - Defaults to 'mixed' for days with multiple activities
  - Enables filtering ("show me all sightseeing days") and statistics
  - Helps with trip planning and balance (not too many transit days!)
- **Location fields**:
  - `place`: User-friendly display name (e.g., "Eiffel Tower, Paris")
  - `place_city`, `place_country`: Structured fields for aggregation/search
  - Used to auto-calculate trip-level destinations (countries_visited, cities_visited)
- JSONB for flexible nested data (transit_details, activities)
- Separate accommodation fields (commonly queried)
- `UNIQUE(trip_id, date)` prevents duplicate days
- GIN index on JSONB for efficient JSON queries

**JSONB Structure Examples:**

```json
// transit_details
{
  "flight": {
    "airline": "United Airlines",
    "flight_number": "UA123",
    "confirmation": "ABC123",
    "departure_airport": "SFO",
    "arrival_airport": "LAX",
    "seat": "12A"
  }
}

// activities
[
  {
    "time": 1730826000,
    "type": "tour",
    "name": "City Walking Tour",
    "booking_url": "https://...",
    "cost": 50.00,
    "confirmation": "XYZ789"
  }
]
```

---

### **Trip Day Types: Categorizing Days**

Each day in a trip has a different purpose. Day types help users organize, filter, and balance their itineraries.

#### Day Type Categories

| Type | Purpose | Examples |
|------|---------|----------|
| **transit** | Travel days | Long flights, train journeys, road trips |
| **sightseeing** | Tourist attractions | Eiffel Tower, museums, landmarks |
| **leisure** | Relaxation | Beach days, pool time, unstructured |
| **activity** | Specific activities | Scuba diving, skiing, hot air balloon |
| **cultural** | Cultural experiences | Theater, concerts, art galleries, local festivals |
| **adventure** | Outdoor/adrenaline | Hiking, rafting, bungee jumping, zip-lining |
| **culinary** | Food-focused | Food tours, cooking classes, wine tasting |
| **shopping** | Shopping | Markets, malls, souvenir hunting |
| **business** | Work-related | Conferences, client meetings, networking |
| **exploration** | Wandering | Discovering neighborhoods, getting lost |
| **rest** | Recovery | Sleep in, catch up on rest, no plans |
| **mixed** | Combination | Multiple activities, varied day |

---

#### Real-World Examples

**Example 1: 10-Day Europe Trip**
```
Day 1: transit      - Flight NYC → Paris
Day 2: rest         - Recover from jet lag
Day 3: sightseeing  - Eiffel Tower, Louvre, Notre Dame
Day 4: cultural     - Versailles Palace, Opera
Day 5: culinary     - Food tour in Le Marais
Day 6: transit      - Train to Amsterdam
Day 7: exploration  - Wander canals, neighborhoods
Day 8: sightseeing  - Anne Frank House, Van Gogh Museum
Day 9: leisure      - Vondelpark, cafes
Day 10: transit     - Flight back home
```

**Day Type Breakdown:**
- Transit: 3 days (30%)
- Sightseeing: 2 days (20%)
- Cultural: 1 day (10%)
- Culinary: 1 day (10%)
- Exploration: 1 day (10%)
- Leisure: 1 day (10%)
- Rest: 1 day (10%)

**Example 2: Adventure Trip**
```
Day 1: transit      - Travel to Queenstown, NZ
Day 2: activity     - Bungee jumping
Day 3: adventure    - Skydiving
Day 4: adventure    - Hiking Milford Sound
Day 5: leisure      - Relax by lake
Day 6: activity     - Jet boating
Day 7: transit      - Return home
```

---

#### Use Cases

**1. Trip Planning Balance**
```python
# Check if trip has too many transit days
def check_trip_balance(trip_id: int, db: Session):
    day_counts = db.query(
        TripDay.day_type,
        func.count(TripDay.id).label('count')
    ).filter(
        TripDay.trip_id == trip_id
    ).group_by(TripDay.day_type).all()

    total_days = sum(count for _, count in day_counts)

    # Warning if more than 30% transit days
    transit_days = next((count for type, count in day_counts if type == 'transit'), 0)
    if transit_days / total_days > 0.3:
        return "Consider reducing transit days for better experience"
```

**2. Filter Days**
```sql
-- Show all sightseeing days
SELECT * FROM trip_days
WHERE trip_id = 1
  AND day_type = 'sightseeing'
ORDER BY date;

-- Show active days (activities + adventure)
SELECT * FROM trip_days
WHERE trip_id = 1
  AND day_type IN ('activity', 'adventure')
ORDER BY date;
```

**3. Trip Statistics**
```sql
-- Day type breakdown for trip
SELECT
    day_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM trip_days
WHERE trip_id = 1
GROUP BY day_type
ORDER BY count DESC;

-- Result:
-- sightseeing | 4 | 40.0%
-- leisure     | 2 | 20.0%
-- transit     | 2 | 20.0%
-- cultural    | 1 | 10.0%
-- rest        | 1 | 10.0%
```

**4. Public Trip Search**
```sql
-- Find adventure-heavy trips
SELECT t.*
FROM trips t
JOIN trip_days td ON t.id = td.trip_id
WHERE t.visibility = 'public'
  AND td.day_type IN ('adventure', 'activity')
GROUP BY t.id
HAVING COUNT(td.id) >= 3  -- At least 3 adventure days
ORDER BY t.views_count DESC;
```

---

#### Display in UI

**Trip Card:**
```
Europe Adventure
📍 Paris, France + 2 more
🗓️ 10 days
🎯 Sightseeing 40% • Cultural 20% • Food 20%
```

**Daily Itinerary:**
```
Day 1 - Transit Day 🚂
  Flight NYC → Paris

Day 2 - Rest & Recover 😴
  Sleep in, gentle exploration

Day 3 - Sightseeing 🏛️
  Eiffel Tower, Louvre, Notre Dame

Day 4 - Culinary Experience 🍷
  Food tour in Le Marais
```

**Trip Planning Helper:**
```
Your trip balance:
━━━━━━━━━━━━━━━━━━━━━━━━━
Transit     ████░░░░░░  30% ⚠️ Consider reducing
Sightseeing ███░░░░░░░  20%
Cultural    ██░░░░░░░░  10%
Leisure     ██░░░░░░░░  10%
Rest        ██░░░░░░░░  10%

💡 Tip: Add more leisure days for better recovery
```

---

#### Benefits

✅ **Better Planning**: Ensure balanced itinerary (not all transit!)
✅ **Easy Filtering**: "Show me all sightseeing days"
✅ **Statistics**: Understand trip composition at a glance
✅ **Discovery**: "Find adventure-heavy trips" in public search
✅ **Templates**: Clone trip patterns ("70% adventure, 30% leisure")
✅ **Pacing**: Identify if trip is too intense or too relaxed

---

#### Smart Defaults

```python
def suggest_day_type(trip_day: TripDay) -> str:
    """Auto-suggest day type based on other fields."""

    # Has transit mode? Likely transit day
    if trip_day.transit_mode in ['flight', 'train', 'bus']:
        return 'transit'

    # Has accommodation check-in? Likely arrival/transit
    if trip_day.accommodation_checkin:
        return 'transit'

    # Has activities in JSONB?
    if trip_day.activities:
        activity_types = extract_activity_types(trip_day.activities)

        if 'museum' in activity_types or 'landmark' in activity_types:
            return 'sightseeing'
        elif 'hiking' in activity_types or 'diving' in activity_types:
            return 'adventure'
        elif 'restaurant' in activity_types or 'food_tour' in activity_types:
            return 'culinary'

    # Default to mixed
    return 'mixed'
```

---

### **Entity: Expenses**

```sql
CREATE TYPE expense_category AS ENUM (
    'accommodation', 'food', 'transport', 'activities',
    'shopping', 'health', 'visa', 'insurance', 'other'
);

CREATE TYPE payment_method AS ENUM (
    'cash', 'credit_card', 'debit_card', 'digital_wallet',
    'bank_transfer', 'other'
);

CREATE TABLE expenses (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    trip_day_id BIGINT REFERENCES trip_days(id) ON DELETE SET NULL,

    -- Amount Info
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    amount_in_base_currency NUMERIC(12, 2), -- Converted to user's default
    exchange_rate NUMERIC(12, 6),

    -- Category
    category expense_category NOT NULL,
    subcategory VARCHAR(100),

    -- Details
    description TEXT NOT NULL,
    merchant VARCHAR(200),
    location VARCHAR(200),

    -- Payment
    payment_method payment_method NOT NULL,

    -- Receipt
    receipt_url TEXT,
    receipt_thumbnail_url TEXT,

    -- Date
    expense_date BIGINT NOT NULL, -- Unix timestamp

    -- Flags
    is_reimbursable BOOLEAN DEFAULT FALSE,
    is_business BOOLEAN DEFAULT FALSE,
    is_shared BOOLEAN DEFAULT FALSE,
    split_details JSONB, -- For shared expenses

    -- Notes
    notes TEXT,
    tags TEXT[],

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_amount CHECK (amount > 0),
    CONSTRAINT valid_exchange_rate CHECK (
        exchange_rate IS NULL OR exchange_rate > 0
    )
);

-- Indexes
CREATE INDEX idx_expenses_user_id ON expenses(user_id);
CREATE INDEX idx_expenses_trip_id ON expenses(trip_id);
CREATE INDEX idx_expenses_trip_day_id ON expenses(trip_day_id);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_trip_date ON expenses(trip_id, expense_date);
CREATE INDEX idx_expenses_tags ON expenses USING GIN(tags);

-- Partial indexes for common queries
CREATE INDEX idx_expenses_reimbursable ON expenses(trip_id)
    WHERE is_reimbursable = TRUE;
CREATE INDEX idx_expenses_business ON expenses(trip_id)
    WHERE is_business = TRUE;
```

**Design Decisions:**
- Store both original and converted amounts for accuracy
- `NUMERIC` for money to avoid floating point errors
- Track exchange rate for historical accuracy
- JSONB for flexible split expense data
- Partial indexes for filtered queries (reimbursable, business)
- `ON DELETE SET NULL` for trip_day (preserve expense if day deleted)
- Array of tags for flexible categorization

**split_details JSONB Example:**
```json
{
  "total_people": 3,
  "splits": [
    {"user_id": 1, "amount": 50.00, "paid": true},
    {"user_id": 2, "amount": 50.00, "paid": false}
  ]
}
```

---

### **Entity: Photos**

```sql
CREATE TABLE photos (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    trip_day_id BIGINT REFERENCES trip_days(id) ON DELETE SET NULL,

    -- File Info
    file_url TEXT NOT NULL,
    thumbnail_url TEXT,
    original_filename VARCHAR(255),
    file_size BIGINT NOT NULL, -- Bytes
    mime_type VARCHAR(50) NOT NULL,

    -- Image Dimensions
    width INTEGER,
    height INTEGER,

    -- Metadata
    title VARCHAR(200),
    description TEXT,
    caption TEXT,

    -- EXIF Data (extracted from image)
    taken_at BIGINT, -- Original photo timestamp
    camera_make VARCHAR(100),
    camera_model VARCHAR(100),

    -- Location (from EXIF or manual)
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    location_name VARCHAR(200),
    altitude NUMERIC(8, 2),

    -- Organization
    display_order INTEGER DEFAULT 0,
    is_cover_photo BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    tags TEXT[],

    -- Processing Status
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_file_size CHECK (file_size > 0),
    CONSTRAINT valid_coordinates CHECK (
        (latitude IS NULL AND longitude IS NULL) OR
        (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
    )
);

-- Indexes
CREATE INDEX idx_photos_user_id ON photos(user_id);
CREATE INDEX idx_photos_trip_id ON photos(trip_id);
CREATE INDEX idx_photos_trip_day_id ON photos(trip_day_id);
CREATE INDEX idx_photos_trip_order ON photos(trip_id, display_order);
CREATE INDEX idx_photos_taken_at ON photos(taken_at);
CREATE INDEX idx_photos_location ON photos(latitude, longitude)
    WHERE latitude IS NOT NULL;
CREATE INDEX idx_photos_tags ON photos USING GIN(tags);
CREATE INDEX idx_photos_favorites ON photos(trip_id)
    WHERE is_favorite = TRUE;
```

**Design Decisions:**
- Store both full and thumbnail URLs for performance
- NUMERIC for coordinates (7 decimal places = ~1cm precision)
- Separate EXIF fields for queryability
- Processing status for async thumbnail generation
- `display_order` for custom sorting
- Constraint validation for coordinate ranges
- GIN index on tags for efficient tag searches

---

### **Entity: Notes**

```sql
CREATE TYPE note_type AS ENUM (
    'general', 'highlight', 'tip', 'warning',
    'restaurant', 'activity', 'memory'
);

CREATE TABLE notes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    trip_day_id BIGINT REFERENCES trip_days(id) ON DELETE SET NULL,

    -- Content
    title VARCHAR(200),
    content TEXT NOT NULL,
    note_type note_type DEFAULT 'general',

    -- Rating & Mood
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    mood VARCHAR(50), -- 'happy', 'excited', 'tired', etc.
    mood_emoji VARCHAR(10),

    -- Organization
    is_pinned BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    tags TEXT[],

    -- Rich Content
    mentioned_places TEXT[], -- Places mentioned in note
    mentioned_people TEXT[], -- People mentioned

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Full-Text Search
    content_tsv TSVECTOR -- For PostgreSQL full-text search
);

-- Indexes
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_trip_id ON notes(trip_id);
CREATE INDEX idx_notes_trip_day_id ON notes(trip_day_id);
CREATE INDEX idx_notes_type ON notes(note_type);
CREATE INDEX idx_notes_pinned ON notes(trip_id) WHERE is_pinned = TRUE;
CREATE INDEX idx_notes_tags ON notes USING GIN(tags);

-- Full-text search index
CREATE INDEX idx_notes_content_search ON notes USING GIN(content_tsv);

-- Trigger for auto-updating full-text search vector
CREATE TRIGGER notes_content_tsv_update
    BEFORE INSERT OR UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(content_tsv, 'pg_catalog.english', title, content);
```

**Design Decisions:**
- Simple text content (can extend to markdown/rich text later)
- Full-text search with `TSVECTOR` for efficient searching
- Arrays for tags, places, people (flexible categorization)
- Rating optional (1-5 scale standard)
- Auto-updating search vector with trigger
- Separate mood fields (emoji + text for flexibility)

---

### **Entity: Packing Lists & Items**

```sql
CREATE TABLE packing_lists (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,

    name VARCHAR(200) DEFAULT 'Packing List',
    description TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE packing_category AS ENUM (
    'clothing', 'shoes', 'electronics', 'documents',
    'toiletries', 'medications', 'gear', 'other'
);

CREATE TYPE packing_priority AS ENUM ('low', 'medium', 'high', 'essential');

CREATE TABLE packing_items (
    id BIGSERIAL PRIMARY KEY,
    packing_list_id BIGINT NOT NULL REFERENCES packing_lists(id) ON DELETE CASCADE,

    -- Item Details
    item_name VARCHAR(200) NOT NULL,
    category packing_category NOT NULL,
    subcategory VARCHAR(100),

    -- Quantity
    quantity INTEGER DEFAULT 1,

    -- Status
    is_packed BOOLEAN DEFAULT FALSE,
    priority packing_priority DEFAULT 'medium',

    -- Additional Info
    notes TEXT,
    weight_grams INTEGER, -- For luggage weight tracking

    -- Organization
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    packed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_quantity CHECK (quantity > 0)
);

-- Indexes
CREATE INDEX idx_packing_lists_trip_id ON packing_lists(trip_id);
CREATE INDEX idx_packing_items_list_id ON packing_items(packing_list_id);
CREATE INDEX idx_packing_items_category ON packing_items(category);
CREATE INDEX idx_packing_items_packed ON packing_items(packing_list_id, is_packed);
```

**Design Decisions:**
- Separate lists for flexibility (can have multiple lists per trip)
- ENUMs for categories and priorities for consistency
- `weight_grams` for luggage tracking feature
- `packed_at` timestamp to track packing progress over time
- Simple structure (can extend with templates later)

---

### **Entity: User Sessions (for JWT refresh tokens)**

```sql
CREATE TABLE user_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token Info
    refresh_token_hash VARCHAR(255) NOT NULL UNIQUE,
    access_token_jti VARCHAR(255), -- JWT ID for blacklisting

    -- Session Info
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50), -- 'web', 'mobile', 'desktop'

    -- Expiry
    expires_at TIMESTAMP NOT NULL,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_refresh_token ON user_sessions(refresh_token_hash);
CREATE INDEX idx_sessions_active ON user_sessions(user_id, is_active)
    WHERE expires_at > CURRENT_TIMESTAMP;
CREATE INDEX idx_sessions_expires ON user_sessions(expires_at)
    WHERE is_active = TRUE;
```

**Design Decisions:**
- Store refresh tokens securely (hashed)
- Track device info for security monitoring
- `INET` type for IP addresses (PostgreSQL native)
- Expiry index for cleanup job
- Can revoke specific sessions or all user sessions

---

### **No Email Verification Tokens Needed**

**Google OAuth handles all email verification.** No need for:
- ❌ Email verification tokens
- ❌ Password reset tokens
- ❌ Email change tokens

Google provides verified email addresses, eliminating the need for a verification token system.

---

### 2.3 Database Relationships (Entity-Relationship Diagram)

```
┌─────────────┐                    ┌─────────────┐
│    users    │                    │    trips    │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │ N                                │ 1
       │         ┌──────────────────┐     │
       └────────►│trip_collaborators│◄────┘
                 │  (junction)      │
                 │  - role          │
                 │  - invitation    │
                 └──────────────────┘
                          │
                          │ The trip has multiple collaborators
                          │ (family, couple, friends)
                          │
                          ↓
                    ┌─────────────┐
                    │    trips    │
                    └──────┬──────┘
                           │ 1
                           │
                           ├──────────┬───────────┬────────────┐
                           │          │           │            │
                           │ N        │ N         │ N          │ N
                           ↓          ↓           ↓            ↓
                    ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
                    │trip_days │ │ expenses│ │ photos  │ │  notes   │
                    └────┬─────┘ └─────────┘ └─────────┘ └──────────┘
                         │ 1
                         │
                         │ N
                         ├──────────┬──────────┐
                         ↓          ↓          ↓
                    ┌─────────┐ ┌────────┐ ┌───────┐
                    │ photos  │ │ notes  │ │expenses│
                    └─────────┘ └────────┘ └───────┘

                    ┌─────────────┐
                    │    trips    │
                    └──────┬──────┘
                           │ 1
                           │
                           │ N
                           ↓
                    ┌──────────────┐
                    │ packing_lists│
                    └──────┬───────┘
                           │ 1
                           │
                           │ N
                           ↓
                    ┌──────────────┐
                    │packing_items │
                    └──────────────┘
```

**Key Relationship Rules:**

1. **Users ↔ Trips** (N:N through trip_collaborators)
   - Many-to-many relationship allows multiple users per trip
   - Each collaborator has a role (owner, editor, viewer)
   - User deleted → Removed from collaborators (CASCADE)
   - **User deletion smart handling:**
     - Private trips without remaining owners → Deleted
     - Public/unlisted trips → First editor promoted to owner, trip persists
   - Trip deleted → Remove all collaborators (CASCADE)

2. **Trips → Trip Creator** (N:1, SET NULL)
   - Each trip has ONE original creator (created_by field, can be NULL)
   - Creator deleted → created_by set to NULL, trip persists if public
   - Creator automatically becomes 'owner' collaborator on trip creation

3. **Trip → TripDays** (1:N, CASCADE)
   - Trip deleted → All trip days deleted

4. **Trip → Expenses/Photos/Notes** (1:N, CASCADE)
   - Trip deleted → All associated data deleted
   - Each expense/photo/note tracks which user added it (user_id)

5. **TripDay → Expenses/Photos/Notes** (1:N, SET NULL)
   - TripDay deleted → Keep data but set trip_day_id to NULL

6. **Trip → PackingLists** (1:N, CASCADE)
   - Trip deleted → All packing lists deleted

---

### 2.4 Database Migrations Strategy

**Tool:** Alembic (SQLAlchemy migration tool)

**Migration Workflow:**
```bash
# Create new migration
alembic revision --autogenerate -m "Add expenses table"

# Review and edit migration file
# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Migration Naming Convention:**
```
YYYY_MM_DD_HHMM_description.py
Example: 2025_11_05_1400_add_expenses_table.py
```

**Best Practices:**
- Never edit applied migrations
- Always review auto-generated migrations
- Test migrations on copy of production data
- Include both upgrade() and downgrade()
- Keep migrations atomic (one logical change per migration)

---

### 2.5 Database Indexing Strategy

**Index Types Used:**

1. **B-Tree Indexes** (Default)
   - Single column: `CREATE INDEX idx_trips_user_id ON trips(user_id)`
   - Composite: `CREATE INDEX idx_trips_user_status ON trips(user_id, status)`
   - Use for: Equality, range queries, sorting

2. **GIN Indexes** (Generalized Inverted Index)
   - Arrays: `CREATE INDEX idx_trips_tags ON trips USING GIN(tags)`
   - JSONB: `CREATE INDEX idx_trip_days_activities ON trip_days USING GIN(activities)`
   - Full-text: `CREATE INDEX idx_notes_search ON notes USING GIN(content_tsv)`
   - Use for: Array containment, JSON queries, text search

3. **Partial Indexes**
   - `CREATE INDEX idx_trips_active ON trips(user_id) WHERE deleted_at IS NULL`
   - Use for: Commonly filtered subsets (active records, specific statuses)

4. **Unique Indexes**
   - `CREATE UNIQUE INDEX idx_users_email ON users(email)`
   - Enforces data integrity + provides index benefits

**Indexing Guidelines:**
- Index all foreign keys
- Index commonly queried columns
- Index columns used in WHERE, JOIN, ORDER BY
- Don't over-index (slows writes, uses space)
- Monitor query performance and add indexes as needed

---

## 3. API Design Patterns

### 3.1 RESTful API Design Principles

**Resource-Based URLs:**
```
✅ Good:
GET    /trips
GET    /trips/{trip_id}
POST   /trips
PUT    /trips/{trip_id}
DELETE /trips/{trip_id}

❌ Bad:
GET    /getTrips
POST   /createTrip
POST   /trip/delete
```

**Hierarchical Resources:**
```
GET    /trips/{trip_id}/days
GET    /trips/{trip_id}/expenses
GET    /trips/{trip_id}/photos
POST   /trips/{trip_id}/days

# Specific items can use direct access too
GET    /trip_days/{day_id}
PUT    /trip_days/{day_id}
```

---

### 3.2 API Response Structure

**Standard Success Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Europe Trip"
  },
  "meta": {
    "timestamp": 1730819200,
    "request_id": "req_abc123"
  }
}
```

**Paginated Response:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "timestamp": 1730819200,
    "request_id": "req_abc123"
  }
}
```

**Standard Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "name": ["This field is required"],
      "start_date": ["Must be before end_date"]
    },
    "request_id": "req_abc123"
  },
  "meta": {
    "timestamp": 1730819200
  }
}
```

**Error Codes:**
```python
# Authentication
AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
TOKEN_EXPIRED = "TOKEN_EXPIRED"
TOKEN_INVALID = "TOKEN_INVALID"
INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

# Validation
VALIDATION_ERROR = "VALIDATION_ERROR"
INVALID_INPUT = "INVALID_INPUT"
MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

# Resources
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

# Business Logic
INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"

# System
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
```

---

### 3.3 HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE (no body) |
| 400 | Bad Request | Validation error, invalid input |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists, state conflict |
| 422 | Unprocessable Entity | Semantic validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary unavailability |

---

### 3.4 API Versioning Strategy

**Decision: URL Path Versioning**

```
https://api.logbook.com/v1/trips
https://api.logbook.com/v2/trips
```

**Why not header versioning?**
- URL versioning is more visible and easier to use
- Better for API documentation
- Simpler for testing and debugging
- Standard practice for REST APIs

**Version Strategy:**
- Major version in URL (v1, v2)
- Minor changes backward compatible (no version change)
- Breaking changes require new major version
- Maintain previous version for 6 months after new release

---

### 3.5 Filtering, Sorting, and Pagination

**Query Parameter Conventions:**

**Filtering:**
```
GET /trips?status=ongoing
GET /trips?destination_country=France
GET /expenses?category=food&min_amount=50
GET /trips?start_date_after=1730000000
GET /trips?tags=beach,adventure
```

**Sorting:**
```
GET /trips?sort=start_date         # Ascending
GET /trips?sort=-start_date        # Descending (-)
GET /trips?sort=-created_at,name   # Multiple fields
```

**Pagination:**
```
# Offset-based (simple, for small datasets)
GET /trips?page=2&page_size=20

# Cursor-based (for large datasets, better performance)
GET /trips?cursor=eyJpZCI6MTAwfQ&limit=20
```

**Full Example:**
```
GET /expenses?trip_id=5&category=food&sort=-expense_date&page=1&page_size=20
```

---

### 3.6 Field Selection (Sparse Fieldsets)

**Query Parameter: `fields`**

```
# Only return specific fields
GET /trips?fields=id,name,start_date

# Exclude fields
GET /trips?fields=-description,-notes

# Include related resources
GET /trips?include=trip_days,expenses
```

**Implementation:**
```python
# Pydantic schema with flexibility
class TripResponse(BaseModel):
    id: int
    name: str
    start_date: Optional[int] = None
    # ... other fields

    class Config:
        from_attributes = True
        # Allow excluding fields dynamically
```

---

## 4. Authentication & Authorization

### 4.1 Authentication Strategy: Google OAuth 2.0

**Why Google OAuth?**
- ✅ **More secure**: No password storage, Google handles security
- ✅ **Faster implementation**: No email verification, password reset, etc.
- ✅ **Better UX**: One-click sign-in, no registration forms
- ✅ **Trust**: Users trust Google authentication
- ✅ **Always verified**: Google emails are verified by default
- ✅ **Profile data**: Get name, photo from Google automatically

**OAuth Flow: Authorization Code Grant**

**1. Google OAuth Token (from Google):**
```json
{
  "sub": "google_user_id_123456789",
  "email": "user@example.com",
  "email_verified": true,
  "name": "John Doe",
  "given_name": "John",
  "family_name": "Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "aud": "YOUR_GOOGLE_CLIENT_ID",
  "iss": "https://accounts.google.com",
  "iat": 1730819400,
  "exp": 1730823000
}
```

**2. Our JWT Access Token (issued after OAuth):**
```json
{
  "sub": "our_user_id_123",
  "google_id": "google_user_id_123456789",
  "email": "user@example.com",
  "type": "access",
  "exp": 1730823000,
  "iat": 1730819400,
  "jti": "unique_token_id"
}
```
- **Expiry:** 1 hour
- **Storage:** Memory or httpOnly cookie
- **Purpose:** API authentication after OAuth

**3. Our Refresh Token:**
```json
{
  "sub": "our_user_id_123",
  "type": "refresh",
  "exp": 1731424200,
  "iat": 1730819400,
  "jti": "unique_refresh_id"
}
```
- **Expiry:** 7 days
- **Storage:** httpOnly cookie (secure)
- **Purpose:** Get new access token without re-authentication

---

### 4.2 Google OAuth Authentication Flow

```
┌────────┐              ┌────────┐              ┌────────────┐
│ Client │              │  Our   │              │   Google   │
│        │              │ Server │              │   OAuth    │
└───┬────┘              └───┬────┘              └──────┬─────┘
    │                       │                          │
    │ 1. Click "Sign in    │                          │
    │     with Google"     │                          │
    │                       │                          │
    │ 2. GET /auth/google  │                          │
    ├──────────────────────►│                          │
    │                       │                          │
    │ 3. Redirect to Google OAuth                     │
    │◄──────────────────────┤                          │
    │                       │                          │
    │ 4. User authenticates with Google               │
    ├─────────────────────────────────────────────────►│
    │                       │                          │
    │                       │                          │ 5. User approves
    │                       │                          │
    │ 6. Redirect back with code                      │
    │◄─────────────────────────────────────────────────┤
    │   ?code=AUTH_CODE    │                          │
    │                       │                          │
    │ 7. Send code to backend                         │
    ├──────────────────────►│                          │
    │                       │                          │
    │                       │ 8. Exchange code for token
    │                       ├─────────────────────────►│
    │                       │                          │
    │                       │ 9. Google ID token       │
    │                       │   (with user profile)    │
    │                       │◄─────────────────────────┤
    │                       │                          │
    │                       │ 10. Verify Google token  │
    │                       │ 11. Get/create user      │
    │                       │     in our database      │
    │                       │ 12. Generate our JWT     │
    │                       │                          │
    │ 13. Response:         │                          │
    │   - access_token      │                          │
    │   - refresh_token     │                          │
    │   - user profile      │                          │
    │◄──────────────────────┤                          │
    │                       │                          │
    │ 14. GET /trips        │                          │
    │   Header:             │                          │
    │   Authorization:      │                          │
    │   Bearer {token}      │                          │
    ├──────────────────────►│                          │
    │                       │ 15. Verify our JWT       │
    │                       │ 16. Extract user_id      │
    │                       │ 17. Process request      │
    │                       │                          │
    │ 18. Response          │                          │
    │◄──────────────────────┤                          │
```

**Implementation Details:**

```python
# Backend OAuth handler
@router.get("/auth/google")
async def google_login(request: Request):
    """Redirect to Google OAuth"""
    redirect_uri = f"{settings.BASE_URL}/auth/google/callback"
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid email profile&"
        "access_type=offline"  # Get refresh token
    )
    return RedirectResponse(google_auth_url)

@router.get("/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""

    # 1. Exchange code for token
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{settings.BASE_URL}/auth/google/callback",
            "grant_type": "authorization_code"
        }
    )
    google_token = token_response.json()

    # 2. Verify and decode Google ID token
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    user_info = id_token.verify_oauth2_token(
        google_token['id_token'],
        google_requests.Request(),
        settings.GOOGLE_CLIENT_ID
    )

    # 3. Get or create user
    user = db.query(User).filter(
        User.google_id == user_info['sub']
    ).first()

    if not user:
        # Create new user from Google profile
        user = User(
            google_id=user_info['sub'],
            email=user_info['email'],
            email_verified=user_info['email_verified'],
            first_name=user_info.get('given_name'),
            last_name=user_info.get('family_name'),
            profile_photo_url=user_info.get('picture')
        )
        db.add(user)
        db.commit()

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # 4. Generate our JWT tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # 5. Store refresh token in database
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(session)
    db.commit()

    # 6. Return tokens
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback")
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800  # 7 days
    )
    return response
```

**No Password Security Needed!** 🎉
- ❌ No password hashing
- ❌ No password validation
- ❌ No password reset flow
- ❌ No email verification
- ✅ Google handles all security

---

### 4.3 Authorization Strategy: Collaborative Role-Based Access Control (RBAC)

**Collaborative Trip Model with Roles**

```python
from enum import Enum
from fastapi import HTTPException, status

class CollaboratorRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

# Permission checker
def check_trip_access(trip_id: int, user_id: int, required_role: CollaboratorRole, db: Session):
    """
    Check if user has access to trip with required role.
    Returns the collaborator record if authorized, raises 403 if not.
    """
    collaborator = db.query(TripCollaborator).filter(
        TripCollaborator.trip_id == trip_id,
        TripCollaborator.user_id == user_id
    ).first()

    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this trip"
        )

    # Role hierarchy: owner > editor > viewer
    role_hierarchy = {
        CollaboratorRole.OWNER: 3,
        CollaboratorRole.EDITOR: 2,
        CollaboratorRole.VIEWER: 1
    }

    if role_hierarchy[collaborator.role] < role_hierarchy[required_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You need {required_role} role for this action"
        )

    return collaborator

# Usage examples
async def get_trip(trip_id: int, current_user: User, db: Session):
    """Any collaborator can view trip"""
    check_trip_access(trip_id, current_user.id, CollaboratorRole.VIEWER, db)
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    return trip

async def update_trip(trip_id: int, data: TripUpdate, current_user: User, db: Session):
    """Only editors and owners can update trip"""
    check_trip_access(trip_id, current_user.id, CollaboratorRole.EDITOR, db)
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    # Update logic here
    return trip

async def delete_trip(trip_id: int, current_user: User, db: Session):
    """Only owners can delete trip"""
    check_trip_access(trip_id, current_user.id, CollaboratorRole.OWNER, db)
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    db.delete(trip)
    db.commit()

async def add_collaborator(
    trip_id: int,
    new_user_id: int,
    role: CollaboratorRole,
    current_user: User,
    db: Session
):
    """Only owners can add/remove collaborators"""
    check_trip_access(trip_id, current_user.id, CollaboratorRole.OWNER, db)

    # Add new collaborator
    collaborator = TripCollaborator(
        trip_id=trip_id,
        user_id=new_user_id,
        role=role,
        invited_by=current_user.id
    )
    db.add(collaborator)
    db.commit()
    return collaborator
```

**Permission Matrix:**

| Action | Owner | Editor | Viewer |
|--------|-------|--------|--------|
| View trip details | ✅ | ✅ | ✅ |
| View expenses/photos | ✅ | ✅ | ✅ |
| Add expenses/photos | ✅ | ✅ | ❌ |
| Edit trip details | ✅ | ✅ | ❌ |
| Edit trip days | ✅ | ✅ | ❌ |
| Delete expenses/photos | ✅ | ✅ | ❌ |
| Add collaborators | ✅ | ❌ | ❌ |
| Remove collaborators | ✅ | ❌ | ❌ |
| Change roles | ✅ | ❌ | ❌ |
| Delete trip | ✅ | ❌ | ❌ |

**Use Cases:**

1. **Couple Trip**: Both partners are 'owners' - equal control
2. **Family Trip**: Parents are 'owners', kids are 'viewers'
3. **Group Trip**: Organizer is 'owner', friends are 'editors'
4. **Shared Itinerary**: Trip planner is 'owner', clients are 'viewers'

---

### 4.5 Security Best Practices

**1. Token Security:**
- Never log tokens
- Use HTTPS only (no plain HTTP)
- Short-lived access tokens (1 hour)
- Rotate refresh tokens on use
- Store refresh tokens hashed in database
- Implement token blacklist for logout

**2. Rate Limiting:**
```python
# Per endpoint limits
/auth/login:       5 requests/minute
/auth/register:    3 requests/minute
/auth/refresh:     10 requests/minute
/api/* :          100 requests/minute (authenticated)
```

**3. CORS Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://logbook.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

**4. SQL Injection Prevention:**
- Use parameterized queries (SQLAlchemy handles this)
- Never build raw SQL from user input
- Validate all inputs with Pydantic

**5. XSS Prevention:**
- Sanitize user input (especially notes, descriptions)
- Escape HTML in responses
- Use Content Security Policy headers

---

## 5. File Storage Architecture

### 5.1 Storage Strategy

**Development: Local File System**
```
/uploads/
  ├── photos/
  │   ├── {user_id}/
  │   │   ├── {trip_id}/
  │   │   │   ├── {photo_id}_original.jpg
  │   │   │   ├── {photo_id}_thumb.jpg
  ├── receipts/
  │   ├── {user_id}/
  │   │   ├── {expense_id}_receipt.pdf
```

**Production: AWS S3 / CloudFlare R2**
```
s3://logbook-photos/
  ├── users/{user_id}/
  │   ├── trips/{trip_id}/
  │   │   ├── photos/
  │   │   │   ├── {photo_id}_original.jpg
  │   │   │   ├── {photo_id}_thumb.jpg

s3://logbook-documents/
  ├── users/{user_id}/
  │   ├── receipts/
  │   │   ├── {expense_id}_receipt.pdf
```

---

### 5.2 Storage Abstraction (Strategy Pattern)

```python
from abc import ABC, abstractmethod

class FileStorage(ABC):
    @abstractmethod
    async def upload(self, file, path: str) -> str:
        """Upload file and return URL"""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file"""
        pass

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Get file URL"""
        pass

class LocalFileStorage(FileStorage):
    async def upload(self, file, path: str) -> str:
        # Save to local filesystem
        return f"/static/{path}"

class S3FileStorage(FileStorage):
    async def upload(self, file, path: str) -> str:
        # Upload to S3
        return f"https://cdn.logbook.com/{path}"

# Factory pattern
def get_file_storage() -> FileStorage:
    if settings.ENVIRONMENT == "development":
        return LocalFileStorage()
    else:
        return S3FileStorage()
```

---

### 5.3 Image Processing Pipeline

```
Upload → Validate → Process → Store → Database

1. Upload (multipart/form-data)
   ↓
2. Validate
   - Check file type (JPEG, PNG, HEIC)
   - Check file size (< 10MB)
   - Scan for malware (optional)
   ↓
3. Process (Async via Celery)
   - Extract EXIF data
   - Generate thumbnail (200x200)
   - Optimize original (compress if needed)
   - Extract GPS coordinates
   ↓
4. Store
   - Upload original to S3
   - Upload thumbnail to S3
   - Get CDN URLs
   ↓
5. Database
   - Save photo record with URLs
   - Update processing_status
```

**Implementation:**
```python
# API endpoint
@router.post("/photos/")
async def upload_photo(
    file: UploadFile,
    trip_id: int,
    storage: FileStorage = Depends(get_file_storage),
    current_user: User = Depends(get_current_user),
):
    # Validate file
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, "Invalid file type")

    # Save original temporarily
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Queue processing job
    task = process_photo.delay(temp_path, trip_id, current_user.id)

    # Return immediately with pending status
    return {
        "status": "processing",
        "task_id": task.id,
        "message": "Photo is being processed"
    }

# Celery task
@celery_app.task
def process_photo(temp_path: str, trip_id: int, user_id: int):
    # Extract EXIF
    exif_data = extract_exif(temp_path)

    # Generate thumbnail
    thumb_path = generate_thumbnail(temp_path)

    # Upload to S3
    original_url = upload_to_s3(temp_path, f"photos/{user_id}/{uuid.uuid4()}.jpg")
    thumb_url = upload_to_s3(thumb_path, f"thumbs/{user_id}/{uuid.uuid4()}.jpg")

    # Save to database
    photo = Photo(
        user_id=user_id,
        trip_id=trip_id,
        file_url=original_url,
        thumbnail_url=thumb_url,
        taken_at=exif_data.get("taken_at"),
        latitude=exif_data.get("latitude"),
        longitude=exif_data.get("longitude"),
        processing_status="completed"
    )
    db.add(photo)
    db.commit()
```

---

### 5.4 CDN Strategy

**Production Setup:**
```
User Request → CloudFlare CDN → S3 Origin

Benefits:
- Global edge caching
- Faster delivery worldwide
- Reduced S3 costs (fewer origin requests)
- DDoS protection
```

**URL Structure:**
```
https://cdn.logbook.com/photos/{user_id}/{photo_id}_original.jpg
https://cdn.logbook.com/thumbs/{user_id}/{photo_id}_thumb.jpg
```

---

## 6. Caching Strategy

### 6.1 Caching Layers

```
┌──────────────────────────────────┐
│   Client-Side Cache (Browser)    │  304 Not Modified
└───────────────┬──────────────────┘
                │
┌───────────────▼──────────────────┐
│   CDN Cache (CloudFlare)         │  Static assets, images
└───────────────┬──────────────────┘
                │
┌───────────────▼──────────────────┐
│   Application Cache (Redis)      │  API responses, sessions
└───────────────┬──────────────────┘
                │
┌───────────────▼──────────────────┐
│   Database Query Cache           │  PostgreSQL query results
└───────────────┬──────────────────┘
                │
┌───────────────▼──────────────────┐
│   PostgreSQL Database            │  Source of truth
└──────────────────────────────────┘
```

---

### 6.2 Redis Caching Strategy

**Cache Keys Pattern:**
```
user:{user_id}
trip:{trip_id}
trip:{trip_id}:days
trip:{trip_id}:expenses:summary
user:{user_id}:trips:list
```

**Cache TTL:**
```python
USER_CACHE_TTL = 3600           # 1 hour
TRIP_CACHE_TTL = 1800           # 30 minutes
TRIP_LIST_CACHE_TTL = 300       # 5 minutes
EXPENSE_SUMMARY_CACHE_TTL = 600 # 10 minutes
```

**Caching Implementation:**
```python
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(key_pattern: str, ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_pattern.format(*args, **kwargs)

            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

# Usage
@cache_result("trip:{}", ttl=1800)
async def get_trip(trip_id: int):
    return db.query(Trip).filter(Trip.id == trip_id).first()
```

---

### 6.3 Cache Invalidation Strategy

**Write-Through Cache:**
```python
async def update_trip(trip_id: int, data: dict):
    # Update database
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    for key, value in data.items():
        setattr(trip, key, value)
    db.commit()

    # Invalidate cache
    redis_client.delete(f"trip:{trip_id}")
    redis_client.delete(f"user:{trip.user_id}:trips:list")

    return trip
```

**Cache Patterns:**

1. **Cache-Aside (Lazy Loading)**
   - Check cache first
   - If miss, query database
   - Store in cache
   - Return result

2. **Write-Through**
   - Write to database
   - Update/invalidate cache
   - Return result

3. **Write-Behind (for high write loads)**
   - Write to cache
   - Queue database write (async)
   - Return immediately

**For Logbook: Use Cache-Aside + Write-Through**
- Most reads benefit from caching
- Write-through keeps cache consistent
- Simple to implement and reason about

---

## 7. Error Handling & Validation

### 7.1 Exception Hierarchy

```python
# Custom exceptions
class LogbookException(Exception):
    """Base exception for all Logbook errors"""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationException(LogbookException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.details = details

class NotFoundException(LogbookException):
    def __init__(self, resource: str, resource_id: any):
        message = f"{resource} with id {resource_id} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND", 404)

class AuthenticationException(LogbookException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_FAILED", 401)

class AuthorizationException(LogbookException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "INSUFFICIENT_PERMISSIONS", 403)

class ConflictException(LogbookException):
    def __init__(self, message: str):
        super().__init__(message, "RESOURCE_CONFLICT", 409)
```

---

### 7.2 Global Exception Handler

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse

@app.exception_handler(LogbookException)
async def logbook_exception_handler(request: Request, exc: LogbookException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": getattr(exc, 'details', None),
                "request_id": request.state.request_id
            },
            "meta": {
                "timestamp": int(time.time())
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't expose internal errors to client
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request.state.request_id
            },
            "meta": {
                "timestamp": int(time.time())
            }
        }
    )
```

---

### 7.3 Request Validation (Pydantic)

**Schema Definition:**
```python
from pydantic import BaseModel, validator, Field
from datetime import datetime

class TripCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    start_date_timestamp: int = Field(..., gt=0)
    end_date_timestamp: int = Field(..., gt=0)
    budget_total: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")

    @validator('end_date_timestamp')
    def validate_date_range(cls, v, values):
        if 'start_date_timestamp' in values and v < values['start_date_timestamp']:
            raise ValueError('end_date must be after start_date')
        return v

    @validator('start_date_timestamp', 'end_date_timestamp')
    def validate_future_date(cls, v):
        # Optionally prevent dates too far in past/future
        min_timestamp = int(datetime(2000, 1, 1).timestamp())
        max_timestamp = int(datetime(2100, 1, 1).timestamp())
        if v < min_timestamp or v > max_timestamp:
            raise ValueError('Date must be between 2000 and 2100')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Europe Summer Trip",
                "description": "2 weeks exploring Europe",
                "start_date_timestamp": 1730000000,
                "end_date_timestamp": 1731000000,
                "budget_total": 5000.00,
                "currency": "USD"
            }
        }
```

**Custom Validators:**
```python
from pydantic import validator

class ExpenseCreate(BaseModel):
    trip_id: int
    amount: Decimal = Field(..., gt=0)
    currency: str
    category: ExpenseCategory
    description: str = Field(..., min_length=1, max_length=500)
    expense_date: int

    @validator('expense_date')
    def validate_expense_within_trip(cls, v, values):
        # This validation happens in business logic layer
        # where we have access to database
        return v
```

---

### 7.4 Business Logic Validation

```python
async def create_expense(
    expense_data: ExpenseCreate,
    db: Session,
    current_user: User
):
    # Get trip
    trip = db.query(Trip).filter(Trip.id == expense_data.trip_id).first()
    if not trip:
        raise NotFoundException("Trip", expense_data.trip_id)

    # Authorization check
    if trip.user_id != current_user.id:
        raise AuthorizationException("You don't have access to this trip")

    # Business rule validation
    if expense_data.expense_date < trip.start_date_timestamp:
        raise ValidationException(
            "Expense date is before trip start date",
            {"expense_date": "Must be within trip dates"}
        )

    # Warning if expense exceeds budget (don't fail, just warn)
    if trip.budget_total:
        total_expenses = calculate_total_expenses(trip.id, db)
        if total_expenses + expense_data.amount > trip.budget_total:
            # Could store this warning in a separate table
            # or return it in the response
            pass

    # Create expense
    expense = Expense(**expense_data.dict(), user_id=current_user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense
```

---

## 8. Performance & Scalability

### 8.1 Database Performance Optimization

**1. Connection Pooling:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Number of connections to maintain
    max_overflow=10,       # Additional connections when needed
    pool_pre_ping=True,    # Verify connection before using
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

**2. Query Optimization:**
```python
# ❌ Bad: N+1 query problem
trips = db.query(Trip).filter(Trip.user_id == user_id).all()
for trip in trips:
    # This creates a new query for each trip!
    trip_days = db.query(TripDay).filter(TripDay.trip_id == trip.id).all()

# ✅ Good: Use eager loading
from sqlalchemy.orm import joinedload

trips = db.query(Trip)\
    .options(joinedload(Trip.trip_days))\
    .filter(Trip.user_id == user_id)\
    .all()
```

**3. Pagination:**
```python
# Always paginate large result sets
def get_trips_paginated(user_id: int, page: int = 1, page_size: int = 20):
    query = db.query(Trip).filter(Trip.user_id == user_id)

    total = query.count()
    trips = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": trips,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
```

**4. Database Indexing** (covered in section 2.5)

---

### 8.2 API Performance

**1. Response Compression:**
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**2. Async Operations:**
```python
# Use async/await for I/O operations
@router.get("/trips/{trip_id}")
async def get_trip(trip_id: int, db: Session = Depends(get_db)):
    # Database operation
    trip = await get_trip_async(trip_id, db)

    # External API call
    weather = await fetch_weather_async(trip.destination_city)

    return {
        "trip": trip,
        "weather": weather
    }
```

**3. Caching** (covered in section 6)

**4. Database Read Replicas:**
```
Write Operations → Primary Database
Read Operations → Read Replicas (load balanced)
```

---

### 8.3 Scalability Architecture

**Horizontal Scaling:**
```
               ┌─────────────┐
User ────────► │Load Balancer│
               └──────┬──────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼───┐    ┌───▼────┐   ┌───▼────┐
   │ API 1  │    │ API 2  │   │ API 3  │
   └────┬───┘    └───┬────┘   └───┬────┘
        │            │            │
        └────────────┼────────────┘
                     │
            ┌────────▼────────┐
            │   PostgreSQL    │
            │   (Primary +    │
            │   Read Replicas)│
            └─────────────────┘
```

**Stateless API Design:**
- No session data stored in application
- JWT tokens carry user info
- Redis for shared state (if needed)
- Easy to add/remove API instances

---

### 8.4 Background Job Processing (Celery)

**Architecture:**
```
FastAPI → Queue (Redis) → Celery Workers → Process Jobs
```

**Use Cases:**
- Photo processing (thumbnail generation, EXIF extraction)
- Email sending (verification, password reset)
- Data export (PDF generation, Excel export)
- Currency rate updates
- Database cleanup jobs

**Implementation:**
```python
# celery_app.py
from celery import Celery

celery_app = Celery(
    "logbook",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# tasks.py
@celery_app.task
def process_photo(photo_id: int):
    # Heavy processing here
    pass

@celery_app.task
def send_email(to: str, subject: str, body: str):
    # Email sending
    pass

# Usage in API
@router.post("/photos/")
async def upload_photo(...):
    # Save initial record
    photo = Photo(...)
    db.add(photo)
    db.commit()

    # Queue processing
    process_photo.delay(photo.id)

    return {"status": "processing", "photo_id": photo.id}
```

---

## 9. Security Considerations

### 9.1 Security Checklist

**Authentication & Authorization:**
- [x] JWT with short expiry (1 hour)
- [x] Refresh token rotation
- [x] Password hashing with bcrypt
- [x] Rate limiting on auth endpoints
- [x] Email verification required
- [x] Strong password requirements
- [x] Token blacklist for logout

**Data Protection:**
- [x] HTTPS only in production
- [x] Parameterized queries (SQLAlchemy)
- [x] Input validation (Pydantic)
- [x] Output sanitization for user content
- [x] CORS with specific origins
- [x] CSP headers

**File Upload Security:**
- [x] File type validation (whitelist)
- [x] File size limits (10MB for photos)
- [x] Unique file names (prevent overwrites)
- [x] Virus scanning (optional but recommended)
- [x] Separate storage buckets for different file types

**Database Security:**
- [x] Least privilege database user
- [x] Connection encryption
- [x] Regular backups
- [x] Audit logging for sensitive operations

---

### 9.2 Rate Limiting Implementation

```python
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to routes
@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...

@app.get("/trips/")
@limiter.limit("100/minute")
async def get_trips(request: Request, ...):
    ...
```

---

### 9.3 Secrets Management

**Environment Variables (never commit):**
```python
# .env (not in git)
DATABASE_URL=postgresql://user:pass@localhost/logbook
SECRET_KEY=your-secret-key-here
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
REDIS_URL=redis://localhost:6379

# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    aws_access_key_id: str
    aws_secret_access_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

**Production: Use Secret Manager**
- AWS Secrets Manager
- HashiCorp Vault
- Environment variables from orchestration tool (K8s secrets)

---

## 10. Technology Stack Decisions

### 10.1 Backend Framework: FastAPI ✅

**Why FastAPI?**

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Performance | Very High | Medium | Medium |
| Async Support | Native | Limited | Limited |
| Type Safety | Excellent | None | Partial |
| Auto Documentation | Built-in | Manual | Django REST |
| Learning Curve | Low | Low | High |
| Microservices | Excellent | Good | Overkill |

**Decision: FastAPI**
- Modern, async-first framework
- Automatic API documentation (Swagger/ReDoc)
- Built-in request validation (Pydantic)
- Excellent performance
- Type hints throughout
- Great for microservices architecture

---

### 10.2 Database: PostgreSQL ✅

**Why PostgreSQL?**

| Feature | PostgreSQL | MySQL | MongoDB |
|---------|------------|-------|---------|
| JSON Support | Excellent (JSONB) | Limited | Native |
| Full-Text Search | Excellent | Basic | Good |
| Transactions | ACID | ACID | Limited |
| Scalability | Excellent | Excellent | Excellent |
| Geospatial | PostGIS | Limited | Native |
| Data Integrity | Excellent | Good | Flexible |

**Decision: PostgreSQL**
- Best-in-class JSONB support (for flexible fields)
- Advanced indexing (GIN, GIST, partial)
- Excellent full-text search
- Strong ACID compliance
- PostGIS for geospatial features
- Large community and ecosystem

---

### 10.3 ORM: SQLAlchemy 2.0 ✅

**Why SQLAlchemy?**
- Industry standard for Python
- Supports async (SQLAlchemy 2.0+)
- Powerful query builder
- Works with Alembic for migrations
- Connection pooling built-in
- Supports PostgreSQL-specific features

**Alternative Considered:**
- **Tortoise ORM**: Async-first but less mature
- **Raw SQL**: Too low-level, no abstraction benefits

---

### 10.4 Caching: Redis ✅

**Why Redis?**
- In-memory speed (microsecond latency)
- Rich data structures (strings, hashes, sets, sorted sets)
- TTL support built-in
- Pub/sub for real-time features
- Can be used as Celery broker
- Persistence options available

**Alternative Considered:**
- **Memcached**: Simpler but less features
- **In-memory cache**: Not shared across instances

---

### 10.5 Task Queue: Celery + Redis ✅

**Why Celery?**
- Mature and battle-tested
- Supports periodic tasks (cron-like)
- Good monitoring tools (Flower)
- Retry logic built-in
- Works with multiple brokers (Redis, RabbitMQ)

**Alternative Considered:**
- **RQ (Redis Queue)**: Simpler but less features
- **Dramatiq**: Modern but smaller community

---

### 10.6 File Storage: AWS S3 / CloudFlare R2 ✅

**Why S3/R2?**
- Highly durable (11 nines)
- Unlimited scalability
- CDN integration
- Lifecycle policies (auto-delete old files)
- Versioning support
- R2 has no egress fees (cost-effective)

**Alternative Considered:**
- **Local storage**: Not scalable, single point of failure
- **Digital Ocean Spaces**: Good but less ecosystem support

---

## 11. Data Flow Diagrams

### 11.1 User Registration Flow

```
┌────────┐           ┌────────┐           ┌──────────┐
│ Client │           │  API   │           │ Database │
└───┬────┘           └───┬────┘           └────┬─────┘
    │                    │                     │
    │ POST /auth/register│                     │
    │ {email, password}  │                     │
    ├───────────────────►│                     │
    │                    │                     │
    │                    │ Validate input      │
    │                    │ Hash password       │
    │                    │                     │
    │                    │ INSERT user         │
    │                    ├────────────────────►│
    │                    │                     │
    │                    │◄────────────────────┤
    │                    │ user_id = 123       │
    │                    │                     │
    │                    │ Generate token      │
    │                    │ Queue email         │
    │                    │                     │
    │ 201 Created        │                     │
    │ {user, token}      │                     │
    │◄───────────────────┤                     │
    │                    │                     │
    │                    ▼                     │
    │              ┌──────────┐                │
    │              │  Celery  │                │
    │              │  Worker  │                │
    │              └─────┬────┘                │
    │                    │                     │
    │                    │ Send verification   │
    │                    │ email               │
    │                    │                     │
    │                    ▼                     │
    │              ┌──────────┐                │
    │              │  Email   │                │
    │              │ Service  │                │
    │              └──────────┘                │
```

---

### 11.2 Trip Creation with Days Flow

```
Client                  API                 Database               Cache
  │                      │                      │                     │
  │ POST /trips          │                      │                     │
  ├─────────────────────►│                      │                     │
  │                      │ Validate data        │                     │
  │                      │                      │                     │
  │                      │ BEGIN TRANSACTION    │                     │
  │                      ├─────────────────────►│                     │
  │                      │                      │                     │
  │                      │ INSERT trip          │                     │
  │                      ├─────────────────────►│                     │
  │                      │◄─────────────────────┤                     │
  │                      │ trip_id = 1          │                     │
  │                      │                      │                     │
  │                      │ COMMIT               │                     │
  │                      ├─────────────────────►│                     │
  │                      │                      │                     │
  │                      │ Invalidate cache     │                     │
  │                      ├─────────────────────────────────────────►  │
  │                      │                      │                     │
  │ 201 Created          │                      │                     │
  │ {trip}               │                      │                     │
  │◄─────────────────────┤                      │                     │
  │                      │                      │                     │
  │ POST /trip_days      │                      │                     │
  │ {trip_id: 1, ...}    │                      │                     │
  ├─────────────────────►│                      │                     │
  │                      │ Validate date range  │                     │
  │                      │                      │                     │
  │                      │ INSERT trip_day      │                     │
  │                      ├─────────────────────►│                     │
  │                      │◄─────────────────────┤                     │
  │                      │                      │                     │
  │                      │ Invalidate caches    │                     │
  │                      ├─────────────────────────────────────────►  │
  │                      │                      │                     │
  │ 201 Created          │                      │                     │
  │◄─────────────────────┤                      │                     │
```

---

### 11.3 Photo Upload & Processing Flow

```
Client          API          Storage         Celery         Database
  │              │              │               │               │
  │ POST /photos │              │               │               │
  │ (multipart)  │              │               │               │
  ├─────────────►│              │               │               │
  │              │ Validate     │               │               │
  │              │ file type    │               │               │
  │              │              │               │               │
  │              │ Save temp    │               │               │
  │              │ file         │               │               │
  │              │              │               │               │
  │              │ Queue job    │               │               │
  │              ├──────────────────────────────►│               │
  │              │              │               │               │
  │ 202 Accepted │              │               │               │
  │ {task_id}    │              │               │               │
  │◄─────────────┤              │               │               │
  │              │              │               │               │
  │              │              │               │ Extract EXIF  │
  │              │              │               │ Generate      │
  │              │              │               │ thumbnail     │
  │              │              │               │               │
  │              │              │◄──────────────┤ Upload        │
  │              │              │   original    │ original      │
  │              │              │               │               │
  │              │              │◄──────────────┤ Upload        │
  │              │              │   thumbnail   │ thumbnail     │
  │              │              │               │               │
  │              │              │               │ INSERT photo  │
  │              │              │               ├──────────────►│
  │              │              │               │◄──────────────┤
  │              │              │               │               │
  │ GET /photos/ │              │               │               │
  │ {photo_id}   │              │               │               │
  ├─────────────►│              │               │               │
  │              │ Query        │               │               │
  │              ├──────────────────────────────────────────────►│
  │              │◄─────────────────────────────────────────────┤
  │              │ photo with URLs              │               │
  │              │              │               │               │
  │ 200 OK       │              │               │               │
  │ {photo}      │              │               │               │
  │◄─────────────┤              │               │               │
```

---

## 12. Deployment Architecture

### 12.1 Development Environment

```
Local Machine:
  ├── FastAPI (uvicorn --reload)
  ├── PostgreSQL (Docker or local)
  ├── Redis (Docker or local)
  ├── Celery Worker
  └── Local file storage
```

**Docker Compose for Dev:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: logbook_dev
      POSTGRES_USER: logbook
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://logbook:devpassword@postgres/logbook_dev
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  celery:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    volumes:
      - .:/app
    environment:
      DATABASE_URL: postgresql://logbook:devpassword@postgres/logbook_dev
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

---

### 12.2 Production Environment (AWS)

```
┌─────────────────────────────────────────────────────────┐
│                     CloudFlare CDN                      │
│                  (Static Assets, Images)                │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  AWS Load Balancer (ALB)                │
│                    (SSL Termination)                    │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼────────┐ ┌───▼────────┐
│   ECS Task 1    │ │ ECS Task 2 │ │ ECS Task 3 │
│  (FastAPI + API)│ │            │ │            │
└────────┬────────┘ └───┬────────┘ └───┬────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐  ┌────▼─────┐  ┌──────▼──────┐
│ RDS          │  │ ElastiCache│ │  S3 Bucket  │
│ PostgreSQL   │  │  (Redis)   │  │  (Photos)   │
│ Multi-AZ     │  │            │  │             │
└──────────────┘  └────────────┘  └─────────────┘
        │
┌───────▼──────┐
│ ECS Tasks    │
│ (Celery      │
│  Workers)    │
└──────────────┘
```

**Infrastructure Components:**

1. **Compute: AWS ECS Fargate**
   - Serverless container orchestration
   - Auto-scaling based on CPU/memory
   - No server management

2. **Database: Amazon RDS PostgreSQL**
   - Multi-AZ for high availability
   - Automated backups
   - Read replicas for scaling reads

3. **Cache: Amazon ElastiCache (Redis)**
   - Managed Redis service
   - Automatic failover
   - Cluster mode for scaling

4. **Storage: Amazon S3**
   - Highly durable object storage
   - Lifecycle policies for cost optimization
   - Versioning enabled

5. **CDN: CloudFlare**
   - Global edge network
   - DDoS protection
   - Web Application Firewall (WAF)

6. **Load Balancer: AWS ALB**
   - SSL/TLS termination
   - Path-based routing
   - Health checks

---

### 12.3 CI/CD Pipeline

```
GitHub → GitHub Actions → Build → Test → Deploy

Stages:
1. Lint & Format Check
   - Black, Ruff, mypy

2. Run Tests
   - pytest with coverage
   - Minimum 80% coverage

3. Build Docker Image
   - Tag with commit SHA
   - Push to ECR

4. Deploy to Staging
   - Run migrations
   - Deploy to staging ECS
   - Run smoke tests

5. Deploy to Production (manual approval)
   - Run migrations
   - Blue-green deployment
   - Monitor for errors
```

**GitHub Actions Workflow:**
```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS
        # Deployment steps here
```

---

### 12.4 Monitoring & Logging

**Monitoring Stack:**

1. **Application Performance Monitoring: Sentry**
   - Error tracking
   - Performance monitoring
   - Release tracking

2. **Logs: CloudWatch Logs**
   - Centralized logging
   - Log aggregation from all containers
   - Alerting on error patterns

3. **Metrics: CloudWatch Metrics + Datadog**
   - Custom metrics (API latency, request count)
   - Database metrics (connections, query time)
   - Infrastructure metrics (CPU, memory)

4. **Uptime Monitoring: UptimeRobot**
   - Endpoint availability checks
   - Alert on downtime

**Key Metrics to Track:**
```
Application:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active users

Database:
- Query time (ms)
- Connection pool usage
- Cache hit rate
- Slow queries

Infrastructure:
- CPU usage (%)
- Memory usage (%)
- Network I/O
- Disk I/O
```

---

## Summary & Key Decisions

### Critical Design Decisions

1. **Database: PostgreSQL**
   - JSONB for flexibility
   - Advanced indexing
   - Production-ready scalability

2. **Authentication: JWT**
   - Stateless, scalable
   - Short-lived access tokens
   - Secure refresh token rotation

3. **File Storage: S3 + CDN**
   - Scalable and durable
   - Global delivery via CDN
   - Cost-effective with R2

4. **Caching: Redis**
   - Application-level caching
   - Session management
   - Message broker for Celery

5. **Architecture: Layered + Async**
   - Clear separation of concerns
   - Async for I/O operations
   - Background jobs for heavy tasks

6. **API Design: RESTful**
   - Resource-based URLs
   - Standard HTTP methods
   - Consistent response format

### Trade-offs Made

| Decision | Benefit | Trade-off |
|----------|---------|-----------|
| PostgreSQL over MongoDB | Strong consistency, relations | Less flexible schema changes |
| JWT over sessions | Scalability | Can't revoke before expiry (needs blacklist) |
| Async FastAPI | High performance | More complex than sync |
| JSONB for flexible fields | Schema flexibility | Harder to query than columns |
| Celery for async jobs | Mature ecosystem | Additional infrastructure (Redis) |

---

## Additional API Endpoints for Collaborative Trips

### Trip Collaborators

```
# Get all collaborators for a trip
GET    /trips/{trip_id}/collaborators
Response: List of collaborators with roles

# Add collaborator to trip (owner only)
POST   /trips/{trip_id}/collaborators
Body: { user_id, role }
Response: Collaborator object

# Update collaborator role (owner only)
PUT    /trips/{trip_id}/collaborators/{user_id}
Body: { role }
Response: Updated collaborator

# Remove collaborator from trip (owner only)
DELETE /trips/{trip_id}/collaborators/{user_id}
Response: 204 No Content

# Get all trips user is collaborating on
GET    /users/me/trips
Query: ?role=owner&status=ongoing
Response: Paginated list of trips with user's role

# Leave trip (self-removal, except last owner)
DELETE /trips/{trip_id}/collaborators/me
Response: 204 No Content
```

**Business Rules:**
- At least one 'owner' must remain on a trip
- Cannot remove yourself if you're the last owner
- Owners can promote editors to owners
- Owners can demote other owners (as long as 1+ owner remains)

---

## Next Steps

1. **Review & Approve Design**
   - Stakeholder review
   - Technical team feedback
   - Security review

2. **Set Up Development Environment**
   - PostgreSQL + Redis
   - Database schema creation
   - Sample data seeding

3. **Implement Foundation (Phase 1)**
   - User model & auth
   - Trip & TripDay complete CRUD
   - **Trip collaborator management**
   - Database migrations
   - Basic tests

4. **Iterate & Improve**
   - Monitor performance
   - Gather feedback
   - Optimize bottlenecks

---

## Summary of Collaborative & Open Source Trip Features

### What Changed:

#### 1. **Multi-User Collaborative Trips**
**Database Schema:**
- `trips.user_id` → `trips.created_by` (original creator, can be NULL)
- Added `trip_collaborators` junction table (N:N relationship)
- Added `collaborator_role` enum (owner, editor, viewer)
- Added trigger to auto-add creator as owner
- Smart user deletion handling (preserve public trips)

**Authorization Model:**
- Role-based access control (RBAC)
- Permission hierarchy: owner > editor > viewer
- Permission matrix for all operations
- Separate view/edit permissions

**API Changes:**
- Collaborator management endpoints
- Updated trip queries to filter by collaboration
- User can see all trips they collaborate on

#### 2. **Open Source / Public Trips**
**Database Schema:**
- Changed `is_private` → `visibility` enum (private, unlisted, public)
- Added `is_featured` flag for curated trips
- Added engagement metrics: `views_count`, `clones_count`, `likes_count`
- Added `trip_views` table (analytics)
- Added `trip_likes` table (social engagement)
- Optional: `trip_comments` table (community feedback)

**Features:**
- Public trip gallery/discovery
- Trip cloning (fork) functionality
- Trip likes and engagement tracking
- Featured trips curation
- Search and browse public trips
- Trending trips

**User Deletion Strategy:**
- **Private trips**: Deleted if no owners remain
- **Public/unlisted trips**: Persist indefinitely
- **Public trips**: First editor promoted to owner
- **Created_by**: Set to NULL (trip remains accessible)

### Benefits:

#### Collaboration Benefits:
- ✅ Supports family trips (multiple owners)
- ✅ Supports couple trips (shared control)
- ✅ Supports group trips (organizer + participants)
- ✅ Flexible permission system
- ✅ Built-in invitation system for future
- ✅ Tracks who added each expense/photo/note

#### Open Source Benefits:
- ✅ **Community-driven**: Users contribute travel knowledge
- ✅ **Travel inspiration**: Browse real itineraries
- ✅ **Trip templates**: Clone and customize
- ✅ **Knowledge sharing**: Learn from others' experiences
- ✅ **Social proof**: Popular trips validated by community
- ✅ **Discovery**: Find trips by destination, tags, popularity
- ✅ **Persistence**: Public trips survive user deletion
- ✅ **Attribution**: Original creator tracked even after deletion

### Use Cases Enabled:

1. **Private Family Trip**: Parents as owners, kids as viewers, stays private
2. **Couple's Honeymoon**: Both partners as owners, shared planning
3. **Group Backpacking**: Organizer as owner, friends as editors
4. **Public Travel Guide**: Solo traveler shares detailed itinerary publicly
5. **Influencer Trip**: Travel blogger publishes trip, thousands clone it
6. **Travel Agency**: Agency creates trips as templates, clients clone them
7. **Open Source Planning**: Community collaboratively improves popular routes

---

**This system design document should be treated as a living document and updated as the system evolves.**
