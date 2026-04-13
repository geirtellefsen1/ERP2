"""
Mock Nordic identity providers — deterministic sign flows.

Each mock walks the full state machine (pending → user_sign → complete)
so tests that poll status() see the same sequence a real BankID client
would see. Seeded from the real vendor test fixtures so the test data
is actually representative, not hand-waved.
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from .base import (
    IdentityProfile,
    SignRequest,
    SignSession,
    SignStatus,
    SignerAdapter,
    SignerError,
)
from .test_fixtures import (
    FI_TEST_FIXTURE,
    NO_TEST_FIXTURE,
    SE_TEST_FIXTURE,
    TestEnvFixture,
)


class _BaseMockSigner(SignerAdapter):
    """
    Shared mock state machine.

    Each session starts in 'pending', transitions to 'user_sign' on the
    second status poll, and 'complete' on the third. This mimics the
    real polling UX where the client checks every second or two and
    the state advances as the user interacts with their app.
    """

    fixture: TestEnvFixture

    def __init__(self, fail_session_ids: Optional[set[str]] = None):
        self._lock = threading.Lock()
        self._sessions: dict[str, SignSession] = {}
        self._poll_counts: dict[str, int] = {}
        self._fail_session_ids = fail_session_ids or set()

    def start(self, request: SignRequest) -> SignSession:
        session_id = f"mock-{uuid.uuid4()}"
        now = datetime.now(timezone.utc)
        session = SignSession(
            session_id=session_id,
            auto_start_token=uuid.uuid4().hex,
            qr_data=f"mock-qr-{session_id}",
            status="pending",
            created_at=now,
        )
        with self._lock:
            self._sessions[session_id] = session
            self._poll_counts[session_id] = 0
        return session

    def status(self, session_id: str) -> SignSession:
        with self._lock:
            if session_id not in self._sessions:
                raise SignerError(f"Unknown session: {session_id}")
            if session_id in self._fail_session_ids:
                session = self._sessions[session_id]
                session.status = "failed"
                session.error = "Injected test failure"
                return session

            self._poll_counts[session_id] += 1
            count = self._poll_counts[session_id]
            session = self._sessions[session_id]

            if count == 1:
                session.status = "pending"
            elif count == 2:
                session.status = "user_sign"
            else:
                session.status = "complete"
                session.completed_at = datetime.now(timezone.utc)
                session.profile = IdentityProfile(
                    personal_id=self.fixture.personal_id,
                    given_name=self.fixture.given_name,
                    surname=self.fixture.surname,
                    full_name=self.fixture.full_name,
                    signature="mock-base64-signature",
                    ocsp_response="mock-ocsp",
                    country=self.fixture.country,
                )
            return session

    def cancel(self, session_id: str) -> None:
        with self._lock:
            if session_id not in self._sessions:
                raise SignerError(f"Unknown session: {session_id}")
            self._sessions[session_id].status = "cancelled_rp"


class MockNorwegianBankID(_BaseMockSigner):
    provider_name = "mock_bankid_no"
    country = "NO"
    fixture = NO_TEST_FIXTURE


class MockSwedishBankID(_BaseMockSigner):
    provider_name = "mock_bankid_se"
    country = "SE"
    fixture = SE_TEST_FIXTURE


class MockFinnishFTN(_BaseMockSigner):
    provider_name = "mock_ftn_fi"
    country = "FI"
    fixture = FI_TEST_FIXTURE
