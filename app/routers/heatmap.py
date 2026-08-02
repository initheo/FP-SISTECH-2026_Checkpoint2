from fastapi import APIRouter, Query

from app.loader import LOOKUP
from app.schemas import HeatmapResponse
from app.utils import parse_datetime_or_400

router = APIRouter()


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(datetime_value: str = Query(..., alias="datetime")):
    dt = parse_datetime_or_400(datetime_value)
    dow, hour = dt.weekday(), dt.hour

    subset = LOOKUP[(LOOKUP['dow'] == dow) & (LOOKUP['hour'] == hour)]
    points = [
        {"lat": row.grid_lat, "lon": row.grid_lon, "risk_score": round(row.risk_score, 2)}
        for row in subset.itertuples()
    ]

    return {"datetime": datetime_value, "point_count": len(points), "points": points}