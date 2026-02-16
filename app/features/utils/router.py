"""Utility endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from urllib.parse import urlparse, parse_qs
import httpx
import re

from app.core.deps import get_current_active_user
from app.features.users.models import User
from app.core.config import settings

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


@router.get("/utils/resolve-map-link", status_code=status.HTTP_200_OK)
async def resolve_map_link(
    url: str = Query(..., description="Google Maps shared link"),
    current_user: User = Depends(get_current_active_user)
):
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=400, detail="Google Maps API key not configured")

    try:
        # Expand short link if needed
        parsed = urlparse(url)
        host = parsed.hostname or ""
        expanded_url = url

        if host in {"maps.app.goo.gl", "goo.gl"}:
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
                    resp = await client.get(url)
                    expanded_url = str(resp.url)
            except Exception:
                expanded_url = url

        # Parse expanded URL
        u = urlparse(expanded_url)
        qs = parse_qs(u.query)

        # Some links embed a nested `link=` param
        if 'link' in qs and qs['link']:
            try:
                expanded_url = qs['link'][0]
                u = urlparse(expanded_url)
                qs = parse_qs(u.query)
            except Exception:
                pass

        place_id = None
        for key in ["place_id", "query_place_id", "destination_place_id"]:
            if key in qs and qs[key]:
                place_id = qs[key][0]
                break

        name = None
        q = qs.get("q", [None])[0] or qs.get("query", [None])[0]
        if q:
            name = q

        place_match = re.search(r"/place/([^/]+)", u.path)
        if not name and place_match:
            name = place_match.group(1).replace("+", " ")

        # Try place_id from !1s segment in data param
        data_match = re.search(r"!1s([^!]+)", u.path + ("?" + u.query if u.query else ""))
        if not place_id and data_match:
            candidate = data_match.group(1)
            if candidate.startswith("ChI"):
                place_id = candidate

        # Extract lat/lng from @lat,lng
        lat = lng = None
        at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", u.path)
        if at_match:
            lat = float(at_match.group(1))
            lng = float(at_match.group(2))

        headers = {
            "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,location,photos,regularOpeningHours,types,rating",
        }

        async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
            place = None

            # If no name, try scraping og:title from expanded URL
            if not name:
                try:
                    html_resp = await client.get(expanded_url)
                    if html_resp.status_code == 200:
                        m = re.search(r"<meta property=\"og:title\" content=\"([^\"]+)\"", html_resp.text)
                        if m:
                            name = m.group(1)
                except Exception:
                    pass

            if place_id:
                resp = await client.get(f"https://places.googleapis.com/v1/places/{place_id}", headers=headers)
                if resp.status_code == 200:
                    place = resp.json()

            if not place:
                if not name:
                    name = expanded_url
                body = {"textQuery": name}
                if lat is not None and lng is not None:
                    body["locationBias"] = {
                        "circle": {
                            "center": {"latitude": lat, "longitude": lng},
                            "radius": 50000,
                        }
                    }
                resp = await client.post("https://places.googleapis.com/v1/places:searchText", json=body, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("places") or []
                    place = places[0] if places else None

        if not place:
            return {
                "expanded_url": expanded_url,
                "name": name,
                "lat": lat,
                "lng": lng,
                "debug": {
                    "place_id": place_id,
                    "query": name,
                }
            }

        display_name = (place.get("displayName") or {}).get("text")
        location = place.get("location") or {}
        return {
            "expanded_url": expanded_url,
            "name": display_name or name,
            "address": place.get("formattedAddress"),
            "lat": location.get("latitude") or lat,
            "lng": location.get("longitude") or lng,
            "place_id": place.get("id"),
            "types": place.get("types"),
            "rating": place.get("rating"),
        }

    except HTTPException:
        raise
    except Exception:
        return {"expanded_url": url, "error": "Failed to resolve map link"}
