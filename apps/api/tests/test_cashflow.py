"""Cashflow forecaster + narrator tests."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.money import Money
from app.services.cashflow import (
    CashflowItem,
    ForecastInput,
    forecast,
    generate_narrative,
)
from app.services.ai import (
    MockClaudeClient,
    set_claude_client,
    reset_claude_client,
)


@pytest.fixture(autouse=True)
def _reset_claude():
    reset_claude_client()
    yield
    reset_claude_client()


# ── Pure forecaster ──────────────────────────────────────────────────────


def test_empty_forecast_holds_opening_balance():
    """13 weeks with no items: every week's closing == opening."""
    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),  # Monday
            items=[],
        )
    )
    assert len(result.weeks) == 13
    assert result.opening_balance == Money("100000", "NOK")
    assert result.closing_balance == Money("100000", "NOK")
    for week in result.weeks:
        assert week.inflows == Money.zero("NOK")
        assert week.outflows == Money.zero("NOK")
        assert week.opening_balance == Money("100000", "NOK")
        assert week.closing_balance == Money("100000", "NOK")


def test_inflow_increases_closing_balance():
    result = forecast(
        ForecastInput(
            opening_balance=Money("50000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(
                    expected_date=date(2026, 4, 15),  # week 0
                    amount=Money("25000", "NOK"),
                    direction="inflow",
                    description="Acme invoice payment",
                ),
            ],
        )
    )
    assert result.weeks[0].inflows == Money("25000", "NOK")
    assert result.weeks[0].closing_balance == Money("75000", "NOK")
    # Subsequent weeks roll the new balance forward
    assert result.weeks[1].opening_balance == Money("75000", "NOK")


def test_outflow_decreases_closing_balance():
    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(
                    expected_date=date(2026, 4, 14),
                    amount=Money("30000", "NOK"),
                    direction="outflow",
                    description="Payroll",
                ),
            ],
        )
    )
    assert result.weeks[0].outflows == Money("30000", "NOK")
    assert result.weeks[0].closing_balance == Money("70000", "NOK")


def test_items_drop_into_correct_week_buckets():
    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),  # Monday week 0
            items=[
                CashflowItem(date(2026, 4, 14), Money("100", "NOK"), "inflow"),  # week 0
                CashflowItem(date(2026, 4, 21), Money("200", "NOK"), "inflow"),  # week 1
                CashflowItem(date(2026, 5, 5), Money("300", "NOK"), "inflow"),   # week 3
            ],
        )
    )
    assert result.weeks[0].inflows == Money("100", "NOK")
    assert result.weeks[1].inflows == Money("200", "NOK")
    assert result.weeks[3].inflows == Money("300", "NOK")
    assert result.weeks[2].inflows == Money.zero("NOK")


def test_items_outside_window_clamp_to_first_or_last():
    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(date(2026, 1, 1), Money("500", "NOK"), "inflow"),  # before start
                CashflowItem(date(2027, 1, 1), Money("700", "NOK"), "inflow"),  # after end
            ],
        )
    )
    assert result.weeks[0].inflows == Money("500", "NOK")
    assert result.weeks[-1].inflows == Money("700", "NOK")


def test_threshold_breach_detection():
    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(date(2026, 4, 14), Money("80000", "NOK"), "outflow"),
            ],
            threshold=Money("50000", "NOK"),
        )
    )
    assert result.has_breach
    assert 0 in result.breach_weeks
    # Subsequent weeks still flagged (running balance stays low)
    assert result.weeks[0].below_threshold


def test_no_breach_when_above_threshold():
    result = forecast(
        ForecastInput(
            opening_balance=Money("200000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(date(2026, 4, 14), Money("10000", "NOK"), "outflow"),
            ],
            threshold=Money("50000", "NOK"),
        )
    )
    assert not result.has_breach
    assert result.breach_weeks == []


def test_confidence_discounts_amount():
    """A 50% confident inflow only contributes half its value."""
    result = forecast(
        ForecastInput(
            opening_balance=Money("0", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(
                    expected_date=date(2026, 4, 14),
                    amount=Money("10000", "NOK"),
                    direction="inflow",
                    confidence=0.5,
                ),
            ],
        )
    )
    assert result.weeks[0].inflows == Money("5000", "NOK")


def test_currency_mismatch_rejected():
    with pytest.raises(ValueError):
        forecast(
            ForecastInput(
                opening_balance=Money("100000", "NOK"),
                forecast_start=date(2026, 4, 13),
                items=[
                    CashflowItem(date(2026, 4, 14), Money("100", "EUR"), "inflow"),
                ],
            )
        )


def test_threshold_currency_mismatch_rejected():
    with pytest.raises(ValueError):
        forecast(
            ForecastInput(
                opening_balance=Money("100000", "NOK"),
                forecast_start=date(2026, 4, 13),
                items=[],
                threshold=Money("50000", "EUR"),
            )
        )


def test_lowest_balance_returns_correct_week():
    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(date(2026, 4, 14), Money("60000", "NOK"), "outflow"),  # w0
                CashflowItem(date(2026, 4, 28), Money("80000", "NOK"), "inflow"),   # w2
            ],
        )
    )
    lowest = result.lowest_balance
    assert lowest is not None
    week_idx, balance = lowest
    # Week 0 ends at 40000 (lowest), week 2 ends at 120000
    assert week_idx in (0, 1)  # weeks 0 and 1 both at 40000
    assert balance == Money("40000", "NOK")


def test_totals_aggregate_correctly():
    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(date(2026, 4, 14), Money("10000", "NOK"), "inflow"),
                CashflowItem(date(2026, 4, 21), Money("15000", "NOK"), "inflow"),
                CashflowItem(date(2026, 4, 28), Money("8000", "NOK"), "outflow"),
            ],
        )
    )
    assert result.total_inflows == Money("25000", "NOK")
    assert result.total_outflows == Money("8000", "NOK")
    assert result.closing_balance == Money("117000", "NOK")


def test_invalid_weeks_count_rejected():
    with pytest.raises(ValueError):
        forecast(
            ForecastInput(
                opening_balance=Money("100000", "NOK"),
                forecast_start=date(2026, 4, 13),
                items=[],
                weeks=0,
            )
        )
    with pytest.raises(ValueError):
        forecast(
            ForecastInput(
                opening_balance=Money("100000", "NOK"),
                forecast_start=date(2026, 4, 13),
                items=[],
                weeks=53,
            )
        )


# ── Narrator (with mocked Claude) ────────────────────────────────────────


def test_narrator_calls_claude_and_returns_text():
    mock = MockClaudeClient(canned_response="Cash looks healthy through week 13.")
    set_claude_client(mock)

    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[],
        )
    )
    narrative = generate_narrative(result, language="nb-NO")
    assert narrative == "Cash looks healthy through week 13."
    assert result.narrative == narrative
    assert len(mock.calls) == 1


def test_narrator_passes_language_to_claude():
    mock = MockClaudeClient(canned_response="ok")
    set_claude_client(mock)

    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[],
        )
    )
    generate_narrative(result, language="nb-NO")
    call = mock.last_call()
    assert call.language == "nb-NO"
    assert "nb-NO" in call.system  # appended directive


def test_narrator_uses_opus_model():
    """Narrative generation is high-stakes — must use the Opus model per spec."""
    mock = MockClaudeClient(canned_response="ok")
    set_claude_client(mock)

    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[],
        )
    )
    generate_narrative(result)
    assert mock.last_call().model == "claude-opus-4-6"


def test_narrator_includes_forecast_data_in_prompt():
    """The user message must contain the actual numbers so Claude can
    reference them. No hallucinated data."""
    mock = MockClaudeClient(canned_response="ok")
    set_claude_client(mock)

    result = forecast(
        ForecastInput(
            opening_balance=Money("123456", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(date(2026, 4, 14), Money("9999", "NOK"), "outflow"),
            ],
        )
    )
    generate_narrative(result)
    user_msg = mock.last_call().messages[0].content
    assert "123456" in user_msg
    assert "9999" in user_msg
    assert "NOK" in user_msg


def test_narrator_includes_threshold_breach_info():
    mock = MockClaudeClient(canned_response="ok")
    set_claude_client(mock)

    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[
                CashflowItem(date(2026, 4, 14), Money("80000", "NOK"), "outflow"),
            ],
            threshold=Money("50000", "NOK"),
        )
    )
    generate_narrative(result)
    user_msg = mock.last_call().messages[0].content
    assert "Threshold breached" in user_msg
    assert "50000" in user_msg


def test_narrator_passes_industry_when_provided():
    mock = MockClaudeClient(canned_response="ok")
    set_claude_client(mock)

    result = forecast(
        ForecastInput(
            opening_balance=Money("100000", "NOK"),
            forecast_start=date(2026, 4, 13),
            items=[],
            client_industry="Hospitality",
        )
    )
    generate_narrative(result, industry="Hospitality")
    user_msg = mock.last_call().messages[0].content
    assert "Hospitality" in user_msg
