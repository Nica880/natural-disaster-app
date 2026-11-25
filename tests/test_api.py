"""HTTP-level smoke tests: the app boots, degrades gracefully without model
weights, and the monitor endpoints work against an empty database."""
from __future__ import annotations

import io

from PIL import Image


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (120, 120, 120)).save(buf, format="JPEG")
    return buf.getvalue()


def test_health_lists_every_model(client):
    res = client.get("/health")
    assert res.status_code == 200
    names = {m["name"] for m in res.json()["models"]}
    assert {"classifier", "fire", "flood", "carcrash"} <= names


def test_models_report_unavailable_without_weights(client):
    models = client.get("/health").json()["models"]
    assert not any(m["loaded"] for m in models if m["name"] != "detector")


def test_analyze_returns_503_when_classifier_missing(client):
    res = client.post("/api/v1/analyze", files={"file": ("frame.jpg", _jpeg(), "image/jpeg")})
    assert res.status_code == 503


def test_incident_board_starts_empty(client):
    assert client.get("/api/v1/incidents").json() == []
    assert client.get("/api/v1/incidents/history").json() == []


def test_unknown_incident_is_404(client):
    assert client.get("/api/v1/incidents/does-not-exist").status_code == 404


def test_feedback_stats_on_empty_db(client):
    res = client.get("/api/v1/feedback/stats")
    assert res.status_code == 200


def test_weather_disabled_without_api_key(client):
    res = client.get("/api/v1/weather", params={"lat": 44.43, "lon": 26.10})
    assert res.status_code == 503
