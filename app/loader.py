import numpy as np
import pandas as pd
import joblib
from sklearn.neighbors import BallTree

from app.config import LOOKUP_PATH, GRID_FEATURES_PATH, MODEL_PATH

LOOKUP = pd.read_csv(LOOKUP_PATH)
GRID_FEATURES = pd.read_csv(GRID_FEATURES_PATH)
MODEL = joblib.load(MODEL_PATH)

NEAREST_GRID_TREE = BallTree(
    np.radians(GRID_FEATURES[['grid_lat', 'grid_lon']].to_numpy()),
    metric='haversine',
)