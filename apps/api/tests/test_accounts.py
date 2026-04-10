from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_accounts_requires_auth():
    response = client.get("/accounts/client/1")
    assert response.status_code == 401


def test_get_hierarchy_requires_auth():
    response = client.get("/accounts/client/1/hierarchy")
    assert response.status_code == 401


def test_create_account_requires_auth():
    response = client.post("/accounts", json={
        "client_id": 1,
        "account_number": "9999",
        "name": "Test",
        "account_type": "asset",
    })
    assert response.status_code == 401


def test_list_coa_templates():
    response = client.get("/coa-import/templates")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert len(data["templates"]) >= 3
