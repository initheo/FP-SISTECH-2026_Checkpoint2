"""Continual learning utilities.

This module simulates time-based batches from the processed event history,
detects drift using batch MAE deterioration, retrains a candidate model on
cumulative history, and promotes a new version only when it improves a fixed
holdout slice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.config import (
    BASE_DIR,
    CP3_BATCH_COUNT,
    CP3_DRIFT_THRESHOLD,
    CP3_QUALITY_GATE,
    CP3_RANDOM_STATE,
    FEATURE_COLUMNS,
    MODEL_PATH,
    MODEL_VERSIONS_PATH,
)

DATASET_PATH = Path(BASE_DIR) / 'data' / 'processed' / 'features_labels_events.csv'
MODEL_DIR = Path(BASE_DIR) / 'models'


@dataclass
class BatchMetrics:
    batch_index: int
    start_date: str
    end_date: str
    row_count: int
    mae: float
    rmse: float
    r2: float
    drift_detected: bool = False
    checkpoint_accepted: bool = False


def _ensure_datetime_frame(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    prepared['Date'] = pd.to_datetime(prepared['Date'])
    prepared = prepared.sort_values('Date').reset_index(drop=True)
    return prepared


def load_event_history(dataset_path: Path | str = DATASET_PATH, max_rows: int | None = None) -> pd.DataFrame:
    frame = pd.read_csv(dataset_path)
    frame = _ensure_datetime_frame(frame)
    if max_rows is not None and len(frame) > max_rows:
        frame = frame.tail(max_rows).reset_index(drop=True)
    return frame


def build_feature_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    missing_columns = [column for column in FEATURE_COLUMNS + ['risk_score'] if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    clean_frame = frame.dropna(subset=FEATURE_COLUMNS + ['risk_score']).copy()
    features = clean_frame[FEATURE_COLUMNS]
    target = clean_frame['risk_score']
    return features, target


def split_time_batches(frame: pd.DataFrame, batch_count: int = CP3_BATCH_COUNT) -> list[pd.DataFrame]:
    prepared = _ensure_datetime_frame(frame)
    normalized_dates = prepared['Date'].dt.normalize()
    unique_dates = pd.Index(normalized_dates.unique()).sort_values()

    if len(unique_dates) < 2:
        raise ValueError('Need at least two distinct dates to simulate continual learning.')

    effective_batch_count = max(2, min(batch_count, len(unique_dates)))
    date_groups = np.array_split(unique_dates, effective_batch_count)

    batches: list[pd.DataFrame] = []
    for date_group in date_groups:
        if len(date_group) == 0:
            continue
        batch = prepared[normalized_dates.isin(date_group)].copy().reset_index(drop=True)
        if not batch.empty:
            batches.append(batch)

    if len(batches) < 2:
        raise ValueError('Unable to create temporal batches from the provided data.')

    return batches


def load_current_model(model_path: Path | str = MODEL_PATH):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', InconsistentVersionWarning)
        return joblib.load(model_path)


def train_candidate_model(frame: pd.DataFrame, random_state: int = CP3_RANDOM_STATE) -> RandomForestRegressor:
    features, target = build_feature_matrix(frame)
    model = RandomForestRegressor(
        n_estimators=120,
        random_state=random_state,
        n_jobs=-1,
        min_samples_leaf=2,
    )
    model.fit(features, target)
    return model


def evaluate_model(model: Any, frame: pd.DataFrame) -> dict[str, float]:
    features, target = build_feature_matrix(frame)
    predictions = model.predict(features)
    return {
        'mae': float(mean_absolute_error(target, predictions)),
        'rmse': float(mean_squared_error(target, predictions, squared=False)),
        'r2': float(r2_score(target, predictions)),
    }


def detect_drift(reference_mae: float, current_mae: float, threshold: float = CP3_DRIFT_THRESHOLD) -> bool:
    if reference_mae <= 0:
        return current_mae > 0
    return current_mae > reference_mae * (1 + threshold)


def build_version_entry(
    *,
    version: str,
    source_model: str,
    training_start: str,
    training_end: str,
    trigger_batch: int,
    drift_reference_mae: float,
    trigger_batch_mae: float,
    trigger_batch_rmse: float,
    trigger_batch_r2: float,
    holdout_before: dict[str, float],
    holdout_after: dict[str, float],
    accepted: bool,
    artifact_path: str,
) -> dict[str, Any]:
    return {
        'version': version,
        'source_model': source_model,
        'artifact_path': artifact_path,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'training_window': {
            'start': training_start,
            'end': training_end,
        },
        'trigger_batch': trigger_batch,
        'drift_reference_mae': float(drift_reference_mae),
        'trigger_batch_metrics': {
            'mae': float(trigger_batch_mae),
            'rmse': float(trigger_batch_rmse),
            'r2': float(trigger_batch_r2),
        },
        'holdout_before': {key: float(value) for key, value in holdout_before.items()},
        'holdout_after': {key: float(value) for key, value in holdout_after.items()},
        'accepted': accepted,
        'notes': 'Promoted only when the candidate improves the fixed holdout slice.' if accepted else 'Rejected by the quality gate.',
    }


def read_model_versions(path: Path | str = MODEL_VERSIONS_PATH) -> dict[str, Any]:
    target_path = Path(path)
    if not target_path.exists():
        return {'model_versions': []}

    with target_path.open('r', encoding='utf-8') as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError:
            return {'model_versions': []}

    if isinstance(data, dict):
        if 'model_versions' in data and isinstance(data['model_versions'], list):
            return data
        return {'model_versions': []}

    if isinstance(data, list):
        return {'model_versions': data}

    return {'model_versions': []}


def _next_version_name(existing_versions: list[dict[str, Any]]) -> str:
    if not existing_versions:
        return 'v1'

    numeric_versions = []
    for item in existing_versions:
        version = str(item.get('version', 'v0')).lower().lstrip('v')
        if version.isdigit():
            numeric_versions.append(int(version))

    if not numeric_versions:
        return f"v{len(existing_versions) + 1}"

    return f"v{max(numeric_versions) + 1}"


def append_model_version(entry: dict[str, Any], path: Path | str = MODEL_VERSIONS_PATH) -> dict[str, Any]:
    payload = read_model_versions(path)
    versions = payload.get('model_versions', [])
    versions.append(entry)
    payload['model_versions'] = versions

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

    return payload


def _batch_window(batch: pd.DataFrame) -> tuple[str, str]:
    dates = pd.to_datetime(batch['Date'])
    return dates.min().date().isoformat(), dates.max().date().isoformat()


def _save_candidate_model(model: Any, version_name: str) -> str:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = MODEL_DIR / f'risk_model_{version_name}.joblib'
    joblib.dump(model, artifact_path)
    return str(artifact_path.relative_to(Path(BASE_DIR)))


def run_cp3_pipeline(
    *,
    max_rows: int | None = None,
    batch_count: int = CP3_BATCH_COUNT,
    drift_threshold: float = CP3_DRIFT_THRESHOLD,
    quality_gate: float = CP3_QUALITY_GATE,
    dataset_path: Path | str = DATASET_PATH,
    model_path: Path | str = MODEL_PATH,
    versions_path: Path | str = MODEL_VERSIONS_PATH,
    persist: bool = True,
) -> dict[str, Any]:
    frame = load_event_history(dataset_path=dataset_path, max_rows=max_rows)
    batches = split_time_batches(frame, batch_count=batch_count)
    holdout_batch = batches[-1]
    training_batches = batches[:-1]

    if len(training_batches) < 1:
        raise ValueError('Need at least one training batch before the holdout batch.')

    current_model = load_current_model(model_path=model_path)
    current_holdout_metrics = evaluate_model(current_model, holdout_batch)

    summary: dict[str, Any] = {
        'dataset_path': str(Path(dataset_path)),
        'model_path': str(Path(model_path)),
        'versions_path': str(Path(versions_path)),
        'batch_count': len(batches),
        'holdout_metrics': current_holdout_metrics,
        'batches': [],
        'drift_events': [],
        'promoted_versions': [],
        'rejected_candidates': [],
    }

    cumulative_training_frames: list[pd.DataFrame] = []
    rolling_reference_mae: float | None = None

    for batch_index, batch in enumerate(training_batches):
        cumulative_training_frames.append(batch)
        batch_metrics = evaluate_model(current_model, batch)
        drift_detected = False
        checkpoint_accepted = False

        if rolling_reference_mae is not None:
            drift_detected = detect_drift(rolling_reference_mae, batch_metrics['mae'], threshold=drift_threshold)

        if drift_detected:
            candidate_training_frame = pd.concat(cumulative_training_frames, ignore_index=True)
            candidate_model = train_candidate_model(candidate_training_frame)
            candidate_holdout_metrics = evaluate_model(candidate_model, holdout_batch)
            candidate_training_metrics = evaluate_model(candidate_model, batch)

            checkpoint_accepted = (
                candidate_holdout_metrics['mae'] <= current_holdout_metrics['mae'] * (1 - quality_gate)
                and candidate_holdout_metrics['rmse'] <= current_holdout_metrics['rmse']
            )

            version_name = _next_version_name(read_model_versions(versions_path).get('model_versions', []))
            training_start, training_end = _batch_window(candidate_training_frame)
            version_entry = build_version_entry(
                version=version_name,
                source_model=str(Path(model_path)),
                training_start=training_start,
                training_end=training_end,
                trigger_batch=batch_index,
                drift_reference_mae=rolling_reference_mae,
                trigger_batch_mae=batch_metrics['mae'],
                trigger_batch_rmse=batch_metrics['rmse'],
                trigger_batch_r2=batch_metrics['r2'],
                holdout_before=current_holdout_metrics,
                holdout_after=candidate_holdout_metrics,
                accepted=checkpoint_accepted,
                artifact_path=str(Path('models') / f'risk_model_{version_name}.joblib'),
            )

            if checkpoint_accepted and persist:
                artifact_path = _save_candidate_model(candidate_model, version_name)
                version_entry['artifact_path'] = artifact_path
                append_model_version(version_entry, path=versions_path)
                current_model = candidate_model
                current_holdout_metrics = candidate_holdout_metrics
                summary['promoted_versions'].append(version_entry)
            else:
                version_entry['artifact_path'] = str(Path('models') / f'risk_model_{version_name}.joblib')
                summary['rejected_candidates'].append(version_entry)

            summary['drift_events'].append({
                'batch_index': batch_index,
                'reference_mae': float(rolling_reference_mae),
                'current_mae': float(batch_metrics['mae']),
                'threshold': float(drift_threshold),
                'drift_detected': drift_detected,
                'checkpoint_accepted': checkpoint_accepted,
            })

            if checkpoint_accepted:
                rolling_reference_mae = candidate_training_metrics['mae']
            else:
                rolling_reference_mae = batch_metrics['mae']
        else:
            rolling_reference_mae = batch_metrics['mae']

        summary['batches'].append(
            asdict(
                BatchMetrics(
                    batch_index=batch_index,
                    start_date=_batch_window(batch)[0],
                    end_date=_batch_window(batch)[1],
                    row_count=len(batch),
                    mae=batch_metrics['mae'],
                    rmse=batch_metrics['rmse'],
                    r2=batch_metrics['r2'],
                    drift_detected=drift_detected,
                    checkpoint_accepted=checkpoint_accepted,
                )
            )
        )

    summary['generated_at'] = datetime.now(timezone.utc).isoformat()
    summary['final_holdout_metrics'] = current_holdout_metrics
    return summary
