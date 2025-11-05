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
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    profile_photo_url TEXT,
    bio TEXT,

    -- Preferences
    default_currency VARCHAR(3) DEFAULT 'USD',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',

    -- Account Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    -- Soft Delete
    deleted_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;
```

**Design Decisions:**
- `BIGSERIAL` for future-proof IDs (supports billions of records)
- Email as primary identifier (unique + indexed)
- Optional username for display purposes
- Soft delete with `deleted_at` to preserve data integrity
- Timezone-aware timestamps for global users
- Separate profile and preference fields for extensibility

---

### **Entity: Trips**

```sql
CREATE TYPE trip_status AS ENUM ('planning', 'ongoing', 'completed', 'cancelled');

CREATE TABLE trips (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Basic Info
    name VARCHAR(200) NOT NULL,
    description TEXT,
    cover_photo_url TEXT,

    -- Dates (stored as Unix timestamps for timezone independence)
    start_date_timestamp BIGINT NOT NULL,
    end_date_timestamp BIGINT NOT NULL,

    -- Location
    destination_country VARCHAR(100),
    destination_city VARCHAR(100),
    destination_coordinates POINT, -- PostGIS for geospatial queries

    -- Status & Visibility
    status trip_status DEFAULT 'planning',
    is_private BOOLEAN DEFAULT TRUE,

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
    CONSTRAINT valid_dates CHECK (end_date_timestamp >= start_date_timestamp),
    CONSTRAINT valid_budget CHECK (budget_total IS NULL OR budget_total >= 0)
);

-- Indexes
CREATE INDEX idx_trips_user_id ON trips(user_id);
CREATE INDEX idx_trips_status ON trips(status);
CREATE INDEX idx_trips_dates ON trips(start_date_timestamp, end_date_timestamp);
CREATE INDEX idx_trips_destination ON trips(destination_country, destination_city);
CREATE INDEX idx_trips_tags ON trips USING GIN(tags); -- For array searches
CREATE INDEX idx_trips_user_status ON trips(user_id, status) WHERE deleted_at IS NULL;
```

**Design Decisions:**
- Unix timestamps for date/time to avoid timezone issues
- `ENUM` for status to enforce valid states
- `NUMERIC(12,2)` for budget to avoid floating point errors
- PostgreSQL `POINT` type for coordinates (can upgrade to PostGIS)
- `TEXT[]` array for flexible tagging
- Composite indexes for common query patterns
- Foreign key with `CASCADE` to auto-cleanup user data

---

### **Entity: TripDays**

```sql
CREATE TYPE transit_mode AS ENUM (
    'flight', 'train', 'bus', 'car', 'boat',
    'walk', 'bicycle', 'motorcycle', 'other'
);

CREATE TABLE trip_days (
    id BIGSERIAL PRIMARY KEY,
    trip_id BIGINT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,

    -- Day Info
    date DATE NOT NULL,
    day_number INTEGER NOT NULL, -- Calculated: 1, 2, 3...
    title VARCHAR(200),

    -- Location
    place VARCHAR(200) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    coordinates POINT,

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
CREATE INDEX idx_trip_days_activities ON trip_days USING GIN(activities);
```

**Design Decisions:**
- `DATE` type for day date (simpler than timestamp for day-level)
- `day_number` auto-calculated for easy ordering
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

### **Entity: Email Verification Tokens**

```sql
CREATE TYPE token_type AS ENUM (
    'email_verification', 'password_reset', 'email_change'
);

CREATE TABLE verification_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,

    token_hash VARCHAR(255) NOT NULL UNIQUE,
    token_type token_type NOT NULL,

    -- Associated Data (JSON for flexibility)
    metadata JSONB, -- e.g., {"new_email": "new@example.com"}

    -- Expiry
    expires_at TIMESTAMP NOT NULL,

    -- Usage
    used_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_tokens_user_id ON verification_tokens(user_id);
CREATE INDEX idx_tokens_hash ON verification_tokens(token_hash)
    WHERE used_at IS NULL;
CREATE INDEX idx_tokens_expires ON verification_tokens(expires_at)
    WHERE used_at IS NULL;
```

---

### 2.3 Database Relationships (Entity-Relationship Diagram)

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │ 1
       │
       │ N
       ↓
┌─────────────┐        1        ┌──────────────┐
│    trips    │◄────────────────│ packing_lists│
└──────┬──────┘                 └──────┬───────┘
       │                               │
       │ 1                             │ 1
       │                               │
       │ N                             │ N
       ├──────────┐                    ↓
       │          │              ┌──────────────┐
       │          │              │packing_items │
       ↓          ↓              └──────────────┘
┌──────────┐  ┌─────────┐
│trip_days │  │ expenses│
└────┬─────┘  └─────────┘
     │ 1
     │
     │ N
     ├──────────┬──────────┐
     ↓          ↓          ↓
┌─────────┐ ┌────────┐ ┌───────┐
│ photos  │ │ notes  │ │expenses│
└─────────┘ └────────┘ └───────┘
```

**Key Relationship Rules:**

1. **User → Trips** (1:N, CASCADE)
   - User deleted → All trips deleted

2. **Trip → TripDays** (1:N, CASCADE)
   - Trip deleted → All trip days deleted

3. **Trip → Expenses/Photos/Notes** (1:N, CASCADE)
   - Trip deleted → All associated data deleted

4. **TripDay → Expenses/Photos/Notes** (1:N, SET NULL)
   - TripDay deleted → Keep data but set trip_day_id to NULL

5. **Trip → PackingLists** (1:N, CASCADE)
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

### 4.1 Authentication Strategy: JWT (JSON Web Tokens)

**Why JWT?**
- Stateless (no session storage needed)
- Scalable (works across multiple servers)
- Contains user info (reduces database queries)
- Standard and well-supported

**Token Structure:**

**Access Token:**
```json
{
  "sub": "user_id_123",
  "email": "user@example.com",
  "type": "access",
  "exp": 1730823000,
  "iat": 1730819400,
  "jti": "unique_token_id"
}
```
- **Expiry:** 1 hour
- **Storage:** Memory (never localStorage)
- **Purpose:** API authentication

**Refresh Token:**
```json
{
  "sub": "user_id_123",
  "type": "refresh",
  "exp": 1731424200,
  "iat": 1730819400,
  "jti": "unique_refresh_id"
}
```
- **Expiry:** 7 days
- **Storage:** httpOnly cookie (secure)
- **Purpose:** Get new access token

---

### 4.2 Authentication Flow

```
┌────────┐                          ┌────────┐
│ Client │                          │ Server │
└───┬────┘                          └───┬────┘
    │                                   │
    │ 1. POST /auth/login              │
    │   {email, password}              │
    ├─────────────────────────────────►│
    │                                   │
    │                                   │ 2. Validate credentials
    │                                   │ 3. Generate tokens
    │                                   │
    │ 4. Response:                     │
    │   - access_token (JSON)          │
    │   - refresh_token (httpOnly)     │
    │◄─────────────────────────────────┤
    │                                   │
    │ 5. GET /trips                    │
    │   Header: Authorization: Bearer  │
    │   {access_token}                 │
    ├─────────────────────────────────►│
    │                                   │
    │                                   │ 6. Verify token
    │                                   │ 7. Extract user_id
    │                                   │ 8. Process request
    │                                   │
    │ 9. Response with data            │
    │◄─────────────────────────────────┤
    │                                   │
    │ (After 1 hour)                   │
    │ 10. GET /trips (401)             │
    │◄─────────────────────────────────┤
    │                                   │
    │ 11. POST /auth/refresh           │
    │   (refresh_token in cookie)      │
    ├─────────────────────────────────►│
    │                                   │
    │                                   │ 12. Validate refresh token
    │                                   │ 13. Generate new tokens
    │                                   │
    │ 14. New access_token             │
    │◄─────────────────────────────────┤
    │                                   │
```

---

### 4.3 Password Security

**Hashing Algorithm: bcrypt**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashing
hashed = pwd_context.hash("user_password")

# Verification
is_valid = pwd_context.verify("user_password", hashed)
```

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- Not in common password list

---

### 4.4 Authorization Strategy: Role-Based Access Control (RBAC)

**For MVP: Simple Ownership Model**
```python
# User can only access their own resources
def get_trip(trip_id: int, current_user: User):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404)
    if trip.user_id != current_user.id:
        raise HTTPException(status_code=403)
    return trip
```

**Future: Role-Based (if sharing features added)**
```python
class Role(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

class TripCollaborator(Base):
    trip_id = Column(BigInteger, ForeignKey("trips.id"))
    user_id = Column(BigInteger, ForeignKey("users.id"))
    role = Column(Enum(Role))
```

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
   - Database migrations
   - Basic tests

4. **Iterate & Improve**
   - Monitor performance
   - Gather feedback
   - Optimize bottlenecks

---

**This system design document should be treated as a living document and updated as the system evolves.**
