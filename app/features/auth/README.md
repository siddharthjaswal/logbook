# Auth Feature

## Overview
The Auth feature handles user authentication via Google OAuth 2.0. For MVP, Logbook uses Google as the **only** authentication provider - no email/password authentication. This simplifies security, eliminates password management, and provides a smooth user experience.

## Current Implementation Status

### ✅ **COMPLETED - Phase 1**

**Core Security Infrastructure:**
- [x] JWT token utilities (create, decode, validate)
- [x] Security module (app/core/security.py)
- [x] Dependency injection for authentication (app/core/deps.py)
- [x] Token types: access (30 min) and refresh tokens (7 days)
- [x] JWT subject (sub) converted to string for spec compliance
- [x] Token type validation (prevent access token used as refresh)

**Google OAuth Integration:**
- [x] Authlib OAuth client configuration
- [x] SessionMiddleware for OAuth state management
- [x] itsdangerous dependency for secure sessions
- [x] Google OpenID Connect auto-discovery
- [x] OAuth scopes: openid, email, profile

**Pydantic Schemas (5 schemas):**
- [x] TokenResponse - Login response with tokens
- [x] TokenRefreshRequest - Refresh token request
- [x] TokenRefreshResponse - New access token response
- [x] GoogleUserInfo - Google OAuth user data
- [x] AuthUserResponse - Combined user + tokens response

**Service Layer (3 functions):**
- [x] get_or_create_user_from_google - OAuth user handling
- [x] generate_tokens_for_user - JWT token generation
- [x] create_auth_response - Format auth response

**API Router (5 endpoints):**
- [x] GET /auth/google - Initiate OAuth flow
- [x] GET /auth/google/callback - Handle OAuth callback
- [x] POST /auth/refresh - Refresh access token
- [x] POST /auth/logout - Logout (client-side token clearing)
- [x] GET /auth/me - Get current authenticated user

**Testing:**
- [x] Bruno API Collection (4 request files)
- [x] Pytest service tests (6 tests)
- [x] Pytest API integration tests (10 tests)
- [x] **Test Results:** 16/16 passing (100% pass rate)

**Documentation:**
- [x] Comprehensive Google OAuth setup guide (docs/GOOGLE_OAUTH_SETUP.md)
- [x] Step-by-step OAuth configuration instructions
- [x] Token refresh workflow documentation
- [x] Troubleshooting guide for common OAuth errors

**Security Features:**
- [x] Stateless JWT authentication (no server-side sessions)
- [x] Automatic last_login_at tracking
- [x] Active user validation
- [x] Deleted user rejection
- [x] Secure token expiration (30 min access, 7 days refresh)

### 📋 Future Enhancements (Phase 2+)
- [ ] Token revocation/blacklist
- [ ] Multi-provider OAuth (GitHub, Apple)
- [ ] Session management dashboard
- [ ] Two-factor authentication (2FA)
- [ ] Email notifications for new logins

---

## Authentication Strategy

### Why Google OAuth Only?

**Decision**: For MVP, Logbook uses Google OAuth exclusively.

**Benefits**:
1. **No password storage**: Google handles all authentication
2. **No password reset flow**: Eliminates forgot-password, email verification
3. **Better security**: Leverages Google's world-class security
4. **User convenience**: Most users already have Google accounts
5. **Email verification**: Google-verified emails are always trusted
6. **Faster MVP**: Simpler implementation, fewer edge cases

**Trade-offs**:
- Users without Google accounts cannot sign up (acceptable for MVP)
- Dependency on Google's service (low risk, high uptime)
- Future: Can add more OAuth providers (GitHub, Apple, etc.)

---

## Authentication Flow

### 1. User Login (First Time)

```
┌─────────┐                 ┌──────────┐                 ┌────────┐                 ┌──────────┐
│ Browser │                 │ Logbook  │                 │ Google │                 │ Database │
└────┬────┘                 └────┬─────┘                 └───┬────┘                 └────┬─────┘
     │                           │                           │                           │
     │ 1. Click "Login with Google"                          │                           │
     ├──────────────────────────>│                           │                           │
     │                           │                           │                           │
     │ 2. Redirect to Google OAuth                           │                           │
     │<──────────────────────────┤                           │                           │
     │                           │                           │                           │
     │ 3. User authenticates with Google                     │                           │
     ├──────────────────────────────────────────────────────>│                           │
     │                           │                           │                           │
     │ 4. Google redirects back with auth code               │                           │
     │<──────────────────────────────────────────────────────┤                           │
     │                           │                           │                           │
     │ 5. Send auth code to backend                          │                           │
     ├──────────────────────────>│                           │                           │
     │                           │                           │                           │
     │                           │ 6. Exchange code for tokens                           │
     │                           ├──────────────────────────>│                           │
     │                           │                           │                           │
     │                           │ 7. Return access token + user info                    │
     │                           │<──────────────────────────┤                           │
     │                           │                           │                           │
     │                           │ 8. Check if user exists (by google_id)                │
     │                           ├──────────────────────────────────────────────────────>│
     │                           │                           │                           │
     │                           │ 9. User not found (first time login)                  │
     │                           │<──────────────────────────────────────────────────────┤
     │                           │                           │                           │
     │                           │ 10. Create user with Google data                      │
     │                           ├──────────────────────────────────────────────────────>│
     │                           │                           │                           │
     │                           │ 11. Return new user                                   │
     │                           │<──────────────────────────────────────────────────────┤
     │                           │                           │                           │
     │                           │ 12. Generate JWT tokens (access + refresh)            │
     │                           │                           │                           │
     │ 13. Return tokens + user data                         │                           │
     │<──────────────────────────┤                           │                           │
     │                           │                           │                           │
     │ 14. Store tokens, navigate to dashboard              │                           │
     │                           │                           │                           │
```

### 2. User Login (Returning User)

```
Steps 1-7: Same as first time login
Step 8: Check if user exists (by google_id)
Step 9: User found → Update last_login_at timestamp
Step 10: Generate JWT tokens (access + refresh)
Step 11: Return tokens + user data
```

### 3. Authenticated API Requests

```
┌─────────┐                 ┌──────────┐                 ┌──────────┐
│ Browser │                 │ Logbook  │                 │ Database │
└────┬────┘                 └────┬─────┘                 └────┬─────┘
     │                           │                           │
     │ 1. GET /trips/me          │                           │
     │    Authorization: Bearer <access_token>               │
     ├──────────────────────────>│                           │
     │                           │                           │
     │                           │ 2. Validate JWT token     │
     │                           │                           │
     │                           │ 3. Extract user_id from token
     │                           │                           │
     │                           │ 4. Get user from DB       │
     │                           ├──────────────────────────>│
     │                           │                           │
     │                           │ 5. Return user            │
     │                           │<──────────────────────────┤
     │                           │                           │
     │                           │ 6. Check is_active, deleted_at
     │                           │                           │
     │                           │ 7. Get user's trips       │
     │                           ├──────────────────────────>│
     │                           │                           │
     │                           │ 8. Return trips           │
     │                           │<──────────────────────────┤
     │                           │                           │
     │ 9. Return trips data      │                           │
     │<──────────────────────────┤                           │
     │                           │                           │
```

### 4. Token Refresh

```
┌─────────┐                 ┌──────────┐                 ┌──────────┐
│ Browser │                 │ Logbook  │                 │ Database │
└────┬────┘                 └────┬─────┘                 └────┬─────┘
     │                           │                           │
     │ 1. Access token expired   │                           │
     │                           │                           │
     │ 2. POST /auth/refresh     │                           │
     │    Body: {refresh_token}  │                           │
     ├──────────────────────────>│                           │
     │                           │                           │
     │                           │ 3. Validate refresh token │
     │                           │                           │
     │                           │ 4. Extract user_id        │
     │                           │                           │
     │                           │ 5. Verify user exists & active
     │                           ├──────────────────────────>│
     │                           │                           │
     │                           │ 6. Return user            │
     │                           │<──────────────────────────┤
     │                           │                           │
     │                           │ 7. Generate new access token
     │                           │                           │
     │ 8. Return new access token│                           │
     │<──────────────────────────┤                           │
     │                           │                           │
     │ 9. Update stored token    │                           │
     │                           │                           │
```

---

## JWT Token Structure

### Access Token

**Purpose**: Short-lived token for API authentication
**Expiration**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
**Storage**: Frontend stores in memory or sessionStorage (NOT localStorage for security)

**Payload**:
```json
{
  "sub": 123,                    // User ID
  "type": "access",              // Token type
  "exp": 1720540800,             // Expiration timestamp
  "iat": 1720539000              // Issued at timestamp
}
```

**Example**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEyMywidHlwZSI6ImFjY2VzcyIsImV4cCI6MTcyMDU0MDgwMCwiaWF0IjoxNzIwNTM5MDAwfQ.signature
```

### Refresh Token

**Purpose**: Long-lived token to obtain new access tokens
**Expiration**: 30 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
**Storage**: Frontend stores in httpOnly cookie (most secure) or localStorage

**Payload**:
```json
{
  "sub": 123,                    // User ID
  "type": "refresh",             // Token type
  "exp": 1723132800,             // Expiration (30 days later)
  "iat": 1720539000              // Issued at timestamp
}
```

**Security**:
- MUST verify token type before use (prevent access token used as refresh)
- Refresh tokens should be rotated on each use (future enhancement)
- Store refresh token hash in database for revocation (Phase 2)

---

## Security Implementation

### 1. JWT Configuration

**File**: `app/core/config.py`
```python
SECRET_KEY: str  # Generated with: openssl rand -hex 32
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 30
```

**Security Notes**:
- SECRET_KEY must be strong, random, and kept secret
- Never commit SECRET_KEY to git (use .env file)
- Rotate SECRET_KEY in production periodically
- Use HS256 algorithm (HMAC with SHA-256)

### 2. Token Creation

**File**: `app/core/security.py`

```python
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### 3. Token Validation

**File**: `app/core/security.py`

```python
def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None  # Wrong token type
        return payload
    except JWTError:
        return None  # Invalid signature, expired, etc.
```

### 4. Dependency Injection

**File**: `app/core/deps.py`

**Get Current User ID**:
```python
async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Extract user ID from JWT token."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return payload.get("sub")
```

**Get Current User Object**:
```python
async def get_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get user object from database."""
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Get Current Active User**:
```python
async def get_current_active_user(current_user = Depends(get_current_user)):
    """Ensure user is active and not deleted."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    if current_user.deleted_at is not None:
        raise HTTPException(status_code=403, detail="User deleted")
    return current_user
```

---

## API Endpoints (To Be Created)

### Google OAuth Flow

**1. Initiate OAuth Login**
```
GET /auth/google
```
**Purpose**: Redirect user to Google OAuth consent screen
**Response**: 302 Redirect to Google

**2. OAuth Callback**
```
GET /auth/google/callback?code={auth_code}
```
**Purpose**: Handle Google OAuth callback
**Flow**:
1. Exchange auth code for Google access token
2. Fetch user info from Google
3. Check if user exists (by google_id)
4. If new: Create user
5. If existing: Update last_login_at
6. Generate JWT tokens
7. Return tokens + user data

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "username": null,
    "first_name": "John",
    "last_name": "Doe",
    "profile_photo_url": "https://lh3.googleusercontent.com/..."
  }
}
```

### Token Management

**3. Refresh Access Token**
```
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}
```
**Purpose**: Get new access token using refresh token
**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**4. Logout**
```
POST /auth/logout
Authorization: Bearer {access_token}
```
**Purpose**: Logout user (frontend clears tokens)
**Note**: Stateless JWT means no server-side session to invalidate
**Future**: Maintain token blacklist or session store

### User Info

**5. Get Current User**
```
GET /auth/me
Authorization: Bearer {access_token}
```
**Purpose**: Get current authenticated user's profile
**Response**: UserResponse schema

---

## Pydantic Schemas (To Be Created)

### TokenResponse
```python
class TokenResponse(BaseModel):
    """Response when user logs in or refreshes token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires
```

### TokenRefreshRequest
```python
class TokenRefreshRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str
```

### TokenRefreshResponse
```python
class TokenRefreshResponse(BaseModel):
    """Response when refreshing token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
```

### GoogleUserInfo
```python
class GoogleUserInfo(BaseModel):
    """User info from Google OAuth."""
    id: str  # Google ID
    email: str
    verified_email: bool
    name: Optional[str]
    given_name: Optional[str]
    family_name: Optional[str]
    picture: Optional[str]
```

---

## Business Logic (To Be Created)

### OAuth Handler

**File**: `app/features/auth/oauth.py`

```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

async def get_google_user_info(token: str) -> GoogleUserInfo:
    """Fetch user info from Google using access token."""
    # Make request to Google's userinfo endpoint
    # Parse response into GoogleUserInfo schema
    pass
```

### User Creation/Update

**File**: `app/features/auth/service.py`

```python
def get_or_create_user_from_google(db: Session, google_user: GoogleUserInfo) -> User:
    """Get existing user or create new user from Google OAuth data."""
    # Check if user exists by google_id
    user = get_user_by_google_id(db, google_user.id)

    if user:
        # Existing user: Update last_login_at
        user.last_login_at = datetime.utcnow()
        db.commit()
        return user
    else:
        # New user: Create from Google data
        user_create = UserCreate(
            google_id=google_user.id,
            email=google_user.email,
            email_verified=google_user.verified_email,
            first_name=google_user.given_name,
            last_name=google_user.family_name,
            profile_photo_url=google_user.picture
        )
        return create_user(db, user_create)
```

### Token Generation

```python
def generate_tokens_for_user(user: User) -> TokenResponse:
    """Generate access and refresh tokens for user."""
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
```

---

## Google OAuth Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "Logbook"
3. Enable Google+ API

### 2. Configure OAuth Consent Screen

1. Navigate to "OAuth consent screen"
2. Choose "External" user type
3. Fill in app information:
   - App name: "Logbook"
   - User support email: your email
   - Developer contact: your email
4. Scopes: Add `openid`, `email`, `profile`
5. Test users: Add your email for testing

### 3. Create OAuth Credentials

1. Navigate to "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Web application"
4. Name: "Logbook Web Client"
5. Authorized JavaScript origins:
   - `http://localhost:3000` (development)
   - `https://logbook.app` (production)
6. Authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/google/callback` (backend dev)
   - `https://api.logbook.app/api/v1/auth/google/callback` (production)
7. Click "Create"
8. Copy Client ID and Client Secret

### 4. Add to Environment Variables

**File**: `.env`
```bash
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

**File**: `app/core/config.py`
```python
class Settings(BaseSettings):
    # ... existing fields
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
```

---

## Testing Strategy

### Unit Tests (pytest)
- Test JWT token creation and validation
- Test token expiration handling
- Test token type validation (access vs refresh)
- Test user creation from Google data
- Test user lookup by google_id
- Test last_login_at update

### Integration Tests
- Test full OAuth flow (mock Google responses)
- Test token refresh endpoint
- Test protected endpoints (require authentication)
- Test inactive user rejection
- Test deleted user rejection

### Bruno Collection
- `collection/auth/google-login.bru` (manual test, opens browser)
- `collection/auth/refresh-token.bru`
- `collection/auth/logout.bru`
- `collection/auth/get-me.bru`

---

## Security Considerations

### 1. Token Security
- **Never log tokens**: Don't log access/refresh tokens in production
- **HTTPS only**: All token transmission over HTTPS
- **Short expiration**: Access tokens expire in 30 minutes
- **Validate token type**: Prevent access token used as refresh token

### 2. Google OAuth
- **Verify email**: Check `verified_email` field from Google
- **Validate state parameter**: Prevent CSRF attacks (add state to OAuth flow)
- **Secure redirect URIs**: Only allow whitelisted redirect URIs
- **Keep secrets secret**: Never commit GOOGLE_CLIENT_SECRET

### 3. User Data
- **Don't expose google_id**: Internal use only, never in API responses
- **Email privacy**: Only show to user themselves, not publicly
- **Profile photo**: Use Google's CDN URL, don't download/reupload

### 4. Rate Limiting
- **Login attempts**: Limit OAuth callback requests (prevent abuse)
- **Token refresh**: Rate limit refresh endpoint
- **API requests**: General rate limiting on all endpoints

### 5. Error Messages
- **Generic errors**: Don't reveal if email exists ("Invalid credentials" vs "User not found")
- **No enumeration**: Prevent attacker from discovering registered emails

---

## Future Enhancements

### Multi-Provider OAuth
```python
# Support multiple OAuth providers
class OAuthProvider(str, Enum):
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"

# Add to User model:
provider = Column(String(20), default="google")
provider_id = Column(String(255))  # Generic provider user ID
```

### Token Revocation
- Store refresh token hash in database
- Revoke tokens on logout
- Revoke all tokens on password change (future)
- Expired token cleanup job

### Session Management
- Track active sessions per user
- Allow user to view/revoke sessions
- "You are logged in on 3 devices"

### Two-Factor Authentication (2FA)
- Optional 2FA for extra security
- TOTP (Time-based One-Time Password)
- Backup codes

### Account Linking
- Link multiple OAuth providers to one account
- "Sign in with Google or GitHub"
- Merge duplicate accounts

### Email Notifications
- Login from new device/location
- Unusual activity detected
- New session started

---

## Related Documentation

- [User Model Documentation](../users/README.md)
- [Core Security Module](../../core/security.py)
- [Core Dependencies Module](../../core/deps.py)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

---

## Environment Variables Required

```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

---

## Dependencies Required

```txt
# Already in requirements.txt:
python-jose[cryptography]  # JWT creation/validation
passlib[bcrypt]           # Password hashing (future use)
python-multipart          # OAuth form data

# To be added:
authlib                   # OAuth client library
httpx                     # HTTP client for Google API calls
```
