"""Utility endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from urllib.parse import urlparse
import httpx

from app.core.deps import get_current_active_user
from app.features.users.models import User

router = APIRouter()

ALLOWED_HOSTS = {
    "maps.app.goo.gl",
    "goo.gl",
    "google.com",
    "www.google.com",
    "google.co.in",
    "www.google.co.in",
}

@router.get("/utils/expand-url", status_code=status.HTTP_200_OK)
async def expand_url(
    url: str = Query(..., description="URL to expand"),
    current_user: User = Depends(get_current_active_user)
):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise HTTPException(status_code=400, detail="Invalid URL")

        host = parsed.hostname or ""
        if host not in ALLOWED_HOSTS:
            raise HTTPException(status_code=400, detail="Host not allowed")

        async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
            resp = await client.get(url)
            return {"url": str(resp.url)}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to expand URL")
