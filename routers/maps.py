from fastapi import APIRouter, Query
import httpx

router = APIRouter(prefix="/maps", tags=["maps"])

@router.get("/autocomplete")
async def autocomplete(q: str = Query(..., min_length=2)):
    """
    Proxy to OpenStreetMap Nominatim for geocoding / autocomplete.
    Since we don't have a Google Maps API key, we fallback to OSM.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": q,
        "format": "json",
        "countrycodes": "vn",
        "limit": 5,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "GTCC-Bot-App/2.0"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "name": item.get("display_name"),
                    "lat": float(item.get("lat")),
                    "lng": float(item.get("lon"))
                } for item in data
            ]
        return []

from services.route_planner import find_route
from fastapi import HTTPException

@router.get("/route")
async def get_route(origin: str = Query(...), destination: str = Query(...)):
    """Find fastest transit route between two points."""
    result = find_route(origin, destination)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
