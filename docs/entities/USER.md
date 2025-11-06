# User Entity

## Overview
The User entity represents a registered user in the Logbook system. Users authenticate via Google OAuth and can create trips, collaborate on trips, and interact with public trips.

## Database Table: `users`

### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | BIGSERIAL | PRIMARY KEY | Unique user identifier |
| `google_id` | VARCHAR(255) | NOT NULL, UNIQUE | Google OAuth user ID |
| `email` | VARCHAR(255) | NOT NULL, UNIQUE | User email from Google (always verified) |
| `email_verified` | BOOLEAN | DEFAULT TRUE | Email verification status (always true for Google OAuth) |
| `username` | VARCHAR(50) | UNIQUE, NULLABLE | Optional username (can be set after signup) |
| `first_name` | VARCHAR(100) | NULLABLE | User's first name from Google profile |
| `last_name` | VARCHAR(100) | NULLABLE | User's last name from Google profile |
| `profile_photo_url` | TEXT | NULLABLE | URL to Google profile picture |
| `bio` | TEXT | NULLABLE | User biography/description |
| `default_currency` | VARCHAR(3) | DEFAULT 'USD' | Default currency for expenses |
| `date_format` | VARCHAR(20) | DEFAULT 'YYYY-MM-DD' | Preferred date format |
| `timezone` | VARCHAR(50) | DEFAULT 'UTC' | User's default timezone |
| `language` | VARCHAR(10) | DEFAULT 'en' | Preferred language code |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account active status |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |
| `last_login_at` | TIMESTAMP | NULLABLE | Last login timestamp |
| `deleted_at` | TIMESTAMP | NULLABLE | Soft delete timestamp |

### Indexes

```sql
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username) WHERE username IS NOT NULL;
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
```

## Relationships

- **trips (via trip_collaborators)**: Many-to-Many - Users can collaborate on multiple trips
- **trips (as creator)**: One-to-Many - User can create multiple trips (trips.created_by)

## Business Rules

### Authentication
1. Users must authenticate via Google OAuth (no email/password)
2. Google ID is the primary authentication identifier
3. Email is always verified (Google handles verification)
4. Username is optional and can be set after initial signup

### Profile Management
1. First name, last name, and profile photo are populated from Google on signup
2. Users can update their profile information after signup
3. Users can change their username (must be unique)
4. Users can set preferences (currency, timezone, date format, language)

### Account Status
1. `is_active`: Controls whether user can access the system
2. `deleted_at`: Soft delete - when set, user is considered deleted
3. Deleted users:
   - Cannot login
   - Private trips are deleted if no other owners exist
   - Public/unlisted trips persist with `created_by = NULL`

### Data Retention
1. Soft delete is used for user accounts
2. User data can be permanently deleted via manual process
3. Trip ownership is transferred or nullified on user deletion

## API Endpoints

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

## Pydantic Schemas

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

## Security Considerations

1. **Google OAuth Only**: No password storage or management required
2. **Google ID Protection**: Never expose Google ID in public APIs
3. **Email Privacy**: Respect user email privacy settings
4. **Profile Photo**: Use Google-provided URLs (no local storage)
5. **Soft Delete**: Preserve data integrity when users delete accounts
6. **PII Protection**: Handle personally identifiable information carefully

## Migration Notes

### From Email/Password to Google OAuth
- Removed: `password_hash`, `is_verified`, `verification_token`
- Added: `google_id`, `email_verified` (always true)
- Changed: Email is now always verified via Google

### Future Considerations
- Multi-provider OAuth (GitHub, Apple, etc.) - add `provider` field
- Email change requests - requires Google re-authentication
- Account linking - merge duplicate accounts
