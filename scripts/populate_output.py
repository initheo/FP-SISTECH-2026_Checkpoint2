"""Script untuk mengisi nilai risk_score di outputs/FP_MLOps_Output.json
secara otomatis menggunakan model dan lookup table yang sudah tersedia.

Cara menjalankan (dari root proyek):
    python scripts/populate_output.py

Output: outputs/FP_MLOps_Output.json akan diupdate dengan nilai risk_score nyata.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Pastikan root proyek masuk ke sys.path agar bisa import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from app.config import LOOKUP_PATH, MODEL_VERSION, LAST_UPDATED
from app.loader import LOOKUP
from app.utils import (
    parse_datetime_or_400,
    predict_with_model_fallback,
    score_to_level,
    to_grid_id,
)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / 'outputs' / 'FP_MLOps_Output.json'


def predict_for_entry(entry: dict) -> dict:
    lat = entry['lat']
    lon = entry['lon']
    dt = parse_datetime_or_400(entry['datetime'])
    grid_id = to_grid_id(lat, lon)
    dow, hour = dt.weekday(), dt.hour

    row = LOOKUP[
        (LOOKUP['grid_id'] == grid_id) & (LOOKUP['dow'] == dow) & (LOOKUP['hour'] == hour)
    ]

    if len(row) > 0:
        score = float(row.iloc[0]['risk_score'])
        source = 'lookup_table'
    else:
        score = predict_with_model_fallback(lat, lon, dt)
        source = 'model_fallback'

    return {
        **entry,
        'risk_score': round(score, 2),
        'level': score_to_level(score),
        'source': source,
        'model_version': MODEL_VERSION,
        'last_updated': LAST_UPDATED,
        'note': None,
    }


def main() -> None:
    with OUTPUT_PATH.open('r', encoding='utf-8') as f:
        payload = json.load(f)

    print(f"Mengisi {len(payload['predictions'])} prediksi...")
    filled = []
    for entry in payload['predictions']:
        result = predict_for_entry(entry)
        print(f"  {result['location_name']:40s} -> {result['risk_score']:5.2f} ({result['level']}) [{result['source']}]")
        filled.append(result)

    payload['predictions'] = filled
    payload['metadata']['generated_at'] = pd.Timestamp.now().isoformat()

    with OUTPUT_PATH.open('w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nSelesai! File diperbarui: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
