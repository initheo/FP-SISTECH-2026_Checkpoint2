from fastapi import FastAPI

from app.routers import risk_score, heatmap, safe_commute, locations, health, monitoring

app = FastAPI(title="Chicago Risk Score API")

app.include_router(risk_score.router)
app.include_router(heatmap.router)
app.include_router(safe_commute.router)
app.include_router(locations.router)
app.include_router(health.router)
app.include_router(monitoring.router)