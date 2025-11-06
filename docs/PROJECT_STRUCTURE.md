# Logbook Project Structure

## Overview
This document describes the FastAPI project structure following industry best practices and clean architecture principles.

## Directory Structure

**Feature-based (Domain-Driven) Structure:**

```
logbook/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── features/                 # Feature modules (domain-driven)
│   │   ├── __init__.py
│   │   │
│   │   ├── trips/               # Trip management feature
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # API routes (/trips endpoints)
│   │   │   ├── models.py        # SQLAlchemy Trip model
│   │   │   ├── schemas.py       # Pydantic Trip schemas
│   │   │   ├── crud.py          # Trip CRUD operations
│   │   │   └── service.py       # Business logic (optional)
│   │   │
│   │   ├── users/               # User management feature
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # API routes (/users endpoints)
│   │   │   ├── models.py        # SQLAlchemy User model
│   │   │   ├── schemas.py       # Pydantic User schemas
│   │   │   └── crud.py          # User CRUD operations
│   │   │
│   │   ├── auth/                # Authentication feature
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # API routes (/auth endpoints)
│   │   │   ├── schemas.py       # Token schemas
│   │   │   └── service.py       # OAuth & JWT logic
│   │   │
│   │   ├── trip_days/           # Trip day planning feature
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # API routes (/trip_days endpoints)
│   │   │   ├── models.py        # SQLAlchemy TripDay model
│   │   │   ├── schemas.py       # Pydantic TripDay schemas
│   │   │   └── crud.py          # TripDay CRUD operations
│   │   │
│   │   └── [future features]/   # expenses, notes, photos, etc.
│   │
│   ├── core/                     # Core infrastructure (shared)
│   │   ├── __init__.py
│   │   ├── config.py            # Settings and environment variables
│   │   ├── database.py          # Database connection and session
│   │   ├── security.py          # JWT, OAuth utilities
│   │   └── deps.py              # Shared dependencies (auth, db)
│   │
│   └── shared/                   # Shared utilities (cross-feature)
│       ├── __init__.py
│       ├── enums.py             # Enum definitions
│       ├── pagination.py        # Pagination utilities
│       └── validators.py        # Custom validators
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and configuration
│   ├── test_auth.py             # Auth endpoint tests
│   ├── test_trips.py            # Trip endpoint tests
│   ├── test_trip_days.py        # TripDay endpoint tests
│   └── test_models.py           # Model tests
│
├── alembic/                      # Database migrations
│   ├── versions/                # Migration files
│   ├── env.py                   # Alembic environment
│   └── script.py.mako           # Migration template
│
├── collection/                   # Bruno API collection
│   ├── bruno.json               # Collection configuration
│   ├── environments/
│   │   ├── local.bru           # Local environment
│   │   └── production.bru      # Production environment
│   ├── auth/                    # Auth requests
│   ├── trips/                   # Trip requests
│   └── trip-days/              # Trip day requests
│
├── docs/                         # Documentation
│   ├── entities/                # Entity documentation
│   │   ├── USER.md
│   │   ├── TRIP.md
│   │   ├── TRIP_DAY.md
│   │   └── TRIP_COLLABORATOR.md
│   ├── api/                     # API documentation
│   └── PROJECT_STRUCTURE.md     # This file
│
├── scripts/                      # Utility scripts
│   ├── init_db.py              # Initialize database
│   ├── seed_data.py            # Seed test data
│   └── reset_db.py             # Reset database
│
├── .env                         # Environment variables (not in git)
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # Project metadata and dependencies (optional)
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project overview
├── PRD.md                      # Product requirements
├── SYSTEM_DESIGN.md            # System design document
└── IMPLEMENTATION_PLAN.md      # Implementation roadmap
```

## Why Feature-based Structure?

**Benefits:**
- ✅ **Cohesion**: All code for a feature is in one place
- ✅ **Scalability**: Easy to add new features without cluttering
- ✅ **Team Collaboration**: Developers can own entire features
- ✅ **Microservices Ready**: Can extract features to separate services
- ✅ **Clear Boundaries**: Features are isolated and self-contained
- ✅ **Less Navigation**: No jumping between api/, models/, schemas/, crud/

**When to use layer-based:**
- Very small projects (< 5 models)
- When following strict MVC pattern
- When all features are tightly coupled

**When to use feature-based:**
- ✅ Growing projects with multiple domains (Logbook!)
- ✅ When features have distinct business logic
- ✅ When you want to scale the codebase

## Feature Module Structure

Each feature folder contains:
- `router.py` - API routes and request handlers
- `models.py` - SQLAlchemy ORM models
- `schemas.py` - Pydantic request/response schemas
- `crud.py` - Database operations
- `service.py` - Complex business logic (optional)

## Layer Responsibilities

### 1. Router Layer (`router.py` in each feature)
**Purpose**: Handle HTTP requests and responses

**Responsibilities**:
- Define route handlers
- Parse request data
- Validate input (via Pydantic schemas)
- Call CRUD operations
- Return responses
- Handle HTTP errors

**Best Practices**:
- Keep route handlers thin
- Delegate business logic to CRUD layer
- Use dependency injection for auth, db session
- Return Pydantic response models

**Example**:
```python
# app/features/trips/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from .schemas import TripCreate, TripResponse
from .crud import create_trip

router = APIRouter()

@router.post("/", response_model=TripResponse, status_code=201)
async def create_trip_endpoint(
    trip_in: TripCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    trip = create_trip(db, obj_in=trip_in, user_id=current_user.id)
    return trip
```

### 2. Core Layer (`app/core/`)
**Purpose**: Application configuration and core utilities

**Responsibilities**:
- Load environment variables
- Database connection setup
- Security functions (JWT, OAuth)
- Global configuration

**Files**:
- `config.py`: Settings class with environment variables
- `security.py`: JWT token creation/validation, OAuth helpers
- `database.py`: SQLAlchemy engine and session factory

### 3. Models Layer (`app/models/`)
**Purpose**: Database schema definition (ORM)

**Responsibilities**:
- Define SQLAlchemy models
- Define relationships
- Define table constraints
- No business logic

**Best Practices**:
- Inherit from Base class
- Use type hints
- Define relationships explicitly
- Add indexes for common queries

**Example**:
```python
# app/features/trips/models.py
from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="trips")
    trip_days = relationship("TripDay", back_populates="trip", cascade="all, delete-orphan")
```

### 4. Schemas Layer (`app/schemas/`)
**Purpose**: Data validation and serialization (Pydantic)

**Responsibilities**:
- Define request schemas (input validation)
- Define response schemas (output serialization)
- Custom validators
- Type conversion

**Types of Schemas**:
- `*Base`: Shared fields
- `*Create`: Fields for creation
- `*Update`: Fields for updates (all optional)
- `*Response`: Fields for API responses
- `*InDB`: Database representation (optional)

**Example**:
```python
# app/features/trips/schemas.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class TripBase(BaseModel):
    name: str
    description: Optional[str] = None

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TripResponse(TripBase):
    id: int
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
```

### 5. CRUD Layer (`app/crud/`)
**Purpose**: Database operations and business logic

**Responsibilities**:
- Create, Read, Update, Delete operations
- Complex queries
- Business logic
- Transaction management

**Best Practices**:
- Inherit from base CRUD class
- Use type hints
- Keep operations atomic
- Handle errors gracefully

**Example**:
```python
# app/features/trips/crud.py
from typing import List, Optional
from sqlalchemy.orm import Session

from .models import Trip
from .schemas import TripCreate, TripUpdate

def get_trip_by_id(db: Session, trip_id: int) -> Optional[Trip]:
    return db.query(Trip).filter(Trip.id == trip_id).first()

def get_user_trips(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[Trip]:
    return (
        db.query(Trip)
        .filter(Trip.created_by == user_id)
        .filter(Trip.deleted_at == None)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_trip(db: Session, trip_in: TripCreate, user_id: int) -> Trip:
    trip = Trip(**trip_in.dict(), created_by=user_id)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip
```

### 6. Utils Layer (`app/utils/`)
**Purpose**: Shared utility functions

**Responsibilities**:
- Date/time utilities
- Validation helpers
- Enum definitions
- Helper functions

### 7. Middleware Layer (`app/middleware/`)
**Purpose**: Request/response processing

**Responsibilities**:
- CORS configuration
- Request logging
- Error handling
- Rate limiting (future)

## Dependency Injection

### Common Dependencies (`app/core/deps.py`)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Get user ID from JWT
async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return payload.get("sub")

# Get full user object
async def get_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    from app.features.users.crud import get_user_by_id
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Check if user is active
async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user
```

## Testing Structure

### Test Organization
```
tests/
├── conftest.py           # Fixtures (db, client, test user)
├── test_auth.py          # Authentication tests
├── test_trips.py         # Trip CRUD tests
├── test_trip_days.py     # TripDay CRUD tests
└── test_models.py        # Model relationship tests
```

### Fixtures
```python
# conftest.py
@pytest.fixture
def db():
    # Create test database
    yield session

@pytest.fixture
def client(db):
    # Create test client
    yield TestClient(app)

@pytest.fixture
def test_user(db):
    # Create test user
    yield user
```

## Configuration Management

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/logbook

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
DEBUG=True
ENVIRONMENT=development
```

### Settings Class (`app/core/config.py`)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

## Database Migrations (Alembic)

### Create Migration
```bash
alembic revision --autogenerate -m "Add trip table"
```

### Apply Migration
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
```

## Best Practices

### 1. Separation of Concerns
- API layer: HTTP handling only
- CRUD layer: Business logic and database operations
- Models: Database schema only
- Schemas: Data validation only

### 2. Dependency Injection
- Use FastAPI's `Depends()` for common dependencies
- Makes testing easier (can inject mocks)
- Improves code reusability

### 3. Error Handling
- Use FastAPI's HTTPException
- Create custom exception handlers
- Return consistent error responses

### 4. Type Hints
- Use type hints everywhere
- Improves IDE autocomplete
- Catches errors early

### 5. Async/Await (Future)
- Phase 1: Synchronous (simpler)
- Future: Async for better performance
- Use async database drivers

### 6. Logging
- Log important events
- Use structured logging
- Different log levels (DEBUG, INFO, ERROR)

### 7. Documentation
- Keep entity docs updated
- Document complex business logic
- Add docstrings to functions

## Development Workflow (Feature-based)

### Adding a New Feature

1. **Create branch**: `git checkout -b feat/feature-name`
2. **Create feature folder**: `mkdir -p app/features/feature_name`
3. **Create files**:
   ```bash
   touch app/features/feature_name/__init__.py
   touch app/features/feature_name/router.py
   touch app/features/feature_name/models.py
   touch app/features/feature_name/schemas.py
   touch app/features/feature_name/crud.py
   ```
4. **Implement feature**:
   - Define model in `models.py`
   - Define schemas in `schemas.py`
   - Implement CRUD in `crud.py`
   - Create routes in `router.py`
   - Register router in `main.py`
5. **Create migration**: `alembic revision --autogenerate -m "Add feature_name"`
6. **Add tests**: Create `tests/test_feature_name.py`
7. **Add Bruno requests**: Create `collection/feature_name/` folder
8. **Test**: `pytest tests/test_feature_name.py -v`
9. **Manual test**: Test in Bruno app
10. **Commit & Push**: `git add . && git commit -m "message" && git push`

### Example: Adding Trips Feature

```bash
# 1. Create feature folder
mkdir -p app/features/trips

# 2. Create files
cd app/features/trips
touch __init__.py router.py models.py schemas.py crud.py

# 3. Implement each file
# ... (write code)

# 4. Register router in main.py
# app.include_router(trips_router, prefix="/api/v1/trips", tags=["trips"])

# 5. Create migration
alembic revision --autogenerate -m "Add Trip model"

# 6. Add tests
touch tests/test_trips.py

# 7. Add Bruno collection
mkdir -p collection/trips
```

## Next Steps

1. Set up PostgreSQL database
2. Configure environment variables
3. Implement Phase 1 models
4. Set up Alembic migrations
5. Implement authentication
6. Implement trip CRUD
7. Add tests
8. Deploy
