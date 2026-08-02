import json
import os

from fastapi import APIRouter

from app.config import MODEL_VERSIONS_PATH

router = APIRouter()


@router.get("/model-metrics")
def get_model_metrics():
    if not os.path.exists(MODEL_VERSIONS_PATH):
        return {"model_versions": []}

    with open(MODEL_VERSIONS_PATH, 'r', encoding='utf-8') as metrics_file:
        try:
            data = json.load(metrics_file)
        except json.JSONDecodeError:
            return {"model_versions": []}

    if isinstance(data, dict) and "model_versions" in data:
        return data

    if isinstance(data, list):
        return {"model_versions": data}

    return {"model_versions": []}