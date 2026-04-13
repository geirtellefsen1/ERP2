"""Factory that picks the right signer per country and config state."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services import integrations as svc

from .base import SignerAdapter, SignerError
from .fi_ftn import FinnishFTN
from .mock import MockFinnishFTN, MockNorwegianBankID, MockSwedishBankID
from .no_bankid import NorwegianBankID
from .se_bankid import SwedishBankID


def get_signer(
    db: Session,
    agency_id: int,
    country: str,
    *,
    force_mock: bool = False,
) -> SignerAdapter:
    """
    Return a SignerAdapter for the requested country.

    Uses the live adapter if the per-agency config has usable
    credentials, otherwise falls back to the mock adapter so dev/test
    flows keep working without real vendor accounts.
    """
    cc = country.upper()

    if force_mock:
        return _mock_for(cc)

    if cc == "NO":
        config = svc.get_config(db, agency_id, "bankid_no")
        try:
            return NorwegianBankID(
                merchant_name=config.get("merchant_name", ""),
                client_certificate=config.get("client_certificate", ""),
                client_key=config.get("client_key", ""),
            )
        except SignerError:
            return MockNorwegianBankID()

    if cc == "SE":
        config = svc.get_config(db, agency_id, "bankid_se")
        try:
            return SwedishBankID(
                rp_certificate=config.get("rp_certificate", ""),
                rp_passphrase=config.get("rp_passphrase", ""),
                environment=config.get("environment", "test"),
            )
        except SignerError:
            return MockSwedishBankID()

    if cc == "FI":
        config = svc.get_config(db, agency_id, "ftn_fi")
        try:
            return FinnishFTN(
                client_id=config.get("client_id", ""),
                client_secret=config.get("client_secret", ""),
            )
        except SignerError:
            return MockFinnishFTN()

    raise SignerError(f"No signer available for country: {country}")


def _mock_for(country: str) -> SignerAdapter:
    if country == "NO":
        return MockNorwegianBankID()
    if country == "SE":
        return MockSwedishBankID()
    if country == "FI":
        return MockFinnishFTN()
    raise SignerError(f"No mock signer for country: {country}")
