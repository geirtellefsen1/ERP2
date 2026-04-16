"""
Tests for the Stripe billing webhook endpoint.

Covers signature verification, the three handled event types, and the
unknown-event fallback path.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

WEBHOOK_URL = "/api/v1/billing/stripe/webhook"


def _make_stripe_event(event_type: str, object_id: str = "obj_123") -> dict:
    """Return a dict shaped like a Stripe Event."""
    return {
        "id": "evt_test",
        "type": event_type,
        "data": {
            "object": {
                "id": object_id,
            }
        },
    }


# -- Valid webhook handling ---------------------------------------------------


@patch("app.services.billing.stripe_client.stripe.Webhook.construct_event")
def test_webhook_checkout_session_completed(mock_construct):
    event = _make_stripe_event("checkout.session.completed", "cs_abc")
    mock_construct.return_value = event

    resp = client.post(
        WEBHOOK_URL,
        content=b'{"fake":"payload"}',
        headers={"stripe-signature": "sig_valid"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    mock_construct.assert_called_once()


@patch("app.services.billing.stripe_client.stripe.Webhook.construct_event")
def test_webhook_subscription_updated(mock_construct):
    event = _make_stripe_event("customer.subscription.updated", "sub_xyz")
    mock_construct.return_value = event

    resp = client.post(
        WEBHOOK_URL,
        content=b'{"fake":"payload"}',
        headers={"stripe-signature": "sig_valid"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("app.services.billing.stripe_client.stripe.Webhook.construct_event")
def test_webhook_invoice_paid(mock_construct):
    event = _make_stripe_event("invoice.paid", "in_999")
    mock_construct.return_value = event

    resp = client.post(
        WEBHOOK_URL,
        content=b'{"fake":"payload"}',
        headers={"stripe-signature": "sig_valid"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# -- Unknown event type -------------------------------------------------------


@patch("app.services.billing.stripe_client.stripe.Webhook.construct_event")
def test_webhook_unknown_event_returns_ignored(mock_construct):
    event = _make_stripe_event("some.unknown.event")
    mock_construct.return_value = event

    resp = client.post(
        WEBHOOK_URL,
        content=b'{"fake":"payload"}',
        headers={"stripe-signature": "sig_valid"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ignored"}


# -- Signature verification failure -------------------------------------------


@patch("app.services.billing.stripe_client.stripe.Webhook.construct_event")
def test_webhook_invalid_signature_returns_400(mock_construct):
    mock_construct.side_effect = Exception("Signature verification failed")

    resp = client.post(
        WEBHOOK_URL,
        content=b'{"fake":"payload"}',
        headers={"stripe-signature": "sig_bad"},
    )

    assert resp.status_code == 400
    assert "Signature verification failed" in resp.json()["detail"]


# -- Invalid payload ----------------------------------------------------------


@patch("app.services.billing.stripe_client.stripe.Webhook.construct_event")
def test_webhook_invalid_payload_returns_400(mock_construct):
    mock_construct.side_effect = ValueError("Invalid payload")

    resp = client.post(
        WEBHOOK_URL,
        content=b'not json',
        headers={"stripe-signature": "sig_whatever"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid payload"
