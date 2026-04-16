"""Tests for the subscription flow and feature-gating middleware.

Covers:
- POST /billing/subscribe (mocked Stripe calls)
- GET  /billing/subscription
- Feature gate: growth tier allows ai_chat
- Feature gate: starter tier blocked from premium features (402)
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import Agency, AgencySubscription
from app.database import SessionLocal

AUTH_HEADERS = {
    "x-user-id": "1",
    "x-agency-id": "1",
    "x-user-email": "admin@test.com",
    "x-user-role": "admin",
}


@pytest.fixture()
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def agency(db: Session) -> Agency:
    a = Agency(id=1, name="Test Agency", slug="test-agency")
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@pytest.fixture()
def client():
    return TestClient(app)


# -- POST /billing/subscribe --------------------------------------------------


@patch("app.routers.billing_stripe.create_subscription")
@patch("app.routers.billing_stripe.create_customer")
def test_subscribe_creates_subscription(
    mock_create_customer: MagicMock,
    mock_create_sub: MagicMock,
    client: TestClient,
    agency: Agency,
):
    mock_create_customer.return_value = {"id": "cus_test123"}
    mock_create_sub.return_value = {
        "id": "sub_test456",
        "status": "active",
        "current_period_end": 1700000000,
    }

    resp = client.post(
        "/api/v1/billing/subscribe",
        json={"tier": "growth"},
        headers=AUTH_HEADERS,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "growth"
    assert data["stripe_customer_id"] == "cus_test123"
    assert data["stripe_subscription_id"] == "sub_test456"
    assert data["status"] == "active"

    mock_create_customer.assert_called_once()
    mock_create_sub.assert_called_once_with("cus_test123", "price_growth_monthly")


# -- GET /billing/subscription ------------------------------------------------


@patch("app.routers.billing_stripe.create_subscription")
@patch("app.routers.billing_stripe.create_customer")
def test_get_subscription(
    mock_create_customer: MagicMock,
    mock_create_sub: MagicMock,
    client: TestClient,
    agency: Agency,
):
    mock_create_customer.return_value = {"id": "cus_abc"}
    mock_create_sub.return_value = {
        "id": "sub_xyz",
        "status": "active",
        "current_period_end": 1700000000,
    }

    # Create a subscription first
    client.post(
        "/api/v1/billing/subscribe",
        json={"tier": "starter"},
        headers=AUTH_HEADERS,
    )

    resp = client.get("/api/v1/billing/subscription", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "starter"
    assert data["agency_id"] == 1


def test_get_subscription_none(client: TestClient, agency: Agency):
    """GET /billing/subscription returns null when no subscription exists."""
    resp = client.get("/api/v1/billing/subscription", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() is None


# -- Feature gate --------------------------------------------------------------


def test_feature_gate_allows_starter_feature(
    client: TestClient, agency: Agency, db: Session
):
    """Growth tier includes 'ai_chat', so the AI endpoint gate should pass."""
    sub = AgencySubscription(
        agency_id=1,
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        tier="growth",
        status="active",
    )
    db.add(sub)
    db.commit()

    # The AI /gl-code endpoint is gated on 'ai_chat' -- growth tier should pass.
    # We expect a downstream error (e.g. 501 for Claude API not configured)
    # rather than 402 (payment required).
    resp = client.post(
        "/api/v1/ai/gl-code",
        json={"description": "Test", "amount": 100, "client_id": 1},
        headers=AUTH_HEADERS,
    )
    # Should NOT be 402 -- the gate passed
    assert resp.status_code != 402


def test_feature_gate_blocks_premium_feature(
    client: TestClient, agency: Agency, db: Session
):
    """Starter tier does NOT include 'ai_chat', so the gate should return 402."""
    sub = AgencySubscription(
        agency_id=1,
        stripe_customer_id="cus_test",
        stripe_subscription_id="sub_test",
        tier="starter",
        status="active",
    )
    db.add(sub)
    db.commit()

    resp = client.post(
        "/api/v1/ai/gl-code",
        json={"description": "Test", "amount": 100, "client_id": 1},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 402
    assert "ai_chat" in resp.json()["detail"]


def test_feature_gate_no_subscription_defaults_starter(
    client: TestClient, agency: Agency
):
    """When no subscription exists, defaults to starter tier -- premium features blocked."""
    resp = client.post(
        "/api/v1/ai/gl-code",
        json={"description": "Test", "amount": 100, "client_id": 1},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 402
