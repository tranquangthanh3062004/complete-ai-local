from fastapi import APIRouter, Query
import httpx

router = APIRouter(prefix="/maps", tags=["maps"])

@router.get("/autocomplete")
async def autocomplete(q: str = Query(..., min_length=2)):
    """
    Proxy to OpenStreetMap Nominatim for geocoding / autocomplete (Hà Nội First).
    """
    url = "https://nominatim.openstreetmap.org/search"
    search_q = q if "hà nội" in q.lower() or "hanoi" in q.lower() else f"{q}, Hà Nội, Việt Nam"
    
    params = {
        "q": search_q,
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
        data = response.json() if response.status_code == 200 else []
        
        # Fallback to general search if no result for Hanoi
        if not data and search_q != q:
            params["q"] = q
            response = await client.get(url, params=params, headers=headers)
            data = response.json() if response.status_code == 200 else []
            
        return [
            {
                "name": item.get("display_name"),
                "lat": float(item.get("lat")),
                "lng": float(item.get("lon"))
            } for item in data
        ]

from services.route_planner import find_route
from services.smart_route import find_multiple_routes
from fastapi import HTTPException

@router.get("/route")
async def get_route(origin: str = Query(...), destination: str = Query(...)):
    """Find multi-option transit route between two points."""
    multi_opts = find_multiple_routes(origin, destination, city="HN")
    primary = find_route(origin, destination)
    
    if "error" in primary and not multi_opts:
        raise HTTPException(status_code=404, detail=primary.get("error", "Không tìm thấy lộ trình phù hợp."))
        
    # Standardize options format
    options = multi_opts if multi_opts else []
    if not options and "error" not in primary:
        options.append({
            "option_name": "Nhanh nhất",
            "origin": primary.get("origin", origin),
            "destination": primary.get("destination", destination),
            "origin_lat": primary.get("origin_lat", 21.0285),
            "origin_lng": primary.get("origin_lng", 105.8542),
            "dest_lat": primary.get("dest_lat", 21.0285),
            "dest_lng": primary.get("dest_lng", 105.8542),
            "total_time": primary.get("total_time", 20),
            "total_cost": primary.get("total_cost", 7000),
            "transfers": primary.get("transfers", 0),
            "walk_km": 0.5,
            "co2_kg": 0.2,
            "steps": primary.get("steps", [])
        })
        
    return {
        "primary": primary if "error" not in primary else (options[0] if options else None),
        "options": options
    }
