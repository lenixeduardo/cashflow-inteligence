from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_forecast_endpoint_exposes_validation_evidence():
    response = client.get("/cash-flow/forecast?horizon_days=10")
    assert response.status_code == 200
    body = response.json()
    assert body["data_kind"] == "synthetic"
    assert body["comparison"]["test_rows"] == 28
    assert len(body["forecast"]) == 10


def test_scenario_endpoint_is_explicitly_a_simulation():
    response = client.post("/cash-flow/scenarios", json={"name": "Atraso", "receivables_change_pct": -20})
    assert response.status_code == 200
    assert response.json()["kind"] == "scenario_simulation"
