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
from app.features.trip_days import router as trip_days_router
from app.features.activities import router as activities_router
from app.features.bookings import router as bookings_router
from app.features.accommodations import router as accommodations_router
from app.features.transits import router as transits_router
from app.features.timeline import router as timeline_router
from app.features.expenses import router as expenses_router
from app.features.trip_notes import router as trip_notes_router
from app.features.packing_lists import router as packing_lists_router
from app.features.checklists import router as checklists_router

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

app.include_router(
    trip_days_router.router,
    prefix=f"{settings.API_V1_PREFIX}/trip-days",
    tags=["trip-days"]
)

app.include_router(
    activities_router.router,
    prefix=f"{settings.API_V1_PREFIX}/activities",
    tags=["activities"]
)

app.include_router(
    bookings_router.router,
    prefix=f"{settings.API_V1_PREFIX}/bookings",
    tags=["bookings"]
)

app.include_router(
    accommodations_router.router,
    prefix=f"{settings.API_V1_PREFIX}/accommodations",
    tags=["accommodations"]
)

app.include_router(
    transits_router.router,
    prefix=f"{settings.API_V1_PREFIX}/transits",
    tags=["transits"]
)

app.include_router(
    timeline_router.router,
    prefix=settings.API_V1_PREFIX,
    tags=["timeline"]
)

app.include_router(
    expenses_router.router,
    prefix=settings.API_V1_PREFIX,
    tags=["expenses"]
)

app.include_router(
    trip_notes_router.router,
    prefix=settings.API_V1_PREFIX,
    tags=["trip-notes"]
)

app.include_router(
    packing_lists_router.router,
    prefix=settings.API_V1_PREFIX,
    tags=["packing-lists"]
)

app.include_router(
    checklists_router.router,
    prefix=settings.API_V1_PREFIX,
    tags=["checklists"]
)
