from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_risk_score_returns_valid_response():
    response = client.get(
        "/risk-score",
        params={"lat": 41.86, "lon": -87.67, "datetime": "2026-07-30T00:00:00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["level"] in {"Low", "Medium", "High", "Very High"}
    assert body["source"] in {"lookup_table", "model_fallback"}


def test_risk_score_rejects_invalid_datetime():
    response = client.get(
        "/risk-score",
        params={"lat": 41.86, "lon": -87.67, "datetime": "not-a-date"},
    )
    assert response.status_code == 400


def test_heatmap_returns_points_for_valid_datetime():
    response = client.get("/heatmap", params={"datetime": "2026-07-30T14:00:00"})
    assert response.status_code == 200
    body = response.json()
    assert body["point_count"] == len(body["points"])
    assert body["point_count"] > 0


def test_safe_commute_returns_recommended_option():
    response = client.get(
        "/safe-commute",
        params={
            "lat_start": 41.88, "lon_start": -87.63,
            "lat_end": 41.90, "lon_end": -87.60,
            "datetime": "2026-07-30T14:00:00",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["route_points"]) > 0
    assert body["recommended"] in body["options"]


def test_locations_returns_non_empty_list():
    response = client.get("/locations")
    assert response.status_code == 200
    body = response.json()
    assert len(body["locations"]) > 0


def test_health_endpoint_is_available():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_metrics_returns_list_payload():
    response = client.get("/model-metrics")
    assert response.status_code == 200
    body = response.json()
    assert "model_versions" in body
    assert isinstance(body["model_versions"], list)