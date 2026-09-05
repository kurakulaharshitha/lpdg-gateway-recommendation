from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"
    assert body["telemetry_rows"] > 0
    assert body["gateway_count"] > 0


def test_recommendations_endpoint_returns_15_gateways():
    response = client.get(
        "/recommendations/2026-02-02"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["week_start"] == "2026-02-02"
    assert body["count"] == 15
    assert len(body["recommendations"]) == 15


def test_non_monday_returns_400():
    response = client.get(
        "/recommendations/2026-02-03"
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "week_start must be a Monday."
    )


def test_gateway_explanation():
    response = client.get(
        "/gateways/0A2778A31BE3/explanation",
        params={
            "week_start": "2026-02-02"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["gateway_id"] == "0A2778A31BE3"
    assert body["rank"] == 1
    assert body["selected_for_visit"] is True
    assert body["score"] == 43.0


def test_unknown_gateway_returns_404():
    response = client.get(
        "/gateways/DOES_NOT_EXIST/explanation",
        params={
            "week_start": "2026-02-02"
        },
    )

    assert response.status_code == 404
def test_run_endpoint_reloads_fresh_data(monkeypatch):
    import pandas as pd
    import src.api as api_module

    api_module.get_telemetry.cache_clear()

    old_frame = pd.DataFrame(
        {"version": ["old"]}
    )

    fresh_frame = pd.DataFrame(
        {"version": ["fresh"]}
    )

    calls = {"count": 0}
    received = {}

    def fake_load_telemetry():
        calls["count"] += 1

        if calls["count"] == 1:
            return old_frame

        return fresh_frame

    def fake_write_predictions(frame):
        received["frame"] = frame

        weeks = [
            f"week-{week}"
            for week in range(8)
            for _ in range(15)
        ]

        return pd.DataFrame(
            {"week_start": weeks}
        )

    monkeypatch.setattr(
        api_module,
        "load_telemetry",
        fake_load_telemetry,
    )

    monkeypatch.setattr(
        api_module,
        "write_predictions",
        fake_write_predictions,
    )

    # First request puts OLD data in the cache.
    cached_frame = api_module.get_telemetry()

    assert cached_frame is old_frame

    # /run should clear that cache and load fresh data.
    response = client.post("/run")

    assert response.status_code == 200
    assert calls["count"] == 2
    assert received["frame"] is fresh_frame

    api_module.get_telemetry.cache_clear()