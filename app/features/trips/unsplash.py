from typing import Optional

import httpx
from fastapi import HTTPException, status
from app.core.config import settings

UNSPLASH_API_URL = "https://api.unsplash.com"


async def fetch_travel_photo(query: str) -> Optional[dict]:
    """Fetch a travel photo plus attribution metadata from Unsplash.

    Returns a dict with keys: url, external_id, photographer_name,
    photographer_url — or None if no key is configured / the request fails.

    This is the richer counterpart to ``get_random_travel_photo`` (which only
    returns a URL). It exists so the destination-photo cache can persist the
    attribution Unsplash's API guidelines require.
    """
    if not settings.UNSPLASH_ACCESS_KEY:
        return None

    headers = {
        "Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}",
        "Accept-Version": "v1",
    }
    params = {
        "query": query,
        "orientation": "landscape",
        "content_filter": "high",
        "topics": "travel,nature,architecture",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{UNSPLASH_API_URL}/photos/random",
            headers=headers,
            params=params,
            timeout=10.0,
        )

        # Retry once with a generic query if the specific term has no results.
        if response.status_code == 404:
            response = await client.get(
                f"{UNSPLASH_API_URL}/photos/random",
                headers=headers,
                params={**params, "query": "travel"},
                timeout=10.0,
            )

        if response.status_code != 200:
            print(f"Unsplash API Error: {response.status_code} - {response.text}")
            return None

        data = response.json()
        user = data.get("user") or {}
        return {
            "url": data["urls"]["regular"],
            "external_id": data.get("id"),
            "photographer_name": user.get("name"),
            "photographer_url": (user.get("links") or {}).get("html"),
        }

async def get_random_travel_photo(query: str) -> str:
    """
    Fetch a random high-quality travel photo from Unsplash.
    
    Args:
        query: Search term (e.g. "Paris", "Beach", "Mountains")
        
    Returns:
        URL of the image
    """
    if not settings.UNSPLASH_ACCESS_KEY:
        # Fallback if no key configured
        return f"https://source.unsplash.com/1600x900/?{query},travel"

    headers = {
        "Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}",
        "Accept-Version": "v1"
    }

    params = {
        "query": query,
        "orientation": "landscape",
        "content_filter": "high",
        "topics": "travel,nature,architecture"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{UNSPLASH_API_URL}/photos/random",
                headers=headers,
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Return the regular URL (good quality but optimized)
                return data["urls"]["regular"]
            
            elif response.status_code == 404:
                # Fallback to general travel query if specific one fails
                fallback_response = await client.get(
                    f"{UNSPLASH_API_URL}/photos/random",
                    headers=headers,
                    params={**params, "query": "travel"},
                    timeout=10.0
                )
                if fallback_response.status_code == 200:
                    return fallback_response.json()["urls"]["regular"]
                
            # Log error but return fallback
            print(f"Unsplash API Error: {response.status_code} - {response.text}")
            return f"https://source.unsplash.com/1600x900/?travel"
            
        except Exception as e:
            print(f"Unsplash Request Failed: {str(e)}")
            return f"https://source.unsplash.com/1600x900/?travel"
