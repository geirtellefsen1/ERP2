"""
Tests for the observability module (Sentry + OpenTelemetry).

These tests verify that:
1. Observability setup does not break normal application startup.
2. The /debug/sentry endpoint returns a 500 (RuntimeError).
3. The X-Trace-Id header is present on responses when OTEL is active.
"""
from __future__ import annotations

import os
import pytest

# Ensure test defaults before importing any app code.
os.environ.setdefault(
    "CLAUDE_API_KEY", "sk-ant-test-key-placeholder-for-jwt-signing-00"
)

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


# ── Basic smoke test ─────────────────────────────────────────────────────────


def test_health_endpoint_still_works(client: TestClient):
    """Observability setup must not break the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# ── Sentry debug endpoint ───────────────────────────────────────────────────


def test_debug_sentry_returns_500(client: TestClient):
    """/debug/sentry should trigger a RuntimeError and return 500."""
    response = client.get("/debug/sentry")
    assert response.status_code == 500


# ── Trace-ID header ─────────────────────────────────────────────────────────


def test_trace_id_header_present(client: TestClient):
    """Responses should include an X-Trace-Id header when OTEL is configured."""
    response = client.get("/health")
    # The header is only present when opentelemetry is installed and the
    # TraceIdMiddleware is active.  We check opportunistically.
    try:
        import opentelemetry  # noqa: F401

        assert "x-trace-id" in response.headers, (
            "X-Trace-Id header missing — is TraceIdMiddleware registered?"
        )
        trace_id = response.headers["x-trace-id"]
        # OTEL trace IDs are 32-char hex strings.
        assert len(trace_id) == 32
        int(trace_id, 16)  # must be valid hex
    except ImportError:
        pytest.skip("opentelemetry not installed — skipping trace-id check")
