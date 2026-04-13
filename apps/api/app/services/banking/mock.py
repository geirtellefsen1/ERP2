"""Mock banking adapter — deterministic test data."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.services.money import Money

from .base import BankAccount, BankingAdapter, BankTransaction


class MockBankingAdapter(BankingAdapter):
    """Returns a fixed set of Nordic-shaped accounts and transactions."""

    provider_name = "mock"

    def list_accounts(self) -> list[BankAccount]:
        return [
            BankAccount(
                provider_account_id="mock-acct-no-001",
                iban="NO9386011117947",
                currency="NOK",
                bank_name="DNB",
                account_name="Driftskonto",
                balance=Money("245830.50", "NOK"),
                last_synced_at=datetime.now(timezone.utc),
            ),
            BankAccount(
                provider_account_id="mock-acct-se-001",
                iban="SE4550000000058398257466",
                currency="SEK",
                bank_name="SEB",
                account_name="Företagskonto",
                balance=Money("318204.75", "SEK"),
                last_synced_at=datetime.now(timezone.utc),
            ),
            BankAccount(
                provider_account_id="mock-acct-fi-001",
                iban="FI2112345600000785",
                currency="EUR",
                bank_name="OP",
                account_name="Yritystili",
                balance=Money("41275.20", "EUR"),
                last_synced_at=datetime.now(timezone.utc),
            ),
        ]

    def fetch_transactions(
        self,
        account_id: str,
        *,
        since: date,
        until: date,
    ) -> list[BankTransaction]:
        # Deterministic synthesis — 5 transactions spanning the window
        currency = {
            "mock-acct-no-001": "NOK",
            "mock-acct-se-001": "SEK",
            "mock-acct-fi-001": "EUR",
        }.get(account_id, "NOK")

        base_day = since
        txs: list[BankTransaction] = []
        samples = [
            ("Salary transfer — April", "Acme Corp", Money("45000", currency), "inflow"),
            ("Adobe Creative Cloud", "Adobe Inc", Money("899", currency), "outflow"),
            ("Office rent", "Property Mgmt", Money("18000", currency), "outflow"),
            ("Client payment INV-2026-0008", "TechStart Ltd", Money("12500", currency), "inflow"),
            ("Coffee & snacks", "Espresso House", Money("185", currency), "outflow"),
        ]
        for i, (desc, counterparty, amount, direction) in enumerate(samples):
            day = base_day + timedelta(days=i)
            if day > until:
                break
            txs.append(
                BankTransaction(
                    provider_transaction_id=f"mock-tx-{account_id}-{i}",
                    account_id=account_id,
                    date=day,
                    amount=amount,
                    direction=direction,
                    description=desc,
                    counterparty_name=counterparty,
                    reference=f"MOCK-REF-{i:04d}",
                )
            )
        return txs

    def get_connect_link(
        self,
        *,
        redirect_uri: str,
        state: str,
    ) -> str:
        return f"https://example.invalid/mock-connect?redirect_uri={redirect_uri}&state={state}"
