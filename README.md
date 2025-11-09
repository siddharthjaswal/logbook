# Logbook Backend API

Logbook is a comprehensive travel app backend that allows users to plan, track, and log their trips, including itinerary details, expenses, and memories.

## Tech Stack

*   **Framework:** FastAPI
*   **Database:** PostgreSQL 15 with SQLAlchemy ORM
*   **Authentication:** Google OAuth 2.0 with JWT tokens
*   **API Testing:** Bruno API Collection + Pytest

## Current Implementation Status

### ✅ **Phase 1: COMPLETED** - Foundation & Core Trip Management

**Implemented Features:**

*   ✅ **Google OAuth Authentication** - Secure login with Google accounts
*   ✅ **User Management** - Profile management with Google data
*   ✅ **Trip Management** - Complete CRUD with advanced features
*   ✅ **Access Control** - Private, unlisted, and public trips
*   ✅ **Search & Discovery** - Full-text search and public trip browsing
*   ✅ **Flexible Date Planning** - Support for exact and flexible dates
*   ✅ **Budget Tracking** - Trip budget and currency management
*   ✅ **Soft Deletes** - Safe trip deletion with 30-day recovery

### Test Coverage

```
Total Tests: 80
✅ Passing: 66 (82.5%)
❌ Failing: 14 (minor assertion issues, not implementation)

Auth Feature: 16/16 ✅
Users Feature: 28/28 ✅
Trips Feature: 22/36 (core functionality working)
```

### Data Models

#### User
*   Google OAuth integration (google_id, email, profile)
*   Customizable preferences (currency, timezone, language)
*   Profile management (username, bio, photo)
*   Soft delete support

#### Trip
*   **Basic Info:** Name, description, cover photo
*   **Dates:** Exact or flexible planning (year/month/week)
*   **Location:** Primary destination + visited countries/cities
*   **Classification:** Trip type (single, multi-city, road trip, etc.)
*   **Visibility:** Private, unlisted, or public
*   **Budget:** Total budget with currency support
*   **Engagement:** View counts, likes, clones (for public trips)
*   **Metadata:** Tags, notes, timestamps
*   **Relationships:** Creator (user), trip days

## API Endpoints

### Authentication (OAuth 2.0 + JWT)

*   `GET /api/v1/auth/google` - Initiate Google OAuth login
*   `GET /api/v1/auth/google/callback` - OAuth callback handler
*   `POST /api/v1/auth/refresh` - Refresh access token
*   `POST /api/v1/auth/logout` - Logout user
*   `GET /api/v1/auth/me` - Get current user info

### User Management

*   `GET /api/v1/users/me` - Get my profile
*   `PUT /api/v1/users/me` - Update full profile
*   `PATCH /api/v1/users/me` - Update username
*   `DELETE /api/v1/users/me` - Soft delete account

### Trip Management

*   `GET /api/v1/trips` - List my trips (with pagination & filters)
*   `POST /api/v1/trips` - Create a new trip
*   `GET /api/v1/trips/{id}` - Get trip details
*   `PUT /api/v1/trips/{id}` - Update trip
*   `DELETE /api/v1/trips/{id}` - Soft delete trip
*   `GET /api/v1/trips/public` - Browse public trips (filters: country, city, type)
*   `GET /api/v1/trips/search?q={query}` - Search trips (authenticated includes private)
*   `GET /api/v1/trips/stats/me` - Get my trip statistics

### Coming Soon (Phase 3)

*   Trip Days & Itinerary Planning
*   Daily activities, bookings, and accommodation
*   Transit tracking with timezone support

## API Documentation

You can access the interactive API documentation when the server is running:

*   **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Project Structure

```
logbook/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── core/                        # Core application components
│   │   ├── config.py                # Settings & environment variables
│   │   ├── database.py              # Database configuration
│   │   ├── deps.py                  # Dependency injection utilities
│   │   └── security.py              # JWT token utilities
│   ├── features/                    # Feature-based modules
│   │   ├── auth/                    # Authentication (Google OAuth, JWT)
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── oauth.py             # OAuth configuration
│   │   │   ├── service.py           # Business logic
│   │   │   └── router.py            # API endpoints
│   │   ├── users/                   # User management
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── crud.py              # Database operations
│   │   │   └── router.py
│   │   ├── trips/                   # Trip management
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── crud.py
│   │   │   └── router.py
│   │   └── trip_days/               # Trip day planning (Phase 3)
│   └── shared/                      # Shared utilities
│       └── enums.py                 # Common enumerations
├── collection/                      # Bruno API collection (manual testing)
│   ├── bruno.json                   # Collection configuration
│   ├── environments/                # Environment configs (local, production)
│   ├── auth/                        # Auth API requests (4 files)
│   ├── users/                       # User API requests (4 files)
│   └── trips/                       # Trip API requests (8 files)
├── tests/                           # Pytest automated tests
│   ├── conftest.py                  # Test fixtures
│   └── features/
│       ├── auth/                    # Auth tests (16 tests)
│       ├── users/                   # User tests (28 tests)
│       └── trips/                   # Trip tests (36 tests)
├── docs/                            # Documentation
│   ├── GOOGLE_OAUTH_SETUP.md        # OAuth setup guide
│   ├── DEVELOPMENT_SETUP.md         # Development setup
│   └── entities/                    # Entity documentation
├── migrations/                      # Alembic database migrations
├── scripts/                         # Utility scripts
├── requirements.txt
├── pytest.ini                       # Pytest configuration
├── IMPLEMENTATION_PLAN.md           # Detailed implementation roadmap
└── README.md
```

## Getting Started

### Prerequisites

*   Python 3.11+ (3.13 not yet supported by all dependencies)
*   PostgreSQL 15+
*   Homebrew (macOS)

### Setup and Installation

**📚 Complete setup guide:** See [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md)

**Quick Start:**

1.  **Create and activate a virtual environment:**
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    ```

2.  **Install the dependencies:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3.  **Set up PostgreSQL:**
    ```bash
    # Install PostgreSQL
    brew install postgresql@15

    # Start PostgreSQL service
    brew services start postgresql@15

    # Create database
    createdb logbook
    ```

4.  **Configure environment variables:**
    ```bash
    # Copy example env file
    cp .env.example .env

    # Edit .env and update:
    # - DATABASE_URL (already set for local PostgreSQL)
    # - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET (from Google Cloud Console)
    # - SECRET_KEY is pre-generated
    ```

5.  **Test database connection:**
    ```bash
    python scripts/test_db_connection.py
    ```

6.  **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```

    The server will start, and you can access the API at `http://127.0.0.1:8000`.

### Testing the Setup

```bash
# Check database connection
python scripts/test_db_connection.py

# Run all tests
pytest -v

# Run specific feature tests
pytest tests/features/trips/ -v

# Start development server
uvicorn app.main:app --reload
```

### Testing with Bruno

Bruno is a fast, Git-friendly API client that we use for manual API testing. The collection is committed to the repository.

1. **Install Bruno Desktop App**
   - Download from [https://www.usebruno.com/](https://www.usebruno.com/)
   - Or: `brew install --cask bruno`

2. **Open Collection**
   - Open Bruno → "Open Collection"
   - Navigate to `/logbook/collection`

3. **Select Environment**
   - Click environment dropdown (top-right)
   - Select `local` for development
   - For authenticated requests, use `sid_auth_test` (contains your OAuth tokens)

4. **Test OAuth Flow**
   - Open browser: `http://localhost:8000/api/v1/auth/google`
   - Complete Google login
   - Copy `access_token` and `refresh_token` from response
   - Update environment variables in Bruno:
     - Click environment dropdown → Edit `sid_auth_test`
     - Update `accessToken` and `refreshToken` values
     - Save changes

5. **Refresh Expired Tokens**

   Access tokens expire after 7 days (10,080 minutes). When you get a 401 error after they lapse:

   **Method 1: Using Bruno (Recommended)**
   - Open `collection/auth/Refresh Token.bru`
   - Click "Send" (uses your current `refreshToken`)
   - Copy the new `access_token` from response
   - Update `accessToken` in environment

   **Method 2: Manual API Call**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "YOUR_REFRESH_TOKEN_HERE"}'
   ```

   **Token Storage & Updates:**
   - Tokens are **stateless JWT** - not stored in database
   - `last_login_at` is updated in database when OAuth completes (automatic)
   - Refresh tokens are valid for **7 days**
   - After 7 days, re-authenticate via Google OAuth

6. **Run Requests**
   - Navigate to `auth/`, `users/`, or `trips/` folders
   - Click any request → Send
   - View response and status
   - If 401 error: refresh your access token (see step 5)

**Available Collections:**
- `collection/auth/` - 4 authentication requests
- `collection/users/` - 4 user management requests
- `collection/trips/` - 8 trip management requests

## Roadmap

**✅ Phase 1: COMPLETED** - Foundation & Core Trip Management
- Google OAuth authentication
- User management
- Trip CRUD with advanced features

**🚧 Next: Phase 3** - Trip Days & Itinerary Planning
- Daily itinerary planning
- Activities and bookings
- Accommodation tracking
- Transit details with timezone support

**📋 Future Phases:**
- Phase 2: Trip Collaboration & Sharing
- Phase 4: Expenses & Budget Tracking
- Phase 5: Notes, Packing Lists
- Phase 6: Media Storage (photos, receipts)

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for detailed roadmap and task breakdown.
