from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_profit_loss_requires_auth():
    response = client.get("/reports/profit-loss", params={
        "client_id": 1,
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-03-31T23:59:59Z",
    })
    assert response.status_code == 401


def test_balance_sheet_requires_auth():
    response = client.get("/reports/balance-sheet", params={
        "client_id": 1,
        "as_at": "2026-03-31T23:59:59Z",
    })
    assert response.status_code == 401


def test_trial_balance_requires_auth():
    response = client.get("/reports/trial-balance", params={
        "client_id": 1,
    })
    assert response.status_code == 401


def test_aged_debtors_requires_auth():
    response = client.get("/reports/aged-debtors", params={
        "client_id": 1,
    })
    assert response.status_code == 401
