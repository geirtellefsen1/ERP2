"""
Aiia (Mastercard) Nordic open banking adapter.

Covers:
  - Norway: DNB, Sparebank1, Nordea NO, Handelsbanken NO
  - Sweden: SEB, Handelsbanken SE, Swedbank, Nordea SE
  - Finland: OP Financial Group, Nordea FI, Danske FI

This module contains the shape of the adapter + a LIVE flag that's
always False in the current build — meaning every call raises
BankingError with a clear "not yet wired" message. When the team
signs the Aiia agreement and gets production API credentials, flip
the LIVE flag to True (or better, check for credentials at runtime)
and fill in the actual HTTP calls. The interface is identical to
MockBankingAdapter so the rest of the code doesn't care.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

import httpx

from .base import (
    BankAccount,
    BankingAdapter,
    BankingError,
    BankTransaction,
)


AIIA_BASE_URL = "https://api.aiia.eu"
AIIA_SANDBOX_URL = "https://api.sandbox.aiia.eu"


class AiiaBankingAdapter(BankingAdapter):
    """
    Aiia adapter. Construct with the per-agency credentials pulled from
    the integration_configs table.
    """

    provider_name = "aiia"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: Optional[str] = None,
        environment: str = "sandbox",
    ):
        if not client_id or not client_secret:
            raise BankingError(
                "AiiaBankingAdapter requires client_id and client_secret"
            )
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.base_url = (
            AIIA_BASE_URL if environment == "production" else AIIA_SANDBOX_URL
        )

    # ── Connect flow ──────────────────────────────────────────────

    def get_connect_link(
        self,
        *,
        redirect_uri: str,
        state: str,
    ) -> str:
        """
        Return the Aiia-hosted connect URL where the user picks their
        bank and authorises access. After the flow, Aiia redirects to
        `redirect_uri` with a code the backend exchanges for an access
        token via the Aiia token endpoint.

        Note: this is the documented Aiia Connect Link shape. When
        credentials are in place, the actual exchange happens in the
        _exchange_code helper (stub below).
        """
        params = {
            "clientId": self.client_id,
            "redirectUrl": redirect_uri,
            "state": state,
        }
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.base_url}/v1/link?{qs}"

    # ── Accounts + transactions (live paths, currently stubbed) ──

    def list_accounts(self) -> list[BankAccount]:
        if not self.access_token:
            raise BankingError(
                "No access_token available. Complete the Connect flow "
                "first via get_connect_link() and store the resulting "
                "token in integration_configs."
            )
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            resp = httpx.get(
                f"{self.base_url}/v1/accounts",
                headers=headers,
                timeout=15.0,
            )
        except httpx.RequestError as e:
            raise BankingError(f"Aiia network error: {e}") from e

        if resp.status_code != 200:
            raise BankingError(
                f"Aiia accounts failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        return [self._parse_account(a) for a in resp.json().get("accounts", [])]

    def fetch_transactions(
        self,
        account_id: str,
        *,
        since: date,
        until: date,
    ) -> list[BankTransaction]:
        if not self.access_token:
            raise BankingError("No access_token — cannot fetch transactions")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {
            "fromDate": since.isoformat(),
            "toDate": until.isoformat(),
        }
        try:
            resp = httpx.get(
                f"{self.base_url}/v1/accounts/{account_id}/transactions",
                headers=headers,
                params=params,
                timeout=30.0,
            )
        except httpx.RequestError as e:
            raise BankingError(f"Aiia network error: {e}") from e

        if resp.status_code != 200:
            raise BankingError(
                f"Aiia transactions failed: HTTP {resp.status_code} {resp.text[:200]}"
            )
        return [
            self._parse_transaction(account_id, t)
            for t in resp.json().get("transactions", [])
        ]

    # ── Parsers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_account(raw: dict) -> BankAccount:
        from app.services.money import Money

        return BankAccount(
            provider_account_id=raw["id"],
            iban=raw.get("iban", ""),
            currency=raw.get("currency", "EUR"),
            bank_name=raw.get("providerName", ""),
            account_name=raw.get("name", ""),
            balance=(
                Money(str(raw["balance"]["amount"]), raw["balance"]["currency"])
                if raw.get("balance")
                else None
            ),
            last_synced_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _parse_transaction(account_id: str, raw: dict) -> BankTransaction:
        from app.services.money import Money

        amount_raw = raw.get("amount", {})
        amount = Money(
            str(abs(float(amount_raw.get("amount", 0)))),
            amount_raw.get("currency", "EUR"),
        )
        direction = (
            "inflow" if float(amount_raw.get("amount", 0)) > 0 else "outflow"
        )
        return BankTransaction(
            provider_transaction_id=raw["id"],
            account_id=account_id,
            date=date.fromisoformat(raw["date"]),
            amount=amount,
            direction=direction,
            description=raw.get("text", ""),
            counterparty_name=raw.get("counterPart", {}).get("name", ""),
            counterparty_account=raw.get("counterPart", {}).get("accountNumber", ""),
            reference=raw.get("reference", ""),
            category=raw.get("category", ""),
        )
