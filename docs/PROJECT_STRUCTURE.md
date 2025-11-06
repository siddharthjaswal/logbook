# Logbook Project Structure

## Overview
This document describes the FastAPI project structure following industry best practices and clean architecture principles.

## Directory Structure

```
logbook/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── api/                      # API layer - Route handlers
│   │   ├── __init__.py
│   │   ├── deps.py              # Shared dependencies (auth, db session)
│   │   ├── auth.py              # Authentication routes
│   │   ├── users.py             # User routes
│   │   ├── trips.py             # Trip routes
│   │   └── trip_days.py         # Trip day routes
│   │
│   ├── core/                     # Core application configuration
│   │   ├── __init__.py
│   │   ├── config.py            # Settings and environment variables
│   │   ├── security.py          # JWT, OAuth, password hashing
│   │   └── database.py          # Database connection and session
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py              # Base model class
│   │   ├── user.py              # User model
│   │   ├── trip.py              # Trip model
│   │   ├── trip_day.py          # TripDay model
│   │   └── trip_collaborator.py # TripCollaborator model (Phase 2)
│   │
│   ├── schemas/                  # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── user.py              # User schemas
│   │   ├── trip.py              # Trip schemas
│   │   ├── trip_day.py          # TripDay schemas
│   │   ├── auth.py              # Auth schemas (token, login)
│   │   └── common.py            # Common schemas (pagination, etc.)
│   │
│   ├── crud/                     # Database operations (CRUD)
│   │   ├── __init__.py
│   │   ├── base.py              # Base CRUD class
│   │   ├── user.py              # User CRUD operations
│   │   ├── trip.py              # Trip CRUD operations
│   │   └── trip_day.py          # TripDay CRUD operations
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── dates.py             # Date/timezone utilities
│   │   ├── validators.py        # Custom validators
│   │   └── enums.py             # Enum definitions
│   │
│   └── middleware/               # Custom middleware
│       ├── __init__.py
│       ├── cors.py              # CORS configuration
│       └── logging.py           # Request logging
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

## Layer Responsibilities

### 1. API Layer (`app/api/`)
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
# app/api/trips.py
@router.post("/", response_model=TripResponse, status_code=201)
async def create_trip(
    trip_in: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = crud.trip.create(db, obj_in=trip_in, user_id=current_user.id)
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
# app/models/trip.py
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
# app/schemas/trip.py
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
# app/crud/trip.py
class CRUDTrip(CRUDBase[Trip, TripCreate, TripUpdate]):
    def get_user_trips(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Trip]:
        return (
            db.query(Trip)
            .filter(Trip.created_by == user_id)
            .filter(Trip.deleted_at == None)
            .offset(skip)
            .limit(limit)
            .all()
        )

trip = CRUDTrip(Trip)
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

### Common Dependencies (`app/api/deps.py`)

```python
# Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Current authenticated user
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    payload = decode_jwt(token)
    user = crud.user.get(db, id=payload["sub"])
    if not user:
        raise HTTPException(status_code=401)
    return user

# Check if user is active
def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
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

## Development Workflow

1. **Create branch**: `git checkout -b feat/feature-name`
2. **Create migration**: `alembic revision --autogenerate -m "message"`
3. **Implement feature**:
   - Add model (if needed)
   - Add schema
   - Add CRUD operations
   - Add API route
   - Add tests
   - Add Bruno collection file
4. **Test**: `pytest tests/test_feature.py -v`
5. **Manual test**: Test in Bruno app
6. **Commit**: `git add . && git commit -m "message"`
7. **Push**: `git push origin feat/feature-name`

## Next Steps

1. Set up PostgreSQL database
2. Configure environment variables
3. Implement Phase 1 models
4. Set up Alembic migrations
5. Implement authentication
6. Implement trip CRUD
7. Add tests
8. Deploy
