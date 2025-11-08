# Users Feature

## Overview
The Users feature handles user authentication, profile management, and user preferences. Users authenticate exclusively via Google OAuth (no email/password authentication).

## Current Implementation Status

### ✅ Completed
- [x] User model with SQLAlchemy ORM
- [x] Database migration applied
- [x] Table created in PostgreSQL

### ⏳ In Progress / Not Started
- [ ] Pydantic schemas (UserCreate, UserUpdate, UserResponse)
- [ ] CRUD operations
- [ ] API router (`/users` endpoints)
- [ ] Authentication integration
- [ ] Tests (pytest + Bruno)

---

## Database Schema

### Table: `users`

**Purpose**: Store user account information, profile data, and preferences.

#### Primary Key
- `id` (BIGINT, auto-increment) - Unique user identifier

#### Authentication Fields (Google OAuth)

| Field | Type | Constraints | Purpose |
|-------|------|-------------|---------|
| `google_id` | VARCHAR(255) | NOT NULL, UNIQUE, INDEXED | Google OAuth user ID - primary authentication identifier |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE, INDEXED | User's email from Google (always verified) |
| `email_verified` | BOOLEAN | NOT NULL, DEFAULT TRUE | Email verification status (always TRUE for Google OAuth) |

**Why Google OAuth?**
- No password storage/management required
- Google handles all security and verification
- Simpler implementation for MVP
- Can add other OAuth providers later

#### Profile Fields

| Field | Type | Nullable | Purpose |
|-------|------|----------|---------|
| `username` | VARCHAR(50) | YES, UNIQUE, INDEXED | Optional username (can be set after signup) |
| `first_name` | VARCHAR(100) | YES | User's first name (from Google profile) |
| `last_name` | VARCHAR(100) | YES | User's last name (from Google profile) |
| `profile_photo_url` | TEXT | YES | URL to Google profile picture |
| `bio` | TEXT | YES | User biography/description |

**Key Design Decisions:**
- **Username is optional**: Users can sign up with just Google account, set username later
- **Profile data from Google**: Auto-populated on first login
- **profile_photo_url**: Points to Google's CDN (no local storage)

#### Preferences

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `default_currency` | VARCHAR(3) | 'USD' | Default currency for trip budgets and expenses |
| `date_format` | VARCHAR(20) | 'YYYY-MM-DD' | Preferred date format for display |
| `timezone` | VARCHAR(50) | 'UTC' | User's default timezone |
| `language` | VARCHAR(10) | 'en' | Preferred language code (i18n) |

**Why these preferences?**
- **Currency**: Used when creating trips, calculating budgets
- **Date format**: UI presentation preference
- **Timezone**: Important for trip planning across timezones
- **Language**: Future internationalization support

#### Account Status

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `is_active` | BOOLEAN | TRUE | Account active status (can disable without deleting) |

**Use cases:**
- Temporarily suspend accounts
- User can deactivate their own account
- Admin can disable problematic accounts

#### Timestamps

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `created_at` | TIMESTAMP | CURRENT_TIMESTAMP | Account creation time |
| `updated_at` | TIMESTAMP | CURRENT_TIMESTAMP (auto-update) | Last profile update |
| `last_login_at` | TIMESTAMP | NULL | Last login timestamp |

**Why track these?**
- **created_at**: User tenure, analytics
- **updated_at**: Audit trail, cache invalidation
- **last_login_at**: Activity tracking, inactive account cleanup

#### Soft Delete

| Field | Type | Purpose |
|-------|------|---------|
| `deleted_at` | TIMESTAMP (NULL) | Soft delete timestamp |

**Soft Delete Strategy:**
- When user deletes account, set `deleted_at` timestamp
- Don't immediately remove data (allows recovery)
- Cleanup job can permanently delete after 30 days
- Queries filter `WHERE deleted_at IS NULL`

---

## Relationships

### Trips (One-to-Many)
```python
trips = relationship("Trip", back_populates="creator", foreign_keys="Trip.created_by")
```

**Meaning:**
- One user can create multiple trips
- User is the trip creator
- Relationship via `trips.created_by` foreign key

**Cascade Behavior:**
- When user is deleted → `trips.created_by` is SET NULL
- Trip persists even if creator deleted (for public trips)

### Trip Collaborations (Phase 2)
```python
# trip_collaborations = relationship("TripCollaborator", back_populates="user")
```

**Future**: Many-to-Many relationship via `trip_collaborators` junction table
- User can collaborate on trips they didn't create
- Different roles: owner, editor, viewer

---

## Indexes

### 1. Primary Key Index
```sql
CREATE INDEX ix_users_id ON users(id);
```
**Purpose**: Fast lookups by user ID (every query uses this)

### 2. Google ID Index
```sql
CREATE INDEX ix_users_google_id ON users(google_id);
```
**Purpose**: Fast OAuth login (lookup user by Google ID)

### 3. Email Index
```sql
CREATE INDEX ix_users_email ON users(email);
```
**Purpose**: Search users by email, prevent duplicates

### 4. Username Index
```sql
CREATE INDEX ix_users_username ON users(username) WHERE username IS NOT NULL;
```
**Purpose**:
- Fast lookup by username
- Partial index (only indexes non-NULL values)
- Username uniqueness check

**Why partial index?**
- Many users won't set username (NULL)
- Saves index storage space
- Faster queries

---

## Business Rules

### 1. Authentication
- Users MUST authenticate via Google OAuth
- No password-based authentication
- Email is always verified (Google handles it)

### 2. Username
- Optional on signup
- Can be set/changed later
- Must be unique if provided
- Use email as fallback display name

### 3. Account Creation Flow
```
1. User clicks "Login with Google"
2. Google OAuth flow (handled in auth feature)
3. Receive Google user data
4. Check if user exists (by google_id)
5. If new: Create user with Google data
6. If existing: Update last_login_at
7. Generate JWT tokens
8. Return tokens to frontend
```

### 4. Account Deletion
- Soft delete by default (set deleted_at)
- User's public trips persist with `created_by = NULL`
- User's private trips deleted if they're the only owner
- Permanent deletion after 30-day grace period

### 5. Profile Updates
- Users can update their own profile
- Cannot change google_id or email (from Google)
- Can change username, bio, preferences

---

## API Endpoints (Planned)

### Authentication
- `GET /auth/google` - Redirect to Google OAuth
- `GET /auth/google/callback` - Handle OAuth callback
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user

### User Profile
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `PATCH /users/me/username` - Update username
- `DELETE /users/me` - Delete account (soft delete)

### Admin (Future)
- `GET /users/{user_id}` - Get user by ID (admin only)
- `GET /users/` - List users (admin only)

---

## Pydantic Schemas (To Be Created)

### UserBase
```python
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    default_currency: str = "USD"
    date_format: str = "YYYY-MM-DD"
    timezone: str = "UTC"
    language: str = "en"
```

### UserCreate
```python
class UserCreate(UserBase):
    google_id: str
    email_verified: bool = True
    profile_photo_url: Optional[str] = None
```

### UserUpdate
```python
class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    default_currency: Optional[str] = None
    date_format: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
```

### UserResponse
```python
class UserResponse(UserBase):
    id: int
    google_id: str
    email_verified: bool
    profile_photo_url: Optional[str]
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True
```

---

## CRUD Operations (To Be Created)

### get_user_by_id
```python
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()
```

### get_user_by_google_id
```python
def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    """Get user by Google ID (for OAuth login)."""
    return db.query(User).filter(User.google_id == google_id).first()
```

### get_user_by_email
```python
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()
```

### create_user
```python
def create_user(db: Session, user_in: UserCreate) -> User:
    """Create new user from Google OAuth data."""
    user = User(**user_in.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### update_user
```python
def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """Update user profile."""
    update_data = user_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
```

### delete_user (soft)
```python
def delete_user(db: Session, user: User) -> User:
    """Soft delete user."""
    user.deleted_at = datetime.utcnow()
    db.commit()
    return user
```

---

## Testing Strategy

### Unit Tests (pytest)
- Test user creation with valid Google data
- Test duplicate email/google_id prevention
- Test username uniqueness
- Test profile updates
- Test soft delete

### Integration Tests
- Test full OAuth flow
- Test user creation via API
- Test profile update via API
- Test authentication required for endpoints

### Bruno Collection
- `collection/users/get-my-profile.bru`
- `collection/users/update-profile.bru`
- `collection/users/update-username.bru`
- `collection/users/delete-account.bru`

---

## Security Considerations

### 1. Google OAuth Only
- ✅ No password storage (no bcrypt/hashing needed)
- ✅ No password reset flow
- ✅ No email verification (Google handles it)

### 2. Email Privacy
- Don't expose user emails in public APIs
- Only show emails to user themselves or admins

### 3. Google ID Protection
- Never expose google_id in public responses
- Only use internally for authentication

### 4. Profile Photo URLs
- Use Google's CDN URLs (already secure)
- No local storage needed

### 5. Soft Delete
- Maintain data integrity when users delete accounts
- Allow recovery period

---

## Future Enhancements

### Multi-Provider OAuth
```python
# Add these fields when supporting multiple OAuth providers
provider = Column(String(20), default="google")  # 'google', 'github', 'apple'
provider_id = Column(String(255))  # Generic provider user ID
```

### Email Change
- Require Google re-authentication
- Send confirmation to both old and new email

### Account Linking
- Merge duplicate accounts
- Link multiple OAuth providers to one account

### User Settings
- Email notification preferences
- Privacy settings
- Display preferences

---

## Related Documentation

- [Google OAuth Setup Guide](../../../docs/POSTGRESQL_SETUP.md)
- [Entity Documentation](../../../docs/entities/USER.md)
- [System Design](../../../SYSTEM_DESIGN.md)
- [Authentication Feature](../auth/README.md)
