"""
CRUD + caching logic for destination photos.

Flow when a trip needs a cover photo:

    resolve_destination_photo(db, city, country)
        → build cache_key (city w/ country fallback)
        → count cached photos for that key
        → if pool is healthy (>= POOL_TARGET): return a random cached one  (0 API calls)
        → else: fetch a fresh one from Unsplash, store it, return it
        → on any Unsplash failure: fall back to any cached photo, else a static URL
"""

import random
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.features.destination_photos.models import DestinationPhoto
from app.features.trips.unsplash import fetch_travel_photo

# How many distinct photos we aim to keep per destination before we stop
# calling Unsplash. Higher = more variety but more initial API calls.
POOL_TARGET = 5


def build_cache_key(city: Optional[str], country: Optional[str]) -> Optional[str]:
    """Normalize city/country into a canonical cache key.

    "Reykjavik", "Iceland" -> "iceland|reykjavik"
    None,        "Iceland" -> "iceland"
    """
    c = (country or "").strip().lower()
    ci = (city or "").strip().lower()
    if c and ci:
        return f"{c}|{ci}"
    if ci:
        return ci
    if c:
        return c
    return None


def get_cached_photos(db: Session, cache_key: str) -> list[DestinationPhoto]:
    return (
        db.query(DestinationPhoto)
        .filter(DestinationPhoto.cache_key == cache_key)
        .all()
    )


def _store_photo(
    db: Session,
    *,
    cache_key: str,
    city: Optional[str],
    country: Optional[str],
    photo: dict,
) -> DestinationPhoto:
    row = DestinationPhoto(
        cache_key=cache_key,
        city=(city or None),
        country=(country or None),
        photo_url=photo["url"],
        source="unsplash",
        external_id=photo.get("external_id"),
        photographer_name=photo.get("photographer_name"),
        photographer_url=photo.get("photographer_url"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


async def resolve_destination_photo(
    db: Session,
    *,
    city: Optional[str],
    country: Optional[str],
    fallback_query: Optional[str] = None,
) -> Optional[str]:
    """Return a photo URL for the destination, using the cache first.

    `fallback_query` is used as the Unsplash search term when neither city nor
    country is set (e.g. the trip name).
    """
    cache_key = build_cache_key(city, country)

    # No destination at all — fall back to a one-off Unsplash search (uncached).
    if not cache_key:
        if not fallback_query:
            return None
        photo = await fetch_travel_photo(fallback_query)
        return photo["url"] if photo else None

    cached = get_cached_photos(db, cache_key)

    # Pool is healthy → reuse a random cached photo, zero API calls.
    if len(cached) >= POOL_TARGET:
        return random.choice(cached).photo_url

    # Pool is thin → try to enrich it with a fresh Unsplash photo.
    search_query = city or country or fallback_query or ""
    try:
        photo = await fetch_travel_photo(search_query)
    except Exception as e:  # network/library failure — degrade gracefully
        print(f"[destination_photos] Unsplash fetch failed: {e}")
        photo = None

    if photo and photo.get("url"):
        # Avoid storing a duplicate of one we already have.
        existing_ids = {c.external_id for c in cached if c.external_id}
        if photo.get("external_id") and photo["external_id"] in existing_ids:
            return photo["url"]
        try:
            row = _store_photo(
                db, cache_key=cache_key, city=city, country=country, photo=photo
            )
            return row.photo_url
        except Exception as e:
            db.rollback()
            print(f"[destination_photos] store failed (likely race): {e}")
            return photo["url"]

    # Unsplash failed — serve any cached photo we already had.
    if cached:
        return random.choice(cached).photo_url

    return None
