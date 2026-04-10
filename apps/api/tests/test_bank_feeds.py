from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# --- Bank Feeds endpoints ---

def test_create_connection_requires_auth():
    response = client.post("/bank-feeds/connections", json={
        "client_id": 1,
        "provider": "truelayer",
        "bank_name": "First National Bank",
        "account_number_masked": "****1234",
    })
    assert response.status_code == 401


def test_list_connections_requires_auth():
    response = client.get("/bank-feeds/connections")
    assert response.status_code == 401


def test_sync_transactions_requires_auth():
    response = client.post("/bank-feeds/sync", json={
        "connection_id": 1,
    })
    assert response.status_code == 401


def test_list_bank_transactions_requires_auth():
    response = client.get("/bank-feeds/transactions")
    assert response.status_code == 401


def test_list_bank_transactions_with_filter_requires_auth():
    response = client.get("/bank-feeds/transactions", params={"match_status": "unmatched"})
    assert response.status_code == 401


# --- Reconciliation endpoints ---

def test_auto_match_requires_auth():
    response = client.post("/reconciliation/auto-match")
    assert response.status_code == 401


def test_suggestions_requires_auth():
    response = client.get("/reconciliation/suggestions", params={"bank_transaction_id": 1})
    assert response.status_code == 401


def test_confirm_match_requires_auth():
    response = client.post("/reconciliation/confirm", json={
        "bank_transaction_id": 1,
        "transaction_id": 1,
    })
    assert response.status_code == 401


def test_exclude_requires_auth():
    response = client.post("/reconciliation/exclude", json={
        "bank_transaction_id": 1,
    })
    assert response.status_code == 401
