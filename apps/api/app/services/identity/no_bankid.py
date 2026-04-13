"""
Norwegian BankID adapter (Vipps BankID).

Real Vipps BankID integration requires a commercial agreement with
Vipps MobilePay and an issued merchant ID. Once that exists:
  - Pull merchant_name, client_certificate, client_key from
    integration_configs (provider='bankid_no')
  - Use mTLS + signed JWT bearer against Vipps' merchant API
  - Endpoint base is NO_BANKID_TEST_BASE_URL for preprod,
    https://api.bankid.no/ for production

Until then this adapter raises a clear SignerError on any method so
nothing silently "works" without real credentials. The
MockNorwegianBankID in mock.py is what tests and dev use.
"""
from __future__ import annotations

from typing import Optional

from .base import (
    SignerAdapter,
    SignerError,
    SignRequest,
    SignSession,
)
from .test_fixtures import NO_TEST_FIXTURE


class NorwegianBankID(SignerAdapter):
    provider_name = "bankid_no"
    country = "NO"

    def __init__(
        self,
        merchant_name: str,
        client_certificate: str,
        client_key: str,
        environment: str = "preprod",
    ):
        if not (merchant_name and client_certificate and client_key):
            raise SignerError(
                "NorwegianBankID requires merchant_name, client_certificate, "
                "and client_key. Fill these in via Settings → Integrations → "
                "BankID (Norway)."
            )
        self.merchant_name = merchant_name
        self.client_certificate = client_certificate
        self.client_key = client_key
        self.environment = environment
        self.base_url = (
            "https://api.bankid.no"
            if environment == "production"
            else NO_TEST_FIXTURE.base_url
        )

    def start(self, request: SignRequest) -> SignSession:
        raise SignerError(
            "Live Norwegian BankID is not yet implemented. "
            "Vipps MobilePay merchant agreement and API credentials "
            "are required. Use MockNorwegianBankID for development."
        )

    def status(self, session_id: str) -> SignSession:
        raise SignerError(
            "Live Norwegian BankID is not yet implemented."
        )

    def cancel(self, session_id: str) -> None:
        raise SignerError(
            "Live Norwegian BankID is not yet implemented."
        )
