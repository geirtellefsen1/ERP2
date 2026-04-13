"""
Swedish BankID adapter.

Real Swedish BankID integration uses an mTLS connection to
https://appapi2.test.bankid.com/rp/v6.0 (test) or
https://appapi2.bankid.com/rp/v6.0 (production) with a client
certificate bundle (.p12) issued to the Relying Party by the RP's
bank.

Test certificates are PUBLIC — passphrase "qwerty123", documented at
https://www.bankid.com/en/utvecklare/test. That's why the test
fixtures file includes the real passphrase value.

This adapter raises SignerError on live calls until the p12 bundle
is actually loaded; MockSwedishBankID handles dev and CI flows.
"""
from __future__ import annotations

from typing import Optional

from .base import (
    SignerAdapter,
    SignerError,
    SignRequest,
    SignSession,
)
from .test_fixtures import SE_TEST_FIXTURE


class SwedishBankID(SignerAdapter):
    provider_name = "bankid_se"
    country = "SE"

    def __init__(
        self,
        rp_certificate: str,
        rp_passphrase: str,
        environment: str = "test",
    ):
        if not (rp_certificate and rp_passphrase):
            raise SignerError(
                "SwedishBankID requires rp_certificate (base64 .p12) and "
                "rp_passphrase. Fill these in via Settings → Integrations "
                "→ BankID (Sweden). Test environment uses the documented "
                "vendor .p12 with passphrase 'qwerty123'."
            )
        self.rp_certificate = rp_certificate
        self.rp_passphrase = rp_passphrase
        self.environment = environment
        self.base_url = (
            "https://appapi2.bankid.com/rp/v6.0"
            if environment == "production"
            else SE_TEST_FIXTURE.base_url
        )

    def start(self, request: SignRequest) -> SignSession:
        raise SignerError(
            "Live Swedish BankID is not yet implemented. Certificate "
            "loading + mTLS wiring pending. Use MockSwedishBankID in dev."
        )

    def status(self, session_id: str) -> SignSession:
        raise SignerError("Live Swedish BankID is not yet implemented.")

    def cancel(self, session_id: str) -> None:
        raise SignerError("Live Swedish BankID is not yet implemented.")
