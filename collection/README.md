# Bruno API Collection for Logbook

## Setup

1. **Install Bruno**
   - Download from: https://www.usebruno.com/
   - Or install via Homebrew: `brew install bruno`

2. **Import Collection**
   - Open Bruno
   - Click "Open Collection"
   - Navigate to this `collection/` folder
   - Select the folder

3. **Configure Environment**
   - Select "local" environment in Bruno
   - The `baseUrl` will automatically be set to `http://localhost:8000/api/v1`

4. **Authentication**
   - After logging in via Google OAuth, copy the access token
   - Paste it into the `accessToken` variable in the environment
   - All authenticated requests will automatically use this token

## Collection Structure

```
collection/
├── bruno.json                      # Collection config
├── environments/
│   ├── local.bru                  # Local environment (localhost:8000)
│   └── production.bru             # Production environment
├── auth/
│   ├── google-login.bru           # GET /auth/google
│   └── google-callback.bru        # GET /auth/google/callback
├── trips/
│   ├── create-trip.bru            # POST /trips/
│   ├── list-trips.bru             # GET /trips/
│   ├── get-trip.bru               # GET /trips/{id}
│   ├── update-trip.bru            # PUT /trips/{id}
│   └── delete-trip.bru            # DELETE /trips/{id}
└── trip-days/
    ├── create-trip-day.bru        # POST /trip_days/
    ├── list-trip-days.bru         # GET /trip_days/
    ├── get-trip-day.bru           # GET /trip_days/{id}
    ├── update-trip-day.bru        # PUT /trip_days/{id}
    └── delete-trip-day.bru        # DELETE /trip_days/{id}
```

## Usage

### 1. Start the Server
```bash
uvicorn app.main:app --reload
```

### 2. Test Health Check
- Open `health-check.bru` (to be created)
- Click "Send"
- Should return: `{"status": "healthy"}`

### 3. Authenticate
- Open `auth/google-login.bru`
- Click "Send" - will redirect to Google OAuth
- Complete OAuth flow in browser
- Copy the access token from callback response
- Paste into environment variable `accessToken`

### 4. Make Authenticated Requests
- All requests in `trips/` and `trip-days/` folders
- Automatically include `Authorization: Bearer {{accessToken}}` header
- Test creating a trip, listing trips, etc.

## Environment Variables

### Local Environment
- `baseUrl`: `http://localhost:8000/api/v1`
- `accessToken`: Your JWT access token (set after login)
- `refreshToken`: Your JWT refresh token (for token refresh)

### Production Environment
- `baseUrl`: Your production API URL
- `accessToken`: Production access token
- `refreshToken`: Production refresh token

## Tips

1. **Variable Syntax**: Use `{{variableName}}` to reference environment variables
2. **Auto-complete**: Bruno provides auto-complete for variables
3. **Multiple Environments**: Switch between local/production easily
4. **Request History**: Bruno saves request history
5. **Collections**: Organize requests into folders for better management

## Coming Soon

As we implement features, we'll add:
- Trip collaborator requests (Phase 2)
- Public trip discovery requests (Phase 2)
- Expense tracking requests (Phase 4)
- Notes and packing list requests (Phase 5)
- Photo upload requests (Phase 6)
