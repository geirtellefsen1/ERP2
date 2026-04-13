"""Tests for the delivery service (mock + factory)."""
from __future__ import annotations

import pytest

from app.services.delivery import (
    EmailDelivery,
    DeliveryReceipt,
    MockDeliverer,
    get_deliverer,
    DeliveryError,
)


@pytest.fixture(autouse=True)
def _clear_mock():
    MockDeliverer.clear()
    yield
    MockDeliverer.clear()


def test_get_deliverer_mock_returns_mock():
    d = get_deliverer(mode="mock")
    assert isinstance(d, MockDeliverer)


def test_get_deliverer_live_raises_with_clear_message():
    with pytest.raises(DeliveryError) as exc:
        get_deliverer(mode="live")
    assert "RESEND_API_KEY" in str(exc.value) or "not yet implemented" in str(exc.value).lower()


def test_get_deliverer_unknown_mode_raises():
    with pytest.raises(DeliveryError):
        get_deliverer(mode="something-else")  # type: ignore[arg-type]


def test_mock_send_returns_sent_receipt():
    d = MockDeliverer()
    receipt = d.send(
        EmailDelivery(
            to="admin@acme.no",
            subject="Test",
            body_text="hello",
        )
    )
    assert receipt.status == "sent"
    assert receipt.provider == "mock"
    assert receipt.to == "admin@acme.no"
    assert receipt.message_id.startswith("mock-")


def test_mock_records_deliveries():
    d = MockDeliverer()
    d.send(EmailDelivery(to="a@b.c", subject="A", body_text="x"))
    d.send(EmailDelivery(to="d@e.f", subject="B", body_text="y"))

    all_deliveries = MockDeliverer.all_deliveries()
    assert len(all_deliveries) == 2
    assert all_deliveries[0][0].subject == "A"
    assert all_deliveries[1][0].subject == "B"


def test_mock_last_returns_most_recent():
    d = MockDeliverer()
    d.send(EmailDelivery(to="first@x.com", subject="First", body_text="x"))
    d.send(EmailDelivery(to="second@x.com", subject="Second", body_text="x"))
    last = MockDeliverer.last()
    assert last is not None
    delivery, receipt = last
    assert delivery.subject == "Second"
    assert receipt.to == "second@x.com"


def test_mock_supports_attachments():
    d = MockDeliverer()
    pdf_bytes = b"%PDF-fake-content-bytes"
    d.send(
        EmailDelivery(
            to="admin@acme.no",
            subject="Report",
            body_text="See attached",
            attachments=[("acme-march-2026.pdf", pdf_bytes)],
        )
    )
    last = MockDeliverer.last()
    assert last is not None
    delivery, _ = last
    assert len(delivery.attachments) == 1
    name, content = delivery.attachments[0]
    assert name == "acme-march-2026.pdf"
    assert content == pdf_bytes


def test_mock_clear_resets_state():
    d = MockDeliverer()
    d.send(EmailDelivery(to="a@b.c", subject="X", body_text="y"))
    assert len(MockDeliverer.all_deliveries()) == 1
    MockDeliverer.clear()
    assert len(MockDeliverer.all_deliveries()) == 0
