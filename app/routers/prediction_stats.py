"""Endpoint: GET /prediction-stats

Membaca logs/prediction_log.csv dan mengembalikan ringkasan statistik
penggunaan API secara real-time. Berguna untuk monitoring sederhana
tanpa perlu membuka file log secara manual.
"""

import os
from collections import Counter

import pandas as pd
from fastapi import APIRouter

from app.config import LOG_PATH

router = APIRouter()


@router.get("/prediction-stats")
def get_prediction_stats():
    """Kembalikan ringkasan statistik dari log prediksi."""
    if not os.path.exists(LOG_PATH):
        return {
            "total_requests": 0,
            "avg_risk_score": None,
            "source_breakdown": {},
            "risk_level_breakdown": {},
            "top_grids": [],
            "note": "Log belum tersedia — belum ada request yang dicatat.",
        }

    try:
        log_df = pd.read_csv(LOG_PATH)
    except Exception:
        return {"total_requests": 0, "note": "Gagal membaca file log."}

    if log_df.empty:
        return {"total_requests": 0, "note": "Log kosong."}

    total = len(log_df)
    avg_score = round(float(log_df['risk_score'].mean()), 2)

    # Breakdown per sumber (lookup_table vs model_fallback)
    source_breakdown = log_df['source'].value_counts().to_dict()

    # Breakdown risk level
    def _to_level(s: float) -> str:
        if s >= 75:
            return "Very High"
        if s >= 50:
            return "High"
        if s >= 25:
            return "Medium"
        return "Low"

    log_df['_level'] = log_df['risk_score'].apply(_to_level)
    level_breakdown = log_df['_level'].value_counts().to_dict()

    # Top 5 grid/lokasi paling sering di-query
    log_df['_grid'] = log_df['lat'].round(2).astype(str) + "_" + log_df['lon'].round(2).astype(str)
    top_grids_raw = Counter(log_df['_grid'].tolist()).most_common(5)
    top_grids = [{"grid_id": g, "request_count": c} for g, c in top_grids_raw]

    return {
        "total_requests": total,
        "avg_risk_score": avg_score,
        "source_breakdown": source_breakdown,
        "risk_level_breakdown": level_breakdown,
        "top_grids": top_grids,
        "disclaimer": (
            "Statistik ini didasarkan pada seluruh request yang masuk ke endpoint /risk-score. "
            "Risk score adalah estimasi berbasis pola historis, bukan prediksi kepastian kejadian."
        ),
    }
