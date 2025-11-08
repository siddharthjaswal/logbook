"""
OAuth configuration for Google authentication.

Sets up the OAuth client using authlib.
"""

from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

# Initialize OAuth registry
oauth = OAuth()

# Register Google OAuth provider
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    },
)
