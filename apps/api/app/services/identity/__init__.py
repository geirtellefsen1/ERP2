"""
Electronic identity / signing providers.

Each Nordic country has its own strong-authentication and e-signing
infrastructure:

  - Norway:  BankID (Vipps-owned), RP talks to Merchant API
  - Sweden:  BankID Relying Party API over mTLS with a .p12 certificate
  - Finland: FTN (Finnish Trust Network) via OIDC

All three implement the same SignerAdapter interface so the router
layer doesn't care which one it's talking to. Mock adapters exist for
each so tests can exercise full sign flows without real certificates.
"""
from .base import (
    SignerAdapter,
    SignerError,
    SignRequest,
    SignSession,
    SignStatus,
    IdentityProfile,
)
from .mock import MockNorwegianBankID, MockSwedishBankID, MockFinnishFTN
from .no_bankid import NorwegianBankID
from .se_bankid import SwedishBankID
from .fi_ftn import FinnishFTN
from .factory import get_signer

__all__ = [
    "SignerAdapter",
    "SignerError",
    "SignRequest",
    "SignSession",
    "SignStatus",
    "IdentityProfile",
    "MockNorwegianBankID",
    "MockSwedishBankID",
    "MockFinnishFTN",
    "NorwegianBankID",
    "SwedishBankID",
    "FinnishFTN",
    "get_signer",
]
