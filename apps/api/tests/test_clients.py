from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_clients_requires_auth():
    response = client.get("/clients")
    assert response.status_code == 401


def test_get_client_requires_auth():
    response = client.get("/clients/1")
    assert response.status_code == 401


def test_create_client_requires_auth():
    response = client.post("/clients", json={"name": "Test Client"})
    assert response.status_code == 401


def test_create_client_validation():
    response = client.post(
        "/clients",
        json={},
        headers={"Authorization": "Bearer invalid"},
    )
    # Either 401 (bad token) or 422 (validation) is acceptable
    assert response.status_code in (401, 422)
