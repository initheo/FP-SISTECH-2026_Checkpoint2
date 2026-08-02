"""
Fungsi decay di sini disalin dari notebook pseudo_labeling_feature_engineering.ipynb
dengan tujuan yang sama seperti test_severity_validation.py.
"""
import numpy as np
import pandas as pd

HALF_LIFE_DAYS = 260
SPATIAL_BANDWIDTH_M = 500


def compute_temporal_weight(event_dates, reference_date, half_life_days):
    age_days = (reference_date - event_dates).dt.total_seconds() / 86400.0
    age_days = age_days.clip(lower=0)
    return np.exp(-np.log(2) * age_days / half_life_days)


def spatial_gaussian_weight(distance_m, bandwidth_m):
    return np.exp(-(distance_m ** 2) / (2 * bandwidth_m ** 2))


def test_temporal_weight_yesterday_is_close_to_one():
    reference_date = pd.Timestamp('2026-07-01')
    event_date = pd.Series([reference_date - pd.Timedelta(days=1)])
    weight = compute_temporal_weight(event_date, reference_date, HALF_LIFE_DAYS).iloc[0]
    assert weight > 0.99


def test_temporal_weight_two_years_ago_matches_anchor_example():
    reference_date = pd.Timestamp('2026-07-01')
    event_date = pd.Series([reference_date - pd.Timedelta(days=730)])
    weight = compute_temporal_weight(event_date, reference_date, HALF_LIFE_DAYS).iloc[0]
    assert abs(weight - 0.14) < 0.01


def test_spatial_weight_decreases_with_distance():
    weight_same_cell = spatial_gaussian_weight(0.0, SPATIAL_BANDWIDTH_M)
    weight_1km = spatial_gaussian_weight(1000.0, SPATIAL_BANDWIDTH_M)
    weight_5km = spatial_gaussian_weight(5000.0, SPATIAL_BANDWIDTH_M)
    assert weight_same_cell == 1.0
    assert weight_1km < weight_same_cell
    assert weight_5km < weight_1km
    assert weight_5km < 0.01