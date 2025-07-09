# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
import serve_model

# Create the TestClient after we stub the globals
client = TestClient(serve_model.app)

class DummyRedis:
    def exists(self, key): return True
    def hgetall(self, key): return {b"count": b"5", b"avg_amount": b"100.0"}

class DummyModel:
    def decision_function(self, X): return [0.5]

@pytest.fixture(autouse=True)
def patch_redis_and_model(monkeypatch):
    # Replace the global r and model in serve_model
    monkeypatch.setattr(serve_model, "r", DummyRedis())
    monkeypatch.setattr(serve_model, "model", DummyModel())

def test_predict_success():
    """When Redis has data, /predict returns 200 with expected JSON."""
    response = client.get("/predict?user_id=123")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 123
    assert data["anomaly_score"] == pytest.approx(0.5)
    assert data["is_fraud"] is False

def test_predict_missing_user(monkeypatch):
    """When Redis.exists is False, /predict returns 404."""
    class EmptyRedis:
        def exists(self, key): return False
    monkeypatch.setattr(serve_model, "r", EmptyRedis())

    response = client.get("/predict?user_id=999")
    assert response.status_code == 404
    assert "No features for user" in response.json()["detail"]
