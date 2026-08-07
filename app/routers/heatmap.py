from fastapi import APIRouter, Query

from app.loader import LOOKUP
from app.schemas import HeatmapResponse
from app.utils import parse_datetime_or_400, score_to_level

router = APIRouter()


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(datetime_value: str = Query(..., alias="datetime")):
    dt = parse_datetime_or_400(datetime_value)
    dow, hour = dt.weekday(), dt.hour

    subset = LOOKUP[(LOOKUP['dow'] == dow) & (LOOKUP['hour'] == hour)]
    percentile_values = subset['risk_score'].rank(pct=True)
    points = []
    for row, percentile in zip(subset.itertuples(), percentile_values):
        score = float(row.risk_score)
        points.append({
            "lat": row.grid_lat,
            "lon": row.grid_lon,
            "risk_score": round(score, 2),
            "risk_level": score_to_level(score),
            "risk_percentile": round(float(percentile * 100), 2),
        })

    return {"datetime": datetime_value, "point_count": len(points), "points": points}