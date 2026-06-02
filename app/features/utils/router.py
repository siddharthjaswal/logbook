"""Utility endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from urllib.parse import urlparse, parse_qs, unquote_plus
import httpx
import re

from app.core.deps import get_current_active_user
from app.features.users.models import User
from app.core.config import settings

router = APIRouter()

USER_AGENT = "Travlogue/1.0 (travel planner; +https://travlogue.app)"


def _extract_name(u, qs: dict) -> str | None:
    """Best-effort place name from the expanded Google Maps URL (free)."""
    q = qs.get("q", [None])[0] or qs.get("query", [None])[0]
    if q and not re.match(r"^-?\d+\.\d+,\s*-?\d+\.\d+$", q):
        return q
    place_match = re.search(r"/place/([^/@]+)", u.path)
    if place_match:
        return unquote_plus(place_match.group(1)).strip()
    return None


def _extract_latlng(u):
    """Coordinates from the URL (free). Prefer the precise place marker
    (!3d<lat>!4d<lng>) over the @lat,lng viewport center."""
    haystack = u.path + ("?" + u.query if u.query else "")
    marker = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", haystack)
    if marker:
        return float(marker.group(1)), float(marker.group(2))
    at_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", u.path)
    if at_match:
        return float(at_match.group(1)), float(at_match.group(2))
    return None, None


async def _nominatim_reverse(client: httpx.AsyncClient, lat: float, lng: float) -> dict | None:
    """Free reverse-geocode via OpenStreetMap Nominatim → address + category.
    Does NOT provide photos or opening hours (those need a paid provider)."""
    try:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "jsonv2", "lat": lat, "lon": lng, "zoom": 16, "addressdetails": 1},
            headers={"User-Agent": USER_AGENT},
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

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
    """Resolve a Google Maps link to place details.

    Free path (no API key): expand the short link and parse name + precise
    lat/lng + place id straight from the URL, then enrich the address &
    category via OpenStreetMap Nominatim (free).

    If GOOGLE_MAPS_API_KEY is configured, additionally enrich with Google
    Places (formatted address, rating, opening hours, photos).
    """
    try:
        # 1. Expand short link if needed
        parsed = urlparse(url)
        host = parsed.hostname or ""
        expanded_url = url

        if host in {"maps.app.goo.gl", "goo.gl"}:
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=10.0, headers={"User-Agent": USER_AGENT}) as client:
                    resp = await client.get(url)
                    expanded_url = str(resp.url)
            except Exception:
                expanded_url = url

        u = urlparse(expanded_url)
        qs = parse_qs(u.query)

        # Unwrap consent.google.* and nested `link=` wrappers
        if u.hostname and u.hostname.startswith('consent.google.') and qs.get('continue'):
            expanded_url = qs['continue'][0]
            u = urlparse(expanded_url)
            qs = parse_qs(u.query)
        if qs.get('link'):
            expanded_url = qs['link'][0]
            u = urlparse(expanded_url)
            qs = parse_qs(u.query)

        # 2. FREE extraction straight from the URL
        name = _extract_name(u, qs)
        lat, lng = _extract_latlng(u)

        place_id = None
        for key in ["place_id", "query_place_id", "destination_place_id"]:
            if qs.get(key):
                place_id = qs[key][0]
                break
        if not place_id:
            # Google's "ChIJ..." form is usable by the Places API; the hex
            # 0x..:0x.. / feature-id forms are kept only for reference.
            data_match = re.search(r"!1s(ChI[^!]+)", u.path + ("?" + u.query if u.query else ""))
            if data_match:
                place_id = data_match.group(1)

        result: dict = {
            "expanded_url": expanded_url,
            "name": name,
            "lat": lat,
            "lng": lng,
            "place_id": place_id,
            "source": "url",
        }
    except HTTPException:
        raise
    except Exception:
        # Even URL parsing failed — return the bare minimum.
        return {"expanded_url": url, "error": "Failed to parse map link"}

    # ── Enrichment is best-effort: a failure here must never discard the
    #    name / lat / lng we already parsed from the URL above. ──

    # Primary: Google Places (when a key is configured).
    if settings.GOOGLE_MAPS_API_KEY:
        try:
            place = await _google_places_enrich(name, lat, lng, place_id)
        except Exception:
            place = None
        if place:
            location = place.get("location") or {}
            hours = place.get("regularOpeningHours") or {}
            result.update({
                "name": (place.get("displayName") or {}).get("text") or name,
                "address": place.get("formattedAddress"),
                "lat": location.get("latitude") or lat,
                "lng": location.get("longitude") or lng,
                "place_id": place.get("id") or place_id,
                "types": place.get("types"),
                "rating": place.get("rating"),
                "opening_hours": hours.get("weekdayDescriptions"),
                "photos": [p.get("name") for p in (place.get("photos") or [])][:5] or None,
                "source": "google",
            })
            return result
        # Google was attempted but returned nothing (quota, error, no match):
        # flag it and fall through to the free fallback below.
        result["google_enrichment"] = "unavailable"

    # Fallback: free OSM Nominatim reverse-geocode for an address/category.
    if lat is not None and lng is not None:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                osm = await _nominatim_reverse(client, lat, lng)
        except Exception:
            osm = None
        if osm:
            addr = osm.get("display_name")
            osm_name = osm.get("name")
            category = osm.get("type") or osm.get("category")
            if addr:
                result["address"] = addr
            # Only trust OSM name/category when the URL gave us nothing —
            # reverse-geocoding can snap to an unrelated nearby node.
            if not result.get("name"):
                if osm_name:
                    result["name"] = osm_name
                if category:
                    result["types"] = [category]
            result["source"] = "osm" if result["source"] == "url" else result["source"]

    return result


async def _google_places_enrich(name, lat, lng, place_id) -> dict | None:
    """Google Places enrichment (only when an API key is set).

    Returns the place dict, or None on any non-200 / network failure so the
    caller can fall back gracefully.
    """
    field_mask = "id,displayName,formattedAddress,location,types,rating,regularOpeningHours,photos"
    headers = {"X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY, "X-Goog-FieldMask": field_mask}
    search_mask = "places." + ",places.".join(field_mask.split(","))
    headers_search = {"X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY, "X-Goog-FieldMask": search_mask}

    async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": USER_AGENT}) as client:
        if place_id and place_id.startswith("ChI"):
            try:
                resp = await client.get(f"https://places.googleapis.com/v1/places/{place_id}", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass  # fall through to text search
        if name:
            try:
                body: dict = {"textQuery": name}
                if lat is not None and lng is not None:
                    body["locationBias"] = {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": 50000}}
                resp = await client.post("https://places.googleapis.com/v1/places:searchText", json=body, headers=headers_search)
                if resp.status_code == 200:
                    places = resp.json().get("places") or []
                    return places[0] if places else None
            except Exception:
                pass
    return None


# Google `!3e` travel mode → app transport mode
_GMODE_TO_APP = {"0": "car", "1": "other", "2": "car", "3": "train"}
_GMODE_LABEL = {"0": "driving", "1": "bicycling", "2": "walking", "3": "transit"}


@router.get("/utils/resolve-directions-link", status_code=status.HTTP_200_OK)
async def resolve_directions_link(
    url: str = Query(..., description="Google Maps directions (/dir/) link"),
    current_user: User = Depends(get_current_active_user),
):
    """Parse a shared Google Maps *directions* link into endpoints + mode.

    Free, no API key. Returns origin / destination / waypoints (name + lat/lng)
    and the travel mode. The link does NOT contain the route geometry — drawing
    the actual path is a separate routing step.
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        expanded = url
        if host in {"maps.app.goo.gl", "goo.gl"}:
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=10.0, headers={"User-Agent": USER_AGENT}) as client:
                    expanded = str((await client.get(url)).url)
            except Exception:
                expanded = url

        u = urlparse(expanded)
        path = unquote_plus(u.path)
        if "/dir/" not in path:
            return {"error": "Not a directions link", "expanded_url": expanded}

        # Stop names: the path segments between /dir/ and /@ or /data.
        names: list[str] = []
        m = re.search(r"/dir/(.+?)(?:/@|/data|$)", path)
        if m:
            names = [s.strip() for s in m.group(1).split("/") if s.strip() and not s.startswith("@")]

        # Per-stop coordinates live in the data param as !1d<lng>!2d<lat> pairs.
        raw = u.path + ("?" + u.query if u.query else "")
        pairs = re.findall(r"!1d(-?\d+\.\d+)!2d(-?\d+\.\d+)", raw)
        coords = [(float(lat), float(lng)) for lng, lat in pairs]
        if not coords:
            alt = re.findall(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", raw)
            coords = [(float(lat), float(lng)) for lat, lng in alt]

        mode_match = re.search(r"!3e(\d)", raw)
        gcode = mode_match.group(1) if mode_match else None
        app_mode = _GMODE_TO_APP.get(gcode or "", None)
        google_mode = _GMODE_LABEL.get(gcode or "", None)

        n = max(len(names), len(coords))
        if n < 2:
            return {"error": "Could not parse two endpoints", "expanded_url": expanded}

        def stop(i: int) -> dict:
            name = names[i] if i < len(names) else None
            lat = lng = None
            if i < len(coords):
                lat, lng = coords[i]
            return {"name": name, "lat": lat, "lng": lng}

        return {
            "origin": stop(0),
            "destination": stop(n - 1),
            "waypoints": [stop(i) for i in range(1, n - 1)],
            "mode": app_mode,
            "google_mode": google_mode,
            "expanded_url": expanded,
        }
    except Exception:
        return {"error": "Failed to resolve directions link", "expanded_url": url}
