from datetime import datetime as dt_type

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query

from app.loader import LOOKUP
from app.schemas import SafeCommuteResponse
from app.utils import to_grid_id, parse_datetime_or_400, predict_with_model_fallback

router = APIRouter()


def sample_route_points(lat1, lon1, lat2, lon2, n_points=6):
    lats = np.linspace(lat1, lat2, n_points)
    lons = np.linspace(lon1, lon2, n_points)
    return list(zip(lats, lons))


def route_risk_score(points, dt: dt_type):
    dow, hour = dt.weekday(), dt.hour
    scores = []
    for lat, lon in points:
        grid_id = to_grid_id(lat, lon)
        row = LOOKUP[(LOOKUP['grid_id'] == grid_id) & (LOOKUP['dow'] == dow) & (LOOKUP['hour'] == hour)]
        if len(row) > 0:
            scores.append(float(row.iloc[0]['risk_score']))
        else:
            scores.append(predict_with_model_fallback(lat, lon, dt))
    return scores


@router.get("/safe-commute", response_model=SafeCommuteResponse)
def get_safe_commute(
    lat_start: float,
    lon_start: float,
    lat_end: float,
    lon_end: float,
    datetime_value: str = Query(..., alias="datetime"),
    window_hours: int = 3,
):
    dt = parse_datetime_or_400(datetime_value)
    points = sample_route_points(lat_start, lon_start, lat_end, lon_end)

    options = []
    for offset in range(window_hours + 1):
        candidate_dt = dt + pd.Timedelta(hours=offset)
        scores = route_risk_score(points, candidate_dt)
        options.append({
            "datetime": candidate_dt.isoformat(),
            "avg_risk_score": round(float(np.mean(scores)), 2),
            "max_risk_score": round(float(np.max(scores)), 2),
        })

    recommended = min(options, key=lambda option: option["avg_risk_score"])

    return {
        "route_points": [{"lat": lat, "lon": lon} for lat, lon in points],
        "options": options,
        "recommended": recommended,
    }