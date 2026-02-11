import httpx
from fastapi import HTTPException, status
from app.core.config import settings

UNSPLASH_API_URL = "https://api.unsplash.com"

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
