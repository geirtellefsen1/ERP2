"""Factory that selects the right BankingAdapter based on config."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services import integrations as svc
from app.services.banking.aiia import AiiaBankingAdapter
from app.services.banking.base import BankingAdapter, BankingError
from app.services.banking.mock import MockBankingAdapter


def get_banking_adapter(
    db: Session,
    agency_id: int,
    provider: str = "aiia",
    *,
    force_mock: bool = False,
) -> BankingAdapter:
    """
    Return the adapter for a given agency + provider.

    If `force_mock=True` or the provider's config is empty, returns
    MockBankingAdapter so dev/test/demo flows work without real creds.
    """
    if force_mock or provider == "mock":
        return MockBankingAdapter()

    if provider == "aiia":
        config = svc.get_config(db, agency_id, "aiia")
        if not config.get("client_id") or not config.get("client_secret"):
            # Fall back to mock so developers can still exercise the
            # pipeline without a live Aiia account
            return MockBankingAdapter()
        return AiiaBankingAdapter(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            access_token=config.get("access_token"),
            environment=config.get("environment", "sandbox"),
        )

    if provider == "tink":
        # Tink adapter slots in here when needed
        return MockBankingAdapter()

    raise BankingError(f"Unknown banking provider: {provider}")
