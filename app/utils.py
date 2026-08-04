from datetime import datetime, timezone
import csv
import os

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.config import GRID_DECIMALS, FEATURE_COLUMNS, LOG_PATH, EARTH_RADIUS_M
from app.loader import GRID_FEATURES, MODEL, NEAREST_GRID_TREE


def to_grid_id(lat: float, lon: float) -> str:
    grid_lat = round(lat, GRID_DECIMALS)
    grid_lon = round(lon, GRID_DECIMALS)
    return f"{grid_lat}_{grid_lon}"


def score_to_level(score: float) -> str:
    if score >= 75:
        return "Very High"
    if score >= 50:
        return "High"
    if score >= 25:
        return "Medium"
    return "Low"


def parse_datetime_or_400(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format datetime tidak valid, gunakan format ISO 8601")


def build_time_features(dt: datetime) -> dict:
    dow, hour, month = dt.weekday(), dt.hour, dt.month
    return {
        'hour_sin': np.sin(2 * np.pi * hour / 24),
        'hour_cos': np.cos(2 * np.pi * hour / 24),
        'dow_sin': np.sin(2 * np.pi * dow / 7),
        'dow_cos': np.cos(2 * np.pi * dow / 7),
        'month_sin': np.sin(2 * np.pi * month / 12),
        'month_cos': np.cos(2 * np.pi * month / 12),
        'is_weekend': int(dow in (5, 6)),
    }


def predict_with_model_fallback(lat: float, lon: float, dt: datetime) -> float:
    query = np.radians([[lat, lon]])
    _, idx = NEAREST_GRID_TREE.query(query, k=1)
    nearest = GRID_FEATURES.iloc[idx[0][0]]

    row = {**build_time_features(dt), 'Latitude': lat, 'Longitude': lon}
    row['grid_crime_count'] = nearest['grid_crime_count']
    row['grid_arrest_rate'] = nearest['grid_arrest_rate']
    row['grid_theft_share'] = nearest['grid_theft_share']
    row['grid_narcotics_share'] = nearest['grid_narcotics_share']

    feature_row = pd.DataFrame([row])[FEATURE_COLUMNS]
    prediction = MODEL.predict(feature_row)[0]
    return float(np.clip(prediction, 0, 100))


def log_risk_score_request(lat: float, lon: float, dt: datetime, score: float, source: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    file_exists = os.path.exists(LOG_PATH)

    with open(LOG_PATH, 'a', newline='', encoding='utf-8') as log_file:
        writer = csv.DictWriter(
            log_file,
            fieldnames=['timestamp', 'lat', 'lon', 'datetime', 'risk_score', 'source'],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'lat': lat,
            'lon': lon,
            'datetime': dt.isoformat(),
            'risk_score': round(float(score), 2),
            'source': source,
        })


MAX_FALLBACK_DISTANCE_M = 3000  # di luar radius ini dari grid Chicago terdekat, dianggap tidak tercakup


def is_within_coverage(lat: float, lon: float) -> bool:
    query = np.radians([[lat, lon]])
    dist_rad, _ = NEAREST_GRID_TREE.query(query, k=1)
    dist_m = dist_rad[0][0] * EARTH_RADIUS_M
    return dist_m <= MAX_FALLBACK_DISTANCE_M