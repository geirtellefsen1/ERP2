from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_journals_requires_auth():
    response = client.get("/journals", params={"client_id": 1})
    assert response.status_code == 401


def test_get_journal_requires_auth():
    response = client.get("/journals/1")
    assert response.status_code == 401


def test_create_journal_requires_auth():
    response = client.post("/journals", json={
        "client_id": 1,
        "entry_date": "2026-04-10T00:00:00Z",
        "description": "Test entry",
        "posting_period_id": 1,
        "lines": [
            {"account_id": 1, "debit_amount": 100, "credit_amount": 0},
            {"account_id": 2, "debit_amount": 0, "credit_amount": 100},
        ],
    })
    assert response.status_code == 401


def test_post_journal_requires_auth():
    response = client.post("/journals/1/post")
    assert response.status_code == 401


def test_reverse_journal_requires_auth():
    response = client.post("/journals/1/reverse")
    assert response.status_code == 401


def test_list_posting_periods_requires_auth():
    response = client.get("/posting-periods", params={"client_id": 1})
    assert response.status_code == 401


def test_create_posting_period_requires_auth():
    response = client.post("/posting-periods", json={
        "client_id": 1,
        "period_name": "January 2026",
        "period_start": "2026-01-01T00:00:00Z",
        "period_end": "2026-01-31T23:59:59Z",
    })
    assert response.status_code == 401


def test_close_posting_period_requires_auth():
    response = client.put("/posting-periods/1/close")
    assert response.status_code == 401


def test_lock_posting_period_requires_auth():
    response = client.put("/posting-periods/1/lock")
    assert response.status_code == 401


def test_journal_validator():
    """Test the journal entry validator service."""
    from app.services.journal_validator import validate_entry
    from types import SimpleNamespace

    # Valid entry
    lines = [
        SimpleNamespace(debit_amount=100, credit_amount=0),
        SimpleNamespace(debit_amount=0, credit_amount=100),
    ]
    is_valid, errors = validate_entry(lines)
    assert is_valid is True
    assert errors == []

    # Unbalanced entry
    lines = [
        SimpleNamespace(debit_amount=100, credit_amount=0),
        SimpleNamespace(debit_amount=0, credit_amount=50),
    ]
    is_valid, errors = validate_entry(lines)
    assert is_valid is False
    assert any("not balanced" in e for e in errors)

    # Too few lines
    lines = [
        SimpleNamespace(debit_amount=100, credit_amount=0),
    ]
    is_valid, errors = validate_entry(lines)
    assert is_valid is False
    assert any("at least 2 lines" in e for e in errors)

    # Zero-amount line
    lines = [
        SimpleNamespace(debit_amount=100, credit_amount=0),
        SimpleNamespace(debit_amount=0, credit_amount=0),
        SimpleNamespace(debit_amount=0, credit_amount=100),
    ]
    is_valid, errors = validate_entry(lines)
    assert is_valid is False
    assert any("zero" in e.lower() for e in errors)
