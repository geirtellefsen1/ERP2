"""Abstract signer / identity verification interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


SignStatus = Literal[
    "pending",          # waiting for the user to open the app
    "user_sign",        # user is signing in the BankID app
    "complete",         # signed successfully
    "failed",           # network/signature failure
    "expired",          # user didn't respond in time
    "cancelled_user",   # user hit cancel
    "cancelled_rp",     # we cancelled programmatically
]


@dataclass
class SignRequest:
    """
    Input to a signing session — what the user is actually signing.

    `personal_id` is the country-specific identity number:
      - Norway:  fnr (11 digits) OR leave blank for "anonymous" sign-in
      - Sweden:  personnummer (12 digits, YYYYMMDD-NNNN)
      - Finland: henkilötunnus (DDMMYYX-NNNC)
    """
    personal_id: str = ""
    user_visible_data: str = ""   # what the user sees in their BankID app
    user_hidden_data: str = ""    # appears in the audit trail, not shown
    client_ip: str = ""
    purpose: str = "authentication"


@dataclass
class SignSession:
    """One in-flight signing session."""
    session_id: str             # provider's order/session reference
    auto_start_token: str = ""  # for mobile deep-linking (Swedish BankID)
    qr_data: str = ""           # QR payload for desktop flow
    status: SignStatus = "pending"
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    profile: Optional["IdentityProfile"] = None
    error: str = ""


@dataclass
class IdentityProfile:
    """Result of a successful sign-in — who the user is."""
    personal_id: str
    given_name: str
    surname: str
    full_name: str
    signature: str = ""      # base64 raw signature bytes
    ocsp_response: str = ""  # OCSP proof, for audit
    country: str = ""


class SignerError(Exception):
    """Raised on any signer failure (network, certificate, user cancelled)."""


class SignerAdapter(ABC):
    """Interface every Nordic identity provider implements."""

    provider_name: str
    country: str

    @abstractmethod
    def start(self, request: SignRequest) -> SignSession: ...

    @abstractmethod
    def status(self, session_id: str) -> SignSession: ...

    @abstractmethod
    def cancel(self, session_id: str) -> None: ...
