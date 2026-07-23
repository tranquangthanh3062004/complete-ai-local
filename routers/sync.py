from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
import time

router = APIRouter(
    prefix="/sync",
    tags=["Synchronization"]
)

# Mocked Data for Edge Devices to pull
class SyncRouteResponse(BaseModel):
    version: str
    updated_at: float
    routes: List[Dict[str, Any]]

# Model for incoming telemetry
class TelemetryTask(BaseModel):
    id: str
    type: str
    payload: Any
    timestamp: int

class TelemetryPayload(BaseModel):
    events: List[TelemetryTask]

@router.get("/routes", response_model=SyncRouteResponse)
async def get_sync_routes():
    """
    Endpoint for Edge devices/Kiosks to pull the latest routes and static data.
    In a real app, this would query the database to get changes since a 'last_sync' timestamp.
    """
    return {
        "version": "1.0.0",
        "updated_at": time.time(),
        "routes": [
            {
                "id": "bus_01",
                "name": "Bến xe Yên Nghĩa - BX Gia Lâm",
                "type": "bus",
                "price": 7000
            },
            {
                "id": "metro_2A",
                "name": "Cát Linh - Hà Đông",
                "type": "metro",
                "price": 15000
            }
        ]
    }

@router.post("/telemetry")
async def post_telemetry(payload: TelemetryPayload):
    """
    Endpoint to receive cached events from Edge devices when they reconnect to the internet.
    """
    # In a real app, save these to the database for analytics.
    print(f"[SYNC] Received {len(payload.events)} telemetry events from edge device.")
    for event in payload.events:
        print(f"  - Event ID: {event.id} | Type: {event.type} | Time: {event.timestamp}")
        
    return {"status": "success", "processed": len(payload.events)}
