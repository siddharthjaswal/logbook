"""
FastAPI application entry point.

This module creates and configures the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Travel planning and tracking API",
    debug=settings.DEBUG,
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
from app.features.users import router as users_router

app.include_router(
    users_router.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"]
)

# TODO: Register remaining routers
# from app.features.auth import router as auth_router
# from app.features.trips import router as trips_router
# from app.features.trip_days import router as trip_days_router
# app.include_router(auth_router.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["auth"])
# app.include_router(trips_router.router, prefix=f"{settings.API_V1_PREFIX}/trips", tags=["trips"])
# app.include_router(trip_days_router.router, prefix=f"{settings.API_V1_PREFIX}/trip_days", tags=["trip_days"])
