from typing import List

from pydantic import BaseModel

RISK_SCORE_DISCLAIMER = (
    "Skor ini merupakan estimasi berbasis pola kejahatan historis di Chicago, "
    "bukan prediksi kepastian suatu kejadian. Gunakan sebagai referensi, bukan satu-satunya acuan keputusan."
)


class RiskScoreResponse(BaseModel):
    risk_score: float
    level: str
    model_version: str
    last_updated: str
    source: str
    disclaimer: str


class HeatmapPoint(BaseModel):
    lat: float
    lon: float
    risk_score: float
    risk_level: str
    risk_percentile: float


class HeatmapResponse(BaseModel):
    datetime: str
    point_count: int
    points: List[HeatmapPoint]


class RoutePoint(BaseModel):
    lat: float
    lon: float


class CommuteOption(BaseModel):
    datetime: str
    avg_risk_score: float
    max_risk_score: float


class SafeCommuteResponse(BaseModel):
    route_points: List[RoutePoint]
    options: List[CommuteOption]
    recommended: CommuteOption


class LocationItem(BaseModel):
    name: str
    lat: float
    lon: float


class LocationsResponse(BaseModel):
    locations: List[LocationItem]