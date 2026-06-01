"""
API routes for Trip management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user, get_current_active_user_optional
from app.features.users.models import User
from app.features.trips import crud
from app.features.trips.schemas import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripListResponse,
    TripTimelineResponse
)
from app.features.trips.unsplash import get_random_travel_photo
from app.features.destination_photos import crud as destination_photos_crud
from app.shared.enums import TripStatus

router = APIRouter()


@router.get("/", response_model=List[TripListResponse])
async def list_my_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[TripStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all trips created by the authenticated user."""
    trips = crud.get_trips_by_user(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status_filter=status_filter
    )
    return trips


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_in: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new trip."""
    try:
        # Auto-generate cover image if not provided.
        # Uses the destination-level photo cache: reuses a pooled photo for the
        # same city/country across trips, only calling Unsplash when the pool
        # is still thin. Drastically cuts third-party API calls.
        if not trip_in.cover_photo_url:
            try:
                image_url = await destination_photos_crud.resolve_destination_photo(
                    db,
                    city=trip_in.primary_destination_city,
                    country=trip_in.primary_destination_country,
                    fallback_query=trip_in.name,
                )
                if image_url:
                    trip_in.cover_photo_url = image_url
            except Exception as e:
                # Never block trip creation on photo resolution.
                print(f"Failed to auto-generate cover image: {e}")

        trip = crud.create_trip(db, trip_in, user_id=current_user.id)
        # Force serialization to check for errors
        return TripResponse.from_orm(trip)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Serialization Error: {str(e)}"
        )


@router.get("/public", response_model=List[TripListResponse])
async def browse_public_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    country: Optional[str] = None,
    city: Optional[str] = None,
    trip_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Browse public trips (no authentication required)."""
    trips = crud.get_public_trips(
        db,
        skip=skip,
        limit=limit,
        country=country,
        city=city,
        trip_type=trip_type
    )
    return trips


@router.get("/search", response_model=List[TripListResponse])
async def search_trips(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """
    Search trips by name, description, or destination.

    If authenticated, includes user's private trips in results.
    """
    user_id = current_user.id if current_user else None
    trips = crud.search_trips(
        db,
        search_query=q,
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    return trips


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user_optional)
):
    """
    Get trip by ID.

    Returns trip if:
    - User is the owner (any visibility), OR
    - Trip is public or unlisted

    Increments view count if not the owner.
    """
    user_id = current_user.id if current_user else None
    trip = crud.get_trip_by_id(db, trip_id, user_id=user_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or access denied"
        )

    # Increment view count if not the owner
    if not current_user or trip.created_by != current_user.id:
        crud.increment_trip_views(db, trip)

    return trip


@router.get("/{trip_id}/timeline", response_model=TripTimelineResponse)
async def get_trip_timeline(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user_optional)
):
    """
    Get full timeline for a trip (Days + Activities).
    """
    # Check access
    trip = crud.get_trip_by_id(db, trip_id, user_id=current_user.id if current_user else None)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or access denied"
        )

    days = crud.get_trip_timeline(db, trip_id)
    
    return {
        "trip_id": trip_id,
        "days": days
    }


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: int,
    trip_in: TripUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a trip (owner only)."""
    trip = crud.get_trip_by_id(db, trip_id, user_id=current_user.id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    if not crud.check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this trip"
        )

    trip = crud.update_trip(db, trip, trip_in)
    return trip


@router.delete("/{trip_id}", response_model=dict)
async def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Soft delete a trip (owner only)."""
    trip = crud.get_trip_by_id(db, trip_id, user_id=current_user.id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    if not crud.check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this trip"
        )

    # Store info for response
    trip_name = trip.name

    crud.delete_trip(db, trip)

    return {
        "message": "Trip deleted successfully",
        "trip_id": trip_id,
        "trip_name": trip_name
    }


@router.get("/stats/me")
async def get_my_trip_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get trip statistics for the authenticated user."""
    total_trips = crud.get_user_trip_count(db, current_user.id)

    return {
        "total_trips": total_trips,
        "user_id": current_user.id
    }


@router.patch("/{trip_id}/cover", response_model=TripResponse)
async def regenerate_trip_cover(
    trip_id: int,
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Regenerate trip cover image using Unsplash API.
    """
    trip = crud.get_trip_by_id(db, trip_id, user_id=current_user.id)
    
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
        
    if not crud.check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this trip"
        )
        
    # Use provided query or trip destination/title
    search_query = query or trip.primary_destination_city or trip.primary_destination_country or trip.name
    
    # Get image
    image_url = await get_random_travel_photo(search_query)
    
    # Update trip
    trip_update = TripUpdate(cover_photo_url=image_url)
    updated_trip = crud.update_trip(db, trip, trip_update)
    
    return updated_trip

@router.patch("/{trip_id}/banner", response_model=TripResponse)
async def regenerate_trip_banner(
    trip_id: int,
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Regenerate trip banner image using Unsplash API.
    """
    trip = crud.get_trip_by_id(db, trip_id, user_id=current_user.id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    if not crud.check_trip_ownership(trip, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this trip"
        )

    search_query = query or trip.primary_destination_city or trip.primary_destination_country or trip.name
    search_query = f"{search_query} scenic wide landscape"

    image_url = await get_random_travel_photo(search_query)

    trip_update = TripUpdate(banner_photo_url=image_url)
    updated_trip = crud.update_trip(db, trip, trip_update)

    return updated_trip

