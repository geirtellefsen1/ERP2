"""
Finnish Trust Network (FTN) identity adapter.

FTN is an OIDC federation covering the Finnish banks. Each relying
party registers with the FTN at Traficom and receives a client_id /
client_secret pair. The test environment is:

  Authorisation endpoint:
    https://mtls.apitest.finnishtrustnetwork.fi/oauth/authorize
  Token endpoint:
    https://mtls.apitest.finnishtrustnetwork.fi/oauth/token
  Userinfo endpoint:
    https://mtls.apitest.finnishtrustnetwork.fi/oauth/userinfo

Just like Norwegian and Swedish BankID, the live flow is stubbed
until production credentials exist; MockFinnishFTN covers tests.
"""
from __future__ import annotations

from typing import Optional

from .base import (
    SignerAdapter,
    SignerError,
    SignRequest,
    SignSession,
)
from .test_fixtures import FI_TEST_FIXTURE


class FinnishFTN(SignerAdapter):
    provider_name = "ftn_fi"
    country = "FI"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        environment: str = "test",
    ):
        if not (client_id and client_secret):
            raise SignerError(
                "FinnishFTN requires client_id and client_secret from "
                "the Finnish Trust Network registration. Fill these in "
                "via Settings → Integrations → Finnish Trust Network."
            )
        self.client_id = client_id
        self.client_secret = client_secret
        self.environment = environment
        self.base_url = (
            "https://mtls.api.finnishtrustnetwork.fi"
            if environment == "production"
            else FI_TEST_FIXTURE.base_url
        )

    def start(self, request: SignRequest) -> SignSession:
        raise SignerError(
            "Live Finnish Trust Network is not yet implemented. "
            "Use MockFinnishFTN for development and testing."
        )

    def status(self, session_id: str) -> SignSession:
        raise SignerError("Live Finnish FTN is not yet implemented.")

    def cancel(self, session_id: str) -> None:
        raise SignerError("Live Finnish FTN is not yet implemented.")
