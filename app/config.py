import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOOKUP_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'risk_lookup_table.csv')
GRID_FEATURES_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'grid_feature_reference.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'risk_model_v1.joblib')
MODEL_VERSIONS_PATH = os.path.join(BASE_DIR, 'models', 'model_versions.json')
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'prediction_log.csv')

MODEL_VERSION = 'v1'
LAST_UPDATED = '2026-07-30'
GRID_DECIMALS = 2
EARTH_RADIUS_M = 6371000.0

FEATURE_COLUMNS = [
    'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos',
    'is_weekend', 'grid_crime_count', 'grid_arrest_rate',
    'grid_theft_share', 'grid_narcotics_share', 'Latitude', 'Longitude',
]