from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ALLOW_ORIGINS
from app.routers import (
    risk_score,
    heatmap,
    safe_commute,
    locations,
    health,
    monitoring,
    coverage,
    prediction_stats,
)

app = FastAPI(title="Chicago Risk Score API")

API_ENDPOINTS = [
    "GET /health",
    "GET /api",
    "GET /docs",
    "GET /openapi.json",
    "GET /risk-score",
    "GET /heatmap",
    "GET /safe-commute",
    "GET /locations",
    "GET /coverage",
    "GET /model-metrics",
    "GET /prediction-stats",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(risk_score.router)
app.include_router(heatmap.router)
app.include_router(safe_commute.router)
app.include_router(locations.router)
app.include_router(health.router)
app.include_router(monitoring.router)
app.include_router(coverage.router)
app.include_router(prediction_stats.router)


@app.get("/api")
def api_overview():
    return {
        "message": "Chicago Risk Score API",
        "description": "Read-only geospatial risk API for Chicago reporting and commute analysis.",
        "scope": "Chicago only",
        "endpoints": API_ENDPOINTS,
    }