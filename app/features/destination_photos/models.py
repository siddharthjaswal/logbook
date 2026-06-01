"""
DestinationPhoto model — a destination-level cache of travel photos.

Instead of calling Unsplash every time a trip is created, we cache photos by
destination (city with country fallback) and reuse them across similar trips.
A small pool of photos per destination is kept so covers stay varied while
still drastically cutting third-party API calls.
"""

from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class DestinationPhoto(Base):
    """A cached travel photo for a given destination."""

    __tablename__ = "destination_photos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Cache key components (normalized: lowercased, trimmed)
    # `cache_key` is the canonical lookup value: "iceland|reykjavik" or "iceland"
    cache_key = Column(String(220), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(120), nullable=True, index=True)

    # The photo
    photo_url = Column(Text, nullable=False)
    source = Column(String(50), default="unsplash", nullable=False)

    # Unsplash attribution — required by their API guidelines
    external_id = Column(String(120), nullable=True)        # Unsplash photo id
    photographer_name = Column(String(200), nullable=True)
    photographer_url = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        # The same Unsplash photo should not be stored twice for one destination
        UniqueConstraint("cache_key", "external_id", name="uq_destination_photo_key_external"),
    )
