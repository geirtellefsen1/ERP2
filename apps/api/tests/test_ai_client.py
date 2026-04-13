"""Tests for the shared Claude client wrapper."""
from __future__ import annotations

import pytest

from app.services.ai import (
    ClaudeMessage,
    ClaudeError,
    MockClaudeClient,
    LiveClaudeClient,
    get_claude_client,
    set_claude_client,
    reset_claude_client,
)


@pytest.fixture(autouse=True)
def _reset_factory():
    reset_claude_client()
    yield
    reset_claude_client()


# ── MockClaudeClient ──────────────────────────────────────────────────────


def test_mock_returns_canned_response():
    client = MockClaudeClient(canned_response="hello world")
    response = client.complete(
        system="be helpful",
        messages=[ClaudeMessage(role="user", content="hi")],
    )
    assert response.text == "hello world"
    assert response.input_tokens == 100
    assert response.output_tokens == 50


def test_mock_records_calls():
    client = MockClaudeClient(canned_response="ok")
    client.complete(
        system="sys",
        messages=[ClaudeMessage(role="user", content="msg")],
        model="claude-opus-4-6",
        max_tokens=2048,
        temperature=0.3,
    )
    assert len(client.calls) == 1
    call = client.last_call()
    assert call.system == "sys"
    assert call.messages[0].content == "msg"
    assert call.model == "claude-opus-4-6"
    assert call.max_tokens == 2048
    assert call.temperature == 0.3


def test_mock_appends_language_directive_to_system():
    client = MockClaudeClient(canned_response="ok")
    client.complete(
        system="You analyse financials.",
        messages=[ClaudeMessage(role="user", content="x")],
        language="nb-NO",
    )
    call = client.last_call()
    assert "You analyse financials." in call.system
    assert "nb-NO" in call.system


def test_mock_no_language_no_directive():
    client = MockClaudeClient()
    client.complete(
        system="plain",
        messages=[ClaudeMessage(role="user", content="x")],
    )
    call = client.last_call()
    assert call.system == "plain"


def test_mock_reset_clears_calls():
    client = MockClaudeClient()
    client.complete(system="a", messages=[ClaudeMessage(role="user", content="b")])
    assert len(client.calls) == 1
    client.reset()
    assert client.calls == []


# ── LiveClaudeClient guards ──────────────────────────────────────────────


def test_live_client_refuses_test_placeholder_key():
    """LiveClaudeClient must not be instantiable with a test key — would
    burn API credit and fail intermittently in CI."""
    with pytest.raises(ClaudeError) as exc:
        LiveClaudeClient(api_key="sk-ant-test-key-placeholder-for-jwt-signing-00")
    assert "MockClaudeClient" in str(exc.value)


def test_live_client_refuses_empty_key():
    with pytest.raises(ClaudeError):
        LiveClaudeClient(api_key="")


# ── Factory ──────────────────────────────────────────────────────────────


def test_factory_returns_mock_when_no_real_key():
    """In test env (CLAUDE_API_KEY is a placeholder), factory falls back to mock."""
    client = get_claude_client()
    assert isinstance(client, MockClaudeClient)


def test_factory_returns_injected_client():
    custom = MockClaudeClient(canned_response="custom-response-12345")
    set_claude_client(custom)
    client = get_claude_client()
    assert client is custom
    assert client.complete(
        system="x",
        messages=[ClaudeMessage(role="user", content="y")],
    ).text == "custom-response-12345"


def test_factory_reset_restores_default():
    set_claude_client(MockClaudeClient(canned_response="injected"))
    assert get_claude_client().complete(
        system="x", messages=[ClaudeMessage(role="user", content="y")]
    ).text == "injected"
    reset_claude_client()
    assert get_claude_client().complete(
        system="x", messages=[ClaudeMessage(role="user", content="y")]
    ).text != "injected"
