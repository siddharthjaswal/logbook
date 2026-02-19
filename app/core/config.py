"""
Application configuration and settings.

Loads environment variables and provides a settings object.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Logbook API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # Database
    DATABASE_URL: str = "postgresql://localhost/logbook"

    # Google OAuth (Optional - will be set up in auth feature)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Google OAuth for Mobile Apps (Android/iOS ID token verification)
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None  # Web client ID for ID token verification
    GOOGLE_OAUTH_WEB_CLIENT_ID: Optional[str] = None  # Alternative web client ID

    # JWT
    SECRET_KEY: str  # Generate with: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]  # Frontend URLs
    FRONTEND_URL: str = "http://localhost:3000"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Unsplash (Cover Images)
    UNSPLASH_ACCESS_KEY: Optional[str] = None

    # Resend Email
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM: Optional[str] = None

    # Google Maps / Places
    GOOGLE_MAPS_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Create global settings instance
settings = Settings()
