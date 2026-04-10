from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_health():
    response = client.get("/auth/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "auth"


def test_get_me_without_token():
    response = client.get("/auth/me")
    assert response.status_code == 401  # No bearer token


def test_logout_without_token():
    response = client.post("/auth/logout")
    assert response.status_code == 401  # No bearer token


def test_register_missing_fields():
    response = client.post("/auth/register", json={})
    assert response.status_code == 422
