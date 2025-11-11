# Google OAuth Setup Guide

This guide walks you through setting up Google OAuth for Logbook authentication.

## Prerequisites

- Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)

---

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter project details:
   - **Project name**: `Logbook` (or your preferred name)
   - **Organization**: Select if applicable
5. Click "Create"
6. Wait for project creation to complete
7. Select the newly created project from the dropdown

---

## Step 2: Enable Google+ API

1. In the Google Cloud Console, open the navigation menu (☰)
2. Go to **APIs & Services** → **Library**
3. Search for "Google+ API"
4. Click on "Google+ API"
5. Click **Enable**

> **Note**: While Google+ was deprecated, the API is still used for OAuth user info

---

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (for testing with any Google account)
3. Click **Create**

### App Information

Fill in the required fields:

- **App name**: `Logbook`
- **User support email**: Your email address
- **App logo**: (Optional) Upload your app logo
- **Application home page**: `http://localhost:3000` (or your frontend URL)
- **Application privacy policy link**: (Can skip for development)
- **Application terms of service link**: (Can skip for development)

### Developer Contact Information

- **Email addresses**: Your email address

Click **Save and Continue**

### Scopes

1. Click **Add or Remove Scopes**
2. Select the following scopes:
   - `openid`
   - `email`
   - `profile`

   Or manually add:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`

3. Click **Update**
4. Click **Save and Continue**

### Test Users (Optional for Development)

For development, you can add test users who can access the app:

1. Click **Add Users**
2. Enter email addresses of test users
3. Click **Save and Continue**

### Summary

Review your settings and click **Back to Dashboard**

---

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**

### Application Type

- Select **Web application**

### Configure Web Application

**Name**: `Logbook Web Client` (or your preferred name)

**Authorized JavaScript origins**:
- `http://localhost:3000` (frontend development)
- `http://localhost:5173` (Vite default port)
- Add production URLs when deploying: `https://yourdomain.com`

**Authorized redirect URIs**:
- `http://localhost:8000/api/v1/auth/google/callback` (backend callback)
- Add production URLs when deploying: `https://api.yourdomain.com/api/v1/auth/google/callback`

### Create

1. Click **Create**
2. A dialog will appear with your credentials
3. **Important**: Copy the following:
   - **Client ID**: Long string ending with `.apps.googleusercontent.com`
   - **Client Secret**: Random string (keep this secret!)

---

## Step 5: Configure Environment Variables

Add the credentials to your `.env` file:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
```

### Example `.env`:

```bash
# Application Configuration
APP_NAME=Logbook API
VERSION=0.1.0
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://localhost/logbook

# Google OAuth
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# JWT
SECRET_KEY=your_secret_key_from_openssl
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# API
API_V1_PREFIX=/api/v1
```

---

## Step 6: Test OAuth Flow

### Method 1: Browser Testing

1. Start your backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/api/v1/auth/google
   ```

3. You should be redirected to Google's sign-in page

4. Sign in with your Google account

5. Grant permissions to the app

6. You'll be redirected back to the callback URL with a JSON response containing:
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "token_type": "bearer",
     "expires_in": 604800,
     "user": {
       "id": 1,
       "email": "your.email@gmail.com",
       "first_name": "Your",
       "last_name": "Name",
       ...
     }
   }
   ```

7. **Save the tokens**:
   - Copy the `access_token`
   - Copy the `refresh_token`
   - Store them in Bruno's environment variables

### Method 2: Using Bruno/Postman

Since OAuth requires browser interaction, you'll need to:

1. Complete the browser flow above
2. Copy the `access_token` from the response
3. Add it to Bruno's environment variables as `{{accessToken}}`
4. Copy the `refresh_token` as `{{refreshToken}}`
5. Now you can use authenticated endpoints in Bruno

---

## Step 7: Verify Setup

Test the following endpoints in Bruno:

1. **Refresh Token** (`POST /api/v1/auth/refresh`):
   - Use your refresh token to get a new access token
   - Verifies token refresh mechanism works

2. **Get Current User** (`GET /api/v1/auth/me`):
   - Use your access token
   - Should return your user profile

3. **Logout** (`POST /api/v1/auth/logout`):
   - Use your access token
   - Should return 204 No Content

---

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Problem**: The redirect URI doesn't match what's configured in Google Cloud Console

**Solution**:
1. Check your `.env` file: `GOOGLE_REDIRECT_URI` should match exactly
2. Check Google Cloud Console → Credentials → Your OAuth Client
3. Ensure `http://localhost:8000/api/v1/auth/google/callback` is in the authorized redirect URIs
4. No trailing slashes, exact match required

### Error: "invalid_client"

**Problem**: Client ID or Client Secret is incorrect

**Solution**:
1. Go to Google Cloud Console → Credentials
2. Click on your OAuth 2.0 Client ID
3. Verify the Client ID and regenerate Client Secret if needed
4. Update your `.env` file with correct values
5. Restart your server

### Error: "access_denied"

**Problem**: User denied permission or app is not verified

**Solution**:
1. Try logging in again and grant all permissions
2. If using External user type, add yourself as a test user
3. Check OAuth consent screen configuration

### Error: "Token has been expired or revoked"

**Problem**: Access token expired (after 7 days) or was invalidated

**Solution**:
1. Use the refresh token to get a new access token
2. Send `POST /api/v1/auth/refresh` with your refresh token
3. Update `{{accessToken}}` with the new token

### OAuth Works But Callback Returns Error

**Problem**: Backend error during user creation

**Solution**:
1. Check backend logs for error details
2. Ensure database is running and accessible
3. Verify all migrations have been applied
4. Check that user table exists in database

---

## Production Deployment

When deploying to production:

1. **Update OAuth Consent Screen**:
   - Add production domain
   - Add privacy policy URL
   - Add terms of service URL
   - Submit for verification (if needed)

2. **Update Credentials**:
   - Add production JavaScript origins: `https://yourdomain.com`
   - Add production redirect URI: `https://api.yourdomain.com/api/v1/auth/google/callback`

3. **Update Environment Variables**:
   ```bash
   GOOGLE_REDIRECT_URI=https://api.yourdomain.com/api/v1/auth/google/callback
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

4. **Security**:
   - Use HTTPS for all OAuth redirects
   - Keep Client Secret secure (use secrets manager)
   - Never commit credentials to git
   - Rotate secrets regularly

---

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes)
- [OpenID Connect](https://openid.net/connect/)
- [Authlib Documentation](https://docs.authlib.org/)

---

## Need Help?

If you encounter issues not covered here:

1. Check the backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure your Google Cloud project is configured properly
4. Check that all required APIs are enabled
5. Review the Google Cloud Console audit logs
