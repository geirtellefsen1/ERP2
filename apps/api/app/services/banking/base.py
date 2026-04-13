"""Abstract banking adapter and value objects."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Optional

from app.services.money import Money


TransactionDirection = Literal["inflow", "outflow"]


@dataclass
class BankAccount:
    """A linked bank account at a provider."""
    provider_account_id: str       # Aiia/Tink/OP account ID
    iban: str
    currency: str
    bank_name: str
    account_name: str
    balance: Optional[Money] = None
    last_synced_at: Optional[datetime] = None


@dataclass
class BankTransaction:
    """One bank transaction pulled from an open-banking provider."""
    provider_transaction_id: str   # stable external ID for dedup
    account_id: str                # the BankAccount's provider_account_id
    date: date
    amount: Money
    direction: TransactionDirection
    description: str
    counterparty_name: str = ""
    counterparty_account: str = ""
    reference: str = ""
    category: str = ""


class BankingError(Exception):
    """Raised on adapter-level failures (auth, network, rate limit)."""


class BankingAdapter(ABC):
    """Interface every banking provider must implement."""

    provider_name: str

    @abstractmethod
    def list_accounts(self) -> list[BankAccount]:
        """Return all accounts the agency has linked at this provider."""

    @abstractmethod
    def fetch_transactions(
        self,
        account_id: str,
        *,
        since: date,
        until: date,
    ) -> list[BankTransaction]:
        """Fetch transactions for a linked account within a date range."""

    @abstractmethod
    def get_connect_link(
        self,
        *,
        redirect_uri: str,
        state: str,
    ) -> str:
        """
        Return a provider-hosted authorisation URL the user visits to
        link their bank account. After they complete the flow, the
        provider redirects back to `redirect_uri` with an auth code
        that we exchange for a long-lived access token.
        """
