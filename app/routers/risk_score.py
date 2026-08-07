from fastapi import APIRouter, Query

from app.config import MODEL_VERSION, LAST_UPDATED
from app.loader import LOOKUP
from app.schemas import RiskScoreResponse, RISK_SCORE_DISCLAIMER
from app.utils import (
    to_grid_id,
    score_to_level,
    parse_datetime_or_400,
    predict_with_model_fallback,
    log_risk_score_request,
)

router = APIRouter()


@router.get("/risk-score", response_model=RiskScoreResponse)
def get_risk_score(
    lat: float = Query(...),
    lon: float = Query(...),
    datetime_value: str = Query(..., alias="datetime"),
):
    dt = parse_datetime_or_400(datetime_value)
    grid_id = to_grid_id(lat, lon)
    dow, hour = dt.weekday(), dt.hour

    row = LOOKUP[(LOOKUP['grid_id'] == grid_id) & (LOOKUP['dow'] == dow) & (LOOKUP['hour'] == hour)]

    if len(row) > 0:
        score = float(row.iloc[0]['risk_score'])
        source = "lookup_table"
    else:
        score = predict_with_model_fallback(lat, lon, dt)
        source = "model_fallback"

    log_risk_score_request(lat, lon, dt, score, source)

    return {
        "risk_score": round(score, 2),
        "level": score_to_level(score),
        "model_version": MODEL_VERSION,
        "last_updated": LAST_UPDATED,
        "source": source,
        "disclaimer": RISK_SCORE_DISCLAIMER,
    }