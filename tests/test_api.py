"""Tests d'intégration de l'API REST (C9) via le TestClient FastAPI."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from air_quality.api.main import app
from air_quality.api.security import API_KEY

AUTH = {"X-API-Key": API_KEY}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # déclenche lifespan -> charge le modèle
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["model_loaded"] is True


def test_predict_ok(client, sample_payload):
    r = client.post("/predict", json=sample_payload, headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["aqi"] <= 500
    assert body["category"]
    assert body["dominant_pollutant"]


def test_predict_requires_api_key(client, sample_payload):
    assert client.post("/predict", json=sample_payload).status_code == 401


def test_predict_rejects_out_of_range(client, sample_payload):
    bad = {**sample_payload, "humidity": 500}
    assert client.post("/predict", json=bad, headers=AUTH).status_code == 422


def test_model_info(client):
    r = client.get("/model/info")
    assert r.status_code == 200
    assert r.json()["n_features"] > 0


def test_metrics_exposes_custom_counter(client, sample_payload):
    client.post("/predict", json=sample_payload, headers=AUTH)
    text = client.get("/metrics").text
    assert "aqi_predictions_total" in text
