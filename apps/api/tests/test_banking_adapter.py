"""Aiia + MockBankingAdapter tests."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models import Agency
from app.services import integrations as svc
from app.services.banking import (
    AiiaBankingAdapter,
    BankingError,
    MockBankingAdapter,
    get_banking_adapter,
)
from app.services.money import Money


# ── Mock adapter ─────────────────────────────────────────────────────


def test_mock_lists_three_nordic_accounts():
    adapter = MockBankingAdapter()
    accounts = adapter.list_accounts()
    assert len(accounts) == 3
    countries = {a.currency for a in accounts}
    assert countries == {"NOK", "SEK", "EUR"}


def test_mock_account_ibans_have_correct_country_prefix():
    adapter = MockBankingAdapter()
    accounts = {a.currency: a for a in adapter.list_accounts()}
    assert accounts["NOK"].iban.startswith("NO")
    assert accounts["SEK"].iban.startswith("SE")
    assert accounts["EUR"].iban.startswith("FI")


def test_mock_fetch_transactions_returns_window():
    adapter = MockBankingAdapter()
    today = date(2026, 4, 13)
    txs = adapter.fetch_transactions(
        "mock-acct-no-001",
        since=today,
        until=today + timedelta(days=10),
    )
    assert len(txs) > 0
    for t in txs:
        assert today <= t.date <= today + timedelta(days=10)
        assert t.amount.currency == "NOK"


def test_mock_transactions_are_stable_per_account():
    """Same inputs → same IDs → so dedup works."""
    adapter = MockBankingAdapter()
    today = date(2026, 4, 13)
    a = adapter.fetch_transactions(
        "mock-acct-no-001", since=today, until=today + timedelta(days=5)
    )
    b = adapter.fetch_transactions(
        "mock-acct-no-001", since=today, until=today + timedelta(days=5)
    )
    assert {t.provider_transaction_id for t in a} == {
        t.provider_transaction_id for t in b
    }


def test_mock_connect_link_includes_redirect_and_state():
    adapter = MockBankingAdapter()
    url = adapter.get_connect_link(
        redirect_uri="https://erp.tellefsen.org/bank-callback",
        state="csrf-token-abc",
    )
    assert "redirect_uri=" in url
    assert "state=csrf-token-abc" in url


# ── Aiia adapter ─────────────────────────────────────────────────────


def test_aiia_refuses_without_credentials():
    with pytest.raises(BankingError):
        AiiaBankingAdapter(client_id="", client_secret="")


def test_aiia_connect_link_uses_sandbox_url_by_default():
    adapter = AiiaBankingAdapter(
        client_id="demo-aiia-client",
        client_secret="demo-aiia-secret",
    )
    url = adapter.get_connect_link(
        redirect_uri="https://erp.tellefsen.org/bank-callback",
        state="state-xyz",
    )
    assert "api.sandbox.aiia.eu" in url
    assert "clientId=demo-aiia-client" in url
    assert "state=state-xyz" in url


def test_aiia_production_env_uses_live_base_url():
    adapter = AiiaBankingAdapter(
        client_id="prod-client",
        client_secret="prod-secret",
        environment="production",
    )
    assert "api.aiia.eu" in adapter.base_url
    assert "sandbox" not in adapter.base_url


def test_aiia_list_accounts_requires_access_token():
    """Without an access_token, the adapter must raise instead of 401."""
    adapter = AiiaBankingAdapter(
        client_id="x", client_secret="y",
    )
    with pytest.raises(BankingError) as exc:
        adapter.list_accounts()
    assert "access_token" in str(exc.value)


# ── Factory ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_banking_agency(db):
    agency = Agency(name="Banking Test Agency", slug="banking-test-agency")
    db.add(agency)
    db.commit()
    db.refresh(agency)
    return agency


def test_factory_force_mock_returns_mock(db, sample_banking_agency):
    adapter = get_banking_adapter(db, sample_banking_agency.id, force_mock=True)
    assert isinstance(adapter, MockBankingAdapter)


def test_factory_falls_back_to_mock_without_credentials(db, sample_banking_agency):
    adapter = get_banking_adapter(db, sample_banking_agency.id, "aiia")
    assert isinstance(adapter, MockBankingAdapter)


def test_factory_returns_aiia_when_configured(db, sample_banking_agency):
    svc.set_config(
        db,
        sample_banking_agency.id,
        "aiia",
        {
            "client_id": "configured-client",
            "client_secret": "configured-secret",
            "environment": "sandbox",
        },
    )
    adapter = get_banking_adapter(db, sample_banking_agency.id, "aiia")
    assert isinstance(adapter, AiiaBankingAdapter)
    assert adapter.client_id == "configured-client"


def test_factory_unknown_provider_raises(db, sample_banking_agency):
    with pytest.raises(BankingError):
        get_banking_adapter(db, sample_banking_agency.id, "nonexistent")
