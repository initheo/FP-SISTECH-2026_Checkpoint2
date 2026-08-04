from datetime import datetime, timedelta

import pandas as pd

from app.continual_learning import (
    append_model_version,
    build_version_entry,
    detect_drift,
    read_model_versions,
    split_time_batches,
)


def _make_frame(days: int = 8) -> pd.DataFrame:
    base = datetime(2026, 1, 1)
    rows = []
    for idx in range(days):
        day = base + timedelta(days=idx)
        rows.append(
            {
                'Date': day,
                'hour_sin': 0.0,
                'hour_cos': 1.0,
                'dow_sin': 0.0,
                'dow_cos': 1.0,
                'month_sin': 0.0,
                'month_cos': 1.0,
                'is_weekend': int(day.weekday() >= 5),
                'grid_crime_count': 10 + idx,
                'grid_arrest_rate': 0.1,
                'grid_theft_share': 0.2,
                'grid_narcotics_share': 0.05,
                'Latitude': 41.8 + idx * 0.001,
                'Longitude': -87.6 - idx * 0.001,
                'risk_score': 50 + idx,
            }
        )
    return pd.DataFrame(rows)


def test_split_time_batches_preserves_chronology():
    frame = _make_frame(days=8)
    batches = split_time_batches(frame, batch_count=4)

    assert len(batches) == 4
    assert batches[0]['Date'].min() <= batches[0]['Date'].max()
    assert batches[0]['Date'].max() <= batches[1]['Date'].min()


def test_detect_drift_uses_relative_mae_increase():
    assert detect_drift(10.0, 11.6, threshold=0.15) is True
    assert detect_drift(10.0, 11.4, threshold=0.15) is False


def test_model_version_round_trip(tmp_path):
    version_file = tmp_path / 'model_versions.json'
    entry = build_version_entry(
        version='v2',
        source_model='models/risk_model_v1.joblib',
        training_start='2026-01-01',
        training_end='2026-01-08',
        trigger_batch=1,
        drift_reference_mae=10.0,
        trigger_batch_mae=12.0,
        trigger_batch_rmse=14.0,
        trigger_batch_r2=0.5,
        holdout_before={'mae': 9.0, 'rmse': 11.0, 'r2': 0.4},
        holdout_after={'mae': 8.0, 'rmse': 10.0, 'r2': 0.55},
        accepted=True,
        artifact_path='models/risk_model_v2.joblib',
    )

    payload = append_model_version(entry, path=version_file)
    reloaded = read_model_versions(version_file)

    assert payload == reloaded
    assert reloaded['model_versions'][0]['version'] == 'v2'