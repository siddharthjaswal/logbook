# Logbook Backend API

🚀 **Production**: https://api.travlogue.in
📖 **API Docs**: https://api.travlogue.in/docs

Logbook is a comprehensive travel app backend that allows users to plan, track, and log their trips, including itinerary details, collaboration, expenses, and memories.

## 🚀 Recent Updates (November 2025)

**🎉 Production Deployment Complete** - Logbook API is now live!
- ✅ **Production URL**: https://api.travlogue.in
- ✅ **Auto-Deployment**: GitHub Actions CI/CD pipeline
- ✅ **SSL/HTTPS**: Let's Encrypt certificates with auto-renewal
- ✅ **Infrastructure**: Hetzner VPS with Nginx, PostgreSQL, systemd

**Phase 2: Trip Collaboration & Sharing** - Complete team collaboration features:
- ✅ **Trip Members** - Add collaborators with role-based access (Owner, Editor, Viewer)
- ✅ **Trip Invitations** - Invite users via email with customizable permissions
- ✅ **Activity Logs** - Automatic tracking of all trip changes and activities
- ✅ **Comments** - Threaded comments on trips and entities with @mentions
- ✅ **20 new tests** - Comprehensive test coverage for collaboration features
- ✅ **17 Bruno API requests** - Complete manual testing collection

**Phases 4-5: Expense Tracking & Planning Tools** - Major expansion of trip planning capabilities:
- ✅ **Expense & Budget Tracking** - Track expenses with multi-currency support, budgets, and expense splitting
- ✅ **Trip Notes** - Rich notes with types (tips, warnings, highlights), colors, and pinning
- ✅ **Packing Lists** - Manage multiple packing lists with category organization and pack status tracking
- ✅ **Checklists** - Task management with priorities, due dates, and completion tracking
- ✅ **151 new tests** - Comprehensive test coverage for all new features
- ✅ **35 Bruno API requests** - Complete manual testing collection

**Previous Update (December 2024)** - Major API Refactoring:
- ✅ **No more manual trip_day creation** - All entities (Accommodations, Transits, Activities, Bookings) now auto-create trip days
- ✅ **Intuitive date-based API** - Use trip_id + dates instead of trip_day_id
- ✅ **Multi-day accommodations** - Single API call for 3-night hotel stays

📖 See [API Refactoring Guide](docs/API_REFACTORING_2024.md) for migration details

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
Total Tests: 333
✅ Passing: 333 (100%)

Auth Feature: 16 tests ✅
Users Feature: 28 tests ✅
Trips Feature: 38 tests ✅ (includes auto-owner tests)
Trip Days Feature: 10 tests ✅
Trip Members Feature: 20 tests ✅ (Phase 2 - NEW)
Accommodations Feature: 15 tests ✅
Transits Feature: 15 tests ✅
Activities Feature: 5 tests ✅
Bookings Feature: 5 tests ✅
Timeline Feature: 22 tests ✅
Expenses Feature: 35 tests ✅
Trip Notes Feature: 43 tests ✅
Packing Lists Feature: 37 tests ✅
Checklists Feature: 36 tests ✅
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

### Timeline

*   `GET /api/v1/trips/{id}/timeline` - Get unified timeline for a trip
    *   Query params: `start_date`, `end_date`, `skip`, `limit`
    *   Returns chronologically sorted events (accommodations, transits, activities, bookings)
    *   Supports date range filtering and pagination

### Expenses & Budget Tracking

**Expense Management:**
*   `POST /api/v1/expenses` - Create expense (supports multi-currency)
*   `GET /api/v1/expenses/{id}` - Get expense details
*   `PUT /api/v1/expenses/{id}` - Update expense
*   `DELETE /api/v1/expenses/{id}` - Delete expense (soft delete)
*   `GET /api/v1/trips/{trip_id}/expenses` - List trip expenses (filters: category, dates, pagination)
*   `GET /api/v1/trips/{trip_id}/expenses/summary` - Get expense summary with category breakdown

**Budget Management:**
*   `POST /api/v1/trips/{trip_id}/budget-categories` - Create budget for a category
*   `GET /api/v1/trips/{trip_id}/budget-categories` - List all budget categories
*   `GET /api/v1/trips/{trip_id}/budget/vs-actual` - Compare budget vs actual spending

**Expense Splitting:**
*   `POST /api/v1/expenses/{expense_id}/splits` - Split expense between users
*   `GET /api/v1/expenses/{expense_id}/splits` - Get all splits for an expense

**Categories:** food_drink, accommodation, transportation, activities, shopping, other

### Trip Notes

*   `POST /api/v1/trip-notes` - Create note
*   `GET /api/v1/trip-notes/{id}` - Get note
*   `PUT /api/v1/trip-notes/{id}` - Update note
*   `DELETE /api/v1/trip-notes/{id}` - Delete note (soft delete)
*   `GET /api/v1/trips/{trip_id}/notes` - List trip notes (ordered by pinned, then date)
*   `POST /api/v1/trip-notes/{id}/pin` - Toggle pin status

**Note Types:** general, tip, warning, reminder, highlight

### Packing Lists

**List Management:**
*   `POST /api/v1/packing-lists` - Create packing list
*   `GET /api/v1/packing-lists/{id}` - Get packing list with items
*   `GET /api/v1/trips/{trip_id}/packing-lists` - List trip packing lists
*   `DELETE /api/v1/packing-lists/{id}` - Delete packing list (soft delete)
*   `GET /api/v1/packing-lists/{id}/summary` - Get packing summary

**Item Management:**
*   `POST /api/v1/packing-lists/{list_id}/items` - Add item to list
*   `PUT /api/v1/packing-items/{id}` - Update packing item
*   `POST /api/v1/packing-items/{id}/toggle-pack` - Toggle packed status

**Categories:** clothing, toiletries, electronics, documents, medications, gear, other

### Checklists

**Checklist Management:**
*   `POST /api/v1/checklists` - Create checklist
*   `GET /api/v1/checklists/{id}` - Get checklist with items
*   `GET /api/v1/trips/{trip_id}/checklists` - List trip checklists (filter: checklist_type)
*   `DELETE /api/v1/checklists/{id}` - Delete checklist (soft delete)
*   `GET /api/v1/checklists/{id}/summary` - Get checklist summary with overdue tracking

**Item Management:**
*   `POST /api/v1/checklists/{checklist_id}/items` - Add item to checklist
*   `PUT /api/v1/checklist-items/{id}` - Update checklist item
*   `POST /api/v1/checklist-items/{id}/toggle-complete` - Toggle completion status

**Types:** general, pre_departure, packing, post_trip
**Priorities:** low, medium, high, critical

## API Documentation

**Production:**
*   **Swagger UI:** [https://api.travlogue.in/docs](https://api.travlogue.in/docs)
*   **ReDoc:** [https://api.travlogue.in/redoc](https://api.travlogue.in/redoc)

**Local Development:**
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
│   ├── trips/                       # Trip API requests (8 files)
│   ├── expenses/                    # Expense API requests (12 files)
│   ├── trip-notes/                  # Trip notes API requests (6 files)
│   ├── packing-lists/               # Packing list API requests (8 files)
│   └── checklists/                  # Checklist API requests (9 files)
├── tests/                           # Pytest automated tests
│   ├── conftest.py                  # Test fixtures
│   └── features/
│       ├── auth/                    # Auth tests (16 tests)
│       ├── users/                   # User tests (28 tests)
│       ├── trips/                   # Trip tests (36 tests)
│       ├── expenses/                # Expense tests (35 tests)
│       ├── trip_notes/              # Trip notes tests (43 tests)
│       ├── packing_lists/           # Packing list tests (37 tests)
│       └── checklists/              # Checklist tests (36 tests)
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
- `collection/expenses/` - 12 expense & budget tracking requests
- `collection/trip-notes/` - 6 trip notes requests
- `collection/packing-lists/` - 8 packing list requests
- `collection/checklists/` - 9 checklist requests

## Roadmap

**✅ Phase 1: COMPLETED** - Foundation & Core Trip Management
- Google OAuth authentication
- User management
- Trip CRUD with advanced features

**✅ Phase 3: COMPLETED** - Trip Days & Itinerary Planning
- Daily itinerary planning
- Activities and bookings
- Accommodation tracking
- Transit details with timezone support
- Unified timeline view

**✅ Phase 4: COMPLETED** - Expenses & Budget Tracking
- Expense tracking with multi-currency support
- Budget management by category
- Expense splitting for shared costs
- Budget vs actual comparison
- 35 comprehensive tests

**✅ Phase 5: COMPLETED** - Notes & Packing Lists
- Rich trip notes with types, colors, and pinning
- Multiple packing lists per trip with categories
- Checklist management with priorities and due dates
- 116 comprehensive tests

**✅ Phase 2: COMPLETED** - Trip Collaboration & Sharing
- Trip members with role-based access control
- Trip invitations via email
- Activity logs for trip changes
- Threaded comments with @mentions
- 20 comprehensive tests

**📋 Future Phases:**
- Phase 6: Media Storage (photos, receipts)
- Phase 7: Social Features (following, trip cloning)
- Phase 8: Recommendations & Insights

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for detailed roadmap and task breakdown.

## Production Deployment

The Logbook API is deployed on **Hetzner VPS** with automatic deployments via GitHub Actions.

**Infrastructure:**
- **Server**: Hetzner Cloud (Ubuntu 22.04)
- **Web Server**: Nginx with reverse proxy
- **Application**: FastAPI with Uvicorn (4 workers)
- **Database**: PostgreSQL 15
- **SSL**: Let's Encrypt (auto-renewal)
- **Process Manager**: systemd service
- **CI/CD**: GitHub Actions

**Auto-Deployment:**
Every push to `main` branch automatically:
1. Pulls latest code from GitHub
2. Installs/updates dependencies
3. Runs database migrations (Alembic)
4. Restarts the application service
5. Verifies health check

See [docs/DEPLOYMENT_PLAN.md](./docs/DEPLOYMENT_PLAN.md) for complete deployment guide.

## License

Licensed under the [Apache License, Version 2.0](./LICENSE). You may use, modify, and distribute this software (including commercially) under the terms of that license. See [NOTICE](./NOTICE) for attribution.

Travlogue is open source. The hosted commercial version (with additional features such as real-time collaboration and AI assistance) is maintained separately.
