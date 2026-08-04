from fastapi import APIRouter

from app.loader import GRID_FEATURES

router = APIRouter()


@router.get("/coverage")
def get_coverage():
    return {
        "supported_region": "Chicago, Illinois, USA",
        "bounding_box": {
            "lat_min": float(GRID_FEATURES['grid_lat'].min()),
            "lat_max": float(GRID_FEATURES['grid_lat'].max()),
            "lon_min": float(GRID_FEATURES['grid_lon'].min()),
            "lon_max": float(GRID_FEATURES['grid_lon'].max()),
        },
        "note": "Model saat ini dilatih pada data Chicago Crimes. "
        "Lokasi di luar area ini akan mengembalikan risk_score null.",
    }