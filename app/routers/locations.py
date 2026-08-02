from fastapi import APIRouter

from app.schemas import LocationsResponse

router = APIRouter()

DEMO_LOCATIONS = [
    {"name": "Millennium Park", "lat": 41.8826, "lon": -87.6226},
    {"name": "Navy Pier", "lat": 41.8917, "lon": -87.6086},
    {"name": "Willis Tower", "lat": 41.8789, "lon": -87.6359},
    {"name": "Wrigley Field", "lat": 41.9484, "lon": -87.6553},
    {"name": "University of Chicago", "lat": 41.7897, "lon": -87.5997},
]


@router.get("/locations", response_model=LocationsResponse)
def get_locations():
    return {"locations": DEMO_LOCATIONS}