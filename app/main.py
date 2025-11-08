"""
FastAPI application entry point.

This module creates and configures the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Travel planning and tracking API",
    debug=settings.DEBUG,
)

# Add Session Middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # Session expires after 1 hour
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


# Register API routers
from app.features.auth import router as auth_router
from app.features.users import router as users_router
from app.features.trips import router as trips_router

app.include_router(
    auth_router.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["auth"]
)

app.include_router(
    users_router.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"]
)

app.include_router(
    trips_router.router,
    prefix=f"{settings.API_V1_PREFIX}/trips",
    tags=["trips"]
)

# TODO: Register remaining routers
# from app.features.trip_days import router as trip_days_router
# app.include_router(trip_days_router.router, prefix=f"{settings.API_V1_PREFIX}/trip_days", tags=["trip_days"])
